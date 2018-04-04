#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     12.12.2017
# Copyright:   (c) kristjan.vilgo 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from datetime import datetime
import dateutil.parser
import pytz

start_time = datetime.now()
print "Start [{}] \n". format(start_time)

from Tkinter import *
import ttk
from tkFileDialog import askopenfilename
from tkFileDialog import askopenfilenames
from lxml import etree
import pandas as pd
import os


import uuid

# --- Functions ---

pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 1000)

CET=pytz.timezone("Europe/Brussels")
UTC=pytz.timezone("UTC")
EET=pytz.timezone("Europe/Tallinn")


def loadXMLs (file_paths):

    XML_trees=[]

    for file in file_paths:

        loaded_xml = etree.parse(file)

        XML_trees.append(loaded_xml)
    return XML_trees


def select_file(file_type='.*',dialogue_title="Select file"):
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title=dialogue_title ,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

    print filename
    return [filename] #main function takes files in a list, thus single file must aslo be passed as list

def select_files(file_type='.*' ,dialogue_title="Select file(s)"):
    """ Multiple files selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filenames = askopenfilenames(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the paths to selected files
##    print filenames #[DEBUG]
    return filenames

def get_line_nr (text_file_dir, string_to_search):
    """Finds the first ocurrance of string in the file and returns line number where it was found"""
    with open(text_file_dir, 'r') as text_file:
        for n, line in enumerate(text_file):
            if string_to_search in line:
                return n

def create_XML_from_conf(conf_dic):
    """Create XML file from dictionary conf input"""
    end_key       = len(conf_dic)-1
    current_key   = 0

    xml_elements_dic = {}

    while current_key <= end_key:

        element_name = conf_dic[str(current_key)]["DATA"]["element"]

        #print (element_name) #DEBUG

        #Create Element
        #CHECK if root element
        if (current_key == 0):
            element = etree.Element(element_name)

        else:
            parent_name  = xml_elements_dic[conf_dic[str(current_key)]["PARRENT"]]

            #print (element_name, parent_name) #DEBUG

            element = etree.SubElement(parent_name, element_name)

            #Set Element attributes

        if "attributes" in conf_dic[str(current_key)]["DATA"]:

            for attrib_key in conf_dic[str(current_key)]["DATA"]["attributes"]:

                element.attrib[attrib_key] = conf_dic[str(current_key)]["DATA"]["attributes"][attrib_key]

        #Set Element text value

        element.text = conf_dic[str(current_key)]["DATA"].get("text", "")



        #Add current Element to element list

        xml_elements_dic[str(current_key)] = element

        #Move to next element
        current_key+=1

    xml_file = etree.tostring(xml_elements_dic["0"], pretty_print=True)
    return xml_file
    #return xml_elements_dic["0"]

parser = etree.XMLParser(remove_blank_text=True)

def append_XML_object(root,template_name_string):

    KEY_WORDS_DIC = {"OBJECT_NAME" : OBJECT_NAME,
                            "UUID" : UUID,
                    "utc_time_now" : utc_time_now,
               "utc_time_delivery" : utc_time_delivery,
                      "EQ_profile" : EQ_dependancy,
                 "CURRENT_PROFILE" : CURRENT_PROFILE,
                        "ROTATION" : ROTATION,
                 "OBJECT_REF_UUID" : OBJECT_REF_UUID,
                "DIAGRAM_REF_UUID" : DIAGRAM_REF_UUID,
                     "SEQUENCE_NR" : SEQUENCE_NR,
                               "X" : X,
                               "Y" : Y,
               "PSSE_loc_filename" : PSSE_loc_filename,
                      "VERSION_NR" : VERSION_NR,
             "MODELLING_AUTHOROTY" : MODELLING_AUTHOROTY,
                 }

    if root == "create_root":

        root = etree.XML(create_XML_from_conf(CGMES_DL_dic[template_name_string]).format(**KEY_WORDS_DIC), parser = parser)
        return root

    else:

        root.append(etree.XML(create_XML_from_conf(CGMES_DL_dic[template_name_string]).format(**KEY_WORDS_DIC), parser = parser))

CGMES_DL_dic = {
                                "RDF":{
                                                "0":{"PARRENT":"","DATA":{"element":'{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF',"attributes":{"cim":"http://iec.ch/TC57/2013/CIM-schema-cim16#", "md":"http://iec.ch/TC57/61970-552/ModelDescription/1#", "entsoe":"http://entsoe.eu/CIM/SchemaExtension/3/1#", "dm":"http://iec.ch/TC57/61970-552/DifferenceModel/1#", "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"}}},
                                                "1":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}FullModel", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":"urn:uuid:{UUID:}"}}},
                                                "2":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.created", "text":"{utc_time_now:%Y-%m-%dT%H:%M:%SZ}"}},
                                                "3":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.scenarioTime", "text":"{utc_time_delivery:}"}},
                                                "4":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.description", "text":"DL profile generated from PSSE.loc"}},
                                                "5":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.modelingAuthoritySet", "text":"http://www.elering.ee/OperationalPlanning"}},
                                                "6":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.profile", "text":"http://entsoe.eu/CIM/DiagramLayout/3/1"}},
                                                "7":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.version", "text":"VERSION_NR"}},
                                                "8":{"PARRENT":"1","DATA":{"element":"{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.DependentOn", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":"{EQ_profile:}"}}},
                                },
                                "Diagram":{
                                                "0":{"PARRENT":"","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}Diagram", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID":"_{DIAGRAM_REF_UUID:}"}}},
                                                "1":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}IdentifiedObject.name", "text":"{PSSE_loc_filename:}"}},
                                                "2":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}Diagram.orientation", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":"http://www.w3.org/1999/02/22-rdf-syntax-ns#OrientationKind.negative"}}},
                                },

                                "DiagramObject":{
                                                "0":{"PARRENT":"","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID":"_{UUID:}"}}},
                                                "1":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}IdentifiedObject.name","text":"{OBJECT_NAME:}"}},
                                                "2":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject.rotation", "text":"{ROTATION:}"}},
                                                "3":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject.IdentifiedObject", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":"#{OBJECT_REF_UUID:}"}}},
                                                "4":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject.Diagram", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":"#_{DIAGRAM_REF_UUID:}"}}},
                                },
                                "DiagramObjectPoint":{
                                                "0":{"PARRENT":"","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID":"_{UUID:}"}}},
                                                "1":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.sequenceNumber", "text":"{SEQUENCE_NR:}"}},
                                                "2":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.xPosition", "text":"{X:}"}},
                                                "3":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.yPosition", "text":"{Y:}"}},
                                                "4":{"PARRENT":"0","DATA":{"element":"{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.DiagramObject", "attributes":{"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource":"#_{OBJECT_REF_UUID:}"}}},
                                }

                }







# --- SETTINGS ---

scale = 30

#loc_data_files_list = ["normaalskeem.loc", "IPS.loc"]

loc_data_files_list = select_files(".loc", "Select any number of .loc files")

inversion_dic = {"X": 1, "Y": -1} #Set -1 if you want to invert the model on that axsis



# --- START ---

# Load CGMES profiles

#DL_profile = loadXMLs(["C:/Users/kristjan.vilgo/Desktop/IOP291117/DL_test/20171212T1425Z_1D_ELERING_DL_001.xml"])[0]
#EQ_profile = loadXMLs(["C:/Users/kristjan.vilgo/Desktop/IOP291117/BA02_BD29112017_2D_Elering_001_NodeBreaker/20171128T2330Z_ELERING_EQ_001/20171128T2330Z_ELERING_EQ_001.xml"])[0]
EQ_profile = loadXMLs(select_file(".xml", "Select EQ profile"))[0]



# Message header data

UUID = str(uuid.uuid4()) #For full model

#Reference data

EQ_dependancy           = EQ_profile.find(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}FullModel").attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"]

MODELLING_AUTHOROTY_URL = EQ_profile.find(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.modelingAuthoritySet").text

MODELLING_AUTHOROTY     =  "TEST" #MODELLING_AUTHOROTY_URL.split(".")[1].upper()

VERSION_NR              = EQ_profile.find(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.version").text

CURRENT_PROFILE         = "DL"

utc_time_delivery       = dateutil.parser.parse(EQ_profile.find(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.scenarioTime").text)

#cet_time_delivery       = utc_time_delivery.astimezone(CET)

utc_time_now            = datetime.utcnow()


#To be filled later

PSSE_loc_filename, DIAGRAM_REF_UUID, ROTATION, OBJECT_REF_UUID, SEQUENCE_NR, X, Y, OBJECT_NAME = "", "", "", "", "", "", "", ""

KEY_WORDS_DIC = {"OBJECT_NAME" : OBJECT_NAME,
                        "UUID" : UUID,
                "utc_time_now" : utc_time_now,
           "utc_time_delivery" : utc_time_delivery,
                  "EQ_profile" : EQ_dependancy,
             "CURRENT_PROFILE" : CURRENT_PROFILE,
                    "ROTATION" : ROTATION,
             "OBJECT_REF_UUID" : OBJECT_REF_UUID,
            "DIAGRAM_REF_UUID" : DIAGRAM_REF_UUID,
                 "SEQUENCE_NR" : SEQUENCE_NR,
                           "X" : X,
                           "Y" : Y,
           "PSSE_loc_filename" : PSSE_loc_filename,
                  "VERSION_NR" : VERSION_NR,
         "MODELLING_AUTHOROTY" : MODELLING_AUTHOROTY,
             }




print KEY_WORDS_DIC["EQ_profile"]

# Creates RDF root and FULL model

root = append_XML_object("create_root","RDF")

for loc_data_file in loc_data_files_list:


    # Load BUS locations

    start_of_lines_data = get_line_nr(loc_data_file, "BRANCHES") -1

    PSSE_bus_columns = ['PSSEID', 'DiagramObjectPoint.xPosition', 'DiagramObjectPoint.yPosition', "DiagramObject.rotation", "SIZE"]

    PSSE_bus_locations = pd.read_csv(loc_data_file, skiprows = [0], header = None, delim_whitespace = True, error_bad_lines = True, dtype={0: object}, nrows = start_of_lines_data -1, names = PSSE_bus_columns)


    # Load LINE locations

    PSSE_line_columns = {0:'FROMBUS', 1:'TOBUS', 2:'ID', "X":"{}_X", "Y":"{}_Y" ,"DiagramObjectPoint":"{}_DiagramObjectPoint", "DiagramObject":"DiagramObject"} #Double curly-braces to keep them

    PSSE_line_locations = pd.DataFrame()

    with open(loc_data_file, 'r') as text_file:
            for n, line in enumerate(text_file):
                if n > start_of_lines_data +1:
                    data_list = line.rstrip("\n").split("  ")
                    from_bus, to_bus =  data_list[0].split(" ")
                    data_list[0] = to_bus
                    data_list.insert(0, from_bus)

                    x_counter = 1
                    y_counter = 1

                    PSSE_line_locations.ix[str(n), PSSE_line_columns["DiagramObject"]] = "{}".format(uuid.uuid4())                                 # Add UUID to be used for DiagramObject

                    for position, data in enumerate(data_list):

                        if position <= 2:
                            PSSE_line_locations.ix[str(n), PSSE_line_columns[position]] = str(data)


                        elif position & 1:
                            PSSE_line_locations.ix[str(n), PSSE_line_columns["X"].format(x_counter)] = float(data) # X
                            x_counter +=1

                        else:
                            PSSE_line_locations.ix[str(n), PSSE_line_columns["Y"].format(y_counter)] = float(data) # Y
                            PSSE_line_locations.ix[str(n), PSSE_line_columns["DiagramObjectPoint"].format(y_counter)] = "{}".format(uuid.uuid4())  # Add UUID to be used for DiagramObjectPoint
                            y_counter +=1






    # Make all locations positive and scale

    #margin_from_x_y = 0

    to_positive = min([int(PSSE_bus_locations['DiagramObjectPoint.xPosition'].min()), int(PSSE_bus_locations['DiagramObjectPoint.xPosition'].min())])# + margin_from_x_y

    # Busses

    PSSE_bus_locations['DiagramObjectPoint.xPosition'] = (PSSE_bus_locations['DiagramObjectPoint.xPosition'] + to_positive) * scale * inversion_dic["X"]
    PSSE_bus_locations['DiagramObjectPoint.yPosition'] = (PSSE_bus_locations['DiagramObjectPoint.yPosition'] + to_positive) * scale * inversion_dic["Y"]

    # Lines

    for column in PSSE_line_locations.columns.values.tolist()[4:]:

        if column.endswith("X") or column.endswith("Y"):
            sequence_number, axis = column.split("_")

            PSSE_line_locations[PSSE_line_columns[axis].format(sequence_number)] = ((PSSE_line_locations[PSSE_line_columns[axis].format(sequence_number)]) + to_positive) * scale * inversion_dic[axis]


    #print PSSE_line_locations # DEBUG


    # Creates diagram object per .loc

    DIAGRAM_REF_UUID    = str(uuid.uuid4()) # Generated once per PSSE loc file

    PSSE_loc_filename   = os.path.basename(loc_data_file).split(".")[0]

    append_XML_object(root, "Diagram")



    # --- Start adding points ---

    # Find all AC line segments in model

    ACLinesegmnets_list = EQ_profile.findall(".//{http://iec.ch/TC57/2013/CIM-schema-cim16#}ACLineSegment")

    max_sequence = len(PSSE_line_locations.columns.values.tolist()[4:])/3

    for line in ACLinesegmnets_list:

        OBJECT_REF_UUID = line.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"]

        OBJECT_NAME = line.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}IdentifiedObject.name").text

        object_type, from_bus, to_bus, object_id = OBJECT_NAME.split("-")

        filtered_DataFrame = PSSE_line_locations[(PSSE_line_locations["FROMBUS"] == from_bus) & (PSSE_line_locations["TOBUS"] == to_bus) & (PSSE_line_locations["ID"] == object_id)]

        if not filtered_DataFrame.empty:

            # Add Diagram Object

            #UUID = filtered_DataFrame["DiagramObject"].to_string(index = False)
            #root.append(etree.XML(create_XML_from_conf(CGMES_DL_dic["DiagramObject"]).format(**KEY_WORDS_DIC), parser = parser))

            UUID = str(uuid.uuid4())
            append_XML_object(root,"DiagramObject")


            SEQUENCE_NR = 1

            OBJECT_REF_UUID = UUID #Trasfers Diagramobject UUID to reference

            while SEQUENCE_NR <= max_sequence:

               sequence, column_id = column.split("_")

               if filtered_DataFrame[PSSE_line_columns["X"].format(SEQUENCE_NR)].to_string(index = False) != "NaN":

                       X = filtered_DataFrame[PSSE_line_columns["X"].format(SEQUENCE_NR)].to_string(index = False)
                       Y = filtered_DataFrame[PSSE_line_columns["Y"].format(SEQUENCE_NR)].to_string(index = False)
                       #UUID = filtered_DataFrame[PSSE_line_columns["DiagramObjectPoint"].format(SEQUENCE_NR)].to_string(index = False)
                       UUID = str(uuid.uuid4())

                       # Add Diagram Object Point

                       #root.append(etree.XML(create_XML_from_conf(CGMES_DL_dic["DiagramObjectPoint"]).format(**KEY_WORDS_DIC), parser = parser))
                       append_XML_object(root,"DiagramObjectPoint")


                       SEQUENCE_NR += 1

               else:
                    break


    # Find all Connectivity nodes

    connectivity_nodes_list = EQ_profile.findall(".//{http://iec.ch/TC57/2013/CIM-schema-cim16#}ConnectivityNode")

    for node in connectivity_nodes_list:


        PSSE_bus_ID = node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}IdentifiedObject.name").text
        filtered_DataFrame = PSSE_bus_locations[(PSSE_bus_locations["PSSEID"] == PSSE_bus_ID)]

        if not filtered_DataFrame.empty:

            UUID = str(uuid.uuid4())

            OBJECT_NAME = PSSE_bus_ID

            ROTATION = "0" # filtered_DataFrame["DiagramObject.rotation"].to_string(index=False) # not really useful for busses

            OBJECT_REF_UUID = node.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"]

            #DIAGRAM_REF_UUID #Defined allready in the header section

            # Add Diagram Object

            append_XML_object(root,"DiagramObject")


            OBJECT_REF_UUID = UUID #Trasfers DiagramObject UUID to reference

            UUID = str(uuid.uuid4())

            SEQUENCE_NR = 1

            X = float(filtered_DataFrame["DiagramObjectPoint.xPosition"].to_string(index=False))

            Y = float(filtered_DataFrame["DiagramObjectPoint.yPosition"].to_string(index=False))

            bus_bar_size = float(filtered_DataFrame["SIZE"].to_string(index=False))

            if bus_bar_size <= 0.1:

                # Add Diagram Object Point

                append_XML_object(root,"DiagramObjectPoint")

            else:

                scaled_bus_bar_size = bus_bar_size * scale / 2

                rotation = int(filtered_DataFrame["DiagramObject.rotation"].to_string(index=False))

                bus_direction = round((abs(rotation) / 90),0) # On Y axsis if 0 or 2; On X axsis if 1 or 3

                if bus_direction == 1 or bus_direction == 3:

                    centre_location = X

                    # Add 1 Diagram Object Point
                    X = centre_location - scaled_bus_bar_size

                    append_XML_object(root,"DiagramObjectPoint")

                    # Add 2 Diagram Object Point
                    UUID = str(uuid.uuid4())
                    SEQUENCE_NR = 2
                    X = centre_location + scaled_bus_bar_size

                    append_XML_object(root,"DiagramObjectPoint")

                else:

                    centre_location = Y

                    # Add 1 Diagram Object Point
                    Y = centre_location - scaled_bus_bar_size

                    append_XML_object(root,"DiagramObjectPoint")

                    # Add 2 Diagram Object Point
                    UUID = str(uuid.uuid4())
                    SEQUENCE_NR = 2
                    Y = centre_location + scaled_bus_bar_size

                    append_XML_object(root,"DiagramObjectPoint")




# Export and clean xml

nsmap = {"cim":"http://iec.ch/TC57/2013/CIM-schema-cim16#", "md":"http://iec.ch/TC57/61970-552/ModelDescription/1#", "entsoe":"http://entsoe.eu/CIM/SchemaExtension/3/1#", "dm":"http://iec.ch/TC57/61970-552/DifferenceModel/1#", "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
etree.cleanup_namespaces(root, top_nsmap=nsmap)

print etree.tostring(root, pretty_print=True) # DEBUG

tree = etree.ElementTree(root)

export_file_name = "{utc_time_delivery:%Y%m%dT%H%MZ}_{MODELLING_AUTHOROTY}_{CURRENT_PROFILE}_{VERSION_NR}.xml".format(**KEY_WORDS_DIC)

tree.write(export_file_name, pretty_print=True)



#Print execution time # DEBUG

end_time = datetime.now()

run_duration = end_time  - start_time

print "End    [{}] \n". format(end_time)
print "Done - [{}s]".format(run_duration.seconds)



# OLD CODE

### PSSE bus ID-s and Connectivity nodes
##
##connectivity_nodes_list = EQ_profile.findall(".//{http://iec.ch/TC57/2013/CIM-schema-cim16#}ConnectivityNode")
##
##connectivity_nodes_DataFrame = pd.DataFrame()
##
##for n, node in enumerate(connectivity_nodes_list):
##
##    Connectivity_Node_ID = node.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"]
##    PSSE_bus_ID = node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}IdentifiedObject.name").text
##
##    connectivity_nodes_DataFrame.ix[str(n), "ConnectivityNode"] = Connectivity_Node_ID
##    connectivity_nodes_DataFrame.ix[str(n), "PSSEID"] = PSSE_bus_ID
##
###print connectivity_nodes_DataFrame
##
###print PSSE_bus_locations
##
##PSSE_bus_locations = pd.merge(PSSE_bus_locations, connectivity_nodes_DataFrame, on = "PSSEID")
##
###print PSSE_bus_locations
##
##
### Connectivity Node ID-s and Diagram Objects ID-s
##
##Diagram_Object_list = DL_profile.findall(".//{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject")
##
##Diagram_Object_DataFrame = pd.DataFrame()
##
##for n, node in enumerate(Diagram_Object_list):
##
##
##
##    Diagram_Object_ID = node.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"]
##    Connectivity_Node_ID = node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject.IdentifiedObject").attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"][1:]
##
##    dataframe = PSSE_bus_locations[(PSSE_bus_locations["ConnectivityNode"] == Connectivity_Node_ID)]
##
##    if not dataframe.empty:
##        #print Connectivity_Node_ID
##        node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObject.rotation").text = str(int(dataframe["DiagramObject.rotation"]))
##
##        Diagram_Object_DataFrame.ix[str(n), "DiagramObject"] = Diagram_Object_ID
##        Diagram_Object_DataFrame.ix[str(n), "ConnectivityNode"] = Connectivity_Node_ID
##
##    else:
##        node.getparent().remove(node)
##
###print Diagram_Object_DataFrame
##
##PSSE_bus_locations = pd.merge(PSSE_bus_locations, Diagram_Object_DataFrame, on = "ConnectivityNode")
##
##
###print PSSE_bus_locations
##
##
### Find Diagram object ID-s
##
##Diagram_Point_list = DL_profile.findall(".//{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint")
##
###Diagram_Point_DataFrame = pd.DataFrame()
##
##for n, node in enumerate(Diagram_Point_list):
##
##    #Diagram_Point_ID = node.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"]
##    Diagram_Object_ID = node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.DiagramObject").attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"][1:]
##
##    dataframe = PSSE_bus_locations[(PSSE_bus_locations["DiagramObject"] == Diagram_Object_ID)]
##    if not dataframe.empty:
##        node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.xPosition").text = str(float(dataframe["DiagramObjectPoint.xPosition"]))
##        node.find("{http://iec.ch/TC57/2013/CIM-schema-cim16#}DiagramObjectPoint.yPosition").text = str(float(dataframe["DiagramObjectPoint.yPosition"]))
##    else:
##        node.getparent().remove(node)
##
##
##DL_profile.write("DL_profile.xml")







##    print names_DataFrame


##    PSSE_bus_NAME = node.find("{http://entsoe.eu/CIM/SchemaExtension/3/1#}IdentifiedObject.shortName").text
##
##    names_DataFrame.ix[str(n), "{http://www.pti-us.com/PTI_CIM-schema-cim16#}Resources.PSSEID"] = PSSE_bus_ID
##    names_DataFrame.ix[str(n), "{http://iec.ch/TC57/2013/CIM-schema-cim16#}IdentifiedObject.description"] = PSSE_bus_NAME


