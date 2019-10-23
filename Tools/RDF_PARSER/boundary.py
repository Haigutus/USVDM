#-------------------------------------------------------------------------------
# Name:        Boundary
# Purpose:     Update boundary
#
# Author:      kristjan.vilgo
#
# Created:     15.10.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas
import RDF_parser

from datetime import datetime

def parse_metadata_from_filename_NMD(file_name):

    meta = {}

    parsed_meta = file_name.split(".")[0].split("_")

    #meta["Model.scenarioTime"]      = parsed_meta[0] # Not needed, allready in ModelHeader
    meta["Model.modelingEntity"]     = parsed_meta[1].replace("-","") # - is separator for area, cant be used in a name
    meta["Model.messageType"]        = parsed_meta[2] + parsed_meta[3]
    #meta["Model.version"]           = parsed_meta[4] # Not needed, allready in ModelHeader
    meta["Model.processType"]        = ""

    return meta

def set_value_at_key(data, key, value):
    data.loc[data[data.KEY == key].index, "VALUE"] = value

boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20191023T0000Z_ENTSO-E_BD_1130.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"

# 1 Load data from ZIP
data = RDF_parser.load_all_to_dataframe([boundary_path])


# Add missing metadata form file name to FullModel

additional_meta_list = []
for _,lable in data.query("KEY == 'Lable'").iterrows():

    meta = parse_metadata_from_filename_NMD(lable["VALUE"])

    for key in meta:
        additional_meta_list.append({"ID":lable.INSTANCE_ID, "KEY": key, "VALUE": meta[key], "INSTANCE_ID": lable.INSTANCE_ID})

data = data.append(pandas.DataFrame(additional_meta_list), ignore_index=True, sort=False)

# 2 Update description
data.set_value_at_key(key='Model.description', value="Offcial CGM boundary set") # Proposial to add original version nr

# 3 Update modelling AuthoritySet
data.set_value_at_key(key='Model.modelingAuthoritySet', value="http://tscnet.eu/EMF")

# 4 Update model Scenrio Time
utc_now = datetime.utcnow()
data.set_value_at_key(key='Model.scenarioTime', value=utc_now.date().isoformat() + "T00:00:00Z")

# 5 Update model Created
data.set_value_at_key(key='Model.created', value=utc_now.isoformat() + "Z")

# 6 Update model Version
data.set_value_at_key(key='Model.version', value="001") #Proposial to keep 001

# 7 Update AC line name and description

lines = data.type_tableview("Line")
nodes = data.type_tableview("ConnectivityNode")

# TODO make report on lines without EIC
# TODO make report on line EIC not in cio tool

# 8 Update DC line name and description









##types = data.types_dict()
##
##writer = pandas.ExcelWriter('boundary_data_raw.xlsx')
##
##for class_type in types:
##
##    class_data = data.type_tableview(class_type)
##    class_data.to_excel(writer, class_type)
##
##
##writer.save()







