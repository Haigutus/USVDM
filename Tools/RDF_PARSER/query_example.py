#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     26.01.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from RDF_parser import load_all_to_dataframe

from Tkinter import Tk
from Tkinter import *
import ttk
from tkFileDialog import askopenfilenames



def select_files(file_type='.*' ,dialogue_title="Select file(s)"):
    """ Multiple files selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filenames = askopenfilenames(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the paths to selected files
##    print filenames #[DEBUG]
    return filenames


#path_list = [r"C:\Users\kristjan.vilgo\Downloads\20180829T0130Z_NG_EQ_001.zip"]

#path_list = ["FlowExample.zip"]

path_list = select_files()

data = load_all_to_dataframe(path_list)

print("Loaded types")
print(data[(data.KEY == "Type")]["VALUE"].value_counts())

#print(data.type_view("ACLineSegment"))

##print("One winding data")
##print(data.query("ID == '12d773ab-1521-4e09-8a45-88b5eebf6fdd'"))

##    print(data)
##
##
##    print("Loaded model UUID-s")
##    model_uuids = data[(data["VALUE"]=="FullModel")]
##    print(model_uuids)
##
##    print("Printing loaded profile headers")
##    for uuid in list(model_uuids["ID"]):
##
##        print(uuid)
##
##        header = data[(data["ID"]==uuid)]
##
##        print(header[["KEY", "VALUE"]])
##
##
##
##    print("Loaded attributes")
##    print(data.KEY.value_counts())
##
##
##    print("All transformers rated S")
##    print(data.query(KEY == "PowerTransformerEnd.ratedS"])
##
##
##    print("Powertransformers")
##    print(data[data.VALUE == "PowerTransformer"]) # Sample of not using query to sort/filter data
##



##    power_transformers = data.query("VALUE == 'PowerTransformer' & KEY == 'Type'")
##
##    terminals_conducting_equipment = data.query("KEY == 'Terminal.ConductingEquipment'")
##
##    terminals_svpowerflow = data.query("KEY == 'SvPowerFlow.Terminal'")
##    terminals_svvoltage   = data.query("KEY == 'SvVoltage.TopologicalNode'")
##
##    eq_container_terminals = pandas.merge(power_transformers, terminals_conducting_equipment, how = "inner", left_on = 'ID', right_on = 'VALUE', suffixes = ["_eqcontainer", "_terminal"])
##
##    sv_powerflows = pandas.merge(eq_container_terminals, terminals_svpowerflow, how = "inner", left_on = "ID_terminal", right_on = "VALUE", suffixes = ["", "_svpowerflow"])

