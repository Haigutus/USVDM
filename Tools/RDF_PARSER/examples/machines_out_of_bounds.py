from shapely.geometry import Point, MultiPoint, box
import matplotlib.pyplot as plt
import sys
import pandas
from tkinter import filedialog

sys.path.append("..")
import RDF_parser
import CGMES_tools


def draw_chart(out_of_limits, index):
    fig, ax = plt.subplots()

    if curve_data:
        # PQ curve
        if pandas.notna(out_of_limits["PQ_area"][index]):
            ax.scatter(*out_of_limits["PQ_area"][index].exterior.xy)
            ax.plot(*out_of_limits["PQ_area"][index].exterior.xy, label='PQ_area')

    # PQ limits
    if pandas.notna(out_of_limits["PQ_limits"][index]):
        ax.scatter(*out_of_limits["PQ_limits"][index].exterior.xy)
        ax.plot(*out_of_limits["PQ_limits"][index].exterior.xy, label='PQ_limits')

    # Rated S
    if pandas.notna(out_of_limits["RotatingMachine.ratedS"][index]):
        S = out_of_limits["RotatingMachine.ratedS"][index]
        circle = plt.Circle((0, 0), S, fill=False, color='g', label="S_rated")
        ax.add_artist(circle)

    # PQ SSH setpoint
    ax.plot(out_of_limits["PQ_setpoint"][index].x, out_of_limits["PQ_setpoint"][index].y, "og", label="PQ_setpoint")
    ax.plot(out_of_limits["PQ_solution"][index].x, out_of_limits["PQ_solution"][index].y, "or", label="PQ_solution")

    #ax.annotate("SV_PQ", (out_of_limits.solution[1].x, out_of_limits.solution[1].y))

    # Annotations

    ax.set_xlabel('P')
    ax.set_ylabel('Q')
    #ax.legend([circle], ["S_rated"])
    ax.legend()
    ax.grid(True)

    id = out_of_limits["ID"][index]
    party = out_of_limits["VALUE_PARTY"][index]
    name = out_of_limits["IdentifiedObject.name"][index]

    fig.suptitle(f'{party} -> {name} \n {id}', fontsize=16)
    fig.savefig(f'{party}_{id}')


# Settings

input_data = list(filedialog.askopenfilenames(initialdir="/", title="Select CIMXML files", filetypes=(("CIMXML", "*.zip"), ("CIMXML", "*.xml"))))
#input_data = [r"C:\Users\kristjan.vilgo\Downloads\20200923T2230Z_1D_ELERING_IGM_001.zip"]
#boundary = r"C:\Users\kristjan.vilgo\Downloads\20200129T0000Z_ENTSO-E_BD_1164.zip"
#input_data.append(boundary)

# Parse data
data = pandas.read_RDF(input_data)
# Parse metadata to file header
data = CGMES_tools.update_FullModel_from_filename(data)

"""6_12. For all Terminals, associated with synchronous machines (including slack generator),
 the negated value of SvPowerFlow.q value must be greater than or equal to the minimum of (SynchronousMachine.minQ and ReactiveCapabilityCurve.y1value at
ReactiveCapabilityCurve.xvalue).
In this validation a tolerance is considered of 0.1%)."""

### Find all machines out of PQ limits and disable regulating controls ###
curve_data = data.type_tableview("CurveData")
machine_data = data.type_tableview("SynchronousMachine").reset_index()
generating_units = CGMES_tools.get_GeneratingUnits(data)

Terminals = data.type_tableview("Terminal")
SvPowerFlow = data.type_tableview("SvPowerFlow")

# Add modelingEntity
machine_data = data.query("KEY == 'Model.modelingEntity'")[['VALUE', 'INSTANCE_ID']].merge(machine_data.merge(data.query("KEY == 'Type'")).drop_duplicates("ID"), on="INSTANCE_ID", suffixes=("_PARTY", ""))


