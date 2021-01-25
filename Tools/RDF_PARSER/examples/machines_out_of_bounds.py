from shapely.geometry import Point, MultiPoint, box, LineString, Polygon
import matplotlib.pyplot as plt
import pandas
from tkinter import filedialog

from Tools.RDF_PARSER import RDF_parser
from Tools.RDF_PARSER import CGMES_tools


def y_values_at_x(polygon, x):
    """
    Find the intersection points of a vertical line at
    x with the Polygon.
    Returns list [y_min, y_max]
    """
    # Get bounds
    x_min, y_min, x_max, y_max = polygon.bounds

    if x < x_min or x > x_max:
        #print('x is outside the limits of the Polygon')
        return [None, None]

    if isinstance(polygon, Polygon):
        polygon = polygon.boundary

        line_at_x = LineString([[x, y_min], [x, y_max]])

        intersection = polygon.intersection(line_at_x)

        #print(intersection.type)

        if intersection.type == "LineString":
            intersection = intersection.boundary

        if intersection.type == "Point":
            y_values = [intersection.y]

        else:
            y_values = [pt.xy[1][0] for pt in intersection]

        return y_values


    else:
        #print("Not a polygon")
        return [None, None]


def y_out_of_bounds(y, y_range, tolerance=0.001):

    if None not in y_range:
        # Get min and max y at x
        y_min = min(y_range)
        y_max = max(y_range)

        return max([(y_min - y) - abs(y_min * tolerance),
                    (y - y_max) - abs(y_max * tolerance)])


def draw_chart(out_of_limits, index, save=False, show=True):
    """
    Draw PQ chart for synchronous machine
    """
    fig, ax = plt.subplots()

    if curve_data is not None:
        # PQ curve
        if pandas.notna(out_of_limits["PQ_area"][index]):

            colour = "#1f77b4"  # Blue

            if out_of_limits["PQ_area"][index].type == "Polygon":
                ax.scatter(*out_of_limits["PQ_area"][index].exterior.xy, color=colour)
                ax.plot(*out_of_limits["PQ_area"][index].exterior.xy, label='PQ_area', color=colour)
            else:
                ax.scatter(*out_of_limits["PQ_area"][index].xy, color=colour)
                ax.plot(*out_of_limits["PQ_area"][index].xy, label='PQ_area', color=colour)


    # PQ limits
    if pandas.notna(out_of_limits["PQ_limits"][index]):
        colour = "#ff7f0e"  # Orange
        ax.scatter(*out_of_limits["PQ_limits"][index].exterior.xy, color=colour)
        ax.plot(*out_of_limits["PQ_limits"][index].exterior.xy, label='PQ_limits', color=colour)

    # Rated S
    if pandas.notna(out_of_limits["RotatingMachine.ratedS"][index]):
        colour = "#2ca02c"  # Green
        S = out_of_limits["RotatingMachine.ratedS"][index]
        circle = plt.Circle((0, 0), S, fill=False, color=colour, label="S_rated")
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

    # If name is provided, use it
    if "VALUE_PARTY" in out_of_limits.columns:
        party = out_of_limits["VALUE_PARTY"][index]
    else:
        party = ""

    id = out_of_limits["ID"][index]
    name = out_of_limits["IdentifiedObject.name"][index]

    fig.suptitle(f'{party} -> {name} \n {id}', fontsize=16)

    if save:
        fig.savefig(f'{party}_{id}')


# Settings

input_data = list(filedialog.askopenfilenames(initialdir="/", title="Select CIMXML files", filetypes=(("CIMXML", "*.zip"), ("CIMXML", "*.xml"))))

# Parse data
data = pandas.read_RDF(input_data)
# Parse metadata to file header

filename_status = True
try:
    data = CGMES_tools.update_FullModel_from_filename(data)

except:
    print("Parsing of filename failed")
    filename_status = False

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
if filename_status:
    machine_data = data.query("KEY == 'Model.modelingEntity'")[['VALUE', 'INSTANCE_ID']].merge(machine_data.merge(data.query("KEY == 'Type'")).drop_duplicates("ID"), on="INSTANCE_ID", suffixes=("_PARTY", ""))

