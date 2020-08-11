# Purpose:     Correct input models for merging
#
# Author:      kristjan.vilgo
#
# Created:     26.02.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPLv2
#-------------------------------------------------------------------------------
from shapely.geometry import Point, MultiPoint, box
import sys
sys.path.append("..")
import RDF_parser
import CGMES_tools
import pandas
from uuid import uuid4
import json



def create_object_data_from_dict(object_id, object_type, object_data):
    """Creates triplet representation of key-value pair dictionary of object data"""

    columns = ["ID", "KEY", "VALUE"]
    object_data["Type"] = object_type

    transposed_data = map(list, zip(*[[object_id]*len(object_data), object_data.keys(), object_data.values()]))

    object_triplet = pandas.DataFrame(columns=columns, data=transposed_data)

    return object_triplet

#input_data = r"C:\Users\kristjan.vilgo\Downloads\20200115T0930Z_1D_RTEFRANCE_EQ_001.zip"
#input_data = r"C:\Users\kristjan.vilgo\Downloads\input_data.zip"
#input_data = r"C:\Users\kristjan.vilgo\Downloads\Input_IGMs.zip"
input_data = r"C:\Users\kristjan.vilgo\Downloads\IGM_Aug_CGM_Comp.zip"
boundary = r"C:\Users\kristjan.vilgo\Downloads\20200129T0000Z_ENTSO-E_BD_1164.zip"

xnode_conf = r"xnodes_for_tieflows_052020.xlsx"

# Read data
data = pandas.read_RDF([input_data, boundary])

# Parse metadata to file header
data = CGMES_tools.update_FullModel_from_filename(data)



#import tieflow

#initial_flow = tieflow.get_EquivalentInjections_NetInterchange_TieFlows(data)


### Fix Tieflows ###

# Get all EQ instances
eq_instances = data.query("KEY == 'Model.profile' & VALUE == 'http://entsoe.eu/CIM/EquipmentCore/3/1'")

# Get all ControlAreas in EQ instances
control_areas = data.query("KEY == 'Type' & VALUE == 'ControlArea'").merge(eq_instances["INSTANCE_ID"], on="INSTANCE_ID")

# Get all existing TieFlows
tieflows = data.query("KEY == 'Type' & VALUE == 'TieFlow'")

# Get all xnodes participating in AC NP
ac_xnodes = pandas.read_excel(xnode_conf).query("TieFlow == True")
print("AC TieFlow Terminals form conf = {}".format(len(ac_xnodes)))

# Remove all existing TieFlows
data = data.drop(data.reset_index().merge(tieflows["ID"], on="ID")["index"])

# Create new TieFlow data
"""ID = uuid4, TieFlow.ControlArea, TieFlow.Terminal, TieFlow.positiveFlowIn = true, Type = TieFlow"""

# Find instance ID where Terminal belongs to
new_tieflows = data.merge(ac_xnodes["ID_Terminal"], left_on="ID", right_on="ID_Terminal").drop_duplicates("ID")

# data.merge(ac_xnodes["ID_Terminal"], left_on="ID", right_on="ID_Terminal", how="outer", indicator=True).query("_merge == 'right_only'")["ID_Terminal"] #DEBUG

# Map TieFlows to ControlAreas via INSTANCE_ID
new_tieflows = new_tieflows.merge(control_areas, on="INSTANCE_ID", suffixes=("", "_ControlArea"))

# CleanUp - keep only needed columns and add missing values
new_tieflows = new_tieflows[["INSTANCE_ID", "ID_Terminal", "ID_ControlArea"]].rename(columns={"ID_Terminal": "TieFlow.Terminal",
                                                                                              "ID_ControlArea": "TieFlow.ControlArea"})

new_tieflows["TieFlow.positiveFlowIn"] = "true"
new_tieflows["Type"] = "TieFlow"

# Add TieFlow ID-s
new_tieflows["ID"] = new_tieflows.apply(lambda x: str(uuid4()), axis=1)
new_tieflows = new_tieflows.set_index("ID")

