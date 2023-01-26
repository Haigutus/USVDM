import pandas
import uuid
import json
import sys
from decimal import Decimal
from shapely.geometry import Point, MultiPoint, box

sys.path.append("..")
from RDF_parser import *
import CGMES_tools

pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.width', 1000)

#path = r"C:\Users\kristjan.vilgo\Documents\GitHub\Baasetalon\kehtiv_CIM_versioon\SCADA_EMS_CIM\20211201T2130Z_24_ELERING_TP_001.zip"
#path = r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS\SCADA_EMS_CIM.zip"
path = r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS\20220701_SCADA_EMS.zip"
path = r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS\SCADA_EMS_EXPORT_2022-10-25T0928.zip"
#path = r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS\SCADA_EMS_EXPORT_2022-11-30T1306.zip"

data = pandas.read_RDF([path])

profiles = data.query("KEY == 'Model.profile'")#.set_index("VALUE").INSTANCE_ID

# Create map of instance ID-s
profile_keywords = {
    'EquipmentCore': {'keyword': 'EQ'},
    'SteadyStateHypothesis': {'keyword': 'SSH'},
    'Topology/': {'keyword': 'TP'},
    'StateVariables': {'keyword': 'SV'}
}

for profile_name, profile in profile_keywords.items():
    profile_data = pandas.DataFrame(profiles[profiles.VALUE.str.contains(profile_name)])

    profile_data["KEY"] = "Model.messageType"
    profile_data["VALUE"] = profile["keyword"]
    data = data.append(profile_data)

    profile_keywords[profile_name]["ID"] = profile_data.iloc[0].ID
    profile_keywords[profile_name]["INSTANCE_ID"] = profile_data.iloc[0].INSTANCE_ID

EQ_INSTANCE_ID = profile_keywords["EquipmentCore"]["INSTANCE_ID"]
TP_INSTANCE_ID = profile_keywords["Topology/"]["INSTANCE_ID"]


# Fix connectivity nodes
terminals_missing_CN = data.query("KEY == 'Type' and VALUE == 'Terminal'").drop_duplicates("ID").merge(data.query("KEY == 'Terminal.ConnectivityNode'").ID, indicator=True, how="outer").query("_merge == 'left_only'").ID

connecting_equipment_missing_CN = data.merge(data.merge(terminals_missing_CN).query("KEY == 'Terminal.ConductingEquipment'")[["VALUE"]].rename(columns={"VALUE": "ID"}))#.query("KEY == 'IdentifiedObject.name' or KEY == 'Type'")

missing_CN_report = connecting_equipment_missing_CN.query("KEY == 'IdentifiedObject.name'")[["ID", "VALUE"]]\
    .merge(connecting_equipment_missing_CN.query("KEY == 'Type'")[["ID", "VALUE"]], on="ID", suffixes=["_EQ_NAME", "_EQ_TYPE"])\
    .merge(connecting_equipment_missing_CN.query("KEY == 'ConductingEquipment.BaseVoltage'")[["ID", "VALUE"]].rename(columns={"VALUE": "ConductingEquipment.BaseVoltage"}), on="ID")\
    .merge(data.merge(terminals_missing_CN)\
    .type_tableview("Terminal").reset_index()[["IdentifiedObject.name", "ACDCTerminal.sequenceNumber", "ID", "Terminal.ConductingEquipment"]], left_on="ID", right_on="Terminal.ConductingEquipment", suffixes=["_EQ", "_TERMINAL"])\
    .drop_duplicates()
missing_CN_report["IdentifiedObject.name_LINE"] = missing_CN_report.VALUE_EQ_NAME.str.replace(" ", "").str[0:4]
#117114  05dcf690-213b-46ac-a3e8-d92ae45d1681                                        Type                      ConnectivityNode  b903c6fe-09af-43ca-8209-2e6c3c275618
#117115  05dcf690-213b-46ac-a3e8-d92ae45d1681                       IdentifiedObject.name                                131.21  b903c6fe-09af-43ca-8209-2e6c3c275618
#117116  05dcf690-213b-46ac-a3e8-d92ae45d1681  ConnectivityNode.ConnectivityNodeContainer  4bca4299-17fe-4246-bed4-30e641800e46  b903c6fe-09af-43ca-8209-2e6c3c275618

