#-------------------------------------------------------------------------------
# Name:        CGMEStools
# Purpose:     Collection of functions to work with CGMES files
#
# Author:      kristjan.vilgo
#
# Created:     10.06.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPLv2
#-------------------------------------------------------------------------------
from __future__ import print_function
import pandas

from uuid import uuid4

from pyvis.network import Network
import pyvis.options as options
import os

import aniso8601

import tempfile

from lxml.builder import ElementMaker
from lxml.etree import QName
from lxml import etree

from collections import OrderedDict
from builtins import str

dependencies = dict(EQ   = ["EQBD"],
                    SSH  = ["EQ"],
                    TP   = ["EQ"],
                    SV   = ["TPBD", "TP", "SSH"],
                    TPBD = ["EQBD"],
                    EQBD = [])

def generate_instances_ID(dependencies=dependencies):
    """Generate UUID for each profile defined in dependencies dict"""
    return {profile: str(uuid4()) for profile in dependencies}


def get_metadata_from_filename(file_name):

    # Separators
    file_type_separator           = "."
    meta_separator                = "_"
    entity_and_domain_separator   = "-"

    #print(file_name)
    file_metadata = {}
    file_name, file_type = file_name.split(file_type_separator)

    # Parse file metadata
    file_meta_list = file_name.split(meta_separator)

    # Naming before QoDC 2.1, where EQ might not have processType
    if len(file_meta_list) == 4:

        file_metadata["Model.scenarioTime"],\
        file_metadata["Model.modelingEntity"],\
        file_metadata["Model.messageType"],\
        file_metadata["Model.version"] = file_meta_list
        file_metadata["Model.processType"] = ""

        print("Warning - only 4 meta elements found, expecting 5, setting Model.processType to empty string")

    # Naming after QoDC 2.1, always 5 positions
    elif len(file_meta_list) == 5:

        file_metadata["Model.scenarioTime"],\
        file_metadata["Model.processType"],\
        file_metadata["Model.modelingEntity"],\
        file_metadata["Model.messageType"],\
        file_metadata["Model.version"] = file_meta_list

    else:
        print("Non CGMES file {}".format(file_name))

    if file_metadata.get("Model.modelingEntity", False):

        entity_and_area_list = file_metadata["Model.modelingEntity"].split(entity_and_domain_separator)

        if len(entity_and_area_list) == 1:
            file_metadata["Model.mergingEntity"],\
            file_metadata["Model.domain"] = "", "" # Set empty string for both
            file_metadata["Model.forEntity"] = entity_and_area_list[0]

        if len(entity_and_area_list) == 2:
            file_metadata["Model.mergingEntity"],\
            file_metadata["Model.domain"] = entity_and_area_list
            file_metadata["Model.forEntity"] = ""

        if len(entity_and_area_list) == 3:
            file_metadata["Model.mergingEntity"],\
            file_metadata["Model.domain"],\
            file_metadata["Model.forEntity"] = entity_and_area_list


    return file_metadata


default_filename_mask = "{scenarioTime:%Y%m%dT%H%MZ}_{processType}_{modelingEntity}_{messageType}_{version:03d}"


def get_filename_from_metadata(meta_data, file_type="xml", filename_mask=default_filename_mask):

    """Convert metadata to filename by using filename mask and file type"""
    # Separators
    file_type_separator = "."
    meta_separator = "_"
    entity_and_area_separator = "-"

    # Remove Model. form dictionary as python string format can't use . in variable name
    meta_data = {key.split(".")[1]:meta_data[key] for key in meta_data}

    # DateTime fields from text to DateTime
    DateTime_fields = ["scenarioTime", 'created']
    for field in DateTime_fields:
        meta_data[field] = aniso8601.parse_datetime(meta_data[field])

    # Integers to integers
    meta_data["version"] = int(meta_data["version"])

    # Add metadata to file name string
    file_name = filename_mask.format(**meta_data)

    # Add file type to file name string
    file_name = file_type_separator.join([file_name, file_type])

    return file_name


