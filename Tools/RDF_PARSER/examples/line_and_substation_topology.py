import sys
sys.path.append("..")
import pandas
import RDF_parser
import CGMES_tools
from pyvis.network import Network

data = pandas.read_RDF([r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS_ENHANCED\20220629T2330Z_ELERING_EQ_001.xml",
                        r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS_ENHANCED\20210504T0000Z__ENTSOE_EQBD_005.xml"])


# We can connect/aggregate all trough Substations
# CN -> Bay -> VoltageLevel -> Substation
# Line -> Terminal -> CN -> Substation
# Loads (with eic) -> CN -> Substation

# Data item to map CN-s to Substations
VoltageLevels_Substations_BaseVolatge = pandas.merge(data.type_tableview("VoltageLevel").reset_index(), data.type_tableview("Substation").reset_index(), left_on="VoltageLevel.Substation", right_on="ID", suffixes=("_VoltageLevel", "_Substation"))
VoltageLevels_Substations_BaseVolatge = VoltageLevels_Substations_BaseVolatge.merge(data.type_tableview("BaseVoltage")[["BaseVoltage.nominalVoltage"]], left_on="VoltageLevel.BaseVoltage", right_on="ID")

# Data on lines
# TODO - add line rates
ACLineSegments_Terminals_ConnectivityNodes = pandas.merge(data.type_tableview("ACLineSegment")[["IdentifiedObject.name"]].reset_index(), data.type_tableview("Terminal").reset_index(), left_on="ID", right_on="Terminal.ConductingEquipment", suffixes=("_ACLineSegment", "_Terminal"))
ACLineSegments_Terminals_ConnectivityNodes = ACLineSegments_Terminals_ConnectivityNodes.merge(data.type_tableview("ConnectivityNode")[["ConnectivityNode.ConnectivityNodeContainer"]], left_on="Terminal.ConnectivityNode", right_on="ID")

# Merge all together
ACLineSegments_Substations = ACLineSegments_Terminals_ConnectivityNodes.merge(VoltageLevels_Substations_BaseVolatge, left_on="ConnectivityNode.ConnectivityNodeContainer", right_on="ID_VoltageLevel")

# Convert to Branches
line_branch_columns = ["ID_ACLineSegment", "ID_Substation", "IdentifiedObject.name_Substation", "IdentifiedObject.name_ACLineSegment", "BaseVoltage.nominalVoltage"]
line_branches = pandas.merge(ACLineSegments_Substations[line_branch_columns], ACLineSegments_Substations[line_branch_columns], how="inner", on="ID_ACLineSegment", suffixes=("_from", "_to"))
line_branches = line_branches[(line_branches["ID_Substation_from"] != line_branches["ID_Substation_to"])]
branches = line_branches[["ID_ACLineSegment", "ID_Substation_from", "ID_Substation_to"]].to_dict("records")

# Convert to Nodes
substation_nodes = ACLineSegments_Substations.drop_duplicates("ID_Substation")[["ID_Substation", "IdentifiedObject.name_Substation", "BaseVoltage.nominalVoltage"]]
nodes = substation_nodes.to_dict("records")
# TODO - Add grid connection point nodes

graph = Network(directed=False, width="100%", height="100%", notebook=False)

colour_map = {110.0: "#B23CFD", 330.0: "#FFA900", 6.0: "#39C0ED", 35.0: "#FF8800"}


graph.add_nodes(tuple(substation_nodes["ID_Substation"]), label=tuple(substation_nodes["IdentifiedObject.name_Substation"]))


#connections = tuple(line_branches[["ID_Substation_from", "ID_Substation_to"]].to_records(index=False))

for id, branch in line_branches.T.iteritems():
    graph.add_edge(branch["ID_Substation_from"], branch["ID_Substation_to"], color=colour_map.get(branch["BaseVoltage.nominalVoltage_from"], "#39C0ED"))


graph.toggle_physics(True)
#graph.show_buttons()
#graph.set_options()
graph.show('network.html')