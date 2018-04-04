#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     04.04.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Get detailes from EIC registry

path = select_file( ".xml", "Select EIC registry file")

EIC_registry_data = loadXMLs(path)[0]

EIC_DataFrame = pandas.DataFrame()

EIC_registry_elements = EIC_registry_data.findall("{urn:iec62325.351:tc57wg16:451-n:eicdocument:1:0}EICCode_MarketDocument")

for element in EIC_registry_elements:

    data_dic = {}

    children = list(element)

    for child in children:


        if list(child) !=[]:
            children.extend(list(child))

        else:
            data_dic[get_XML_element(child.tag)] = child.text


    EIC_DataFrame = EIC_DataFrame.append(pandas.DataFrame([data_dic.values()], index = [0], columns = data_dic.keys()), ignore_index = True)

##TSO_columns = ['country', 'description', 'display_Names.name', 'long_Names.name', 'mRID', 'name']
##
##TSO_DataFrame = EIC_DataFrame[(EIC_DataFrame["name"]=="System Operator")][TSO_columns]
##
###DataFrame.columns.values[0]='mRID'
##
##merged_data = pandas.merge(DataFrame, TSO_DataFrame, on='mRID', how="left")
##
##"C:/Users/kristjan.vilgo/Downloads/allocated-eic-codes (4)/allocated-eic-codes.xml"