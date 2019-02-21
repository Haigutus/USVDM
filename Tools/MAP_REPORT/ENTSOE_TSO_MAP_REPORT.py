#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     20.03.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from __future__ import print_function

from lxml import etree
import pandas

def svg_to_DataFrame(file_path, attributes):

    loaded_xml = etree.parse(file_path)
    paths = loaded_xml.findall("//{http://www.w3.org/2000/svg}path")

    paths_DataFrame = pandas.DataFrame()


    for path in paths:
        data_dic = {}

        for attribute in path_attributes:
            data_dic[attribute] = path.attrib[attribute]

        print (data_dic["id"])

        try:
            data_dic["__description__"] = path.find("{http://www.w3.org/2000/svg}desc").text

        except:
            print ("No Description available")
            data_dic["__description__"] = "NAN"


        try:
            data_dic["__title__"] = path.find("{http://www.w3.org/2000/svg}title").text

        except:
            print ("No Title available")
            data_dic["__title__"] = "NAN"

        paths_DataFrame = paths_DataFrame.append(pandas.DataFrame([data_dic.values()], columns = data_dic.keys()), ignore_index = True)

    return paths_DataFrame


def update_svg_paths(loaded_xml, DataFrame, identificator_tag, unknown_attrbute_namespace):


    paths = loaded_xml.findall("//{http://www.w3.org/2000/svg}path")

    DataFrame_keys = DataFrame.keys()


    for path in paths:

        path_keys = path.keys()

        try:
            identificator = path.attrib[identificator_tag]

        except:
            print ("{} has no attribute {} -> skipping".format(path, identificator_tag))
            continue


        for key in DataFrame_keys:

            if key in path_keys:
                write_key = key

            else:
                write_key = unknown_attrbute_namespace + key


            try:
                path.attrib[write_key] = DataFrame[(DataFrame[identificator_tag])==identificator][key].tolist()[0]
            except:
                print ("ID not found in DataFrame: {}".format(identificator))



def update_svg_texts(loaded_xml, texts_dic):

    text_elements = loaded_xml.findall("//{http://www.w3.org/2000/svg}text")

    for text_element in text_elements:

        if text_element.attrib["id"] in texts_dic:

            text_element.find("{http://www.w3.org/2000/svg}tspan").text = texts_dic[text_element.attrib["id"]]

            print ("New text defined for text element with id: {} -> new value: {}".format(text_element.attrib["id"], texts_dic[text_element.attrib["id"]]))

        else:
            print ("No new text defined for text element with id: {}".format(text_element.attrib["id"]))




###path_attributes = ["style", "id", "class", "d"]
##path_attributes = ["style", "id"]
###path_attributes = ["id"]
##
##
##template_file_name = "C:/Users/kristjan.vilgo/Desktop/European TSOs_20032018.svg"
##
##
##paths_DataFrame = svg_to_DataFrame(template_file_name, path_attributes)
##
##
##paths_DataFrame.to_clipboard(encoding='utf-8')

##file_path                   = "TSO_MAP_TEMPALTE_23022018_KV.svg"
##identificator_tag           = "id"
##unknown_attrbute_namespace  = "{urn:iec62325.351:tc57wg16:451-n:eicdocument:1:0}"
##texts_dic                   = {"TitleText" : "CGMA"}
##output_filename             = "CGMA_REPORT_D2_22032018"
##
##
##loaded_xml = etree.parse(file_path)
##
###DataFrame = pandas.read_clipboard()
##
##
##
###DataFrame = pandas.read_excel("C:/Users/kristjan.vilgo/Desktop/MAP_ENTSOE.xlsm", sheetname = "TSOs_full", parse_cols = "B:J")
##
###update_svg_paths(loaded_xml, DataFrame, identificator_tag, unknown_attrbute_namespace)
##
##
###update_svg_texts(loaded_xml, texts_dic)
##
##
##
##file = open("{}.svg".format(output_filename), "w+")
##
##file.write(etree.tostring(loaded_xml))
##
##file.close()






##    print data_dic["id"]
##
##    try:
##        data_dic["__description__"] = path.find("{http://www.w3.org/2000/svg}desc").text
##
##    except:
##        print "No Description available"
##        data_dic["__description__"] = "NAN"
##
##
##    try:
##        data_dic["__title__"] = path.find("{http://www.w3.org/2000/svg}title").text
##
##    except:
##        print "No Title available"
##        data_dic["__title__"] = "NAN"

#paths_DataFrame = paths_DataFrame.append(pandas.DataFrame([data_dic.values()], columns = data_dic.keys()), ignore_index = True)

#return paths_DataFrame


