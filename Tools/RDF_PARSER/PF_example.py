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

path = "/home/kristjan/GIT/USVDM/Tools/RDF_PARSER/TestConfigurations_packageCASv2.0/MicroGrid/BaseCase_BC/CGMES_v2.4.15_MicroGridTestConfiguration_BC_Assembled_v2.zip"

#path = r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"

data = load_all_to_dataframe([path])

print("Loaded types")
print(data[(data.KEY == "Type")]["VALUE"].value_counts())

# Generate classical data views needed to extract relevant data

ACLineSegments          = data.type_tableview("ACLineSegment")
Terminals               = data.type_tableview("Terminal")
SvVoltages              = data.type_tableview("SvVoltage")
SvPowerFlows            = data.type_tableview("SvPowerFlow")
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

#admittance_matrix = branches[["Terminal.ConductingEquipment","SvVoltage.TopologicalNode_x", "SvVoltage.TopologicalNode_y"]].pivot(index = "SvVoltage.TopologicalNode_x", columns = "SvVoltage.TopologicalNode_y") # Does not work with complex



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

# Reset index to keep UUID
SynchronousMachines = data.type_tableview("SynchronousMachine")
SynchronousMachines = pandas.merge(SynchronousMachines.reset_index(), Terminals.reset_index(), suffixes=('', '_Terminal'),    how = "inner", left_on = "ID", right_on = 'Terminal.ConductingEquipment')
SynchronousMachines = pandas.merge(SynchronousMachines, SvVoltages,              suffixes=('', '_SvVoltage'),   how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')
SynchronousMachines = pandas.merge(SynchronousMachines, SvPowerFlows,            suffixes=('', '_SvPowerFlow'), how = "inner", left_on = 'ID_Terminal', right_on = 'SvPowerFlow.Terminal')

#['Equipment.EquipmentContainer', 'Equipment.aggregate', 'IdentifiedObject.description', 'IdentifiedObject.name', 'IdentifiedObject.shortName', 'RegulatingCondEq.RegulatingControl', 'RegulatingCondEq.controlEnabled', 'RotatingMachine.GeneratingUnit', 'RotatingMachine.p', 'RotatingMachine.q', 'RotatingMachine.ratedPowerFactor', 'RotatingMachine.ratedS', 'RotatingMachine.ratedU', 'SynchronousMachine.InitialReactiveCapabilityCurve', 'SynchronousMachine.earthing', 'SynchronousMachine.earthingStarPointR', 'SynchronousMachine.earthingStarPointX', 'SynchronousMachine.ikk', 'SynchronousMachine.maxQ', 'SynchronousMachine.minQ', 'SynchronousMachine.mu', 'SynchronousMachine.operatingMode', 'SynchronousMachine.qPercent', 'SynchronousMachine.r', 'SynchronousMachine.r0', 'SynchronousMachine.r2', 'SynchronousMachine.referencePriority', 'SynchronousMachine.satDirectSubtransX', 'SynchronousMachine.satDirectSyncX', 'SynchronousMachine.satDirectTransX', 'SynchronousMachine.shortCircuitRotorType', 'SynchronousMachine.type', 'SynchronousMachine.voltageRegulationRange', 'SynchronousMachine.x0', 'SynchronousMachine.x2', 'Type_x', 'ID', 'ACDCTerminal.connected', 'ACDCTerminal.sequenceNumber', 'IdentifiedObject.description_Terminal', 'IdentifiedObject.energyIdentCodeEic', 'IdentifiedObject.name_Terminal', 'IdentifiedObject.shortName_Terminal', 'Terminal.ConductingEquipment', 'Terminal.ConnectivityNode', 'Terminal.TopologicalNode', 'Terminal.phases', 'Type_Terminal', 'SvVoltage.TopologicalNode', 'SvVoltage.angle', 'SvVoltage.v', 'Type_SvVoltage', 'SvPowerFlow.Terminal', 'SvPowerFlow.p', 'SvPowerFlow.q', 'Type_y']
print(SynchronousMachines[["ID", 'IdentifiedObject.name', 'RegulatingCondEq.controlEnabled', 'RotatingMachine.GeneratingUnit', 'RotatingMachine.p', 'RotatingMachine.q', 'RotatingMachine.ratedPowerFactor', 'RotatingMachine.ratedS', 'RotatingMachine.ratedU', 'SynchronousMachine.maxQ', 'SynchronousMachine.referencePriority', 'SynchronousMachine.voltageRegulationRange', 'ACDCTerminal.connected', 'SvVoltage.angle', 'SvVoltage.v', 'SvPowerFlow.p', 'SvPowerFlow.q']])


def tableview_by_IDs(data, IDs_dataframe, IDs_column_name):
    """Filters tripelstore by provided IDs and returns tabular view, IDs- as indexes and KEY-s as columns"""
    class_name = IDs_column_name.split(".")[1]
    meta_separator = "_"
    result = pandas.merge(IDs_dataframe, data, left_on = IDs_column_name, right_on ="ID", how="inner", suffixes=('', meta_separator + class_name))[["ID_" + class_name, "KEY", "VALUE"]].drop_duplicates(["ID" + meta_separator + class_name, "KEY"]).pivot(index="ID" + meta_separator + class_name, columns ="KEY")["VALUE"]

    return  result

#GeneratingUnits = pandas.merge(SynchronousMachines, data, left_on = "RotatingMachine.GeneratingUnit", right_on = "ID", how= "inner", suffixes=('', '_GeneratingUnit'))[["ID_GeneratingUnit", "KEY", "VALUE"]].drop_duplicates(["ID_GeneratingUnit", "KEY"]).pivot(index="ID_GeneratingUnit", columns = "KEY")["VALUE"]

GeneratingUnits = tableview_by_IDs(data, SynchronousMachines, "RotatingMachine.GeneratingUnit")


SynchronousMachines = pandas.merge(SynchronousMachines, GeneratingUnits, left_on = "RotatingMachine.GeneratingUnit", right_index = True, how= "inner", suffixes=('', '_GeneratingUnit'))

RegulatingControls = tableview_by_IDs(data, SynchronousMachines,'RegulatingCondEq.RegulatingControl')


# Join views to get needed AC line data
ACLineSegments = data.type_tableview("ACLineSegment")
ACLineSegments = pandas.merge(ACLineSegments.reset_index(), Terminals.reset_index(), suffixes=('', '_Terminal'), how = "inner", left_on = "ID", right_on = 'Terminal.ConductingEquipment')

#ACLineSegments = pandas.merge(ACLineSegments, SvVoltages,              suffixes=('', '_SvVoltage'),   how = "inner", left_on = 'Terminal.TopologicalNode', right_on = 'SvVoltage.TopologicalNode')
#ACLineSegments = pandas.merge(ACLineSegments, SvPowerFlows,            suffixes=('', '_SvPowerFlow'), how = "inner", left_on = 'ID_Terminal', right_on = 'SvPowerFlow.Terminal')

ConductingEquipment_terminals = pandas.merge(Terminals.reset_index(), Terminals.reset_index(), how = "inner", on = "Terminal.ConductingEquipment")