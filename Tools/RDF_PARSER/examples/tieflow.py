#-------------------------------------------------------------------------------
# Name:     tieflow.py
# Purpose:  Extract tiefwlows, AC NP
#
# Author:      kristjan.vilgo
#
# Created:     28.01.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys
sys.path.append("..")

from RDF_parser import load_all_to_dataframe, get_object_data
from CGMES_tools import get_loaded_models, get_metadata_from_FullModel, get_model_data

import aniso8601
import pandas
pandas.set_option("display.max_rows", 37)



def tieflow_sign_convention(positiveFlowIn):

        mapping = {'true': -1, 'false': 1}
        return mapping[positiveFlowIn.lower()]


def get_EquivalentInjections_NetInterchange_TieFlows(data):

    tieflow_data              = pandas.DataFrame()
    netinterchange_data       = pandas.DataFrame()
    equivalentinjections_data = pandas.DataFrame()
    equivalentinjections_dc   = pandas.DataFrame()
    equivalentinjections_ac   = pandas.DataFrame()

    loaded_IGMs = get_loaded_models(data)

    for IGM in loaded_IGMs:

        dependancies = loaded_IGMs[IGM]
        IGM_data     = get_model_data(data, dependancies)

        metadata     = get_metadata_from_FullModel(IGM_data)

        try:
            EQ_UUID = dependancies.query("PROFILE == 'http://entsoe.eu/CIM/EquipmentCore/3/1'")["INSTANCE_ID"].item() #should be faster
        except:
            print("EQ missing, skipping")
            print(metadata)
            continue

        EQ_data = data.query("INSTANCE_ID == '{}'".format(EQ_UUID))

        #print("Loading TieFlow data from EQ -> {}".format(EQ_UUID))


        TieFlow     = EQ_data.type_tableview("TieFlow")
        Terminal    = EQ_data.type_tableview("Terminal")
        SvPowerFlow = IGM_data.type_tableview("SvPowerFlow")


        Tieflow_Terminal = pandas.merge(TieFlow, Terminal, how = "inner", left_on = 'TieFlow.Terminal', right_index = True)

        ConductingEquipment = pandas.merge(Tieflow_Terminal[["Terminal.ConductingEquipment"]], EQ_data, left_on = "Terminal.ConductingEquipment", right_on = "ID")

        #print(ConductingEquipment_triplet.query("KEY == 'Type'")["VALUE"].value_counts()) # Statistics, on wich kind of equipment the tieflow sits
        #print(ConductingEquipment_triplet.query("KEY == 'IdentifiedObject.name'")[["ID", "VALUE"]]) # Names of the objects where it sits


        Tieflow_SvPowerFlow = pandas.merge(TieFlow, SvPowerFlow, how = "inner", left_on = 'TieFlow.Terminal', right_on = "SvPowerFlow.Terminal")



        # Apply tieflow convention and calculate sum

        Tieflow_SvPowerFlow["TieFlow.Sign"] = Tieflow_SvPowerFlow["TieFlow.positiveFlowIn"].apply(tieflow_sign_convention)

        tieflow_sum = (Tieflow_SvPowerFlow[u'SvPowerFlow.p'] * Tieflow_SvPowerFlow["TieFlow.Sign"]).sum()


        # Find area EIC and scenario time

        ControlArea_UUID = IGM_data.query("VALUE == 'ControlArea'").ID.unique()[0]
        ControlArea      = get_object_data(IGM_data, ControlArea_UUID)

        area_EIC      = ControlArea["IdentifiedObject.energyIdentCodeEic"]
        #area_EIC = IGM_data.query("ID == '{}' & KEY == 'IdentifiedObject.energyIdentCodeEic'".format(ControlArea_UUID))["VALUE"].item() # Tieflow_SvPowerFlow.at[0,"TieFlow.ControlArea"]

        scenario_time = aniso8601.parse_datetime(metadata['Model.scenarioTime'].replace("Z",""))




        # Add tieflows
        tieflow_data.loc[scenario_time, area_EIC]= float(tieflow_sum)  # Lets use area EIC and naive datetime


        # Add netinterchange
        #netInterchange = IGM_data.query("ID == '{}' & KEY == 'ControlArea.netInterchange'".format(ControlArea_UUID))["VALUE"].item() # Tieflow_SvPowerFlow.at[0,"TieFlow.ControlArea"]

        netInterchange = ControlArea["ControlArea.netInterchange"]
        netinterchange_data.loc[scenario_time, area_EIC] = float(netInterchange) * -1


        # Add Equivalent Injection sum
        try:
            TP_BOUNDARY_ID = dependancies_list.query("PROFILE == 'http://entsoe.eu/CIM/TopologyBoundary/3/1'").INSTANCE_ID.tolist()[0]
            TP_TopologicalNodes = IGM_data.query("INSTANCE_ID == '{}'".format(TP_BOUNDARY_ID)).type_tableview("TopologicalNode")
        except:
            #print("No boundary present, using ENTSO-E latest boundary")
            TP_BOUNDARY_ID = data.query("VALUE == 'http://entsoe.eu/CIM/TopologyBoundary/3/1'").INSTANCE_ID.tolist()[0]
            TP_TopologicalNodes = data.query("INSTANCE_ID == '{}'".format(TP_BOUNDARY_ID)).type_tableview("TopologicalNode")

        EquivalentInjections = IGM_data.type_tableview("EquivalentInjection")
        #EquivalentInjections_TopologicalNodes = pandas.merge(Terminal, EquivalentInjections, left_on = "Terminal.ConductingEquipment", right_index = True)

        #print(EquivalentInjections) # DEBUG

        EquivalentInjections_sum = EquivalentInjections[['EquivalentInjection.p']].sum().item()

        equivalentinjections_data.loc[scenario_time, area_EIC] = EquivalentInjections_sum


        #EquivalentInjections_DC = EquivalentInjections[EquivalentInjections['IdentifiedObject.shortName'].str.contains("(XFI_EE52)|(XPU_AN11)")][['EquivalentInjection.p']].sum().item()
        #equivalentinjections_dc.loc[scenario_time, area_EIC] = EquivalentInjections_DC
        #equivalentinjections_ac.loc[scenario_time, area_EIC] = EquivalentInjections_sum - EquivalentInjections_DC




    # Export

    report_dict = {}

    report_dict["NetInterchange"]           = netinterchange_data.sort_index()
    report_dict["TieFlows"]                 = tieflow_data.sort_index()
    report_dict["EquivalentInjections"]     = equivalentinjections_data.sort_index()
    report_dict["ACNP"]                     = equivalentinjections_ac.sort_index()
    #Sreport_dict["DCNP"]                     = equivalentinjections_dc.sort_index()

    return pandas.concat(report_dict, axis=1).round(1)



