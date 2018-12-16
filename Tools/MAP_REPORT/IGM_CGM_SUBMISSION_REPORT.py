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
import datetime

from lxml import etree
import pandas

from Tkinter import *
import ttk
from tkFileDialog import askopenfilename

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

import ENTSOE_TSO_MAP_REPORT

pandas.set_option('display.height', 1000)
pandas.set_option('display.max_rows', 24)
pandas.set_option('display.max_columns', 10)
pandas.set_option('display.width', 1000)
pandas.set_option('precision', 3)



def select_file(file_type='.*',dialogue_title="Select file"):
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

    print filename
    return [filename] #main function takes files in a list, thus single file must aslo be passed as list



#path = select_file()[0]

path ="C:\USVDM\Tools\MAP_REPORT\IGM_SUBMISSION_REPORT.xlsx"
ReportData = pandas.read_excel(path)
mapping_table = pandas.read_excel("MAP_ENTSOE_EIC.xlsx")
report_dataframe = pandas.read_csv("C:\USVDM\Tools\MAP_REPORT\query_result_20181101_0030_20181201_0030_20181207_170959.csv")


unique_submission_parties = list(report_dataframe["pmd:TSO"].unique())


unique_submission_report = report_dataframe["pmd:TSO"].value_counts()["AST"]


##CGM_report_dict = {"active_testing" :{"lower_treshold": 24, "upper_treshold": 800, "style":"opacity:0.85;fill:#2ECC40;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"},
##                  "only_iop_testing":{"lower_treshold":  0, "upper_treshold":  24, "style":"opacity:0.85;fill:#39CCCC;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"}
##                    }

CGM_report_dict = {"active_testing" :{"lower_treshold": 1, "upper_treshold": 800, "style":"opacity:0.85;fill:#2ECC40;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"},
                  #"only_iop_testing":{"lower_treshold":  0, "upper_treshold":  24, "style":"opacity:0.85;fill:#39CCCC;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"}
                    }



#CGM_report_dict["NOK"]["dataframe"] = ReportData
#CGM_report_dict["semi_automatic"]["dataframey"] = ReportData



#report_for_process_types = ["1D"]

report_for_process_types =  list(report_dataframe["pmd:timeHorizon"].unique())

print "Available process types " + str(report_for_process_types)

for process_type in report_for_process_types:

    status_dataframe = pandas.DataFrame()

    report_by_party = report_dataframe[(report_dataframe["pmd:timeHorizon"]==process_type)]["pmd:TSO"].value_counts()

    for status in CGM_report_dict:
        CGM_report_dict[status]["dataframe"] = report_by_party[(report_by_party.le(CGM_report_dict[status]["upper_treshold"]) & report_by_party.gt(CGM_report_dict[status]["lower_treshold"]))]




        for party in CGM_report_dict[status]["dataframe"].index:

            try:
                area_EIC = mapping_table[(mapping_table["CGMES_TSO_NAME"] == party.upper())]["Area_mRID"].item()
            except:
                print "Not found in mapping excel " + party
                continue

            style = CGM_report_dict[status]["style"]


            status_dataframe = status_dataframe.append(pandas.DataFrame([[area_EIC, style]], columns = ["id", "style"]), ignore_index=True)



    #svg_template_path           = "TSO_MAP_TEMPLATE_23022018_KV.svg"
    svg_template_path           = "TSO_MAP_TEMPLATE_12042018_KV.svg"
    svg_identificator_tag       = "id"
    svg_tag_deafut_namespace    = "{urn:iec62325.351:tc57wg16:451-n:eicdocument:1:0}"
    texts_dic                   = {"TitleText" : "IGM submission 11.2018 {}".format(process_type)}
    output_filename             = "CGM_REPORT_{}_{}".format(process_type, datetime.datetime.strftime(datetime.datetime.now(), "%d%m%Y_%H%M"))


    svg_template = etree.parse(svg_template_path)

    #ENTSOE_TSO_MAP_REPORT.update_svg_paths(loaded_xml, CGMA_report_dict["NOK"]["DataFrame"][[identificator_tag,"style"]], identificator_tag, unknown_attrbute_namespace)

    ENTSOE_TSO_MAP_REPORT.update_svg_paths(svg_template, status_dataframe, svg_identificator_tag, svg_tag_deafut_namespace)



    ENTSOE_TSO_MAP_REPORT.update_svg_texts(svg_template, texts_dic)

    svg_file_name = "{}.svg".format(output_filename)

    file = open(svg_file_name, "w+")

    file.write(etree.tostring(svg_template))

    file.close()

    drawing = svg2rlg(svg_file_name)
    drawing = drawing.resized(rpad = 10, lpad = 80, tpad = 10, bpad = 10)
    #renderPDF.drawToFile(drawing, "file.pdf")
    renderPM.drawToFile(drawing, "{}.png".format(output_filename))