def get_metadata_from_xml(filepath_or_fileobject):

    parsed_xml = etree.parse(filepath_or_fileobject)

    header = parsed_xml.find("{*}FullModel")
    meta_elements = header.getchildren()

    meta_list = []
    for element in meta_elements:
         meta_list.append([element.tag, element.text, element.attrib])

    xml_metadata = pandas.DataFrame(meta_list, columns=["tag", "text", "attrib"])

    return xml_metadata


def get_metadata_from_FullModel(data):
    """Returns all data defined in model header 'FullModel'
    Returns  dictionary -> value = meta['meta_key'] """
    # fileheader metadata keys should be aligned with filename ones

    UUID = data.query("KEY == 'Type' and VALUE == 'FullModel'").ID.to_list()[0]
    metadata = data.get_object_data(UUID).to_dict()
    metadata.pop("Type", None) # Remove Type form metadata

    return metadata


def update_FullModel_from_dict(data, metadata, update=True, add=False):

    additional_meta_list = []

    for row in data.query("KEY == 'Type' and VALUE == 'FullModel'").itertuples():
        for key in metadata:
            additional_meta_list.append({"ID": row.ID, "KEY": key, "VALUE": metadata[key], "INSTANCE_ID": row.INSTANCE_ID})

    update_data = pandas.DataFrame(additional_meta_list)

    return data.update_triplet_from_triplet(update_data, update, add)

def update_FullModel_from_filename(data, parser=get_metadata_from_filename, update=False, add=True):
    """Parses filename from label VALUE and by default adds missing attributes to each FullModel
    you can provide your own parser, has to return dictionary of attribute names and values"""

    additional_meta_list = []

    # For each instance that has label, as label contains the filename
    for label in data.query("KEY == 'label'").itertuples():
        # Parse metadata from filename to dictionary
        metadata = parser(label.VALUE)

        # Create triplets form parsed metadata
        for row in data.query("KEY == 'Type' and VALUE == 'FullModel' and INSTANCE_ID == '{}'".format(label.INSTANCE_ID)).itertuples():
            for key in metadata:
                additional_meta_list.append({"ID": row.ID, "KEY": key, "VALUE": metadata[key], "INSTANCE_ID": row.INSTANCE_ID})

    update_data = pandas.DataFrame(additional_meta_list)

    return data.update_triplet_from_triplet(update_data, update, add)


def update_filename_from_FullModel(data, filename_mask=default_filename_mask, filename_key="label"):
    """Updates the file names kept under RDF label tag by default
     by constructing it from metadata kept in FullModel in each instance"""

    list_of_updates = []

    for _, label in data.query("KEY == '{}'".format(filename_key)).iterrows():
        # Get metadata
        metadata = get_metadata_from_FullModel(data.query("INSTANCE_ID == '{}'".format(label.INSTANCE_ID)))
        # Get new filename
        filename = get_filename_from_metadata(metadata, filename_mask=filename_mask)
        # Set new filename
        # data.loc[_, "VALUE"] = filename
        list_of_updates.append({"ID": label.ID, "KEY": filename_key, "VALUE": filename, "INSTANCE_ID": label.INSTANCE_ID})

    update_data = pandas.DataFrame(list_of_updates)
    return data.update_triplet_from_triplet(update_data, add=False)


def get_loaded_models(data):
    """Retunrs a dicitonary of loaded model parts UUID-s in input DataFrame"""

    FullModel_data = data.query("KEY == 'Model.profile' or KEY == 'Model.DependentOn'")

    SV_iterator = FullModel_data.query("VALUE == 'http://entsoe.eu/CIM/StateVariables/4/1'").iterrows()

    dependancies_dict = {}

    for _, SV in SV_iterator:

        current_dependencies = []

        dependancies_list = [SV.ID]

        for instance in dependancies_list:

            # Append current instance

            INSTANCE_ID = instance
            PROFILES    = FullModel_data.query("ID == '{}' & KEY == 'Model.profile'".format(instance)).VALUE.tolist()

            for PROFILE in PROFILES:
                current_dependencies.append(dict(INSTANCE_ID = INSTANCE_ID, PROFILE = PROFILE))

            # Add newly found dependacies to processing
            dependancies_list.extend(FullModel_data.query("ID == '{}' & KEY == 'Model.DependentOn'".format(instance)).VALUE.tolist())


        dependancies_dict[SV.ID] = pandas.DataFrame(current_dependencies).drop_duplicates()

        #print dependancies_dict


    return dependancies_dict

