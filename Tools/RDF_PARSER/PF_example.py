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

ACLineSegments          = data.type_tableview("ACLineSegment")
Terminals               = data.type_tableview("Terminal")
SvVoltages              = data.type_tableview("SvVoltage")
PowerTransformerEnds    = data.type_tableview("PowerTransformerEnd")
#PowerTransformers       = data.type_tableview("PowerTransformer")

# Join views to get needed AC line data
ACLineSegments_Terminals            = pandas.merge(ACLineSegments, Terminals, how = "inner", left_index=True, right_on = 'Terminal.ConductingEquipment')
ACLineSegments_Terminals_SvVoltages = pandas.merge(ACLineSegments_Terminals, SvVoltages, how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')


print(ACLineSegments_Terminals_SvVoltages[["SvVoltage.angle", "SvVoltage.v", "ACLineSegment.r", "ACLineSegment.x"]])

# Set data types
ACLineSegments_Terminals_SvVoltages[["SvVoltage.angle", "SvVoltage.v", "ACLineSegment.r", "ACLineSegment.x"]] = ACLineSegments_Terminals_SvVoltages[["SvVoltage.angle", "SvVoltage.v", "ACLineSegment.r", "ACLineSegment.x"]].astype("float")

# Define variables

r = ACLineSegments_Terminals_SvVoltages["ACLineSegment.r"]
x = ACLineSegments_Terminals_SvVoltages["ACLineSegment.x"]
v = ACLineSegments_Terminals_SvVoltages["SvVoltage.v"]
angle = deg2rad(ACLineSegments_Terminals_SvVoltages["SvVoltage.angle"])

# ACLineSegment formulas

Y = 1/(r + x * 1j)
V = v * cos(angle) + v * sin(angle) * 1j

# Save values

admittance_name ="Branch.y"
node_voltage = "TopologicalNode.v"

ACLineSegments_Terminals_SvVoltages[admittance_name] = Y
ACLineSegments_Terminals_SvVoltages[node_voltage]    = V


line_branches = pandas.merge(ACLineSegments_Terminals_SvVoltages[["Terminal.ConductingEquipment","SvVoltage.TopologicalNode"]], ACLineSegments_Terminals_SvVoltages[["Terminal.ConductingEquipment","SvVoltage.TopologicalNode",admittance_name]], how = "inner", left_on = "Terminal.ConductingEquipment", right_on = "Terminal.ConductingEquipment")

branches = line_branches[(line_branches["SvVoltage.TopologicalNode_x"] != line_branches["SvVoltage.TopologicalNode_y"])]

admittance_matrix = branches[["Terminal.ConductingEquipment","SvVoltage.TopologicalNode_x", "SvVoltage.TopologicalNode_y"]].pivot(index = "SvVoltage.TopologicalNode_x", columns = "SvVoltage.TopologicalNode_y") # Does not work with complex



# Join views to get Transformer data
PowerTransformerEnds_Terminals              = pandas.merge(PowerTransformerEnds, Terminals, how = "inner", left_on="TransformerEnd.Terminal", right_index = True)
PowerTransformerEnds_Terminals_SvVoltages   = pandas.merge(PowerTransformerEnds_Terminals, SvVoltages, how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')

print(PowerTransformerEnds_Terminals_SvVoltages[["SvVoltage.v", "SvVoltage.angle", "PowerTransformerEnd.ratedS", "PowerTransformerEnd.ratedU", "PowerTransformerEnd.r", "PowerTransformerEnd.x", "PowerTransformerEnd.g", "PowerTransformerEnd.b"]])

# Define variables

r = PowerTransformerEnds_Terminals_SvVoltages["PowerTransformerEnd.r"]
x = PowerTransformerEnds_Terminals_SvVoltages["PowerTransformerEnd.x"]
u = PowerTransformerEnds_Terminals_SvVoltages["PowerTransformerEnd.ratedU"]

v = PowerTransformerEnds_Terminals_SvVoltages["SvVoltage.v"]
angle = PowerTransformerEnds_Terminals_SvVoltages["SvVoltage.angle"]

S_base = 100