#                                        ID                                  KEY                                 VALUE                           INSTANCE_ID ISNTANCE_ID
#2946  399b01a6-667c-4941-8f23-711573079d8a                                 Type                                  Line  0308e2ff-e42b-475e-b10e-00e0ab7a80cf         NaN
#2947  399b01a6-667c-4941-8f23-711573079d8a                          Line.Region  d81cedde-fca0-4ab8-9604-33e4a8839325  0308e2ff-e42b-475e-b10e-00e0ab7a80cf         NaN
#2948  399b01a6-667c-4941-8f23-711573079d8a                IdentifiedObject.name                        81-Tartu-Pskov  0308e2ff-e42b-475e-b10e-00e0ab7a80cf         NaN
#2949  399b01a6-667c-4941-8f23-711573079d8a           IdentifiedObject.shortName                                  L358  0308e2ff-e42b-475e-b10e-00e0ab7a80cf         NaN
#2950  399b01a6-667c-4941-8f23-711573079d8a         IdentifiedObject.description         AC tie line between EE and RU  0308e2ff-e42b-475e-b10e-00e0ab7a80cf         NaN
#2951  399b01a6-667c-4941-8f23-711573079d8a  IdentifiedObject.energyIdentCodeEic                      10T-EE-RU-00001M  0308e2ff-e42b-475e-b10e-00e0ab7a80cf         NaN

# Fix L502 name in BDS
data.loc[data.query("ID == '6a3a841d-c2a8-45ee-941c-6697cf1800ca' and KEY == 'IdentifiedObject.shortName'").index[0], "VALUE"] = "L502"

# Fix L677 name in BDS
data.loc[data.query("ID == '3a7890d1-5fde-422a-a911-2993aa9' and KEY == 'IdentifiedObject.shortName'").index[0], "VALUE"] = "L677"



# Turn regulating control off on Pärnu CHP. 2022-11-02 wrong setpoint
#data.loc[data.query("ID == '0f4f29f1-d566-46a6-85e4-ab345e798123' and KEY == 'RegulatingCondEq.controlEnabled'").index, "VALUE"] = "false"