def get_model_data(data, model_instances_dataframe):
    """Input is one DataFrame of model instances returned by function get_loaded_models"""

    IGM_data = pandas.merge(data, model_instances_dataframe[["INSTANCE_ID"]].drop_duplicates(), right_on="INSTANCE_ID", left_on="INSTANCE_ID")

    return IGM_data



def get_loaded_model_parts(data):
    """Returns a pandas DataFrame of loaded CGMES instance files or model parts with their header (FullModel) data (does not return correct dependant on)"""
    return data.type_tableview("FullModel")


def statistics_GeneratingUnit_types(data):
    """Returns statistics of GeneratingUnit types """

    list_of_generating_units = data.query("KEY == 'GeneratingUnit.initialP'").ID.tolist() # Random compulsory field in all Genrating units
    value_counts = pandas.DataFrame(data[data.ID.isin(list_of_generating_units)].query("KEY == 'Type'")[["ID", "VALUE"]].drop_duplicates()["VALUE"].value_counts())

    #value_counts= pandas.DataFrame(statistics_ConcreteClasses(data).filter(like="Generating")) # Should be faster, but not might find all
    value_counts["TOTAL"] = value_counts.sum()["VALUE"]
    value_counts["%"] = value_counts["VALUE"]/value_counts["TOTAL"]*100

    return value_counts


def get_GeneratingUnits(data):
    """Returns table of GeneratingUnits"""
    return data.merge(data.query("KEY == 'GeneratingUnit.initialP'").ID).drop_duplicates(["ID", "KEY"]).pivot(index="ID", columns="KEY")["VALUE"]


def statistics_ConcreteClasses(data):
    """Returns statistics on all loaded Concrete Classes"""
    value_counts = data.query("KEY == 'Type'")["VALUE"].value_counts()
    return value_counts


def get_diff_between_model_parts(UUID_1, UUID_2):

    diff = data.query("INSTANCE_ID == '{}' or INSTANCE_ID == '{}'".format(UUID_1, UUID_2)).drop_duplicates(["ID", "KEY", "VALUE"], keep=False)

    return diff

def filter_dataframe_by_dataframe(data, filter_data, filter_column_name):
    """Filter triplestore on ID column with another data frame column containing ID-s"""

    class_name = filter_column_name.split(".")[1]
    meta_separator = "_"

    result = pandas.merge(filter_column_name, data, left_on=filter_column_name, right_on="ID", how="inner", suffixes=('', meta_separator + class_name))[["ID_" + class_name, "KEY", "VALUE"]]

    return result

def tableview_by_IDs(data, IDs_dataframe, IDs_column_name):
    """Filters tripelstore by provided IDs and returns tabular view, IDs- as indexes and KEY-s as columns"""
    class_name = IDs_column_name.split(".")[1]
    meta_separator = "_"
    result = pandas.merge(IDs_dataframe, data,
                          left_on  = IDs_column_name,
                          right_on = "ID",
                          how      = "inner",
                          suffixes=('', meta_separator + class_name))\
                          [["ID_" + class_name, "KEY", "VALUE"]].\
                          drop_duplicates(["ID" + meta_separator + class_name, "KEY"]).\
                          pivot(index="ID" + meta_separator + class_name, columns ="KEY")["VALUE"]

    return result


