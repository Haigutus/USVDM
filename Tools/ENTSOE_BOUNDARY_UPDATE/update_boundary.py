#-------------------------------------------------------------------------------
# Name:        Boundary
# Purpose:     Update boundary
#
# Author:      kristjan.vilgo
#
# Created:     24.10.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPLv2
#-------------------------------------------------------------------------------
from os import path
from datetime import datetime
from uuid import uuid4

import sys
import pandas
import json

sys.path.append("../RDF_PARSER")
import RDF_parser
import CGMES_tools



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

### Input conf ###
data_to_add = pandas.read_excel("configurations/MAP_AREA_PARTY.xlsx", sheet_name=None)
boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20200129T0000Z_ENTSO-E_BD_1164.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20191023T0000Z_ENTSO-E_BD_1130.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"
#boundary_path = r"/home/kristjan/Downloads/20191023T0000Z_ENTSO-E_BD_1130.zip"

# CGMES export
export_undefined = False
export_type      = "xml_per_instance_zip_per_all"
#export_type     = "xml_per_instance_zip_per_xml"
#export_type     = "xml_per_instance"
export_format    = "configurations/CGMES_2_4_15.json"


### Output conf ###
eic_report_path = "EIC_report.xlsx"

# 1 Load data from CGMES boundary global ZIP, exported by NMD
data = RDF_parser.load_all_to_dataframe([boundary_path])

# DEBUG export initial data in excel
#data.export_to_excel()

# Add missing metadata form filename to FullModel
data = CGMES_tools.update_FullModel_from_filename(data, parser=get_metadata_from_filename_NMD)

# Get current time, to update created DateTime and ScenarioTime
utc_now = datetime.utcnow()

# Update FullModel
meta_updates = {'Model.description':          "Official CGM boundary set +//-2 years",    # 2.2 Update description
                #'Model.description':          "Official CGM boundary set",               # 2.1 Update description            TODO - add +//-2 years, add original BD version nr
                'Model.modelingAuthoritySet': "http://tscnet.eu/EMF",                     # 3 Update modelling AuthoritySet
                'Model.scenarioTime':         utc_now.date().isoformat() + "T00:00:00Z",  # 4 Update model Scenario Time      TODO - update to 00:30 and test on OPDM
                'Model.created':              utc_now.isoformat() + "Z",                  # 5 Update model Created
                'Model.version':              "001"                                       # 6 Set model Version to 001
                }

# Update metadata
data = CGMES_tools.update_FullModel_from_dict(data, meta_updates)

# Update uuid

for INSTANCE_ID in data.INSTANCE_ID.unique():
    data = data.replace(INSTANCE_ID, str(uuid4()))


# Get all Lines, TP nad CN nodes for later use

lines    = data.type_tableview("Line").reset_index()
cn_nodes = data.type_tableview("ConnectivityNode").reset_index()
tp_nodes = data.type_tableview("TopologicalNode").reset_index()

#TODO add name and description to ConnectivityNode and TopologicalNode?
line_and_nodes = lines.merge(cn_nodes, left_on="ID",
                                      right_on='ConnectivityNode.ConnectivityNodeContainer',
                                      suffixes=("", "_ConnectivityNode"))

line_and_nodes = line_and_nodes.merge(tp_nodes, left_on="ID",
                                      right_on='TopologicalNode.ConnectivityNodeContainer',
                                      suffixes=("", "_TopologicalNode"))

### EIC REPORT ###
# TODO move eic report to seperate script
# TODO report per TSO not per Country

eic_report_columns = ['ID', 'IdentifiedObject.description', 'IdentifiedObject.energyIdentCodeEic', 'IdentifiedObject.name', 'IdentifiedObject.shortName']

# Find lines with out EIC
Lines_without_EIC = line_and_nodes[~(line_and_nodes["IdentifiedObject.energyIdentCodeEic"].notna())]
unique_country = pandas.unique(Lines_without_EIC[['ConnectivityNode.fromEndIsoCode', 'ConnectivityNode.toEndIsoCode']].values.ravel())

missing_eic_report_dict = {}

for country in unique_country:
    missing_eic = Lines_without_EIC[(Lines_without_EIC['ConnectivityNode.fromEndIsoCode'] == country) | (Lines_without_EIC['ConnectivityNode.toEndIsoCode'] == country)]
    missing_eic_report_dict[country] = missing_eic

