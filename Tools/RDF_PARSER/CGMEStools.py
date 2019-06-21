#-------------------------------------------------------------------------------
# Name:        CGMEStools
# Purpose:     Collection of functions to work with CGMES files
#
# Author:      kristjan.vilgo
#
# Created:     10.06.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from __future__ import print_function
import pandas

from urlparse import urlparse
from pyvis.network import Network
import pyvis.options as options
import os

import tempfile

from lxml import etree

def get_metadata_from_filename(file_name):

    #print(file_name)
    file_metadata = {}
    file_name, file_metadata["file_type"] = file_name.split(".")

    if "_EQ_" in file_name or "_BD_" in file_name:

        file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)
        file_metadata["process_type"] = ""

    else:
        try:
            file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)
        except:
            print ("Non CGMES file {}".format(file_name))

    return file_metadata

def get_filename_from_metadata(file_metadata):

    if file_metadata["profile"] == "EQ" or file_metadata["profile"] == "BD":
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    else:
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    file_name = ".".join([file_name, file_metadata["file_type"]])

    return file_name


def get_metadata_from_xml(filepath_or_fileobject):

    parsed_xml = etree.parse(filepath_or_fileobject)

    header = parsed_xml.find("{*}FullModel")
    meta_elements = header.getchildren()

    meta_list = []
    for element in meta_elements:
         meta_list.append([element.tag, element.text, element.attrib])

    xml_metadata = pandas.DataFrame(meta_list, columns = ["tag", "text", "attrib"])

    return xml_metadata

def get_metadata_from_dataframe(data, UUID):
    """Currently returns all data defined in model header 'FullModel'
    Returns pandas array which can be accessed the same way as dictionary -> value = meta['meta_key'] """
    # fileheader metadata keys should be aligned with filename ones

    raw_metadata = data.query("ID == '{}'".format(UUID)).set_index("KEY")["VALUE"]

    return raw_metadata


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

    IGM_data = pandas.merge(data, model_instances_dataframe[["INSTANCE_ID"]].drop_duplicates(), right_on = "INSTANCE_ID", left_on = "INSTANCE_ID")

    return IGM_data


def get_object_data(data, object_UUID):

    object_data = data.query("ID == '{}'".format(object_UUID)).set_index("KEY")["VALUE"]

    return object_data


def get_loaded_model_parts(data):
    """Returns a pandas DataFrame of loaded CGMES instance files or model parts with their header (FullModel) data (does not return correct dependant on)"""
    return data.type_tableview("FullModel")


def get_relations_from(data, from_UUID, show = True, notebook = False):
    """Returns all found realtions from given object or model UUID
    show=True creates an temporary XML file to visualize realations
    returns connections and identified objects"""

    level = 1

    identified_objects  = {from_UUID:{"data":data[data.ID == from_UUID], "level":level}}
    connections         = []
    UUID_list           = [from_UUID]


    for UUID in UUID_list:

        level += 1

        # TODO - use merge instead of a loop

        for _, row in identified_objects[UUID]["data"].iterrows():


            refered_UUID   = row.VALUE
            refered_object = data[data.ID == refered_UUID]

            # Test if valid reference to object (if dataframe is empty, no object was found)
            if refered_object.empty: # All fields are tested, no assumption is if filed contains reference or not
                continue

            # Lets add connection to valid object
            connections.append(dict(FROM = UUID, TO = refered_UUID, NAME = row.KEY))

            # Test if we allready don't have the element
            if refered_UUID in UUID_list:
                #print("This object is allready analyzed -> {}".format(refered_UUID))
                continue

            # If not then add it
            identified_objects[refered_UUID] = {"data":refered_object, "level":level}
            UUID_list.append(refered_UUID)


    # Visulise with pyvis

    if show == True:

        graph = Network(directed = True, width = "100%", height = 750, notebook=notebook)

        for identified_object in identified_objects.keys():

            level     = identified_objects[identified_object]["level"]
            dataframe = identified_objects[identified_object]["data"]
            node_type = dataframe[dataframe.KEY == "Type"].VALUE.tolist()[0]

            node_name_list = dataframe[dataframe.KEY == "IdentifiedObject.name"].VALUE.tolist()

            if node_name_list:
                node_name = node_name_list[0]
            else:
                node_name = urlparse(dataframe[dataframe.KEY == "Model.profile"].VALUE.tolist()[0]).path # FullModel does not have IdentifiedObject.name


            graph.add_node(identified_object, node_type + " - " + node_name, title = dataframe.to_html(index = False), size = 10, level = level) #[["KEY", "VALUE"]]

        for connection in connections:
            graph.add_edge(connection["FROM"], connection["TO"], title = connection["NAME"])


        # Set options

        options = {
          "nodes": {
            "shape": "dot",
            "size": 10
          },
          "edges": {
            "color": {
              "inherit": True
            },
            "smooth": False
          },
          "layout": {
            "hierarchical": {
              "enabled": True,
              "direction": "LR",
              "sortMethod": "directed"
            }
          },
          "interaction": {
            "navigationButtons": True
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
        }

        #graph.show_buttons()

        graph.options = options

        if notebook == False:
            os.chdir(tempfile.mkdtemp())
            graph.show(r"{}.html".format(from_UUID))


    return connections, identified_objects, graph

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
    list_of_generating_units = EQ_data.query("KEY == 'GeneratingUnit.initialP'").ID.tolist()
    GeneratingUnits = EQ_data[EQ_data.ID.isin(list_of_generating_units)].pivot(index="ID", columns = "KEY")["VALUE"]

    return generating_units_data


def statistics_ConcreteClasses(data):
    """Returns statistics on all loaded Concrete Classes"""
    value_counts = data.query("KEY == 'Type'")["VALUE"].value_counts()
    return value_counts


def get_diff_between_model_parts(UUID_1, UUID_2):

    diff = data.query("INSTANCE_ID == '{}' or INSTANCE_ID == '{}'".format(UUID_1,UUID_2)).drop_duplicates(["ID","KEY","VALUE"],keep = False)

    return diff

def filter_dataframe_by_dataframe(data, filter_data, filter_column_name):
    """Filter triplestore on ID column with another dataframe column containing ID-s"""

    class_name = filter_column_name.split(".")[1]
    meta_separator = "_"

    result = pandas.merge(IDs_dataframe, data, left_on = IDs_column_name, right_on ="ID", how="inner", suffixes=('', meta_separator + class_name))[["ID_" + class_name, "KEY", "VALUE"]]

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

    return  result



# TEST and examples
if __name__ == '__main__':

    from RDF_parser import load_all_to_dataframe

    path_list = ["C:\IOPs\IOP160119\BA02_BD16012019_1D_Elering_001_NodeBreaker.zip"]

    data = load_all_to_dataframe(path_list)