# Convert to triplet
new_tieflows_triplet = RDF_parser.tableview_to_triplet(new_tieflows[['TieFlow.Terminal', 'TieFlow.ControlArea', 'TieFlow.positiveFlowIn', 'Type']])

# Add INSTANCE_ID to triplet
new_tieflows_triplet = new_tieflows_triplet.merge(new_tieflows.reset_index()[["ID", "INSTANCE_ID"]], on="ID")

# Add to data
data = data.append(new_tieflows_triplet, ignore_index=True)

#final_flow = tieflow.get_EquivalentInjections_NetInterchange_TieFlows(data)

### Disable regulation on EquivalentInjection ###

injections = data.query("KEY == 'EquivalentInjection.regulationStatus' and VALUE == 'true'")
injections.VALUE = 'false'
data.update(injections)


### Fix EnergyConsumers to ConformLoads ###

loads = data.query("KEY == 'Type' & VALUE == 'EnergyConsumer'")
loads.VALUE = "ConformLoad"
data.update(loads)

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

for instance_id in eq_instances.ID.to_list():

    objects_list = []

    eq = data.query("INSTANCE_ID == @instance_id")
    entity = eq.get_object_data(instance_id)["Model.modelingEntity"]

    print(f"INFO - START fixing Loads for {entity} in EQ {instance_id}")

    # Lets first check if all needed items exist and what is their ID, if it does not exist, lets create ID for them
    items_data = {}

    for item in items:
        item_data = eq.query("KEY == 'Type' & VALUE == @item")

        # In case of missing or if we have a load group, create new object
        if item_data.empty or "LoadGroup" in item:
            item_ID = str(uuid4())
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

    print(f"INFO - END fixing Loads for {entity} in EQ {instance_id}")

data = data.append(data_to_add, ignore_index=True)
data = data.drop_duplicates()
#data = data.update_triplet_from_triplet(data_to_add, update=True, add=True)

### Find all machines out of PQ limits and disable regulating controls ###
curve_data = data.type_tableview("CurveData")
synchronous_machine = data.type_tableview("SynchronousMachine").reset_index()
generating_units = CGMES_tools.get_GeneratingUnits(data)

# Separate to coordinate pairs
first_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y1value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y1value": "y"})
second_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y2value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y2value": "y"})  # TODO Y2 might not exist, so drop NA?
all_points = first_point.append(second_point)

# Convert to coordinate points
all_points["PQ_area"] = all_points[["x", "y"]].apply(Point, axis=1)

# Lets group points and create polygons by using the convex hull function
curve_polygons = all_points.groupby("CurveData.Curve")["PQ_area"].apply(lambda x: MultiPoint(x).convex_hull)


machine_curve = synchronous_machine.merge(curve_polygons, left_on="SynchronousMachine.InitialReactiveCapabilityCurve", right_on="CurveData.Curve", how="left")
machine_curve = machine_curve.merge(generating_units, left_on='RotatingMachine.GeneratingUnit', right_index=True, how="left", suffixes=("", "GeneratingUnit"))
machine_curve["PQ_setpoint"] = machine_curve[['RotatingMachine.p', 'RotatingMachine.q']].multiply(-1).apply(Point, axis=1)
machine_curve["PQ_limits"] = machine_curve[['GeneratingUnit.minOperatingP', 'SynchronousMachine.minQ', 'GeneratingUnit.maxOperatingP', 'SynchronousMachine.maxQ']].dropna().apply(pandas.to_numeric, errors='ignore').apply(lambda x: box(x['GeneratingUnit.minOperatingP'], x['SynchronousMachine.minQ'], x['GeneratingUnit.maxOperatingP'], x['SynchronousMachine.maxQ']), axis=1)