report_columns = ["ID","IdentifiedObject.name_ConnectivityNode", "IdentifiedObject.name", 'IdentifiedObject.energyIdentCodeEic', 'ConnectivityNode.fromEndName', 'ConnectivityNode.toEndName', 'ConnectivityNode.fromEndIsoCode', 'ConnectivityNode.toEndIsoCode']


# check if EIC is valid
from stdnum.eu import eic
Lines_with_EIC = line_and_nodes[(line_and_nodes["IdentifiedObject.energyIdentCodeEic"].notna())]
InvalidEIC = Lines_with_EIC[~Lines_with_EIC["IdentifiedObject.energyIdentCodeEic"].apply(eic.is_valid)]

# check if EIC is in CIO list
from entsoe_eic_registry import get_allocated_eic

# create excel file where to write reports

writer = pandas.ExcelWriter(eic_report_path)

try:
    allocated_eic = get_allocated_eic()
    eic_not_registered = Lines_with_EIC.merge(allocated_eic, left_on="IdentifiedObject.energyIdentCodeEic", right_on="mRID", indicator=True, how="outer").query("_merge=='left_only'")
    eic_not_registered[report_columns].to_excel(writer, "EIC_NotRegistered", index=False)

except:
    print("Error getting ENTSO-E EIC registry")


# check if there are duplicated boundary names
duplicated_boundary_names = line_and_nodes[line_and_nodes.duplicated("IdentifiedObject.name_ConnectivityNode", keep=False)][report_columns]

# Export to excel EIC check results

duplicated_boundary_names[report_columns].to_excel(writer, "DuplicatedBoundaryPointName", index=False)

InvalidEIC[report_columns].to_excel(writer, "EIC_Invalid", index=False)

for country in missing_eic_report_dict:
    missing_eic_report_dict[country][report_columns].to_excel(writer, country, index=False)

# Get sheet to do some formatting
for sheet_name in writer.sheets:

    sheet = writer.sheets[sheet_name]

    # Set default column size, if this does not work you are missing XslxWriter module
    first_col = 0
    last_col = len(report_columns)
    width = 38
    sheet.set_column(first_col, last_col, width)

    # freeze column names and ID column
    sheet.freeze_panes(1, 1)

writer.close()

### EIC check end ###

# 7 Update Line name and description

### Update AC line names and descriptions ###
# Create new Line name
fromEndName = line_and_nodes['ConnectivityNode.fromEndName']
toEndName   = line_and_nodes['ConnectivityNode.toEndName']
#line_and_nodes["IdentifiedObject.name"] = (fromEndName + " - " + toEndName).str[:32] # Limit to 32 character # OLD

# Update to have unique line name, add last char from boundary point name
line_cb_id = line_and_nodes["IdentifiedObject.name_ConnectivityNode"].str[-1]
line_and_nodes["IdentifiedObject.name"] = (line_cb_id + "-" + fromEndName + "-" + toEndName).str[:32] # Limit to 32 character


# Create new Line description
fromEndIsoCode = line_and_nodes['ConnectivityNode.fromEndIsoCode']
toEndIsoCode   = line_and_nodes['ConnectivityNode.toEndIsoCode']
line_and_nodes["IdentifiedObject.description"] = "AC tie line between " + fromEndIsoCode + ' and ' + toEndIsoCode

# Update Line data
data = data.update_triplet_from_tableview(line_and_nodes.set_index("ID")[["IdentifiedObject.name", "IdentifiedObject.description"]], add=False)



# 8 Update DC line name and description

# Update Lines
columns_to_update = ["IdentifiedObject.name", "IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic", "IdentifiedObject.shortName"]

#HVDC_data = pandas.read_csv("configurations/HVDC_mapping.csv", index_col=0)

HVDC_data = data_to_add['LINE_CGMproject']

DC_LINES = HVDC_data.set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_LINES, add=False)

# Update nodes
columns_to_update = ["IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic"]
HVDC_lines_and_nodes = HVDC_data.merge(line_and_nodes, on='ID', suffixes=("", "_old"))

# Update ConnectivityNodes
DC_CN_NODES = HVDC_lines_and_nodes.rename(columns={"ID_ConnectivityNode": "ID"}).set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_CN_NODES, add=False)

