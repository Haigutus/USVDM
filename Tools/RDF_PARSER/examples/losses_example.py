#-------------------------------------------------------------------------------
# Name:        PF_EXAMPLE
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     28.01.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from numpy import sin, cos, deg2rad, triu
import sys
sys.path.append("..")

from RDF_parser import load_all_to_dataframe
import pandas


path = "../test_models/FlowExample.zip"

#path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

data = load_all_to_dataframe([path])

print("Loaded types")
print(data[(data.KEY == "Type")]["VALUE"].value_counts())

# Generate classical data views needed to extract relevant data

ACLineSegments          = data.type_tableview("ACLineSegment")
Terminals               = data.type_tableview("Terminal")
SvVoltages              = data.type_tableview("SvVoltage")
PowerTransformerEnds    = data.type_tableview("PowerTransformerEnd")
PowerTransformers       = data.type_tableview("PowerTransformer")


Terminals = data.query("KEY == 'Terminal.ConductingEquipment'")

SvPowerFlow = data.type_tableview("SvPowerFlow")

# Join views to get needed AC line data
SvPowerflow_Terminals            = pandas.merge(Terminals, SvPowerFlow, how = "inner", left_on = "ID", right_on = "SvPowerFlow.Terminal")
#ACLineSegments_Terminals_SvVoltages = pandas.merge(ACLineSegments_Terminals, SvVoltages, how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')

#"[{Terminal.ConductingEquipment@1}->{SvPowerFlow.Terminal@1}->SvPowerFlow.p] + [{Terminal.ConductingEquipment@2}->{SvPowerFlow.Terminal@1}->SvPowerFlow.p]"
#[{Terminal.ConductingEquipment@1}->{SvPowerFlow.Terminal@1}->SvPowerFlow.q] + [{Terminal.ConductingEquipment@2}->{SvPowerFlow.Terminal@1}->SvPowerFlow.q]