# Merge all needed data
machine_data = machine_data.merge(generating_units, left_on='RotatingMachine.GeneratingUnit', right_index=True, how="left", suffixes=("", "GeneratingUnit"))
machine_data = machine_data.merge(Terminals.reset_index(), right_on='Terminal.ConductingEquipment', left_on="ID", how="left", suffixes=("", "_Terminal"))
machine_data = machine_data.merge(SvPowerFlow.reset_index(), right_on='SvPowerFlow.Terminal', left_on="ID_Terminal", how="left", suffixes=("", "_SvPowerFlow"))

# Convert to spacial objects
machine_data["PQ_setpoint"] = machine_data[['RotatingMachine.p', 'RotatingMachine.q']].multiply(-1).apply(Point, axis=1)
machine_data["PQ_solution"] = machine_data[['SvPowerFlow.p', 'SvPowerFlow.q']].multiply(-1).apply(Point, axis=1)
machine_data["PQ_limits"] = machine_data[['GeneratingUnit.minOperatingP', 'SynchronousMachine.minQ', 'GeneratingUnit.maxOperatingP', 'SynchronousMachine.maxQ']].dropna().apply(pandas.to_numeric, errors='ignore').apply(lambda x: box(x['GeneratingUnit.minOperatingP'], x['SynchronousMachine.minQ'], x['GeneratingUnit.maxOperatingP'], x['SynchronousMachine.maxQ']), axis=1)

#out_of_limits = machine_curve[~machine_curve.apply(lambda x: x["point"].contains(x["solution"]), axis=1)]


if curve_data is not None:
    # Separate to coordinate pairs
    first_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y1value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y1value": "y"})
    second_point = curve_data[["CurveData.Curve", "CurveData.xvalue", "CurveData.y2value"]].rename(columns={"CurveData.xvalue": "x", "CurveData.y2value": "y"})  # TODO Y2 might not exist, so drop NA?
    all_points = first_point.append(second_point)

    # Convert to coordinate points
    all_points["PQ_area"] = all_points[["x", "y"]].apply(Point, axis=1)

    # Lets group points and create polygons by using the convex hull function
    curve_polygons = all_points.groupby("CurveData.Curve")["PQ_area"].apply(lambda x: MultiPoint(x).convex_hull)

    # Add curve to data as polygon
    machine_data = machine_data.merge(curve_polygons, left_on="SynchronousMachine.InitialReactiveCapabilityCurve", right_on="CurveData.Curve", how="left")

# Test both P and Q
# Add how far set-point from limits
machine_data["limits_distance_setpoint"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: x["PQ_limits"].distance(x["PQ_setpoint"]), axis=1)
machine_data["limits_distance_solution"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: x["PQ_limits"].distance(x["PQ_solution"]), axis=1)

# Update if curve available
if curve_data is not None:
    machine_data["limits_distance_setpoint"].update(machine_data.dropna(subset=["PQ_area"]).apply(lambda x: x["PQ_area"].distance(x["PQ_setpoint"]), axis=1))
    machine_data["limits_distance_solution"].update(machine_data.dropna(subset=["PQ_area"]).apply(lambda x: x["PQ_area"].distance(x["PQ_solution"]), axis=1))



# Test only Q
# Rule 6_12 and 6_13

tolerance = 0.001
_out_of_limits_setpoint_Q = machine_data[(machine_data["RotatingMachine.q"]*-1 > machine_data["SynchronousMachine.maxQ"]*(1+tolerance)) | (machine_data["RotatingMachine.q"]*-1 < machine_data["SynchronousMachine.minQ"]*(1-tolerance))]
_out_of_limits_solution_Q = machine_data[(machine_data["SvPowerFlow.q"]*-1 > machine_data["SynchronousMachine.maxQ"]*(1+tolerance)) | (machine_data["SvPowerFlow.q"]*-1 < machine_data["SynchronousMachine.minQ"]*(1-tolerance))]