# TEST and examples
if __name__ == '__main__':

    #list_of_regulating_controls = data.query("KEY == 'RegulatingControl.mode'").ID.tolist()
    model_path = r'C:/IOPs/IOP210819/BA02_BD21082019_1D_Elering_001_NodeBreaker.zip'
    model_path = r"C:\Users\kristjan.vilgo\Downloads\2019_10_09_InputDataSmallMerge+PEVFv6\2019_10_09_InputDataSmallMerge+PEVFv6\CGM_2_TSOs_ELES_TERNA\20191009T0930Z_1D_TERNA_EQ_001 (2).zip"
    dataframe = load_all_to_dataframe([model_path, r"C:\Users\kristjan.vilgo\Downloads\2019_10_09_InputDataSmallMerge+PEVFv6\2019_10_09_InputDataSmallMerge+PEVFv6\CGM_2_TSOs_ELES_TERNA\20191009T0930Z_1D_ELES_TP_002 (2).zip",  r"C:\Users\kristjan.vilgo\Downloads\20200129T0000Z_ENTSO-E_BD_1164.zip"
                                       ])
    #dataframe = load_all_to_dataframe([r"C:\Users\kristjan.vilgo\Downloads\20190624T2330Z_1D_RTEFRANCE_739.zip", r"C:\Users\kristjan.vilgo\Downloads\20190625T0030Z_1D_RTEFRANCE_777.zip"])
    tieflows = get_EquivalentInjections_NetInterchange_TieFlows(dataframe)
    print(tieflows)
