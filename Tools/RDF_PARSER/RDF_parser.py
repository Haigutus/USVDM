#-------------------------------------------------------------------------------
# Name:        RDF parser
# Purpose:     Loads RDF XMLs from zip and xml files to pandas DataFrame in a triplestore manner
#
# Author:      kristjan.vilgo
#
# Created:     13.12.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     GPLv2
#-------------------------------------------------------------------------------
from __future__ import print_function

from io import BytesIO

from lxml import etree
import pandas
import datetime
import zipfile
import uuid

#from collections import deque

#from multiprocessing import Pool - TODO add parallel loading for import ALL DASK, SPARK, MODIN, VAEX


#pandas.set_option("display.height", 1000)
pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)
#pandas.set_option('display.max_colwidth', -1)

# FUNCTIONS - go down for sample code

def print_duration(text, start_time):

    """Print duration between now and start time
    Input: text, start_time
    Output: duration (in seconds), end_time"""

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(text, duration)

    return duration, end_time

def remove_prefix(original_string, prefix_string):
    "Removes prefix from a string"

    prefix_lenght = len(prefix_string)

    if original_string[0:prefix_lenght] == prefix_string:
        return original_string[prefix_lenght:]

    return original_string

def clean_ID(ID):
    """Removes ID prefixes used in CIM - first occourance of 'urn:uuid:', '#_', '_' is replaced by empty string"""

    # TODO - a lot of replacements have been done using replace function, but is it valid that these charecaters are not present in UUID-s? is replace once sufficent?

    #replace_count = 1 # Remove only once the ID prefix string, otherwise we risk of removing characters from within ID
    #clean_ID      = ID.replace("urn:uuid:", "", replace_count).replace("#_", "", replace_count).replace("_", "", replace_count)
    ID = remove_prefix(ID, "urn:uuid:")
    ID = remove_prefix(ID, "#_")
    ID = remove_prefix(ID, "_")

    return ID


def load_RDF_objects_from_XML(path_or_fileobject, debug = False):

    # START TIMER
    if debug:
        start_time = datetime.datetime.now()

    # LOAD XML
    parser     = etree.XMLParser(remove_comments=True, collect_ids=False, remove_blank_text=True)
    parsed_xml = etree.parse(path_or_fileobject, parser = parser)           # TODO - add iterparse for Python3

    # Get unique ID for loaded instance
    instance_id = clean_ID(parsed_xml.find("./").attrib.values()[0]) # Lets asume that the first RDF element describes the whole document - TODO replace it with hash of whole XML

    if debug:
        _, start_time = print_duration("XML loaded to tree object", start_time)


    # EXTRACT RDF OBJECTS
    RDF_objects = parsed_xml.getroot().iterchildren()

    if debug:
        _, start_time = print_duration("All children put to a generator", start_time)



    return RDF_objects, instance_id


def find_all_xmls(list_of_paths_to_zip_globalzip_xml, debug = False):
    """Retunrs list of file objects and/or paths"""

    xml_files_list = []
    zip_files_list = [] # TODO - add support random folders awell

    for item in list_of_paths_to_zip_globalzip_xml:


        item_lower = item.lower()

        if ".xml" in item_lower or ".rdf" in item_lower: # TODO - add item.lower()
            xml_files_list.append(item)

            if debug:
                print("Added: {}".format(item))

        elif ".zip" in item_lower:
            zip_files_list.append(item)

            if debug:
                print("Added for further processing: {}".format(item))

        else: print("WARNING 1 - Not supported file: {}".format(item))


    for zip_file_path in zip_files_list:

        zip_container = zipfile.ZipFile(zip_file_path)
        zipped_files  = zip_container.namelist()

        for zipped_file in zipped_files:

            zipped_file_lower = zipped_file.lower()

            if ".xml" in zipped_file_lower or ".rdf" in zipped_file_lower:
                file_object = BytesIO(zip_container.read(zipped_file))
                file_object.name = zipped_file
                xml_files_list.append(file_object)

                if debug:
                    print("Added: {}".format(zipped_file))

            elif ".zip" in zipped_file_lower:
                zip_files_list.append(BytesIO(zip_container.read(zipped_file)))

                if debug:
                    print("Added for further processing: {}".format(zipped_file))

            else: print("WARNING 2 - Not supported file: {}".format(zipped_file))


    return xml_files_list