# Add missing CN-id
data_to_add = []
for line_name, terminals in missing_CN_report.groupby("IdentifiedObject.name_LINE"):

    # Find existing line ID or create new line
    line_ID = data.query("VALUE == @line_name")

    if len(line_ID) > 0:
        line_ID = line_ID.iloc[0].ID
        cn_ID = data.references_to_simple(line_ID).reset_index().query("Type == 'ConnectivityNode'").iloc[0].ID_FROM
        tn_ID = data.references_to_simple(line_ID).reset_index().query("Type == 'TopologicalNode'").iloc[0].ID_FROM

    else:
        # Create/Get needed ID-s
        line_ID = str(uuid.uuid5(uuid.NAMESPACE_OID, f"Line:{line_name}"))
        cn_ID = str(uuid.uuid5(uuid.NAMESPACE_OID, f"ConnectivityNode:{line_name}"))
        tn_ID = str(uuid.uuid5(uuid.NAMESPACE_OID, f"TopologicalNode:{line_name}"))
        #region_ID = data.merge(data.query("KEY == 'Type' and VALUE == 'GeographicalRegion'").ID).query("VALUE == 'Estonia'").iloc[0].ID
        region_ID = "de92e3fa-13f0-4608-bedb-06cb41b823b1" # Needs to be SGR

        data_to_add.extend([
            # Create Lines in EQ
            (line_ID, "Type", "Line", EQ_INSTANCE_ID),
            (line_ID, "Line.Region", region_ID, EQ_INSTANCE_ID),
            (line_ID, "IdentifiedObject.name", line_name, EQ_INSTANCE_ID),
            (line_ID, "IdentifiedObject.shortName", line_name, EQ_INSTANCE_ID),

            # Create CN in EQ
            (cn_ID, "Type", "ConnectivityNode", EQ_INSTANCE_ID),
            (cn_ID, "IdentifiedObject.name", f"Missing CN {line_name}", EQ_INSTANCE_ID),
            (cn_ID, "ConnectivityNode.ConnectivityNodeContainer", line_ID, EQ_INSTANCE_ID),

            # Create CN in TP
            (cn_ID, "Type", "ConnectivityNode", TP_INSTANCE_ID),
            (cn_ID, "ConnectivityNode.TopologicalNode", tn_ID, TP_INSTANCE_ID),

            # Create TN in TP
            (tn_ID, "Type", "TopologicalNode", TP_INSTANCE_ID),
            (tn_ID, "IdentifiedObject.name", f"Missing TN {line_name}", TP_INSTANCE_ID),
            (tn_ID, "TopologicalNode.ConnectivityNodeContainer", line_ID, TP_INSTANCE_ID),
            (tn_ID, "TopologicalNode.BaseVoltage", terminals["ConductingEquipment.BaseVoltage"].iloc[0], TP_INSTANCE_ID),
        ])

    for terminal in terminals.itertuples():

        terminal_ID = terminal.ID_TERMINAL

        data_to_add.extend([
            (terminal_ID, "Terminal.ConnectivityNode", cn_ID, EQ_INSTANCE_ID),
            #(terminal_ID, "Terminal.TopologicalNode", tn_ID, TP_INSTANCE_ID),
        ])

data = data.append(pandas.DataFrame(data_to_add, columns=["ID", "KEY", "VALUE", "INSTANCE_ID"]))

### Connect all terminals
#data.query("KEY == 'Type'")[["ID", "VALUE"]].merge(data.query("KEY == 'Terminal.ConductingEquipment'"), suffixes=["_EQUIPMENT", ""], left_on="ID", right_on="VALUE")
data.loc[data.query("KEY == 'ACDCTerminal.connected'").index, "VALUE"] = "true"


### Fix negative ConformLoads to NonConformLoads

# Find all negative loads
negative_loads = data.query("KEY == 'EnergyConsumer.p'").astype({'VALUE': 'float'}).query("VALUE < 0")

# Find negative ConformLoads
negative_conform_loads = data.reset_index().merge(negative_loads.ID).query("KEY == 'Type' & VALUE == 'ConformLoad'").set_index("index")

# Change class to NonConformLoad on negative Conformloads
negative_conform_loads.VALUE = "NonConformLoad"
data.update(negative_conform_loads)

# Remove reference to Conformload LoadGroup as we need to add NonConform LoadGroup later
data = data.drop(data.reset_index().merge(negative_conform_loads.ID).query("KEY == 'ConformLoad.LoadGroup'")["index"])


### Link ConformLoads to ControlArea ###

# ConformLoad -> ConformLoadGroup -> SubLoadArea -> LoadArea <- ControlArea

items = ["ControlArea", "LoadArea", "SubLoadArea", "ConformLoadGroup", "NonConformLoadGroup"]

data_to_add = pandas.DataFrame()

instance_id = EQ_INSTANCE_ID

objects_list = []

eq = data.query("INSTANCE_ID == @instance_id")

# Lets first check if all needed items exist and what is their ID, if it does not exist, lets create ID for them
items_data = {}

for item in items:
    item_data = eq.query("KEY == 'Type' & VALUE == @item")

    # In case of missing or if we have a load group, create new object
    if item_data.empty or "LoadGroup" in item:
        item_ID = str(uuid.uuid4())
        item_exists = False

    else:
        item_ID = item_data.ID.item()
        item_exists = True

    items_data[item] = {"ID": item_ID, "exists": item_exists}