if curve_data:
    # Separate to coordinate pairs
    first_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y1value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y1value": "y"})
    second_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y2value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y2value": "y"})  # TODO Y2 might not exist, so drop NA?
    all_points = first_point.append(second_point)

    # Convert to coordinate points
    all_points["PQ_area"] = all_points[["x", "y"]].apply(Point, axis=1)

    # Lets group points and create polygons by using the convex hull function
    curve_polygons = all_points.groupby("CurveData.Curve")["PQ_area"].apply(lambda x: MultiPoint(x).convex_hull)



if curve_data:
    machine_data = machine_data.merge(curve_polygons, left_on="SynchronousMachine.InitialReactiveCapabilityCurve", right_on="CurveData.Curve", how="left")

machine_data = machine_data.merge(generating_units, left_on='RotatingMachine.GeneratingUnit', right_index=True, how="left", suffixes=("", "GeneratingUnit"))
machine_data = machine_data.merge(Terminals.reset_index(), right_on='Terminal.ConductingEquipment', left_on="ID", how="left", suffixes=("", "_Terminal"))
machine_data = machine_data.merge(SvPowerFlow.reset_index(), right_on='SvPowerFlow.Terminal', left_on="ID_Terminal", how="left", suffixes=("", "_SvPowerFlow"))


machine_data["PQ_setpoint"] = machine_data[['RotatingMachine.p', 'RotatingMachine.q']].multiply(-1).apply(Point, axis=1)
machine_data["PQ_solution"] = machine_data[['SvPowerFlow.p', 'SvPowerFlow.q']].multiply(-1).apply(Point, axis=1)
machine_data["PQ_limits"] = machine_data[['GeneratingUnit.minOperatingP', 'SynchronousMachine.minQ', 'GeneratingUnit.maxOperatingP', 'SynchronousMachine.maxQ']].dropna().apply(pandas.to_numeric, errors='ignore').apply(lambda x: box(x['GeneratingUnit.minOperatingP'], x['SynchronousMachine.minQ'], x['GeneratingUnit.maxOperatingP'], x['SynchronousMachine.maxQ']), axis=1)

#out_of_limits = machine_curve[~machine_curve.apply(lambda x: x["point"].contains(x["solution"]), axis=1)]
if curve_data:
    machine_data["area_distance"] = machine_data.dropna(subset=["PQ_area"]).apply(lambda x: x["PQ_area"].distance(x["PQ_setpoint"]), axis=1)

machine_data["limits_distance"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: x["PQ_limits"].distance(x["PQ_setpoint"]), axis=1)
machine_data["limits_distance_solution"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: x["PQ_limits"].distance(x["PQ_solution"]), axis=1)

# Rule 6_12 and 6_13
# TODO - Add tolerance
out_of_limits_solution_Q = machine_data[(machine_data["SvPowerFlow.q"] > machine_data["SynchronousMachine.maxQ"]) | (machine_data["SvPowerFlow.q"] < machine_data["SynchronousMachine.minQ"])]
out_of_limits_setpoint_Q = machine_data[(machine_data["RotatingMachine.q"] > machine_data["SynchronousMachine.maxQ"]) | (machine_data["RotatingMachine.q"] < machine_data["SynchronousMachine.minQ"])]

# Find machines outside of PQ area or PQ limits
if curve_data:
    out_of_limits = machine_data.query("area_distance > 0 or limits_distance > 0")
else:
    out_of_limits = machine_data.query("limits_distance > 0")


# Filter out switched off generators
out_of_limits = out_of_limits[~((out_of_limits['RotatingMachine.p'] == 0) & (out_of_limits['RotatingMachine.q'] == 0))]

print("WARNING - {}/{} Machines outside their limits or curve".format(len(out_of_limits), len(machine_data)))


for machine_id in out_of_limits_solution_Q.index:
    draw_chart(machine_data, machine_id)


#for machine_id in out_of_limits.index:
#    draw_chart(machine_id)

# print(out_of_limits.VALUE_PARTY.value_counts())

# machine_data[machine_data["PQ_area"].apply(lambda x: type(x) == LineString)]
