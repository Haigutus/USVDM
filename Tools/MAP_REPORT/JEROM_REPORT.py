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



path = select_file()[0]

#path ="C:/USVDM_pahn/20180221-CVG_IOP latest.xlsx"


ReportData = pandas.read_excel(path)

report_colour_dict = {"ok" :"opacity:0.85;fill:#66cc66;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round",
                      "yes" :"opacity:0.85;fill:#66cc66;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round",
                      "nan" :"opacity:0.85;fill:#BDBDBD;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round",
                      "ko" :"opacity:0.85;fill:#fc6262;stroke:#ffffff;stroke-width:0.25;stroke-linecap:square;stroke-linejoin:round"}


for status in report_colour_dict:

     ReportData = ReportData.replace([status], [report_colour_dict[status]])

## Replace statuses with fromatting


report_columns_list = [ u'Import status ', u'Load-flow status (at least 1 TS)', u'Merge']


for report in report_columns_list:



    template_path               = "TSO_MAP_TEMPLATE_12042018_KV.svg"
    identificator_tag           = "id"
    unknown_attrbute_namespace  = "{urn:iec62325.351:tc57wg16:451-n:eicdocument:1:0}"
    texts_dic                   = {"TitleText" : report}
    output_filename             = "{}_{}.svg".format(os.path.basename(path), report)


    template_xml = etree.parse(template_path)

    ExportData = ReportData.rename(columns={report: 'style', "Area_mRID":identificator_tag})

    ENTSOE_TSO_MAP_REPORT.update_svg_paths(template_xml, ExportData[[identificator_tag,"style"]], identificator_tag, unknown_attrbute_namespace)

    ENTSOE_TSO_MAP_REPORT.update_svg_texts(template_xml, texts_dic)



    file = open(output_filename, "w+")

    file.write(etree.tostring(template_xml))

    file.close()

    drawing = svg2rlg(output_filename)
    drawing = drawing.resized(rpad = 10, lpad = 120, tpad = 10, bpad = 10)
    #renderPDF.drawToFile(drawing, "file.pdf")
    renderPM.drawToFile(drawing, "{}_{}.png".format(os.path.basename(path), report))