# Lets add all missing elements

for object_type, item in items_data.items():

    if not item["exists"]:

        print(f"INFO - Adding {object_type}")

        object_data = [
            (item["ID"], 'IdentifiedObject.name', f'Default{object_type}', instance_id),
            (item["ID"], 'IdentifiedObject.description', 'Added for CGM BP IOP', instance_id),
            (item["ID"], 'Type', object_type, instance_id),
        ]

        # TODO - add also correct EIC form boundary
        if object_type == "ControlArea":
            object_data.append((item["ID"], "ControlArea.type", r"http://iec.ch/TC57/2013/CIM-schema-cim16#ControlAreaTypeKind.Interchange"))

        objects_list.extend(object_data)


# Add all missing links

# Definition of item links
# Links are added later, because maybe item existed, but we still want to add the link if missing

items_links = [
               #{"from": "ConformLoad", "to": "ConformLoadGroup", "link_name": "ConformLoad.ConformLoadGroup"},
               {"from": "ConformLoadGroup", "to": "SubLoadArea", "link_name": "LoadGroup.SubLoadArea"},
               {"from": "NonConformLoadGroup", "to": "SubLoadArea", "link_name": "LoadGroup.SubLoadArea"},
               {"from": "SubLoadArea", "to": "LoadArea", "link_name": "SubLoadArea.LoadArea"},
               #{"from": "LoadArea", "to": "ControlArea", "link_name": "EnergyArea.ControlArea"},
               {"from": "ControlArea", "to": "LoadArea", "link_name": "ControlArea.EnergyArea"}
]


for link in items_links:
    objects_list.append((items_data[link["from"]]["ID"], link["link_name"], items_data[link["to"]]["ID"], instance_id))

data_to_add = data_to_add.append(pandas.DataFrame(objects_list, columns=["ID", "KEY", "VALUE", "INSTANCE_ID"]), ignore_index=True)

# Add LoadGroups to default SubLoadArea

All_ConformLoadGroups_ID = eq.query("KEY == 'Type' & VALUE == 'ConformLoadGroup'")
All_ConformLoadGroups = eq.merge(All_ConformLoadGroups_ID.ID, on="ID")
Contained_ConformLoadGroups_ID = All_ConformLoadGroups.query("KEY == 'ConformLoad.LoadGroup'")

Not_Contained_ConformLoadGroups = Contained_ConformLoadGroups_ID.append(All_ConformLoadGroups_ID)[["ID"]].drop_duplicates(keep=False)

if not Not_Contained_ConformLoadGroups.empty:
    print(f"INFO - Adding {len(Not_Contained_ConformLoadGroups)} ConformLoadGroups to SubLoadArea {items_data['SubLoadArea']['ID']}")

    Not_Contained_ConformLoadGroups["KEY"] = "LoadGroup.SubLoadArea"
    Not_Contained_ConformLoadGroups["VALUE"] = items_data["SubLoadArea"]["ID"]
    Not_Contained_ConformLoadGroups["INSTANCE_ID"] = instance_id

    data_to_add = data_to_add.append(Not_Contained_ConformLoadGroups, ignore_index=True)

# Add ConformLoads to default LoadGroup

All_ConformLoads_ID = eq.query("KEY == 'Type' & VALUE == 'ConformLoad'")
All_ConformLoads    = eq.merge(All_ConformLoads_ID.ID, on="ID")
Contained_ConformLoads_ID = All_ConformLoads.query("KEY == 'ConformLoad.LoadGroup'")

Not_Contained_ConformLoads = Contained_ConformLoads_ID.append(All_ConformLoads_ID)[["ID"]].drop_duplicates(keep=False)