machine_data["limits_distance_setpoint_Q"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: y_out_of_bounds(x["PQ_setpoint"].y, [x["SynchronousMachine.minQ"], x["SynchronousMachine.maxQ"]]), axis=1)
machine_data["limits_distance_solution_Q"] = machine_data.dropna(subset=["PQ_limits"]).apply(lambda x: y_out_of_bounds(x["PQ_solution"].y, [x["SynchronousMachine.minQ"], x["SynchronousMachine.maxQ"]]), axis=1)
#out_of_limits_setpoint_Q

# Update if curve available
if curve_data is not None:
    machine_data["limits_distance_setpoint_Q"].update(machine_data.dropna(subset=["PQ_area"]).apply(lambda x: y_out_of_bounds(x["PQ_setpoint"].y, y_values_at_x(x["PQ_area"], x["PQ_setpoint"].x)), axis=1))
    machine_data["limits_distance_solution_Q"].update(machine_data.dropna(subset=["PQ_area"]).apply(lambda x: y_out_of_bounds(x["PQ_solution"].y, y_values_at_x(x["PQ_area"], x["PQ_solution"].x)), axis=1))
    curve_greater_than_limits = machine_data.dropna(subset=["PQ_limits", "PQ_area"])[~(machine_data.dropna(subset=["PQ_limits", "PQ_area"]).apply(lambda x: x["PQ_limits"].contains(x["PQ_area"]), axis=1))]

# Find machines outside of PQ area or PQ limits
out_of_limits_setpoint_PQ = machine_data.query("limits_distance_setpoint > 0")
out_of_limits_solution_PQ = machine_data.query("limits_distance_solution > 0")

out_of_limits_setpoint_Q = machine_data.query("limits_distance_setpoint_Q > 0")
out_of_limits_solution_Q = machine_data.query("limits_distance_solution_Q > 0")


# Filter out switched off generators
#out_of_limits = out_of_limits[~((out_of_limits['RotatingMachine.p'] == 0) & (out_of_limits['RotatingMachine.q'] == 0))]
out_of_limits_solution_PQ = out_of_limits_solution_PQ[~((out_of_limits_solution_PQ['RotatingMachine.p'] == 0))]
out_of_limits_setpoint_PQ = out_of_limits_setpoint_PQ[~((out_of_limits_setpoint_PQ['RotatingMachine.p'] == 0))]


reports = {"PQ_solution_violations": out_of_limits_solution_PQ,
           "PQ_setpoint_violations": out_of_limits_setpoint_PQ,
           "Q_solution_violations": out_of_limits_solution_Q,
           "Q_setpoint_violations": out_of_limits_setpoint_Q}

number_of_machines = len(machine_data)

print("WARNING - {}/{} Machines SV PF outside their limits or curve".format(len(out_of_limits_solution_PQ), number_of_machines))
print("WARNING - {}/{} Machines SSH setpoint outside their limits or curve".format(len(out_of_limits_setpoint_PQ), number_of_machines))
print("WARNING - {}/{} Machines SV PF Q outside their limits or curve".format(len(out_of_limits_solution_Q), number_of_machines))
print("WARNING - {}/{} Machines SSH Q setpoint outside their limits or curve".format(len(out_of_limits_setpoint_Q), number_of_machines))

if curve_data:
    print("WARNING - {}/{} Machines curve is outside the limits".format(len(curve_greater_than_limits), number_of_machines))
    reports["curve_outside_limits"] = curve_greater_than_limits
# TODO - Add check for curve/limits outside rated S
# TODO - Add check for Machine terminal limits


#for machine_id in out_of_limits_solution_PQ.index:
#    draw_chart(machine_data, machine_id, save=True)






for report_name, report in reports.items():
    report.to_excel("{}.xlsx".format(report_name))

for machine_id in out_of_limits_solution_Q.index:
    draw_chart(machine_data, machine_id, save=True)

# print(out_of_limits.VALUE_PARTY.value_counts())

# Test where PQ area is actually not an area, but a line
# machine_data[machine_data["PQ_area"].apply(lambda x: type(x) == LineString)]
