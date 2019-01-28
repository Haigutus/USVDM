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

import numpy
from RDF_parser import load_all_to_dataframe
import pandas


path = "FlowExample.zip"

#path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

data = load_all_to_dataframe([path])

print("Loaded types")
print(data[(data.KEY == "Type")]["VALUE"].value_counts())

# Generate classical data views needed to extract relevant data

ACLineSegments          = data.type_view("ACLineSegment")
Terminals               = data.type_view("Terminal")
SvVoltages              = data.type_view("SvVoltage")
PowerTransformerEnds    = data.type_view("PowerTransformerEnd")
#PowerTransformers       = data.type_view("PowerTransformer")

# Join views to get needed AC line data
ACLineSegments_Terminals            = pandas.merge(ACLineSegments, Terminals, how = "inner", left_index=True, right_on = 'Terminal.ConductingEquipment')
ACLineSegments_Terminals_SvVoltages = pandas.merge(ACLineSegments_Terminals, SvVoltages, how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')


print(ACLineSegments_Terminals_SvVoltages[["SvVoltage.angle", "SvVoltage.v", "ACLineSegment.r", "ACLineSegment.x"]])

# Set data types
ACLineSegments_Terminals_SvVoltages[["SvVoltage.angle", "SvVoltage.v", "ACLineSegment.r", "ACLineSegment.x"]] = ACLineSegments_Terminals_SvVoltages[["SvVoltage.angle", "SvVoltage.v", "ACLineSegment.r", "ACLineSegment.x"]].astype("float")


r = ACLineSegments_Terminals_SvVoltages["ACLineSegment.r"]
x = ACLineSegments_Terminals_SvVoltages["ACLineSegment.x"]
v = ACLineSegments_Terminals_SvVoltages["SvVoltage.v"]
angle = numpy.deg2rad(ACLineSegments_Terminals_SvVoltages["SvVoltage.angle"])

impedance   = r + x * 1j

voltage     = v * numpy.cos(angle) + v * numpy.sin(angle) * 1j



# Join views to get Transformer data
PowerTransformerEnds_Terminals              = pandas.merge(PowerTransformerEnds, Terminals, how = "inner", left_on="TransformerEnd.Terminal", right_index = True)
PowerTransformerEnds_Terminals_SvVoltages   = pandas.merge(PowerTransformerEnds_Terminals, SvVoltages, how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')

print(PowerTransformerEnds_Terminals_SvVoltages[["SvVoltage.v", "SvVoltage.angle", "PowerTransformerEnd.ratedS", "PowerTransformerEnd.ratedU", "PowerTransformerEnd.r", "PowerTransformerEnd.x", "PowerTransformerEnd.g", "PowerTransformerEnd.b"]])