if not Not_Contained_ConformLoads.empty:

    print(f"INFO - Adding {len(Not_Contained_ConformLoads)} ConformLoads to ConformLoadGroup {items_data['ConformLoadGroup']['ID']}")

    Not_Contained_ConformLoads["KEY"] = "ConformLoad.LoadGroup"
    Not_Contained_ConformLoads["VALUE"] = items_data["ConformLoadGroup"]["ID"]
    Not_Contained_ConformLoads["INSTANCE_ID"] = instance_id

    data_to_add = data_to_add.append(Not_Contained_ConformLoads, ignore_index=True)

# Add NonConformLoads to default LoadGroup

All_NonConformLoads_ID = eq.query("KEY == 'Type' & VALUE == 'NonConformLoad'")
All_NonConformLoads = eq.merge(All_NonConformLoads_ID.ID, on="ID")
Contained_NonConformLoads_ID = All_NonConformLoads.query("KEY == 'NonConformLoad.LoadGroup'")

Not_Contained_NonConformLoads = Contained_NonConformLoads_ID.append(All_NonConformLoads_ID)[["ID"]].drop_duplicates(keep=False)

if not Not_Contained_NonConformLoads.empty:

    print(f"INFO - Adding {len(Not_Contained_NonConformLoads)} NonConformLoads to NonConformLoadGroup {items_data['NonConformLoadGroup']['ID']}")

    Not_Contained_NonConformLoads["KEY"] = "NonConformLoad.LoadGroup"
    Not_Contained_NonConformLoads["VALUE"] = items_data["NonConformLoadGroup"]["ID"]
    Not_Contained_NonConformLoads["INSTANCE_ID"] = instance_id

    data_to_add = data_to_add.append(Not_Contained_NonConformLoads, ignore_index=True)

print(f"INFO - END fixing Loads in EQ {instance_id}")

data = data.append(data_to_add, ignore_index=True)
data = data.drop_duplicates()


## Set non patl limits with 15min duration
#TODO - high and low Voltage limits should be allewd without duration - chekc QoCDC
non_patl_limits = data.query("KEY == 'OperationalLimitType.limitType'")[~data.query("KEY == 'OperationalLimitType.limitType'").VALUE.str.contains("patl")]
non_patl_limits["KEY"] = "OperationalLimitType.acceptableDuration"
non_patl_limits["VALUE"] = str(15*60)  # Default is 15 min
data = data.append(non_patl_limits, ignore_index=True)
data = data.drop_duplicates()


### Find all machines out of PQ limits and expand PQ limits ###
curve_data = data.type_tableview("CurveData")
synchronous_machine = data.type_tableview("SynchronousMachine").reset_index()
generating_units = CGMES_tools.get_GeneratingUnits(data)
Terminals = data.type_tableview("Terminal")
SvPowerFlow = data.type_tableview("SvPowerFlow")

# Separate to coordinate pairs
first_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y1value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y1value": "y"})
second_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y2value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y2value": "y"})  # TODO Y2 might not exist, so drop NA?
all_points = first_point.append(second_point)

# Convert to coordinate points
all_points["PQ_area"] = all_points[["x", "y"]].apply(Point, axis=1)

# Lets group points and create polygons by using the convex hull function
curve_polygons = all_points.groupby("CurveData.Curve")["PQ_area"].apply(lambda x: MultiPoint(x).convex_hull)

# Merge all needed data
machine_data = synchronous_machine.merge(curve_polygons, left_on="SynchronousMachine.InitialReactiveCapabilityCurve", right_on="CurveData.Curve", how="left")
machine_data = machine_data.merge(generating_units, left_on='RotatingMachine.GeneratingUnit', right_index=True, how="left", suffixes=("", "GeneratingUnit"))
machine_data = machine_data.merge(Terminals.reset_index(), right_on='Terminal.ConductingEquipment', left_on="ID", how="left", suffixes=("", "_Terminal"))
machine_data = machine_data.merge(SvPowerFlow.reset_index(), right_on='SvPowerFlow.Terminal', left_on="ID_Terminal", how="left", suffixes=("", "_SvPowerFlow"))

