# -------------------------------------------------------------------------------
# Name:        RDF parser
# Purpose:     Loads RDF XMLs from zip and xml files to pandas DataFrame in a triplestore manner
#
# Author:      kristjan.vilgo
#
# Created:     13.12.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     GPLv2
# -------------------------------------------------------------------------------
from __future__ import print_function

from io import BytesIO

from lxml import etree
from lxml.builder import ElementMaker
from lxml.etree import QName

import pandas
import datetime
import zipfile
import uuid
import time

from collections import OrderedDict

# from collections import deque

# from multiprocessing import Pool - TODO add parallel loading for import ALL DASK, SPARK, MODIN, VAEX


# pandas.set_option("display.height", 1000)
pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)


# pandas.set_option('display.max_colwidth', -1)

# FUNCTIONS - go down for sample code


def print_duration(text, start_time):
    """Print duration between now and start time
    Input: text, start_time
    Output: duration (in seconds), end_time"""

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print(text, duration)

    return duration, end_time


def remove_prefix(original_string, prefix_string):
    """Removes prefix from a string"""

    prefix_length = len(prefix_string)

    if original_string[0:prefix_length] == prefix_string:
        return original_string[prefix_length:]

    return original_string


def clean_ID(ID):
    """Removes ID prefixes used in CIM - first occourance of 'urn:uuid:', '#_', '_' is replaced by empty string"""

    # TODO - a lot of replacements have been done using replace function, but is it valid that these charecaters are not present in UUID-s? is replace once sufficent?

    # replace_count = 1 # Remove only once the ID prefix string, otherwise we risk of removing characters from within ID
    # clean_ID      = ID.replace("urn:uuid:", "", replace_count).replace("#_", "", replace_count).replace("_", "", replace_count)
    ID = remove_prefix(ID, "urn:uuid:")
    ID = remove_prefix(ID, "#_")
    ID = remove_prefix(ID, "_")

    return ID


def load_RDF_objects_from_XML(path_or_fileobject, debug=False):
    """Parse XML and return iterator of RDF objects and instance ID"""

    # START TIMER
    if debug:
        start_time = datetime.datetime.now()

    # LOAD XML
    parser = etree.XMLParser(remove_comments=True, collect_ids=False, remove_blank_text=True)
    parsed_xml = etree.parse(path_or_fileobject, parser=parser)  # TODO - add iterparse for Python3

    # Get unique ID for loaded instance
    # instance_id = clean_ID(parsed_xml.find("./").attrib.values()[0]) # Lets asume that the first RDF element describes the whole document - TODO replace it with hash of whole XML
    instance_id = str(uuid.uuid4())  # Guarantees unique ID for each loaded instance of data

    if debug:
        _, start_time = print_duration("XML loaded to tree object", start_time)

    # EXTRACT RDF OBJECTS
    RDF_objects = parsed_xml.getroot().iterchildren()

    if debug:
        _, start_time = print_duration("All children put to a generator", start_time)

    return RDF_objects, instance_id


def find_all_xml(list_of_paths_to_zip_globalzip_xml, debug=False):
    """Returns list of XML file objects and/or paths in ZIP file"""

    xml_files_list = []
    zip_files_list = []  # TODO - add support random folders as well

    for item in list_of_paths_to_zip_globalzip_xml:

        item_lower = item.lower()

        if ".xml" in item_lower or ".rdf" in item_lower:
            xml_files_list.append(item)

            if debug:
                print("Added: {}".format(item))

        elif ".zip" in item_lower:
            zip_files_list.append(item)

            if debug:
                print("Added for further processing: {}".format(item))

        else:
            print("WARNING 1 - Not supported file: {}".format(item))

    for zip_file_path in zip_files_list:

        zip_container = zipfile.ZipFile(zip_file_path)
        zipped_files = zip_container.namelist()

        for zipped_file in zipped_files:

            zipped_file_lower = zipped_file.lower()

            if ".xml" in zipped_file_lower or ".rdf" in zipped_file_lower:
                file_object = BytesIO(zip_container.read(zipped_file))
                file_object.name = zipped_file
                xml_files_list.append(file_object)

                if debug:
                    print("INFO - Added: {}".format(zipped_file))

            elif ".zip" in zipped_file_lower:
                zip_files_list.append(BytesIO(zip_container.read(zipped_file)))

                if debug:
                    print("INFO - Added for further processing: {}".format(zipped_file))

            else:
                print("WARNING - Not supported file: {}".format(zipped_file))

    return xml_files_list