#out_of_limits = machine_curve[~machine_curve.apply(lambda x: x["point"].contains(x["solution"]), axis=1)]
machine_curve["area_distance"] = machine_curve.dropna(subset=["PQ_area"]).apply(lambda x: x["PQ_area"].distance(x["PQ_setpoint"]), axis=1)
machine_curve["limits_distance"] = machine_curve.dropna(subset=["PQ_limits"]).apply(lambda x: x["PQ_limits"].distance(x["PQ_setpoint"]), axis=1)

# Find machines outside of PQ area or PQ limits
out_of_limits = machine_curve.query("area_distance > 0 or limits_distance > 0")

# Set Regulating Control to False on all out of bounds machines
#out_of_limits['RegulatingCondEq.controlEnabled'] = "false"
RegulatingCondEq = data.query("KEY == 'RegulatingCondEq.controlEnabled'").reset_index().merge(out_of_limits.ID).set_index("index")
RegulatingCondEq.VALUE = "false"
data.update(RegulatingCondEq)

RegulatingControl = data.reset_index().merge(out_of_limits["RegulatingCondEq.RegulatingControl"], left_on="ID", right_on="RegulatingCondEq.RegulatingControl").set_index("index").query("KEY == 'RegulatingControl.enabled'")
RegulatingControl.VALUE = "false"
data.update(RegulatingControl)

# TODO - extract reporting and drawing of PQ curves to seperate file
# Filter out switched off generators
#out_of_limits = out_of_limits[~((out_of_limits['RotatingMachine.p'] == 0) & (out_of_limits['RotatingMachine.q'] == 0))]

# Add modelingEntity
#out_of_limits = data.query("KEY == 'Model.modelingEntity'")[['VALUE', 'INSTANCE_ID']].merge(out_of_limits.merge(data.query("KEY == 'Type'")).drop_duplicates("ID"), on="INSTANCE_ID", suffixes=("_PARTY", ""))


# import matplotlib.pyplot as plt
# def draw_chart(index):
#     fig, ax = plt.subplots()
#
#     # PQ curve
#     if pandas.notna(out_of_limits["PQ_area"][index]):
#         ax.scatter(*out_of_limits["PQ_area"][index].exterior.xy)
#         ax.plot(*out_of_limits["PQ_area"][index].exterior.xy, label='PQ_area')
#
#     # PQ limits
#     if pandas.notna(out_of_limits["PQ_limits"][index]):
#         ax.scatter(*out_of_limits["PQ_limits"][index].exterior.xy)
#         ax.plot(*out_of_limits["PQ_limits"][index].exterior.xy, label='PQ_limits')
#
#     # Rated S
#     if pandas.notna(out_of_limits["RotatingMachine.ratedS"][index]):
#         S = out_of_limits["RotatingMachine.ratedS"][index]
#         circle = plt.Circle((0, 0), S, fill=False, color='g', label="S_rated")
#         ax.add_artist(circle)
#
#     # PQ powerflow solution
#     ax.plot(out_of_limits["PQ_setpoint"][index].x, out_of_limits["PQ_setpoint"][index].y, "or", label="PQ_setpoint")
#     #ax.annotate("SV_PQ", (out_of_limits.solution[1].x, out_of_limits.solution[1].y))
#
#     # Annotations
#
#     ax.set_xlabel('P')
#     ax.set_ylabel('Q')
#     #ax.legend([circle], ["S_rated"])
#     ax.legend()
#     ax.grid(True)
#
#     id = out_of_limits["ID"][index]
#     party = out_of_limits["VALUE_PARTY"][index]
#     name = out_of_limits["IdentifiedObject.name"][index]
#
#     fig.suptitle(f'{party} -> {name} \n {id}', fontsize=16)
#     fig.savefig(f'{party}_{id}')


#for machine_id in out_of_limits.index:
#    draw_chart(machine_id)

# print(out_of_limits.VALUE_PARTY.value_counts())

# machine_curve[machine_curve["PQ_area"].apply(lambda x: type(x) == LineString)]


## EXPORT ###

# Set namepsaces for export

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
#data.export_to_cimxml(rdf_map=rdf_map, namespace_map=namespace_map, export_undefined=export_undefined, export_type=export_type)