# Convert to spacial objects
machine_data["PQ_setpoint"] = machine_data[['RotatingMachine.p', 'RotatingMachine.q']].multiply(-1).apply(Point, axis=1)
machine_data["PQ_solution"] = machine_data[['SvPowerFlow.p', 'SvPowerFlow.q']].multiply(-1).apply(Point, axis=1)
machine_data["PQ_limits"] = machine_data[['GeneratingUnit.minOperatingP', 'SynchronousMachine.minQ', 'GeneratingUnit.maxOperatingP', 'SynchronousMachine.maxQ']].dropna().apply(pandas.to_numeric, errors='ignore').apply(lambda x: box(x['GeneratingUnit.minOperatingP'], x['SynchronousMachine.minQ'], x['GeneratingUnit.maxOperatingP'], x['SynchronousMachine.maxQ']), axis=1)

#out_of_limits = machine_data[~machine_data.apply(lambda x: x["point"].contains(x["solution"]), axis=1)]
machine_data["area_distance"] = machine_data.dropna(subset=["PQ_area"]).apply(lambda x: x["PQ_area"].distance(x["PQ_setpoint"]), axis=1)
machine_data["limits_distance"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: x["PQ_limits"].distance(x["PQ_setpoint"]), axis=1)

# Find machines outside of PQ area or PQ limits
out_of_limits = machine_data.query("area_distance > 0 or limits_distance > 0")
print(f"WARN - {len(out_of_limits)} Synchronous Machines out of limits")

PQ_curve_out_of_PQ_limits = machine_data.dropna(subset=["PQ_area"])[~machine_data.dropna(subset=["PQ_area"]).apply(lambda x: x.PQ_limits.contains(x.PQ_area), axis=1)]

# curve.bounds -> (Pmin, Qmin, Pmax, Qmax)
# Update limits to fit PQ area
PQ_curve_out_of_PQ_limits[['GeneratingUnit.minOperatingP', 'SynchronousMachine.minQ', 'GeneratingUnit.maxOperatingP', 'SynchronousMachine.maxQ']] = PQ_curve_out_of_PQ_limits.apply(lambda x: x.PQ_area.bounds, axis=1, result_type="expand")
data = data.update_triplet_from_tableview(PQ_curve_out_of_PQ_limits[['ID', 'SynchronousMachine.minQ', 'SynchronousMachine.maxQ']], update=True, add=False, instance_id=EQ_INSTANCE_ID)
data = data.update_triplet_from_tableview(PQ_curve_out_of_PQ_limits[['RotatingMachine.GeneratingUnit', 'GeneratingUnit.minOperatingP', 'GeneratingUnit.maxOperatingP']].rename(columns={'RotatingMachine.GeneratingUnit': "ID"}), update=True, add=False, instance_id=EQ_INSTANCE_ID)

# TODO - report missing EIC on Generating Units

# Get Load data
load_data = data.type_tableview('ConformLoad')
load_data = load_data.append(data.type_tableview('NonConformLoad'))
load_data = load_data.reset_index().merge(Terminals.reset_index(), right_on='Terminal.ConductingEquipment', left_on="ID", how="left", suffixes=("", "_Terminal"))
load_data = load_data.merge(SvPowerFlow.reset_index(), right_on='SvPowerFlow.Terminal', left_on="ID_Terminal", how="left", suffixes=("", "_SvPowerFlow"))

# Get TieFlow data
tieflow_data = data.type_tableview('TieFlow').reset_index()
tieflow_data = tieflow_data.merge(SvPowerFlow.reset_index(), right_on='SvPowerFlow.Terminal', left_on="TieFlow.Terminal", how="left", suffixes=("", "_SvPowerFlow"))

generation_p = machine_data["SvPowerFlow.p"].sum()
generation_q = machine_data["SvPowerFlow.q"].sum()
load_p = load_data["SvPowerFlow.p"].sum()
load_q = load_data["SvPowerFlow.q"].sum()
tieflow_p = tieflow_data["SvPowerFlow.p"].sum()
tieflow_q = tieflow_data["SvPowerFlow.q"].sum()

