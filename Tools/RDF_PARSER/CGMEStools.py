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

#from urlparse import urlparse
from urllib.parse import urlparse
from pyvis.network import Network
import pyvis.options as options
import os

import aniso8601

import tempfile

from lxml import etree

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


default_filename_mask = "{scenarioTime:%Y%m%dT%H%MZ}_{modelingEntity}_{processType}_{messageType}_{version:03d}"


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

    xml_metadata = pandas.DataFrame(meta_list, columns = ["tag", "text", "attrib"])

    return xml_metadata


def get_metadata_from_dataframe(data, UUID):
    """Currently returns all data defined in model header 'FullModel'
    Returns  dictionary -> value = meta['meta_key'] """
    # fileheader metadata keys should be aligned with filename ones

    #raw_metadata = data.query("ID == '{}'".format(UUID)).set_index("KEY")["VALUE"]
    metadata = data.get_object_data(UUID).to_dict()
    metadata.pop("Type", None) # Remove Type form metadata

    return metadata


def add_metadata_to_FullModel(data, metadata, update=True, add=False):

    additional_meta_list = []

    for INSTANCE_ID in data.INSTANCE_ID.unique():
        for key in metadata:
            additional_meta_list.append({"ID": INSTANCE_ID, "KEY": key, "VALUE": metadata[key], "INSTANCE_ID": INSTANCE_ID})

    update_data = pandas.DataFrame(additional_meta_list)

    return data.update_triplet_from_triplet(update_data, update, add)

def add_metadata_to_FullModel_from_filename(data, parser=get_filename_from_metadata, update=False, add=True):
    """Parses filename from label VALUE and by default adds missing attributes to each FullModel
    you can provide your own parser, has to return dictionary of attribute names and values"""

    additional_meta_list = []

    # For each instance that has label, as label contains the filename
    for _, label in data.query("KEY == 'Label'").iterrows():
        # Parse metadata from filename to dictionary
        meta = parser(label["VALUE"])
        # Create triplets form parsed metadata
        for key in meta:
            additional_meta_list.append(
                {"ID": label.INSTANCE_ID, "KEY": key, "VALUE": meta[key], "INSTANCE_ID": label.INSTANCE_ID})

    update_data = pandas.DataFrame(additional_meta_list)

    return data.update_triplet_from_triplet(update_data, update, add)


def update_filename_from_FullModel(data, filename_mask=default_filename_mask):
    """Updates the file names kept under RDF Label tag
     by constructing it from metadata kept in FullModel in each instance"""

    filename_key = "Label"  # KEY under which the filename is kept
    list_of_updates = []

    for _, label in data.query("KEY == '{}'".format(filename_key)).iterrows():
        # Get metadata
        metadata = get_metadata_from_dataframe(data, label.INSTANCE_ID)
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

    IGM_data = pandas.merge(data, model_instances_dataframe[["INSTANCE_ID"]].drop_duplicates(), right_on = "INSTANCE_ID", left_on = "INSTANCE_ID")

    return IGM_data





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

        graph.show_buttons()

        #graph.options = options

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
    list_of_generating_units = data.query("KEY == 'GeneratingUnit.initialP'").ID.tolist()
    generating_units = data[data.ID.isin(list_of_generating_units)].pivot(index="ID", columns = "KEY")["VALUE"]

    return generating_units


def statistics_ConcreteClasses(data):
    """Returns statistics on all loaded Concrete Classes"""
    value_counts = data.query("KEY == 'Type'")["VALUE"].value_counts()
    return value_counts


def get_diff_between_model_parts(UUID_1, UUID_2):

    diff = data.query("INSTANCE_ID == '{}' or INSTANCE_ID == '{}'".format(UUID_1,UUID_2)).drop_duplicates(["ID","KEY","VALUE"],keep = False)

    return diff

def filter_dataframe_by_dataframe(data, filter_data, filter_column_name):
    """Filter triplestore on ID column with another data frame column containing ID-s"""

    class_name = filter_column_name.split(".")[1]
    meta_separator = "_"

    result = pandas.merge(filter_column_name, data, left_on = filter_column_name, right_on ="ID", how="inner", suffixes=('', meta_separator + class_name))[["ID_" + class_name, "KEY", "VALUE"]]

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
        html_table = object_data[[ID_COLUMN, "KEY", "VALUE", "INSTANCE_ID"]].rename(
            columns={ID_COLUMN: "ID"}).to_html(index=False)

        #"".join([x if ord(x) < 128 else '?' for x in str(node["name"]]))

        graph.add_node(ID, unicode(node["Type"]) + u" - " + unicode(node["name"]), title=html_table, size=10,
                       level=object_data.level.tolist()[0])

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



# TEST and examples
if __name__ == '__main__':

    from RDF_parser import load_all_to_dataframe

    path_list = ["TestConfigurations_packageCASv2.0/RealGrid/CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"]

    data = load_all_to_dataframe(path_list)


    object_UUID = "99722373_VL_TN1"

    draw_relations_from(object_UUID, data)
    draw_relations_to(object_UUID, data)










