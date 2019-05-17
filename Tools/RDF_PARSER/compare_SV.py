#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     24.03.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from RDF_parser import load_all_to_dataframe

from itertools import permutations

import pandas
from urlparse import urlparse

from pyvis.network import Network
import pyvis.options as options
import os

import tempfile

pandas.set_option("display.max_rows", 10)
pandas.set_option("display.max_columns", 6)
pandas.set_option("display.width", 1000)


paths = [r"C:\Users\kristjan.vilgo\Downloads\results_CVG\20190116T0930Z_1D_CGMEU_SV_000.zip",
         r"C:\Users\kristjan.vilgo\Downloads\20190116_0930Z_ELES_HOPS_NOSBIH_TNA\20190116T0930Z_1D_CGMCE_SCC_SV_000\20190116T0930Z_1D_CGMCE_SCC_SV_000.xml",
         r"C:\Users\kristjan.vilgo\Downloads\20190116T0930Z_1D_AMICA_merged_model_RGCE_Prague_meeting\20190116T0930Z_1D_CGMCE_SV_002.zip",
         r"C:\Users\kristjan.vilgo\Downloads\2019016_0930Z_ELES_HOPS_NOSBIH_PowerFactory\3TSOsMerge\20190116T0930Z_1D_Abildgaard_SV_001\20190116T0930Z_1D_Abildgaard_SV_001.xml",
         r"C:\Users\kristjan.vilgo\Downloads\export\20190325T1722Z_1D_CGMBA_SV_001\20190325T1722Z_1D_CGMBA_SV_001.xml",
         r"C:\Users\kristjan.vilgo\Downloads\IGM_data.zip",
         r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"]


data = load_all_to_dataframe(paths)

loaded_profiles = data.type_tableview("FullModel")[[u'Model.created', u'Model.description', u'Model.modelingAuthoritySet', u'Model.profile', u'Model.scenarioTime', u'Model.version']] #
print(loaded_profiles)

comparison_dict = {"statistics":{}, "data":{}, "report":{"Instances": loaded_profiles}}
SV_UUID_list = data.query("VALUE == 'http://entsoe.eu/CIM/StateVariables/4/1'").ID.tolist()

for SV_UUID in SV_UUID_list:

    instance_data = data.query("INSTANCE_ID == '{}'".format(SV_UUID))
    authority = instance_data.query("KEY == 'Model.modelingAuthoritySet'").VALUE.item()

    try:
        EMF_name = urlparse(authority).netloc

    except:
        print("No modelling authorityset found or invalid url -> {}, using SV UUID".format(authority))
        EMF_name = SV_UUID


    comparison_dict["statistics"]["{}".format(EMF_name)] = instance_data.types_dict()
    comparison_dict["data"]["{}".format(EMF_name)]       = instance_data


statistics = pandas.DataFrame(comparison_dict["statistics"])
comparison_dict["report"]["SvStatistics"] = statistics
print(statistics)


# Add here parameters to compere and at what index
settings = [dict(index = "SvTapStep.TapChanger",      merge_column = "SvTapStep.position"),
            dict(index = "SvPowerFlow.Terminal",      merge_column = "SvPowerFlow.p"),
            dict(index = "SvPowerFlow.Terminal",      merge_column = "SvPowerFlow.q"),
            dict(index = "SvVoltage.TopologicalNode", merge_column = "SvVoltage.v"),
            dict(index = "SvVoltage.TopologicalNode", merge_column = "SvVoltage.angle")]

data.query("VALUE == 'ControlArea'")

# Create all comparison tables
for setting in settings:

    column_name = setting["merge_column"]
    type_name = setting["merge_column"].split(".")[0]

    comparison_dict[column_name] = {}
    comparison_data = pandas.DataFrame()

    for SV_UUID in comparison_dict["data"].keys():

        rename_dict = {column_name:SV_UUID}

        data_view = comparison_dict["data"][SV_UUID].\
                    type_tableview(type_name).\
                    set_index(setting["index"])\
                    [[column_name]].\
                    rename(rename_dict, axis = "columns").\
                    apply(pandas.to_numeric, errors = "ignore")#, drop = False) # use .reset_index() before .set_index() to keep result UUID

        comparison_data = comparison_data.join(data_view, how = "outer")

    # Report all SV combinations
    combinations = permutations(comparison_dict["data"].keys(), 2)

    for combination in combinations:

        diff_column_name = "<{}> - <{}>".format(combination[0], combination[1])
        comparison_data[diff_column_name] = comparison_data[combination[0]] - comparison_data[combination[1]]

    comparison_dict["report"][column_name] = comparison_data

    # Add statistics

    columns = [u'<baltic-rsc.eu> - <rte-france.fr>', u'<baltic-rsc.eu> - <nordic-rsc.net>', u'<baltic-rsc.eu> - <tscnet.eu>', u'<baltic-rsc.eu> - <scc-rsci.com>']

    comparison_dict["report"][column_name + "_" + "statistics"] = comparison_dict["report"][column_name][columns].describe()

excel_writer = pandas.ExcelWriter(r"C:\Users\kristjan.vilgo\Downloads\SV_comparison.xlsx")

for report in comparison_dict["report"].keys():
    comparison_dict["report"][report].to_excel(excel_writer, sheet_name = report)

excel_writer.save()



### Test realtion visulisation
##
##def relations_from(from_UUID, show = True):
##
##    level = 1
##
##    identified_objects  = {from_UUID:{"data":data[data.ID == from_UUID], "level":level}}
##    connections         = []
##    UUID_list           = [from_UUID]
##
##    for UUID in UUID_list:
##
##        level += 1
##
##        for _, row in identified_objects[UUID]["data"].iterrows():
##
##
##            refered_UUID   = row.VALUE
##            refered_object = data[data.ID == refered_UUID]
##
##            # Test if valid reference to object (if dataframe is empty, no object was found)
##            if refered_object.empty:
##                continue
##
##            # Lets add connection to valid object
##            connections.append(dict(FROM = UUID, TO = refered_UUID, NAME = row.KEY))
##
##            # Test if we allready don't have the element
##            if refered_UUID in UUID_list:
##                print("This object is allready analyzed -> {}".format(refered_UUID))
##                continue
##
##            # If not then add it
##            identified_objects[refered_UUID] = {"data":refered_object, "level":level}
##            UUID_list.append(refered_UUID)
##
##
##    # Visulise with pyvis
##
##    if show == True:
##
##        graph = Network(directed = True, width = "100%", height = 750)
##
##        for identified_object in identified_objects.keys():
##
##            level     = identified_objects[identified_object]["level"]
##            dataframe = identified_objects[identified_object]["data"]
##            node_type = dataframe[dataframe.KEY == "Type"].VALUE.tolist()[0]
##
##            node_name_list = dataframe[dataframe.KEY == "IdentifiedObject.name"].VALUE.tolist()
##
##            if node_name_list:
##                node_name = node_name_list[0]
##            else:
##                node_name = urlparse(dataframe[dataframe.KEY == "Model.profile"].VALUE.tolist()[0]).path # FullModel does not have IdentifiedObject.name
##
##
##            graph.add_node(identified_object, node_type + " - " + node_name, title = dataframe.to_html(index = False), size = 10, level = level) #[["KEY", "VALUE"]]
##
##        for connection in connections:
##            graph.add_edge(connection["FROM"], connection["TO"], title = connection["NAME"])
##
##
##        # Set options
##
##        options = {
##          "nodes": {
##            "shape": "dot",
##            "size": 10
##          },
##          "edges": {
##            "color": {
##              "inherit": True
##            },
##            "smooth": False
##          },
##          "layout": {
##            "hierarchical": {
##              "enabled": True,
##              "direction": "LR",
##              "sortMethod": "directed"
##            }
##          },
##          "interaction": {
##            "navigationButtons": True
##          },
##          "physics": {
##            "hierarchicalRepulsion": {
##              "centralGravity": 0,
##              "springLength": 75,
##              "nodeDistance": 145,
##              "damping": 0.2
##            },
##            "maxVelocity": 28,
##            "minVelocity": 0.75,
##            "solver": "hierarchicalRepulsion"
##          }
##        }
##
##
##
##        #graph.show_buttons()
##
##        graph.options = options
##
##        os.chdir(tempfile.mkdtemp())
##        graph.show(r"{}.html".format(from_UUID))
##
##
##    return connections, identified_objects
##
##
##
##relations_from('000319d5-61de-4ed8-a5a3-9058d85012d1')