def load_RDF_to_list(path_or_fileobject, debug=False):
    """Parse single file to triplestore list"""

    file_name = path_or_fileobject

    if type(path_or_fileobject) != str:
        file_name = path_or_fileobject.name

    print("INFO - Loading {}".format(file_name))

    RDF_objects, INSTANCE_ID = load_RDF_objects_from_XML(path_or_fileobject, debug)

    if debug:
        start_time = datetime.datetime.now()

    # Lets generate list for RDF data and store the original filename under rdf:label
    data_list = [(str(uuid.uuid4()), "label", file_name, INSTANCE_ID)]

    # lets create all variables, so that in loops they are reused, rather than new ones are created, green thinking
    ID = ""
    KEY = ""
    VALUE = ""

    for RDF_object in RDF_objects:

        ID = clean_ID(RDF_object.attrib.values()[0])
        # KEY        = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Type' # If we would like to keep all with correct namespace
        KEY = 'Type'
        VALUE = RDF_object.tag.split("}")[1]
        # VALUE       = etree.QName(object).localname
        # ID_TYPE    = object.attrib.keys()[0].split("}")[1] # Adds column to identifi "ID" and "about" types of ID

        # data_list.append([ID, ID_TYPE, KEY, VALUE]) # If using ID TYPE, maybe also namespace should be kept?
        data_list.append((ID, KEY, VALUE, INSTANCE_ID))

        for element in RDF_object.iterchildren():

            KEY = element.tag.split("}")[1]
            # KEY = etree.QName(element).localname
            VALUE = element.text

            if VALUE is None and len(element.attrib.values()) > 0:
                VALUE = clean_ID(element.attrib.values()[0])

            # data_list.append([ID, ID_TYPE, KEY_NAMESPACE, KEY, VALUE]) # If using ID TYPE
            data_list.append((ID, KEY, VALUE, INSTANCE_ID))

    if debug:
        _, start_time = print_duration("All values put to data list", start_time)

    return data_list


def load_RDF_to_dataframe(path_or_fileobject, debug=False):
    """Parse single file to Pandas DataFrame"""

    data_list = load_RDF_to_list(path_or_fileobject, debug)

    if debug:
        start_time = datetime.datetime.now()

    data = pandas.DataFrame(data_list, columns=["ID", "KEY", "VALUE", "INSTANCE_ID"])

    if debug:
        _, start_time = print_duration("List of data loaded to DataFrame", start_time)

    return data


def load_all_to_dataframe(list_of_paths_to_zip_globalzip_xml, debug=False):
    """Parse contents of provided list of paths to Pandas DataFrame (zip, global zip or XML)"""

    if debug:
        process_start = datetime.datetime.now()

    list_of_xmls = find_all_xml(list_of_paths_to_zip_globalzip_xml, debug)

    data_list = []

    #    TODO - add parallel processing if number inputs is greater than X - to be decided
    #    process_pool = Pool(5)
    #    data_list = sum(process_pool.map(load_RDF_to_list, list_of_xml),[])

    for xml in list_of_xmls:
        data_list.extend(load_RDF_to_list(xml, debug))

    if debug:
        start_time = datetime.datetime.now()

    data = pandas.DataFrame(data_list, columns=["ID", "KEY", "VALUE", "INSTANCE_ID"])

    if debug:
        print_duration("Data list loaded to DataFrame", start_time)
        print_duration("All loaded in ", process_start)
        # print(data.info())

    return data


# Extend this functionality to pandas DataFrame
pandas.read_RDF = load_all_to_dataframe


def type_tableview(data, type_name, string_to_number=True):
    """Creates a table view of all objects of same type, with their parameters in columns"""

    # Get all ID-s of rows where Type == type_name
    type_id = data.query("VALUE == '{}' & KEY == 'Type'".format(type_name))

    if type_id.empty:
        print('WARNING - No data available for {}'.format(type_name))
        return None

    # Filter original data by found type_id data
    type_data = pandas.merge(type_id[["ID"]], data, right_on="ID", left_on="ID").drop_duplicates(["ID",
                                                                                                  "KEY"])  # There can't be duplicate ID and KEY pairs for pivot, but this will lose data on full model DependantOn and other info, solution would be to use pivot table function.

    # Convert form triplets to a table view all objects of same type
    data_view = type_data.pivot(index="ID", columns="KEY")["VALUE"]

    if string_to_number:
        # Convert to data type to numeric in columns that contain only numbers (for easier data usage later on)
        data_view = data_view.apply(pandas.to_numeric, errors='ignore')

    return data_view