def darw_relations_graph(reference_data, ID_COLUMN, notebook=False):
    """Creates an temporary XML file to visualize relations
            returns  temp filename"""

    node_data = reference_data.drop_duplicates([ID_COLUMN, "KEY"]).pivot(index=ID_COLUMN, columns="KEY")["VALUE"]

    columns = node_data.columns

    if "IdentifiedObject.name" in columns:
        node_data = node_data[["Type", "IdentifiedObject.name"]].rename(columns={"IdentifiedObject.name": "name"})
    elif "Model.profile" in columns:
        node_data = node_data[["Type", "Model.profile"]].rename(columns={"Model.profile": "name"})
    else:
        node_data = node_data[["Type"]]
        node_data["name"] = ""

    # Visulise with pyvis

    graph = Network(directed=True, width="100%", height=750, notebook=notebook)
    # node_name = urlparse(dataframe[dataframe.KEY == "Model.profile"].VALUE.tolist()[0]).path  # FullModel does not have IdentifiedObject.name

    # Add nodes/objects
    for ID, node in node_data.iterrows():
        object_data = reference_data.query("{} == '{}'".format(ID_COLUMN, ID))

        node_name  = u"{} - {}".format(node["Type"], node["name"])
        node_title = object_data[[ID_COLUMN, "KEY", "VALUE", "INSTANCE_ID"]].rename(columns={ID_COLUMN: "ID"}).to_html(index=False) # Add object data table to node hover titel
        node_level = object_data.level.tolist()[0]

        graph.add_node(ID, node_name, title=node_title, size=10, level=node_level)


    # Add connections

    reference_data_columns = reference_data.columns

    if "ID_FROM" in reference_data_columns and "ID_TO" in reference_data_columns:

        connections = list(reference_data[["ID_FROM", "ID_TO"]].dropna().drop_duplicates().to_records(index=False))
        graph.add_edges(connections)

    # Set options

    graph.set_options("""
    var options = {
        "nodes": {
            "shape": "dot",
            "size": 10
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": false
        },
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "LR",
                "sortMethod": "directed"
            }
        },
        "interaction": {
            "navigationButtons": true
        },
        "physics": {
            "hierarchicalRepulsion": {
                "centralGravity": 0,
                "springLength": 75,
                "nodeDistance": 145,
                "damping": 0.2
            },
            "maxVelocity": 28,
            "minVelocity": 0.75,
            "solver": "hierarchicalRepulsion"
        }
    }""")

    # graph.show_buttons()

    graph.set_options = options

    if notebook == False:
        # Change directory to temp
        os.chdir(tempfile.mkdtemp())

        # Create unique filename
        from_UUID = reference_data[ID_COLUMN].tolist()[0]
        file_name = r"{}.html".format(from_UUID)

        # Show graph
        graph.show(file_name)

        # Returns file path
        return os.path.abspath(file_name)

    return graph



def draw_relations_to(UUID, data, notebook=False):
    reference_data = data.references_to(UUID, levels=99)

    ID_COLUMN = "ID"

    return darw_relations_graph(reference_data, ID_COLUMN, notebook)


def draw_relations_from(UUID, data, notebook=False):
    reference_data = data.references_from(UUID, levels=99)

    ID_COLUMN = "ID"

    return darw_relations_graph(reference_data, ID_COLUMN, notebook)

