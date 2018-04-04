#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     22.03.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os

from lxml import etree
import pandas

from Tkinter import *
import ttk
from tkFileDialog import askdirectory
from tkFileDialog import askopenfilename

import ENTSOE_TSO_MAP_REPORT

pandas.set_option('display.height', 1000)
pandas.set_option('display.max_rows', 24)
pandas.set_option('display.max_columns', 10)
pandas.set_option('display.width', 1000)
pandas.set_option('precision', 3)


def select_folder(dialogue_title="Select Folder"):
    """Folder selection popup
    return: string"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    directory = askdirectory(title=dialogue_title) # show an "Open" dialog box and return the path to the selected folder

    print directory
    return directory

def select_file(file_type='.*',dialogue_title="Select file"):
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

    print filename
    return [filename] #main function takes files in a list, thus single file must aslo be passed as list


def loadXMLs (file_paths):

    XML_trees=[]

    #check_path(file_paths)

    for file in file_paths:

        loaded_xml = etree.parse(file)

        XML_trees.append(loaded_xml)

    return XML_trees


def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):



        if filename.endswith(file_extension):
            #logging.info("Processing file:"+filename)
            matches.append(path + "//" + filename)
        else:
            print "Not a {} file: {}".format(file_extension, filename)
            #logging.warning("Not a {} file: {}".format(file_extension,file_text[0]))

    #print matches
    return matches

def get_XML_element(element_tag):

    element = element_tag

    if element_tag[0] == "{":
        namespace, element = element_tag[1:].split("}")

    return element

#path = select_folder("Select CGMA folder")


CGMA_report_dict = {"OK" :{"style":"opacity:0.85;fill:#66cc66;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"},
                    "NOK":{"style":"opacity:0.85;fill:#fc6262;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"}}

#CGMA_report_directory = select_folder("Select CGMA folder")

CGMA_report_directory = "C:/Users/kristjan.vilgo/Downloads/2018-03-22_CGMA_EDI_package"


CGMA_report_dict["NOK"]["directory"] = os.path.join(CGMA_report_directory, "XML\Output\ProblemStatementMarketDocument")
CGMA_report_dict["NOK"]["namespace"] = "{urn:iec62325.351:tc57wg16:451-5:problemdocument:3:0}"
CGMA_report_dict["OK"]["directory"] = os.path.join(CGMA_report_directory, "XML\Input\Processed\ReportingInformationMarketDocument")
CGMA_report_dict["OK"]["namespace"] = "{urn:iec62325.351:tc57wg16:451-n:reportinginformationdocument:2:0}"




for status in CGMA_report_dict:

    DataFrame = pandas.DataFrame()

    path = CGMA_report_dict[status]["directory"]

    files = list_of_files(path, ".xml")

    xml_trees = loadXMLs(files)

    for xml_tree in xml_trees:

        #party_EIC = xml_tree.find(("//{}receiver_MarketParticipant.mRID".format(CGMA_report_dict[status]["namespace"]))).text

        area_EIC = xml_tree.find(("//{}domain.mRID".format(CGMA_report_dict[status]["namespace"]))).text
        style = CGMA_report_dict[status]["style"]

        #DataFrame = DataFrame.append(pandas.DataFrame([[area_EIC,party_EIC, style, status]], columns = ["id", "mRID", "style", "status"]), ignore_index=True)
        DataFrame = DataFrame.append(pandas.DataFrame([[area_EIC, style, status]], columns = ["id", "style", "status"]), ignore_index=True)

    CGMA_report_dict[status]["DataFrame"] = DataFrame


file_path                   = "TSO_MAP_TEMPLATE_23022018_KV.svg"
identificator_tag           = "id"
unknown_attrbute_namespace  = "{urn:iec62325.351:tc57wg16:451-n:eicdocument:1:0}"
texts_dic                   = {"TitleText" : "CGMA"}
output_filename             = "CGMA_REPORT_D2_22032018_V3"


loaded_xml = etree.parse(file_path)

ENTSOE_TSO_MAP_REPORT.update_svg_paths(loaded_xml, CGMA_report_dict["NOK"]["DataFrame"][[identificator_tag,"style"]], identificator_tag, unknown_attrbute_namespace)

ENTSOE_TSO_MAP_REPORT.update_svg_paths(loaded_xml, CGMA_report_dict["OK"]["DataFrame"][[identificator_tag,"style"]], identificator_tag, unknown_attrbute_namespace)



ENTSOE_TSO_MAP_REPORT.update_svg_texts(loaded_xml, texts_dic)



file = open("{}.svg".format(output_filename), "w+")

file.write(etree.tostring(loaded_xml))

file.close()




