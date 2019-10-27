#-------------------------------------------------------------------------------
# Name:        Boundary
# Purpose:     Update boundary
#
# Author:      kristjan.vilgo
#
# Created:     24.10.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import pandas
import RDF_parser
import CGMEStools
from datetime import datetime


def get_metadata_from_filename_NMD(file_name):
    """Parse metadata from Network Model Manager export"""
    meta     = {}
    raw_meta = file_name.split(".")[0].split("_")

    meta["Model.scenarioTime"]       = raw_meta[0]
    meta["Model.modelingEntity"]     = raw_meta[1].replace("-","") # '-' and '_' are meta separators, can't be used in a name
    meta["Model.messageType"]        = raw_meta[2] + raw_meta[3]
    meta["Model.version"]            = raw_meta[4]
    meta["Model.processType"]        = ""

    return meta


#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20191023T0000Z_ENTSO-E_BD_1130.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"
boundary_path = r"/home/kristjan/Downloads/20191023T0000Z_ENTSO-E_BD_1130.zip"

# 1 Load data from CGMES boundary global ZIP, exported by NMD
data = RDF_parser.load_all_to_dataframe([boundary_path])

# DEBUG export initial data in excel
#data.export_to_excel()

# Add missing metadata form filename to FullModel
data = CGMEStools.add_metadata_to_FullModel_from_filename(data, parser=get_metadata_from_filename_NMD)

# Get current time, to update created DateTime and ScenarioTime
utc_now = datetime.utcnow()

# Update FullModel
meta_updates = {'Model.description':          "Official CGM boundary set",                # 2 Update description            TODO Proposal to add original BD version nr
                'Model.modelingAuthoritySet': "http://tscnet.eu/EMF",                     # 3 Update modelling AuthoritySet
                'Model.scenarioTime':         utc_now.date().isoformat() + "T00:00:00Z",  # 4 Update model Scenario Time    TODO update to 00:30 and test on OPDM
                'Model.created':              utc_now.isoformat() + "Z",                  # 5 Update model Created
                'Model.version':              "001"                                       # 6 Set model Version to 001
                }

data = CGMEStools.add_metadata_to_FullModel(data, meta_updates)

# 7 Update Line name and description

lines = data.type_tableview("Line").reset_index()
nodes = data.type_tableview("ConnectivityNode").reset_index()

#TODO filter out AC and DC lines
line_and_nodes = lines.merge(nodes, left_on="ID",
                                    right_on='ConnectivityNode.ConnectivityNodeContainer',
                                    suffixes=("","_node"))

# Update name
fromEndName = line_and_nodes['ConnectivityNode.fromEndName']
toEndName   = line_and_nodes['ConnectivityNode.toEndName']
line_and_nodes["IdentifiedObject.name"] = fromEndName + "-" + toEndName


# Update description
fromEndIsoCode = line_and_nodes['ConnectivityNode.fromEndIsoCode']
toEndIsoCode   = line_and_nodes['ConnectivityNode.toEndIsoCode']
line_and_nodes["IdentifiedObject.description"] = "AC tie line between " + fromEndIsoCode + ' and ' + toEndIsoCode

data.update_triplet_from_tableview(line_and_nodes.set_index("ID")[["IdentifiedObject.name",
                                                                   "IdentifiedObject.description"]], add=False)




# TODO make report on lines without EIC
# TODO make report on line EIC not in cio tool

# 8 Update DC line name and description

# 9 Remove Junctions

# 10 Remove Terminals

# 11 Update version number if it already exists

# 12 Export the boundary

# Export
filename_mask = "{scenarioTime:%Y%m%dT%H%MZ}_{modelingEntity}_{processType}_{messageType}_{version:03d}"
data = CGMEStools.update_filename_from_FullModel(data, filename_mask)
data.export_to_excel()