print(f"""
Generation:     {generation_p*-1:.1f} MW
Load:           {load_p:.1f} MW
NP (gen-con):   {(generation_p + load_p)*-1:.1f} MW
NP (tieflow):   {tieflow_p:.1f} MW
NP (CA.nI)  :   {data.type_tableview("ControlArea").iloc[0]["ControlArea.netInterchange"]} MW
Losses:         {(load_p + tieflow_p + generation_p)*-1:.1f} MW
""")





# Set all normally closed Switches to closed status
open_switches = data.merge(data.query("KEY == 'Switch.normalOpen' and VALUE == 'false'").ID).query("KEY == 'Switch.open' and VALUE == 'true'")
open_switches["VALUE"] = "false"
data = data.update_triplet_from_triplet(open_switches, update=True, add=False)

# # Scale Model 2023-04-19
# ACNP = 930.4
# EL1 = -32.2
# EL2 = -59.2
# load_setpoint = 1400
# generation_setpoint = (EL1 + EL2 + ACNP + load_setpoint) * -1
#
#
# # Set HVDC flows # TODO set by EIC of Connectivity Node
# data.loc[data.query("ID == '2274d9f6-3ac8-40c7-9eb2-2cac250bd824' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = EL2
# data.loc[data.query("ID == '9885bc1f-664c-41e2-aa41-68f94c7db7db' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = EL1
#
# # Set AC Flows
# RU_FLOWS = 300
# # L373
# data.loc[data.query("ID == 'cf3af93a-ad15-4db9-adc2-4e4454bb843f' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = RU_FLOWS / 2
# # L374
# data.loc[data.query("ID == 'd98ec0d4-4e25-4667-b21f-5b816a6e8871' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = RU_FLOWS / 2
#
# LV_FLOWS = ACNP - RU_FLOWS
# # L301
# data.loc[data.query("ID == '227b5f74-9791-4c09-81b1-c46857f91c54' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = LV_FLOWS / 4
# # L354
# data.loc[data.query("ID == '935dc521-a633-44b8-bbcc-dc7171449648' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = LV_FLOWS / 4
# # L502
# data.loc[data.query("ID == 'de62ee44-d086-4133-87f9-7ab99dabf2ea' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = LV_FLOWS / 4
# # L358
# data.loc[data.query("ID == 'e0786c57-57ff-454e-b9e2-7a912d81c674' and KEY == 'EquivalentInjection.p'").index, "VALUE"] = LV_FLOWS / 4


#online_machine_data = machine_data.query("`RotatingMachine.p` < 0")
#available_generation = (online_machine_data['GeneratingUnit.maxOperatingP'].astype(float) * -1) - online_machine_data['RotatingMachine.p']
# available_generation = ((machine_data['GeneratingUnit.maxOperatingP'].astype(float) * -1) - machine_data['SvPowerFlow.p']).sum()
#
# machine_data['SvPowerFlow.p'] = machine_data['SvPowerFlow.p'] + ((machine_data['GeneratingUnit.maxOperatingP'].astype(float) * -1) - machine_data['SvPowerFlow.p']) * (generation_setpoint - generation_p) / available_generation
#
#
# load_data['SvPowerFlow.p'] = load_data['SvPowerFlow.p'] + abs(load_data['SvPowerFlow.p']) * (load_setpoint - load_p) / load_p

# Update SSH values from SV
load_data[['EnergyConsumer.p', 'EnergyConsumer.q']] = load_data[['SvPowerFlow.p', 'SvPowerFlow.q']]
data = data.update_triplet_from_tableview(load_data[['ID', 'EnergyConsumer.p', 'EnergyConsumer.q']], update=True, add=False, instance_id=profile_keywords['SteadyStateHypothesis']["INSTANCE_ID"])

