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
import sys
sys.path.append("..")

from RDF_parser import load_all_to_dataframe

from itertools import permutations

import pandas
#from urlparse import urlparse

from pyvis.network import Network
import pyvis.options as options
import os

import tempfile


from CGMES_tools import *




pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 6)
pandas.set_option("display.width", 1000)


##paths = [r"C:\Users\kristjan.vilgo\Downloads\results_CVG\20190116T0930Z_1D_CGMEU_SV_000.zip",
##         r"C:\Users\kristjan.vilgo\Downloads\20190116_0930Z_ELES_HOPS_NOSBIH_TNA\20190116T0930Z_1D_CGMCE_SCC_SV_000\20190116T0930Z_1D_CGMCE_SCC_SV_000.xml",
##         r"C:\Users\kristjan.vilgo\Downloads\20190116T0930Z_1D_AMICA_merged_model_RGCE_Prague_meeting\20190116T0930Z_1D_CGMCE_SV_002.zip",
##         r"C:\Users\kristjan.vilgo\Downloads\2019016_0930Z_ELES_HOPS_NOSBIH_PowerFactory\3TSOsMerge\20190116T0930Z_1D_Abildgaard_SV_001\20190116T0930Z_1D_Abildgaard_SV_001.xml",
##         r"C:\Users\kristjan.vilgo\Downloads\export\20190325T1722Z_1D_CGMBA_SV_001\20190325T1722Z_1D_CGMBA_SV_001.xml",
##         r"C:\Users\kristjan.vilgo\Downloads\IGM_data.zip",
##         r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"]


##paths = [r"C:\IOPs\IOP100419\RSC_MERGE\20190410_0930_Convergence_results_ELES_HOPS_NOSBIH\20190410T0930Z_1D_CGMEU_SV_001.zip",
##        r"C:\IOPs\IOP100419\RSC_MERGE\20190410_0930Z_PowerFactory_ELES_HOPS_NOSBIH\EMF2019-04-10_0930Z_ELESHOPSNOSBIH\19700101T0000Z_1D_PowerFactory_SV_001.zip",
##        r"C:\IOPs\IOP100419\RSC_MERGE\20190410_0930Z_SCC1_results_ELES_HOPS_NOSBIH\2\20190410T0930Z_1D_CGMCE_SCC_SV_001.zip",
##        r"C:\IOPs\IOP100419\RSC_MERGE\20190410T0930Z_1D_BALTICRSC_CGMCE_001\20190410T0930Z_1D_BALTICRSC_CGMCE_001\20190410T0930Z_1D_CGMBA_SV_001.zip",
##        r"C:\IOPs\IOP100419\RSC_MERGE\20190410T0930Z_1D_small_merge_AMICA\20190410T0930Z_1D_CGMCE_SV_002.zip",
##        r"C:\IOPs\IOP100419\RSC_MERGE\20190410T0930Z_NRSC_Merge_ELES_HOPS_NOSBIH\20190410T0930Z_1D_CGMNO_SV_001.zip",
##        r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip",
##        r"C:\IOPs\IOP100419\RSC_MERGE\IGM_TP_EQ.zip"
##]


# Define here paths that you want to load. Load only SV files you want to compare, usually CGM SV files
paths = [r"C:\IOPs\IOP150519\RSC_MERGE\20190515T0930Z_1D_BALTICRSC-CE_002.zip",
         r"C:\IOPs\IOP150519\RSC_MERGE\20190515T0930Z_1D_CORESO-CE_002.zip",
         r"C:\IOPs\IOP150519\RSC_MERGE\20190515T0930Z_1D_HANS-CE_004.zip",
         r"C:\IOPs\IOP150519\RSC_MERGE\20190515T0930Z_1D_TSCNET-CE_003_distributed_slack.zip",
         r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip",
         r"C:\IOPs\IOP150519\RSC_MERGE\IGM.zip"
         ]


data = load_all_to_dataframe(paths)



loaded_profiles = data.type_tableview("FullModel")[[u'Model.created', u'Model.description', u'Model.modelingAuthoritySet', u'Model.profile', u'Model.scenarioTime', u'Model.version']] #
print(loaded_profiles)

comparison_dict = {"statistics":{}, "data":{}, "report":{"Instances": loaded_profiles}}
SV_UUID_list = data.query("VALUE == 'http://entsoe.eu/CIM/StateVariables/4/1'").ID.tolist()