# Extend this functionality to pandas DataFrame
pandas.DataFrame.type_tableview = type_tableview


def references_to_simple(data, reference, columns=["Type"]):
    """Creates a table view of all elements that specified element refers to,
    by default returns two columns ID and Type, but this can be extended"""

    reference_data = data.references_to(reference, levels=1).drop_duplicates(["ID_FROM", "KEY"])

    # Convert form triplets to a table view with columns - ID, Type by default
    data_view = reference_data.pivot(index="ID_FROM", columns="KEY")["VALUE"][columns]

    return data_view


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_to_simple = references_to_simple


def references_to(data, reference, levels=1):
    """Return all object pointing towards reference object"""

    # TODO - add the key on which connection was made

    # Get the object itself
    object_data = data.query("ID == '{}'".format(reference)).copy()
    object_data["level"] = 0
    object_data["ID_FROM"] = reference

    # Dataframe where to keep the results
    objects_data = pandas.DataFrame()
    objects_data = objects_data.append(object_data)

    # Add object to processing list
    objects_list = [object_data]
    level = 1

    for object_data in objects_list:

        # End loop if we have reached desired level
        if level > levels:
            break

        # Get column where possible reference to other objects reside
        reference_column = object_data[["ID"]]

        # Filter original data VALUE-s by found references ID-s
        reference_data = pandas.merge(reference_column, data,
                                      left_on="ID",
                                      right_on="VALUE",
                                      suffixes=("_TO", "_FROM"))[["ID_TO", "ID_FROM"]].drop_duplicates("ID_FROM")

        if not reference_data.empty:
            referring_objects = pandas.merge(reference_data, data,
                                             left_on="ID_FROM",
                                             right_on="ID")  # .drop(columns=["ID_FROM"])

            # Add data for future processing
            objects_list.append(referring_objects.copy())

            # Set object level
            referring_objects["level"] = level

            # Add objects to general objects data frame
            objects_data = objects_data.append(referring_objects)

        level += 1

    return objects_data


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_to = references_to


def references_from_simple(data, reference, columns=["Type"]):
    """Creates a table view of all elements that specified element refers to,
    by default returns two columns ID and Type, but this can be extended"""

    reference_data = data.references_from(reference, levels=1).drop_duplicates(["ID_TO", "KEY"])

    # Convert form triplets to a table view with columns - ID, Type by default
    data_view = reference_data.pivot(index="ID_TO", columns="KEY")["VALUE"][columns]

    return data_view


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_from_simple = references_from_simple


def references_from(data, reference, levels=1):
    """Return all triplets that reference object points to"""

    # TODO - add the key on which connection was made

    # Get all values of reference object VALUE columns

    objects_data = pandas.DataFrame()

    object_data = data.query("ID == '{}'".format(reference)).copy()
    # object_data["ID_FROM"] = object_data["ID"]

    objects_list = [object_data]
    level = 0

    for object_data in objects_list:

        # print("{}/{}".format(level, levels))

        # End loop if we have reached desired level
        if level > levels:
            break

        # Set object level
        object_data["level"] = level

        # Add objects to general objects data frame
        objects_data = objects_data.append(object_data)

        # Get column where possible reference to other objects reside
        reference_column = object_data[["ID", "VALUE"]]

        # Filter original data ID-s by values form reference object
        reference_data = pandas.merge(reference_column, data,
                                      left_on="VALUE",
                                      right_on="ID",
                                      suffixes=("_FROM", ""))

        if not reference_data.empty:
            objects_list.append(reference_data.copy())

        level += 1

        objects_data["ID_TO"] = objects_data["ID"]

    return objects_data


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_from = references_from


def references_all(data):
    """Finds all unique references (links, edges, etc.)
    merges data with itself on ID and VALUE
    INSTANCE ID is not taken into account

    returns DataFrame["ID_FROM", "KEY", "ID_TO"]"""

    return data[["ID", "KEY", "VALUE"]].drop_duplicates().merge(data[["ID"]].drop_duplicates(), left_on="VALUE", right_on="ID", suffixes=("_FROM", "_TO"))[["ID_FROM", "KEY", "ID_TO"]]


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_all = references_all


