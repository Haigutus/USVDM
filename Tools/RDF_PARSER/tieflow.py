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

from RDF_parser import load_all_to_dataframe

import pandas
pandas.set_option("display.max_rows", 24)

import aniso8601

def tieflow_sign_convention(positiveFlowIn):

        mapping = {'true': -1, 'false': 1}
        return mapping[positiveFlowIn.lower()]

#path = "FlowExample.zip"

#path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

#path = "C:\IOPs\IOP160119\CE02_BD16012019_1D_Amprion_BusBranch.zip"

path2 = "C:\IOPs\IOP160119\CE03_BD16012019_1D_APG_BusBranch.zip"

path = "C:\IOPs\IOP160119\BA03_20190116_1D_LITGRID_001_NodeBreaker.zip"

#path = "C:\IOPs\IOP160119\CE09_BD16012019_1D_Energinet_NodeBreaker\CE09_BD16012019_1D_Energinet_NodeBreaker_DKW.zip"

#path = "C:\IOPs\IOP160119\BA02_BD16012019_1D_Elering_001_NodeBreaker.zip"

#path = "C:\IOPs\IOP160119\BA01_BD16012019_1D_AST_001_BusBranch.zip"

data = load_all_to_dataframe([path, path2])

#data = load_all_to_dataframe([path])


print("Loaded types")
print(data.query("KEY == 'Type'")["VALUE"].value_counts())

FullModel   = data.type_tableview("FullModel")
SV_iterator = FullModel[FullModel["Model.profile"] == 'http://entsoe.eu/CIM/StateVariables/4/1'].iterrows()

tieflow_data = pandas.DataFrame()

netinterchange_data = pandas.DataFrame()

#_, SV = SV_iterator.next()

for _, SV in SV_iterator:

    # Find all instances of data

    SV_UUID = SV.name

    dependancies_list = [SV_UUID]

    for dependancie in dependancies_list:

        dependancies_list.extend(data.query("ID == '{}' & KEY == 'Model.DependentOn'".format(dependancie))["VALUE"].tolist())

    dependancies_dataframe = FullModel[FullModel.index.isin(dependancies_list)]

    print("\nAnalysing IGM consiting of following instances: \n")
    print(dependancies_dataframe[[u'Model.profile', u'Model.created', u'Model.modelingAuthoritySet', u'Model.scenarioTime', u'Model.version']])


    IGM_data = data[data.INSTANCE_ID.isin(dependancies_list)]

    EQ_UUID = IGM_data.query("VALUE == 'http://entsoe.eu/CIM/EquipmentCore/3/1'")["INSTANCE_ID"].tolist()[0]
    EQ_data = data.query("INSTANCE_ID == '{}'".format(EQ_UUID))

    #print("Loading TieFlow data from EQ -> {}".format(EQ_UUID))


    TieFlow     = EQ_data.type_tableview("TieFlow")
    Terminal    = EQ_data.type_tableview("Terminal")
    SvPowerFlow = IGM_data.type_tableview("SvPowerFlow")


    Tieflow_Terminal = pandas.merge(TieFlow, Terminal, how = "inner", left_on = 'TieFlow.Terminal', right_index = True)

    ConductingEquipment_triplet = pandas.merge(Tieflow_Terminal[["Terminal.ConductingEquipment"]], EQ_data, left_on = "Terminal.ConductingEquipment", right_on = "ID")

    #print(ConductingEquipment_triplet.query("KEY == 'Type'")["VALUE"].value_counts()) # Statistics, on wich kind of equipment the tieflow sits
    #print(ConductingEquipment_triplet.query("KEY == 'IdentifiedObject.name'")[["ID", "VALUE"]]) # Names of the objects where it sits


    Tieflow_SvPowerFlow = pandas.merge(TieFlow, SvPowerFlow, how = "inner", left_on = 'TieFlow.Terminal', right_on = "SvPowerFlow.Terminal")



    # apply function to series
    Tieflow_SvPowerFlow["TieFlow.Sign"] = Tieflow_SvPowerFlow["TieFlow.positiveFlowIn"].apply(tieflow_sign_convention)

    #sum = Tieflow_SvPowerFlow[[u'SvPowerFlow.p', u'SvPowerFlow.q']].astype("float").sum()

    sum = (Tieflow_SvPowerFlow[u'SvPowerFlow.p'].astype("float") * Tieflow_SvPowerFlow["TieFlow.Sign"]).sum() # Direction sign change is not implemented

    area_EIC = IGM_data.query("ID == '{}' & KEY == 'IdentifiedObject.energyIdentCodeEic'".format(Tieflow_SvPowerFlow.at[0,"TieFlow.ControlArea"]))["VALUE"].item()


    #tieflow_data.loc[SV["Model.scenarioTime"], SV["Model.modelingAuthoritySet"]]= sum["SvPowerFlow.p"]

    tieflow_data.loc[aniso8601.parse_datetime(SV["Model.scenarioTime"].replace("Z","")), area_EIC]= float(sum) #["SvPowerFlow.p"] # Lets use area EIC and naive datetime


    # Add netinterchange
    netInterchange = IGM_data.query("ID == '{}' & KEY == 'ControlArea.netInterchange'".format(Tieflow_SvPowerFlow.at[0,"TieFlow.ControlArea"]))["VALUE"].item()
    netinterchange_data.loc[aniso8601.parse_datetime(SV["Model.scenarioTime"].replace("Z","")), area_EIC] = float(netInterchange)



report_dict = {}

report_dict["NetInterchange"] = netinterchange_data.sort_index()
report_dict["TieFlow"] = tieflow_data.sort_index()

print(pandas.concat(report_dict, axis=1)).round(1)


