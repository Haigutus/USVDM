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
# TODO add locationa data -> from GL or from https://nominatim.openstreetmap.org/search?q=%22leisi,%20Eesti%22&format=json
# TODO handle BusBars/Sections
VoltageLevels_Substations_BaseVolatge = pandas.merge(data.type_tableview("VoltageLevel").reset_index(), data.type_tableview("Substation").reset_index(), left_on="VoltageLevel.Substation", right_on="ID", suffixes=("_VoltageLevel", "_Substation"))
VoltageLevels_Substations_BaseVolatge = VoltageLevels_Substations_BaseVolatge.merge(data.type_tableview("BaseVoltage")[["BaseVoltage.nominalVoltage"]], left_on="VoltageLevel.BaseVoltage", right_on="ID")
# TODO add from and to columns
# TODO add boundary nodes and their containers
# TODO add substation locations
BoundaryPoints = data.merge(data.query("KEY == 'ConnectivityNode.boundaryPoint' and VALUE == 'true'")["ID"]).type_tableview("ConnectivityNode")
loads = pandas.concat([data.type_tableview("NonConformLoad"), data.type_tableview("ConformLoad")])

# Data on lines
# TODO - add line rates (attached to terminals)
ACLineSegments_Terminals_ConnectivityNodes = pandas.merge(data.type_tableview("ACLineSegment")[["IdentifiedObject.name"]].reset_index(), data.type_tableview("Terminal").reset_index(), left_on="ID", right_on="Terminal.ConductingEquipment", suffixes=("_ACLineSegment", "_Terminal"))
ACLineSegments_Terminals_ConnectivityNodes = ACLineSegments_Terminals_ConnectivityNodes.merge(data.type_tableview("ConnectivityNode")[["ConnectivityNode.ConnectivityNodeContainer"]], left_on="Terminal.ConnectivityNode", right_on="ID")


# Merge all together
ACLineSegments_Substations = ACLineSegments_Terminals_ConnectivityNodes.merge(VoltageLevels_Substations_BaseVolatge, left_on="ConnectivityNode.ConnectivityNodeContainer", right_on="ID_VoltageLevel")

toplogy_json = {}

#     "grid-nodes":[
# {
#       "node-id": "DSO1",
#       "grid-node-type": "HIGH_VOLTAGE_NODE",
#       "node-name": "Example Name",
#       "nominal-voltage-kV": 380,
#       "max-voltage-kV": 380,
#       "min-voltage-kV": 380,
#       "slack": true,
#       "critical": true
# }],
#
# "conducting-equipment": [
#     {
#       "connected-from-node": {
#         "node-id": "DSO1",
#         "system-operator": "123456789DSOPTDF"
#       },
#       "connected-to-node-id": "DSO2",
#       "conducting-equipment-id": "CE1",
#       "conducting-equipment-type": "HV overhead line",
#       "conducting-equipment-name": "AHXW240",
#       "max-apparent-power-flow-kVA": "19000",
#       "critical": "true"
#     },

# Convert to Nodes
substation_nodes = ACLineSegments_Substations.drop_duplicates("ID_Substation")[["ID_Substation", "IdentifiedObject.name_Substation"]] #"BaseVoltage.nominalVoltage"
nodes = substation_nodes.rename(columns={"ID_Substation": "node-id", "IdentifiedObject.name_Substation": "node-name"})
nodes["grid-node-type"] = "PRIMARY_SUBSTATION"
toplogy_json["grid-nodes"] = nodes.to_dict("records")
# TODO - Add grid connection point nodes with EIC

# Convert to Branches
line_branch_columns = ["ID_ACLineSegment", "ID_Substation", "IdentifiedObject.name_Substation", "IdentifiedObject.name_ACLineSegment", "BaseVoltage.nominalVoltage"]
line_branches = pandas.merge(ACLineSegments_Substations[line_branch_columns], ACLineSegments_Substations[line_branch_columns], how="inner", on="ID_ACLineSegment", suffixes=("_from", "_to"))
line_branches = line_branches[(line_branches["ID_Substation_from"] != line_branches["ID_Substation_to"])]

node_mapping = {"ID_ACLineSegment": "conducting-equipment-id",
                "IdentifiedObject.name_ACLineSegment_to": "conducting-equipment-name",
                "ID_Substation_from": "connected-from-node-id",
                "ID_Substation_to": "connected-to-node-id"
                }
branches = line_branches[node_mapping.keys()].rename(columns=node_mapping)
branches["conducting-equipment-type"] = "cim:ACLineSegment"
system_operator = "10X1001A1001A39W"
toplogy_json["conducting-equipment"] = [{("connected-from-node" if key=="connected-from-node-id" else key):({"node-id":value, "system-operator": system_operator} if key=="connected-from-node-id" else value) for (key,value) in element.items()} for element in branches.to_dict("records")]

print(toplogy_json)

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