def types_dict(data):
    """Returns dictionary with all types as keys and number of their occurrences as values"""

    types_dictionary = data[(data.KEY == "Type")]["VALUE"].value_counts().to_dict()

    return types_dictionary


# Extend this functionality to pandas DataFrame
pandas.DataFrame.types_dict = types_dict


def set_VALUE_at_KEY(data, key, value):
    """Set all values of provided key to the given value"""  # TODO add debug, to print key, initial value and new value.
    data.loc[data[data.KEY == key].index, "VALUE"] = value  # TODO add changes to change DataFrame


# Extend this functionality to pandas DataFrame
pandas.DataFrame.set_VALUE_at_KEY = set_VALUE_at_KEY


def export_to_excel(data):
    """Exports to excel all data with same INSTACE_ID and if label element exists for it. Each Type is put to a sheet"""
    # TODO add specific folder path
    # TODO set some nice properties - https://xlsxwriter.readthedocs.io/workbook.html#workbook-set-properties

    labels = data.query("KEY == 'label'").iterrows()

    for _, label in labels:
        instance_data = data[data.INSTANCE_ID == label.INSTANCE_ID]

        types = instance_data.types_dict()

        file_name = '{}.xlsx'.format(label.VALUE.split(".")[0])

        print("INFO - Exporting excel: {}".format(file_name))
        writer = pandas.ExcelWriter(file_name)

        for class_type in types:
            class_data = instance_data.type_tableview(class_type)
            class_data.to_excel(writer, class_type)

            # Get sheet to do some formatting
            sheet = writer.sheets[class_type]

            # Set default column size, if this does not work you are missing XslxWriter module
            first_col = 0
            last_col = len(class_data.columns)
            width = 38
            sheet.set_column(first_col, last_col, width)

            # freeze column names and ID column
            sheet.freeze_panes(1, 1)

        writer.save()


# Extend this functionality to pandas DataFrame
pandas.DataFrame.export_to_excel = export_to_excel