def load_RDF_to_list(path_or_fileobject, debug = False):

    file_name = path_or_fileobject

    if type(path_or_fileobject) != str:
        file_name = path_or_fileobject.name

    print("Loading {}".format(file_name))

    RDF_objects, INSTANCE_ID = load_RDF_objects_from_XML(path_or_fileobject, debug)

    if debug:
        start_time = datetime.datetime.now()


    data_list = [(str(uuid.uuid4()), "Lable", file_name, INSTANCE_ID)] # Lets generate list object for all of the RDF data and store the original filename under rdf:Lable

    #lets create all variables, so that in loops they are reused, rather than new ones are created, green thinking
    ID      = ""
    KEY     = ""
    VALUE   = ""

    for object in RDF_objects:

        ID          = clean_ID(object.attrib.values()[0])
        #KEY        = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Type' # If we would like to keep all with correct namespace
        KEY         = 'Type'
        VALUE       = object.tag.split("}")[1]
        #ID_TYPE    = object.attrib.keys()[0].split("}")[1] # Adds column to identifi "ID" and "about" types of ID

        #data_list.append([ID, ID_TYPE, KEY, VALUE]) # If using ID TYPE, maybe also namespace should be kept?
        data_list.append((ID, KEY, VALUE, INSTANCE_ID))

        for element in object.iterchildren():

            KEY = element.tag.split("}")[1]
            VALUE = element.text

            if VALUE == None and len(element.attrib.values()) > 0:

                VALUE = clean_ID(element.attrib.values()[0])

            #data_list.append([ID, ID_TYPE, KEY_NAMESPACE, KEY, VALUE]) # If using ID TYPE
            data_list.append((ID, KEY, VALUE, INSTANCE_ID))

    if debug:
        _,start_time = print_duration("All values put to data list", start_time)

    return data_list



def load_RDF_to_dataframe(path_or_fileobject, debug = False):
    """Parse single file to Pandas DataFrame"""

    data_list = load_RDF_to_list(path_or_fileobject, debug)


    if debug:
        start_time = datetime.datetime.now()

    data = pandas.DataFrame(data_list, columns = ["ID", "KEY", "VALUE", "INSTANCE_ID"])

    if debug:
        _, start_time = print_duration("List of data loaded to DataFrame", start_time)

    return data

def load_all_to_dataframe(list_of_paths_to_zip_globalzip_xml, debug = False):
    """Parse contents of provided list of paths to Pandas DataFrame (zip, global zip or XML)"""

    if debug:
        process_start = datetime.datetime.now()

    list_of_xmls = find_all_xmls(list_of_paths_to_zip_globalzip_xml, debug)

    data_list = []

##    TODO - add paralel processing if number inputs is greater than X - top be decided
##    process_pool = Pool(5)
##    data_list = sum(process_pool.map(load_RDF_to_list, list_of_xmls),[])

    for xml in list_of_xmls:

        data_list.extend(load_RDF_to_list(xml, debug))

    if debug:
        start_time = datetime.datetime.now()

    data = pandas.DataFrame(data_list, columns = ["ID", "KEY", "VALUE", "INSTANCE_ID"])

    if debug:
        print_duration("Data list loaded to DataFrame", start_time)
        print_duration("All loaded in ", process_start)
        #print(data.info())

    return data