# Update TopologicalNodes
DC_TP_NODES = HVDC_lines_and_nodes.rename(columns={"ID_TopologicalNode": "ID"}).set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_TP_NODES, add=False)


# 9 Remove Junctions

# 10 Remove Terminals

# Add additional Areas

mapping_table = data_to_add['Mapping'].dropna(how="all")
INSTANCE_ID   = data.query("VALUE == 'http://entsoe.eu/CIM/EquipmentBoundary/3/1'").INSTANCE_ID.item()


column_map    = {column:column.split("_")[1] for column in mapping_table.columns if "AREA" in column}
areas         = mapping_table[list(column_map.keys())].rename(columns=column_map).drop_duplicates("ID").dropna(subset=["ID"]).set_index("ID")
areas["Type"] = "GeographicalRegion"

areas_triplet = RDF_parser.tableview_to_triplet(areas)
areas_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(areas_triplet, add=True, update=False)

# Add Party

party_column_map = {column:column.split("_")[1] for column in mapping_table.columns if "PARTY" in column}
party = mapping_table[list(party_column_map.keys())].rename(columns=party_column_map).drop_duplicates("ID").dropna(subset=["ID"]).set_index("ID")
party["Type"] = "Party"

party_triplet = RDF_parser.tableview_to_triplet(party)
party_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(party_triplet, add=True, update=False)

party_full_data = party.merge(allocated_eic, left_on="IdentifiedObject.energyIdentCodeEic", right_on="mRID")

# Add references to regions

area_referneces = mapping_table[["PARTY_ID","AREA_ID"]].rename(columns={"PARTY_ID": "ID", "AREA_ID": "VALUE"}).dropna(subset=["ID"])
area_referneces["KEY"] = "Party.Region"
area_referneces["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(area_referneces, add=True, update=False)


# 22.1 Add or update common enumerations

enumerations = pandas.read_excel("configurations/ENUMERATIONS.xlsx", sheet_name=None)

for enumeration in enumerations:
    print("Adding enumerations for {}".format(enumeration))
    enumeration_triplet = RDF_parser.tableview_to_triplet(enumerations[enumeration].set_index("ID"))
    enumeration_triplet["INSTANCE_ID"] = INSTANCE_ID

    data = data.update_triplet_from_triplet(enumeration_triplet, add=True, update=False)




# 13 Remove empty EIC

# 12 Export the boundary


# Exports to RDF all data with same INSTACE_ID and if label element exists for it. Each Type is put to a sheet
# TODO add specific folder path
# TODO set some nice properties - https://xlsxwriter.readthedocs.io/workbook.html#workbook-set-properties




### EXPORT ###

instance_filemask = "{scenarioTime:%Y%m%dT%H%MZ}_{processType}_{modelingEntity}_{messageType}_{version:03d}"
global_zip_filemask = "{scenarioTime:%Y%m%dT%H%MZ}_{processType}_{modelingEntity}_BD_{version:03d}"

def set_export_filenames(data):

    # Set file names for single cimxml
    data = CGMES_tools.update_filename_from_FullModel(data, instance_filemask)

    # Generate filename for global zip
    metadata            = CGMES_tools.get_metadata_from_FullModel(data)
    global_zip_filename = CGMES_tools.get_filename_from_metadata(metadata, filename_mask=global_zip_filemask, file_type='zip')

    # 11 Update version number if it already exists
    if path.exists(global_zip_filename):
        print("File all ready exists {}".format(global_zip_filename))

        # Update version if export all ready exists
        meta_updates = {'Model.version': "{:03d}".format(int(metadata["Model.version"]) + 1)}

        # Update metadata
        data = CGMES_tools.update_FullModel_from_dict(data, meta_updates)

        data, global_zip_filename = set_export_filenames(data)

    return data, global_zip_filename

data, global_zip_filename = set_export_filenames(data)


# Load export format configuration
with open(export_format, "r") as conf_file:
    rdf_map = json.load(conf_file)

# Set namepsaces for export

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#",
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map,
                      namespace_map=namespace_map,
                      export_undefined=export_undefined,
                      export_type=export_type,
                      global_zip_filename=global_zip_filename)

# Excel triplet export
#data.export_to_excel()

# Export changes
#data.changes.to_csv("changes.csv", encoding="UTF-8")

