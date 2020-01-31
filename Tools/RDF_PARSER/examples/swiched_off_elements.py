import sys
sys.path.append("..")

from RDF_parser import *
import pandas

#pandas.set_option("display.height", 1000)
pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)
#pandas.set_option('display.max_colwidth', -1)

path = r"C:\IOPs\Terna_test_25102019\20190821T0930Z_1D_TERNA_TP_001 (2).zip"
path = r"C:\IOPs\20171030T2300Z_DKE_EQ_001.zip"
path = r"C:\IOPs\Litgrid weekly\20180529T0930Z_1D_Litgrid_001.zip"

data = load_all_to_dataframe([path], debug=True)

ACLineSegments          = data.type_tableview("ACLineSegment")
Terminals               = data.type_tableview("Terminal")

ACLineSegments_Terminals            = pandas.merge(ACLineSegments, Terminals, how = "inner", left_index=True, right_on = 'Terminal.ConductingEquipment')

disconnected_lines = ACLineSegments_Terminals[ACLineSegments_Terminals["ACDCTerminal.connected"]=='false'].drop_duplicates("Terminal.ConductingEquipment").set_index("Terminal.ConductingEquipment")[["IdentifiedObject.name_x"]]

print(disconnected_lines)