def type_tableview(data, type_name):
    """Creates a table view of all objects of same type, with their parameters in columns"""

    # Get all ID-s of rows where Type == type_name
    type_id  = data.query("VALUE == '{}' & KEY == 'Type'".format(type_name))

    # Filter original data by found type_id data
    type_data = pandas.merge(type_id[["ID"]], data, right_on = "ID", left_on = "ID").drop_duplicates(["ID", "KEY"]) # There can't be duplicate ID and KEY pairs for pivot, but this will lose data on full model DependantOn and other info, solution would be to use pivot table function.

    # Convert form triplets to a table view all objects of same type
    data_view = type_data.pivot(index="ID", columns = "KEY")["VALUE"]

    # Convert to data type to numeric in columns that contain only numbers (for easier data usage later on)
    data_view = data_view.apply(pandas.to_numeric, errors='ignore')

    return data_view


# Extend this functionality to pandas DataFrame
pandas.DataFrame.type_tableview = type_tableview


def references_to_simple(data, reference, columns=["Type"]):
    """Creates a table view of all elements that specified element refers to,
    by default returns two columns ID and Type, but this can be extended"""

    reference_data = data.references_to(reference, levels=1).drop_duplicates(["ID", "KEY"])

    # Convert form triplets to a table view with columns - ID, Type by default
    data_view = reference_data.pivot(index="ID", columns="KEY")["VALUE"][columns]

    return data_view

# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_to_simple = references_to_simple


def references_to(data, reference, levels=1):
    """Return all triplets referred by reference object"""

    # Get all values of reference object VALUE columns

    objects_data = pandas.DataFrame()

    object_data = data.query("VALUE == '{}'".format(reference)).copy()

    objects_list = [object_data]
    level = 0

    for object in objects_list:

        # End loop if we have reached desired level
        if level > levels:
            break

        # Set object level
        object["level"] = level

        # Add objects to general objects dataframe
        objects_data = objects_data.append(object)

        # Get column where possible reference to other objects reside
        reference_column = object[["ID"]]

        # Filter original data by found references data
        reference_data = pandas.merge(reference_column, data, on="ID").drop_duplicates(["ID", "KEY"])

        if not reference_data.empty:

            reference_data["ID_TO"] = reference
            objects_list.append(reference_data.copy())

        level +=1

    return objects_data


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_to = references_to


def references_from_simple(data, reference, columns=["Type"]):
    """Creates a table view of all elements that specified element refers to,
    by default returns two columns ID and Type, but this can be extended"""

    reference_data = data.references_from(reference, levels=1).drop_duplicates(["ID", "KEY"])

    # Convert form triplets to a table view with columns - ID, Type by default
    data_view = reference_data.pivot(index="ID", columns="KEY")["VALUE"][columns]

    return data_view


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_from_simple = references_from_simple


def references_from(data, reference, levels=1):
    """Return all triplets referred by reference object"""

    # TODO - add levels

    # Get all values of reference object VALUE columns

    objects_data = pandas.DataFrame()

    object_data = data.query("ID == '{}'".format(reference)).copy()

    objects_list = [object_data]
    level = 0

    for object in objects_list:

        # End loop if we have reached desired level
        if level > levels:
            break

        # Set object level
        object["level"] = level

        # Add objects to general objects dataframe
        objects_data = objects_data.append(object)

        # Get column where possible reference to other objects reside
        reference_column = object[["VALUE"]]

        # Filter original data ID-s by values form reference object
        reference_data = pandas.merge(reference_column, data,
                                      left_on="VALUE",
                                      right_on="ID",
                                      suffixes=("_FROM",""))

        if not reference_data.empty:

            reference_data["ID_FROM"] = reference
            objects_list.append(reference_data.copy())

        level +=1

    return objects_data


# Extend this functionality to pandas DataFrame
pandas.DataFrame.references_from = references_from


def types_dict(data):
    """Returns dictionary with all types as keys and number of their occurrences as values"""

    types_dictionary = data[(data.KEY == "Type")]["VALUE"].value_counts().to_dict()

    return types_dictionary


# Extend this functionality to pandas DataFrame
pandas.DataFrame.types_dict = types_dict


# END OF FUNCTIONS


# TEST AND EXAMPLES
if __name__ == '__main__':

    path = "TestConfigurations_packageCASv2.0/RealGrid/CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"

    data = load_all_to_dataframe([path], debug = True)

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