def export_to_cimrdf_depricated(instance_data, rdf_map, namespace_map):

    types = list(instance_data.types_dict())

    print(types)

    header_type = "FullModel"

    # Set Header to first
    types.remove(header_type)
    types.insert(0, header_type)

    # Create xml element builder and the root element
    E = ElementMaker(nsmap=namespace_map)
    RDF = E(QName(namespace_map["rdf"], "RDF"))

    for class_type in types:
        class_data = instance_data.type_tableview(class_type, string_to_number=False).drop(columns="Type")
        class_def = rdf_map.get(class_type, None)

        if class_def:

            for ID, row in class_data.iterrows():

                rdf_object = E(QName(class_def["namespace"], class_type))
                rdf_object.attrib[QName(class_def["attrib"]["attribute"])] = class_def["attrib"]["value_prefix"] + ID

                for KEY, VALUE in row.items():

                    if not pandas.isna(VALUE):

                        tag_def = rdf_map.get(KEY, None)

                        if tag_def:

                            tag = E(QName(tag_def["namespace"], KEY))

                            attrib = tag_def.get("attrib", None)

                            if attrib:
                                tag.attrib[QName(tag_def["attrib"]["attribute"])] = tag_def["attrib"]["value_prefix"] + VALUE
                            else:
                                tag.text = str(VALUE)

                            rdf_object.append(tag)

                        else:
                            print("Definition missing for tag: " + KEY)

                    else:
                        print(
                            "WARNING - VALUE is None at ID-> {} and KEY-> {}, will not be exported".format(ID, KEY))

                RDF.append(rdf_object)

        else:
            print("Definition missing for class: " + class_type)

    # print(etree.tostring(RDF, pretty_print=True).decode())
    return etree.tostring(RDF, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def export_to_cimrdf(instance_data, rdf_map, namespace_map, class_KEY="Type", export_undefined=True):

    # Create xml element builder and the root element
    E = ElementMaker(nsmap=namespace_map)
    RDF = E(QName(namespace_map["rdf"], "RDF"))

    # Store created xml rdf class elements
    objects = OrderedDict()
    # TODO ensure that the Header class is serialised first

    # Get objects
    for _, class_data in instance_data.query("KEY=='{}'".format(class_KEY)).iterrows():

        ID         = class_data["ID"]
        class_name = class_data["VALUE"]

        # Get class export definition
        class_def  = rdf_map.get(class_name, None)

        if class_def is not None:

            class_namespace = class_def["namespace"]
            id_name         = class_def["attrib"]["attribute"]
            id_value_prefix = class_def["attrib"]["value_prefix"]

        else:
            print("WARNING - Definition missing for class: " + class_name + " with ID: " + ID)
            pass

            if export_undefined:
                class_namespace = None
                id_name = "about"
                id_value_prefix = "urn:uuid:"

        # Create class element
        rdf_object = E(QName(class_namespace, class_name))
        # Add ID attribute
        rdf_object.attrib[QName(id_name)] = id_value_prefix + ID
        # Add object to RDF
        RDF.append(rdf_object)
        # Add object with it's ID to dict (later we use it to add attributes to that class)
        objects[ID] = rdf_object


    # Add attribute to objects
    for _, attribute_data in instance_data.query("KEY!='{}'".format(class_KEY)).iterrows():

        ID      = attribute_data["ID"]
        KEY     = attribute_data["KEY"]
        VALUE   = attribute_data["VALUE"]

        _object = objects.get(ID, None)

        if _object is not None:

            if not pandas.isna(VALUE):

                tag_def = rdf_map.get(KEY, None)

                if tag_def:
                    tag     = E(QName(tag_def["namespace"], KEY))
                    attrib  = tag_def.get("attrib", None)

                    if attrib:
                        tag.attrib[QName(attrib["attribute"])] = attrib["value_prefix"] + VALUE
                    else:
                        tag.text = str(VALUE)

                    _object.append(tag)

                else:
                    print("Definition missing for tag: " + KEY)

                    if export_undefined:
                        tag      = E(KEY)
                        tag.text = str(VALUE)

                        _object.append(tag)


            else:
                #print("Attribute VALUE is None, thus not exported: ID: {} KEY: {}".format(ID, KEY))
                pass
        else:
            #print("No Object with ID: {}".format(ID))
            pass

    # etree.tostring(RDF, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    # print(etree.tostring(RDF, pretty_print=True).decode())

    # Convert to XML
    return etree.tostring(RDF, pretty_print=True, xml_declaration=True, encoding='UTF-8')


# TEST and examples
if __name__ == '__main__':

    from RDF_parser import load_all_to_dataframe

    path_list = ["TestConfigurations_packageCASv2.0/RealGrid/CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"]

    data = load_all_to_dataframe(path_list)


    object_UUID = "99722373_VL_TN1"

    #draw_relations_from(object_UUID, data)
    #draw_relations_to(object_UUID, data)










