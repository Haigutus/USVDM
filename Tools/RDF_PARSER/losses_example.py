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
from RDF_parser import load_all_to_dataframe
import pandas


path = "FlowExample.zip"

#path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

data = load_all_to_dataframe([path])

print("Loaded types")
print(data[(data.KEY == "Type")]["VALUE"].value_counts())

# Generate classical data views needed to extract relevant data

#ACLineSegments          = data.type_view("ACLineSegment")
#Terminals               = data.type_view("Terminal")
#SvVoltages              = data.type_view("SvVoltage")
#PowerTransformerEnds    = data.type_view("PowerTransformerEnd")
#PowerTransformers       = data.type_view("PowerTransformer")


Terminals = data.query("KEY == 'Terminal.ConductingEquipment'")

SvPowerFlow = data.type_view("SvPowerFlow")

# Join views to get needed AC line data
SvPowerflow_Terminals            = pandas.merge(Terminals, SvPowerFlow, how = "inner", left_on = "ID", right_on = "SvPowerFlow.Terminal")
ACLineSegments_Terminals_SvVoltages = pandas.merge(ACLineSegments_Terminals, SvVoltages, how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')

#"[{Terminal.ConductingEquipment@1}->{SvPowerFlow.Terminal@1}->SvPowerFlow.p] + [{Terminal.ConductingEquipment@2}->{SvPowerFlow.Terminal@1}->SvPowerFlow.p]"
#[{Terminal.ConductingEquipment@1}->{SvPowerFlow.Terminal@1}->SvPowerFlow.q] + [{Terminal.ConductingEquipment@2}->{SvPowerFlow.Terminal@1}->SvPowerFlow.q]