# Update SSH values from SV
machine_data[['RotatingMachine.p', 'RotatingMachine.q']] = machine_data[['SvPowerFlow.p', 'SvPowerFlow.q']]
data = data.update_triplet_from_tableview(machine_data[['ID', 'RotatingMachine.p', 'RotatingMachine.q']], update=True, add=False, instance_id=profile_keywords['SteadyStateHypothesis']["INSTANCE_ID"])

# Set Slack on machine with highest generation
slack_machine = machine_data.sort_values('RotatingMachine.p').iloc[1]
print(f"Setting {slack_machine['IdentifiedObject.name']} as Slack")

data.loc[data.query("ID == @slack_machine.ID and KEY == 'SynchronousMachine.referencePriority'").index, "VALUE"] = 1

# TODO select the largest island and check that machine is part of it
data.loc[data.query("KEY == 'TopologicalIsland.AngleRefTopologicalNode'").index[0]] = slack_machine["Terminal.TopologicalNode"]



# Ensure regulating control is discrete
controls = data.query("KEY == 'TapChanger.step' or KEY == 'SvTapStep.position' or KEY == 'ShuntCompensator.sections' or KEY == 'SvShuntCompensatorSections.sections'")
data.loc[controls.index, "VALUE"] = controls.VALUE.apply(lambda x: str(int(Decimal(x))))

# Set Tapchanger Neutral U to Winding neutral U
tapchanger_data = data.type_tableview("RatioTapChanger").reset_index().merge(data.type_tableview("PowerTransformerEnd"), left_on="RatioTapChanger.TransformerEnd", right_index=True)
tapchanger_data["TapChanger.neutralU"] = tapchanger_data["PowerTransformerEnd.ratedU"]
data = data.update_triplet_from_tableview(tapchanger_data[['ID', "TapChanger.neutralU"]], update=True, add=False, instance_id=EQ_INSTANCE_ID)

# Fix voltage setpoints to BaseVoltage + 7,28%
terminal_basevoltage = data.type_tableview("Terminal").reset_index().merge(data.type_tableview("ConnectivityNode"), left_on="Terminal.ConnectivityNode", right_on="ID").merge(data.type_tableview("TopologicalNode"), left_on="ConnectivityNode.TopologicalNode", right_on="ID").merge(data.type_tableview("BaseVoltage"), left_on="TopologicalNode.BaseVoltage", right_on="ID")[["ID", "BaseVoltage.nominalVoltage"]]

regulatingcontrol_basevoltage = data.key_tableview('RegulatingControl.Terminal').reset_index().merge(terminal_basevoltage, left_on="RegulatingControl.Terminal", right_on="ID", suffixes=["", "_Terminal"])
regulatingcontrol_basevoltage["RegulatingControl.targetValue_original"] = regulatingcontrol_basevoltage["RegulatingControl.targetValue"]
# TODO maybe apply per Base Voltage different %
regulatingcontrol_basevoltage["RegulatingControl.targetValue"] = regulatingcontrol_basevoltage["BaseVoltage.nominalVoltage"] * 1.0728
regulatingcontrol_basevoltage["diff"] = regulatingcontrol_basevoltage.eval("abs(`RegulatingControl.targetValue` - `RegulatingControl.targetValue_original`) / `RegulatingControl.targetValue`")
data = data.update_triplet_from_tableview(regulatingcontrol_basevoltage[["ID", "RegulatingControl.targetValue"]], update=True, add=False, instance_id=profile_keywords['SteadyStateHypothesis']["INSTANCE_ID"])

# 750

## EXPORT ###

# Set namepsaces for export


now = datetime.datetime.now()

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         #cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#",
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")

export_undefined = False
export_type      = "xml_per_instance_zip_per_all"

# Load export format configuration
with open(r"..\entsoe_v2.4.15_2014-08-07.json", "r") as conf_file:
    rdf_map = json.load(conf_file)

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map, namespace_map=namespace_map, export_undefined=export_undefined, export_type=export_type)