def export_to_cimxml(data, rdf_map={}, namespace_map={"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
                     class_KEY="Type",
                     export_undefined=True,
                     export_type="xml_per_instance_zip_per_instance",
                     global_zip_filename="Export.zip",
                     debug=False):
    if debug:
        start_time = datetime.datetime.now()
        init_time = start_time

    # File names are kept under rdfs:lable
    labels = data.query("KEY == 'label'").itertuples()

    # Keep all file names and data to be exported
    export_files = []

    if debug:
        _, start_time = print_duration("All file instance ID-s identified", start_time)

    for label in labels:

        instance_data = data[data.INSTANCE_ID == label.INSTANCE_ID]

        instance_type = instance_data.query("KEY == 'Model.messageType'").VALUE.item()

        instance_rdf_map = rdf_map.get(instance_type, None)

        if instance_rdf_map is None:
            print("WARNING - No rdf mapping available for {}".format(instance_type))
            if not export_undefined:
                print("INFO - File not created for {}".format(label.VALUE))
                continue

        # Create xml element builder and the root element
        E = ElementMaker(nsmap=namespace_map)
        RDF = E(QName(namespace_map["rdf"], "RDF"))

        # Store created xml rdf class elements
        objects = OrderedDict()
        # TODO ensure that the Header class is serialised first

        if debug:
            _, start_time = print_duration("File root generated", start_time)

        # Get objects
        for class_data in instance_data.query("KEY=='{}'".format(class_KEY)).itertuples():

            ID = class_data.ID
            class_name = class_data.VALUE

            # Get class export definition
            class_def = instance_rdf_map.get(class_name, None)

            if class_def is not None:

                class_namespace = class_def["namespace"]
                id_name = class_def["attrib"]["attribute"]
                id_value_prefix = class_def["attrib"]["value_prefix"]

            else:
                print("WARNING - Definition missing for class: {} with {}: ".format(class_name, ID))

                if export_undefined:
                    class_namespace = None
                    id_name = "about"
                    id_value_prefix = "urn:uuid:"
                else:
                    print("INFO - Not Exported")
                    continue

            # Create class element
            # print(class_namespace, class_name) # DEBUG
            rdf_object = E(QName(class_namespace, class_name))
            # Add ID attribute
            rdf_object.attrib[QName(id_name)] = id_value_prefix + ID
            # Add object to RDF
            RDF.append(rdf_object)
            # Add object with it's ID to dict (later we use it to add attributes to that class)
            objects[ID] = rdf_object

        if debug:
            _, start_time = print_duration("Objects added", start_time)

        # Add attribute to objects
        for attribute_data in instance_data.query("KEY!='{}'".format(class_KEY)).itertuples():

            ID = attribute_data.ID
            KEY = attribute_data.KEY
            VALUE = attribute_data.VALUE

            _object = objects.get(ID, None)

            if _object is not None:

                if not pandas.isna(VALUE):

                    tag_def = instance_rdf_map.get(KEY, None)

                    if tag_def is not None:
                        tag = E(QName(tag_def["namespace"], KEY))
                        attrib = tag_def.get("attrib", None)
                        text_prefix = tag_def.get("text", "")

                        if attrib:
                            tag.attrib[QName(attrib["attribute"])] = attrib["value_prefix"] + str(VALUE)
                        else:
                            if text_prefix != "":
                                print(ID, KEY, VALUE)  # DEBUG
                            # tag.text = text_prefix + str(VALUE)
                            tag.text = str(VALUE)

                        _object.append(tag)

                    else:
                        print("Definition missing for tag: " + KEY)

                        if export_undefined:
                            tag = E(KEY)
                            tag.text = str(VALUE)

                            _object.append(tag)


                else:
                    print("Attribute VALUE is None, thus not exported: ID: {} KEY: {}".format(ID, KEY))
                    pass

            else:
                # print("No Object with ID: {}".format(ID))
                pass

        if debug:
            _, start_time = print_duration("Attributes added", start_time)

        # etree.tostring(RDF, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        # print(etree.tostring(RDF, pretty_print=True).decode())

        # Convert to XML
        xml = etree.tostring(RDF, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        # TODO - clean namespaces

        print("INFO - Exporting RDF to {}".format(label.VALUE))

        export_files.append({"filename": label.VALUE, "file": xml})

        if debug:
            _, start_time = print_duration("XML created", start_time)

    # Export XML
    if export_type == "xml_per_instance":
        for export_file in export_files:
            # Write to file
            with open(export_file["filename"], 'w') as file:
                file.write(export_file["file"].decode())
                print('INFO - Saved {}'.format(export_file["filename"]))

    # Export ZIP containing all xml
    if export_type == "xml_per_instance_zip_per_all":
        from zipfile import ZipFile, ZIP_DEFLATED

        with ZipFile(global_zip_filename, mode='w', compression=ZIP_DEFLATED) as zip_file:
            for export_file in export_files:
                zip_file.writestr(export_file["filename"], export_file["file"])

        print('INFO - Saved {}'.format(global_zip_filename))

    # Export each xml in separate zip
    if export_type == "xml_per_instance_zip_per_xml":
        from zipfile import ZipFile, ZIP_DEFLATED

        for export_file in export_files:
            zip_filename = export_file["filename"].replace('.xml', '.zip')
            with ZipFile(zip_filename, mode='w', compression=ZIP_DEFLATED) as zip_file:
                zip_file.writestr(export_file["filename"], export_file["file"])

                print('INFO - Saved {}'.format(zip_filename))

    if debug:
        print_duration("DEBUG - Files saved in", start_time)
        print_duration("DEBUG - Whole Export done in", init_time)


# Extend this functionality to pandas DataFrame
pandas.DataFrame.export_to_cimxml = export_to_cimxml


def get_object_data(data, object_UUID):
    return data.query("ID == '{}'".format(object_UUID)).set_index("KEY")["VALUE"]


pandas.DataFrame.get_object_data = get_object_data


def tableview_to_triplet(data):
    """Makes a triplet of dataview"""
    # TODO add only when tableveiw is created
    return data.reset_index().melt(id_vars="ID", value_name="VALUE", var_name="KEY")


pandas.DataFrame.tableview_to_triplet = tableview_to_triplet

# Let's add empty dataframe to keep changes
pandas.DataFrame.changes = pandas.DataFrame()


def update_triplet_from_triplet(data, update_data, update=True, add=True):
    """Update or add data to current triplet from another one
    VALUE at ID and KEY is updated and KEY ID pair does not exist it is added together with VALUE
    you can control if data is added or updated with parameters update and add, by default both are True"""
    # TODO add changes dataframe, where to keep all changes done by this function
    # TODO create function to do also ID and KEY changes

    report_columns = ["ID", "INSTANCE_ID", "KEY", "VALUE", "VALUE_OLD"]
    write_columns = ["ID", "INSTANCE_ID", "KEY", "VALUE"]

    # Make merge to see what updated data already exists in old and what needs to be added
    test_merge = data.merge(update_data, on=["ID", "KEY"], how='right', indicator=True, suffixes=("_OLD", ""))

    if update:
        # print("Data updated")
        data_to_update = test_merge.query("_merge == 'both'")
        # print(data_to_update[report_columns])   # TODO DEBUG
        # Store changes
        data.changes = data.changes.append(data_to_update[report_columns], ignore_index=True)
        # Get original index for update to work # TODO could be simplified by keeping index at test merge
        old_index_new_value = \
        data.merge(data_to_update[write_columns], on=["ID", "KEY"], how='left', suffixes=("_OLD", "")).dropna()[
            ["VALUE"]]
        data.update(old_index_new_value)
        # TODO compare performance of append + drop vs update

    if add:
        # print("Data added")
        data_to_add = test_merge.query("_merge == 'right_only'")
        # print(data_to_add[report_columns]) # TODO DEBUG
        data = data.append(data_to_add[write_columns], ignore_index=True)
        # Store changes
        data.changes = data.changes.append(data_to_add[report_columns], ignore_index=True)

    return data


pandas.DataFrame.update_triplet_from_triplet = update_triplet_from_triplet


def update_triplet_from_tableview(data, tableview, update=True, add=True):
    """Update or add data to current triplet from a tableview
    VALUE at ID and KEY is updated and KEY ID pair does not exist it is added together with VALUE
    you can control if data is added or updated with parameters update and add, by default both are True"""

    update_triplet = tableview.tableview_to_triplet()
    return update_triplet_from_triplet(data, update_triplet, update, add)


pandas.DataFrame.update_triplet_from_tableview = update_triplet_from_tableview


def export_to_networkx(data):
    """Converts triplet to networkx graph"""
    import networkx

    #  TODO - Add all node data
    #  TODO - Add all supported graph export formats

    edges = data.references_all()
    nodes = data[["ID", "KEY", "VALUE"]].drop_duplicates().query("KEY == 'Type'")[["ID", "VALUE"]]

    graph = networkx.Graph()

    graph.add_nodes_from([(ID, {"Type": VALUE}) for ID, VALUE in nodes.values])
    graph.add_edges_from([(FROM, TO, {"Type": KEY}) for FROM, KEY, TO in edges.values])

    return graph


pandas.DataFrame.to_networkx = export_to_networkx

# END OF FUNCTIONS


# TEST AND EXAMPLES
if __name__ == '__main__':
    path = "test_models/TestConfigurations_packageCASv2.0/RealGrid/CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"

    data = pandas.read_RDF([path], debug=True)  # Last took 0:00:05.481340

    print("Loaded types")
    print(data.query("KEY == 'Type'")["VALUE"].value_counts())

    print("Example how to get table view of all objects of specified type")
    print(data.type_tableview("ACLineSegment"))

    print("Example how to get objects referring to specified object")
    print(data.references_to_simple("99722373_VL_TN1"))

    print("Example how to get objects that specified object refers to")
    print(data.references_from_simple("99722373_VL_TN1"))

    # model = "FlowExample.zip"
    #
    # rdfs = "C:\Users\kristjan.vilgo\Downloads\ENTSOE_CGMES_v2.4.15_04Jul2016_RDFS\EquipmentProfileCoreOperationRDFSAugmented-v2_4_15-4Jul2016.rdf"
    #
    # data = load_all_to_dataframe([model, rdfs])
    #
    #
    # values_in_linesegment = data.query("VALUE == '#ACLineSegment'")
    # values_in_powertransform_end = data.query("VALUE == '#PowerTransformerEnd'")
    # data.query("ID == '#PowerTransformerEnd.r'")
    # data.query("ID == '#Resistance'")
    #
    # data_types = data.query("KEY == 'dataType'")["VALUE"].drop_duplicates()

    # for quick export of data use data[data.VALUE == "PowerTransformer"].to_csv(export.csv) or data[data.VALUE == "PowerTransformer"].to_clipboard() and  paste to excel, for other method refer to pandas manual