EMF_namelist = []

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

    EMF_namelist.append(EMF_name)


statistics = pandas.DataFrame(comparison_dict["statistics"])
comparison_dict["report"]["SvStatistics"] = statistics
print(statistics)


# Add here parameters to compere and at what index
settings = [dict(index = "SvTapStep.TapChanger",      merge_column = "SvTapStep.position"),
            dict(index = "SvPowerFlow.Terminal",      merge_column = "SvPowerFlow.p"),
            dict(index = "SvPowerFlow.Terminal",      merge_column = "SvPowerFlow.q"),
            dict(index = "SvVoltage.TopologicalNode", merge_column = "SvVoltage.v"),
            dict(index = "SvVoltage.TopologicalNode", merge_column = "SvVoltage.angle")]

#data.query("VALUE == 'ControlArea'")

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

    #columns = [u'<baltic-rsc.eu> - <rte-france.fr>', u'<baltic-rsc.eu> - <nordic-rsc.net>', u'<baltic-rsc.eu> - <tscnet.eu>', u'<baltic-rsc.eu> - <scc-rsci.com>']

    comparison_dict["report"][column_name + "_" + "statistics"] = comparison_dict["report"][column_name][EMF_namelist].describe()

##excel_writer = pandas.ExcelWriter(r"C:\IOPs\IOP150519\RSC_MERGE\SV_comparison_150519.xlsx")
##
##for report in comparison_dict["report"].keys():
##    comparison_dict["report"][report].to_excel(excel_writer, sheet_name = report)
##
##excel_writer.save()


print(loaded_profiles[loaded_profiles["Model.profile"]=="http://entsoe.eu/CIM/StateVariables/4/1"])

print("all data is avaialbel in 'comparison_dict'")
print(comparison_dict.keys())

##relations_from('000319d5-61de-4ed8-a5a3-9058d85012d1')

# Generate classical data views needed to extract relevant data

ACLineSegments          = data.type_tableview("ACLineSegment")
Terminals               = data.type_tableview("Terminal")

PowerTransformerEnds    = data.type_tableview("PowerTransformerEnd")
SynchronousMachines     = data.type_tableview("SynchronousMachine")

#PowerTransformers       = data.type_tableview("PowerTransformer")

SynchronousMachines = pandas.merge(SynchronousMachines.reset_index(), Terminals.reset_index(), suffixes=('', '_Terminal'),    how = "inner", left_on = "ID", right_on = 'Terminal.ConductingEquipment')

# Query for referenced object
GeneratingUnits    = tableview_by_IDs(data, SynchronousMachines,"RotatingMachine.GeneratingUnit")
RegulatingControls = tableview_by_IDs(data, SynchronousMachines,"RegulatingCondEq.RegulatingControl")

# Add data from referenced objects
SynchronousMachines = pandas.merge(SynchronousMachines, GeneratingUnits, left_on = "RotatingMachine.GeneratingUnit", right_index = True, how= "inner", suffixes=('', '_GeneratingUnit'))




sv_profiles = loaded_profiles[loaded_profiles["Model.profile"]=="http://entsoe.eu/CIM/StateVariables/4/1"]

for UUID, row in sv_profiles.iterrows():

    authority = row['Model.modelingAuthoritySet']

    try:
        EMF_name = urlparse(authority).netloc

    except:
        print("No modelling authorityset found or invalid url -> {}, using SV UUID".format(authority))
        EMF_name = SV_UUID

    SvVoltages              = data.query("INSTANCE_ID == '{}'".format(UUID)).type_tableview("SvVoltage").add_prefix(EMF_name + "_")
    SvPowerFlows            = data.query("INSTANCE_ID == '{}'".format(UUID)).type_tableview("SvPowerFlow").add_prefix(EMF_name + "_")

    SynchronousMachines = pandas.merge(SynchronousMachines, SvVoltages,              suffixes=('', '_SvVoltage'),   how = "inner", left_on = 'Terminal.TopologicalNode', right_on = EMF_name + '_SvVoltage.TopologicalNode')
    SynchronousMachines = pandas.merge(SynchronousMachines, SvPowerFlows,            suffixes=('', '_SvPowerFlow'), how = "inner", left_on = 'ID_Terminal', right_on = EMF_name + '_SvPowerFlow.Terminal')





