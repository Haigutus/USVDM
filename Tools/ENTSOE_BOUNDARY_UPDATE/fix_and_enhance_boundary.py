# -------------------------------------------------------------------------------
# Name:        Boundary
# Purpose:     Update boundary
#
# Author:      kristjan.vilgo
#
# Created:     24.10.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPLv2
# -------------------------------------------------------------------------------
from os import path
from datetime import datetime
from uuid import uuid4
import pandas
import json

from Tools.RDF_PARSER import RDF_parser, CGMES_tools


def get_metadata_from_filename_NMD(file_name):
    """Parse metadata from Network Model Manager export"""
    meta = {}
    raw_meta = file_name.split(".")[0].split("_")

    meta["Model.scenarioTime"] = raw_meta[0]
    meta["Model.modelingEntity"] = raw_meta[1].replace("-", "")  # '-' and '_' are meta separators, can't be used in a name
    meta["Model.messageType"] = raw_meta[2] + raw_meta[3]
    meta["Model.version"] = raw_meta[4]
    meta["Model.processType"] = ""

    return meta


### Input conf ###

debug = True

# Mapping tables #
mapping_conf_path = "configurations/CGMProcess_ReferenceData_dev.xlsx"

# Input Boundary #
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20200129T0000Z_ENTSO-E_BD_1164.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20180503T0000Z_ENTSO-E_BD_1210.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20180531T0000Z_ENTSO-E_BD_1210.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20180701T0000Z_ENTSO-E_BD_1210.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20210831T0000Z_ENTSO-E_BD_1276.zip"
boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20181001T0000Z_ENTSO-E_BD_1308 (2).zip"

### Output conf ###

# CGMES export
export_undefined = False
#export_type      = "xml_per_instance_zip_per_all"
export_type = "xml_per_instance_zip_per_xml"
#export_type = "xml_per_instance"
export_format = "configurations/CGMES_2_4_15_and_CGMBP_extentsions.json"

## Process start

# 1 Load data from CGMES boundary global ZIP, exported by NMD
data = RDF_parser.load_all_to_dataframe([boundary_path])

# Load configurations
data_to_add = pandas.read_excel(mapping_conf_path, sheet_name=None)

# DEBUG export initial data in excel
# data.export_to_excel()


### START Update FullModel ###

# Add missing metadata form filename to FullModel
data = CGMES_tools.update_FullModel_from_filename(data, parser=get_metadata_from_filename_NMD)

# Get current time, to update created DateTime and ScenarioTime
utc_now = datetime.utcnow()

# X.X Update boundary instance files FullModel rdf:about TODO - add requirement ID
for FullModel_ID in data.query("KEY == 'Type' and VALUE == 'FullModel'").ID.unique():
    new_ID = str(uuid4())
    data = data.replace(FullModel_ID, new_ID)
    if debug:
        print(f"INFO - FullModel ID replaced {FullModel_ID} -> {new_ID}")


# Get current metadata
old_metadata = CGMES_tools.get_metadata_from_FullModel(data)
new_metadata = {}

if debug:
    print(f"INFO - initial metadata {old_metadata}")

# 2.1 Update description
# metadata['Model.description'] = "Official CGM boundary set"

# 2.2 Update description
# metadata['Model.description'] = "Official CGM boundary set +//-2 years"

# 2.3 Update description
new_metadata['Model.description'] = f"Official CGM boundary set +//-3 years. Based on NMD version {old_metadata['Model.version']}"

# 2.4 Update description
new_metadata['Model.description'] = f"""
<MDE>
    <BP></BP>
    <TOOL>USVDM 0.2.1</TOOL>
    <TXT>Official CGM boundary set +//-3 years. Based on NMD version {old_metadata['Model.version']}</TXT>
    <RSC>BALTIC</RSC>
</MDE>
"""

# 3.1 Update modelling AuthoritySet
# metadata['Model.modelingAuthoritySet'] = "http://tscnet.eu/EMF"

# 3.2 Update modelling AuthoritySet
#new_metadata['Model.modelingAuthoritySet'] = "http://baltic-rsc.eu/Boundary/CGMES/2.4.15"

# 3.3
new_metadata['Model.modelingAuthoritySet'] = "http://www.entsoe.eu/BoundarySet"


# 4.1 Update model Scenario Time  TODO - test 00:30 on OPDM
new_metadata['Model.scenarioTime'] = f"{utc_now.date().isoformat()}T00:00:00Z"

# 5.1 Update model Created
new_metadata['Model.created'] = f"{utc_now.isoformat()}Z"

# 6.1 Set model Version to 001 by default
new_metadata['Model.version'] = "001"

if debug:
    print(f"INFO - updated metadata {new_metadata}")

# Update metadata
data = CGMES_tools.update_FullModel_from_dict(data, new_metadata)


### END Update FullModel ###


# Get all Lines, TP nad CN nodes for later use

lines = data.type_tableview("Line").reset_index()
cn_nodes = data.type_tableview("ConnectivityNode").reset_index()
tp_nodes = data.type_tableview("TopologicalNode").reset_index()

# TODO add name and description to ConnectivityNode and TopologicalNode?
line_and_nodes = lines.merge(cn_nodes,
                             left_on="ID",
                             right_on='ConnectivityNode.ConnectivityNodeContainer',
                             suffixes=("", "_ConnectivityNode"))

line_and_nodes = line_and_nodes.merge(tp_nodes,
                                      left_on="ID",
                                      right_on='TopologicalNode.ConnectivityNodeContainer',
                                      suffixes=("", "_TopologicalNode"))



### START Update AC line names and descriptions ###

fromEndName = line_and_nodes['ConnectivityNode.fromEndName']
toEndName = line_and_nodes['ConnectivityNode.toEndName']
line_cb_id = line_and_nodes["IdentifiedObject.name_ConnectivityNode"].str[-2:]

# 7.1 Create new Line name
# line_and_nodes["IdentifiedObject.name"] = (fromEndName + " - " + toEndName).str[:32] # Limit to 32 character # OLD

# 7.3 Create new Line name and add last char from boundary point name
line_and_nodes["IdentifiedObject.name"] = (line_cb_id + "-" + fromEndName + "-" + toEndName).str[:32]  # Limit to 32 character

# 7.3 Create new Line description
fromEndIsoCode = line_and_nodes['ConnectivityNode.fromEndIsoCode']
toEndIsoCode = line_and_nodes['ConnectivityNode.toEndIsoCode']
line_and_nodes["IdentifiedObject.description"] = "AC tie line between " + fromEndIsoCode + ' and ' + toEndIsoCode

# Update Line data
data = data.update_triplet_from_tableview(line_and_nodes.set_index("ID")[["IdentifiedObject.name", "IdentifiedObject.description"]], add=False)

### END Update AC line names and descriptions ###

# 8 Update DC line name and description

# Update Lines
columns_to_update = ["IdentifiedObject.name", "IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic", "IdentifiedObject.shortName"]

# HVDC_data = pandas.read_csv("configurations/HVDC_mapping.csv", index_col=0)

EQBD_INSTANCE_ID = data.query("KEY == 'Model.profile' and VALUE == 'http://entsoe.eu/CIM/EquipmentBoundary/3/1'").INSTANCE_ID.item()
TPBD_INSTANCE_ID = data.query("KEY == 'Model.profile' and VALUE == 'http://entsoe.eu/CIM/TopologyBoundary/3/1'").INSTANCE_ID.item()


HVDC_data = data_to_add['LINE_CGMproject']

DC_LINES_1 = HVDC_data.set_index("ID")[columns_to_update]
DC_LINES_2 = HVDC_data.dropna(subset=["DUPLICATE_ID"]).drop(columns="ID").rename(columns={"DUPLICATE_ID": "ID"}).set_index("ID")[columns_to_update]

DC_LINES = pandas.concat([DC_LINES_1, DC_LINES_2])

data = data.update_triplet_from_tableview(DC_LINES, add=True, instance_id=EQBD_INSTANCE_ID)

# Update nodes
columns_to_update = ["IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic"]
HVDC_lines_and_nodes = DC_LINES.merge(line_and_nodes, on='ID', suffixes=("", "_old")).set_index("ID")

# Update ConnectivityNodes
DC_CN_NODES = HVDC_lines_and_nodes.rename(columns={"ID_ConnectivityNode": "ID"}).set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_CN_NODES, add=True, instance_id=EQBD_INSTANCE_ID)

# Update TopologicalNodes
DC_TP_NODES = HVDC_lines_and_nodes.rename(columns={"ID_TopologicalNode": "ID"}).set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_TP_NODES, add=True, instance_id=TPBD_INSTANCE_ID)

# 9 Remove Junctions - Removed in export configuration

# 10 Remove Terminals - Removed in export configuration

# 13 Remove empty EIC - If empty, removed in export

# Add additional Areas

INSTANCE_ID = data.query("VALUE == 'http://entsoe.eu/CIM/EquipmentBoundary/3/1'").INSTANCE_ID.item()

areas = data_to_add['AREA_CGMproject'].query("add_to_boundary == True").set_index("ID")

areas_triplet = RDF_parser.tableview_to_triplet(areas)
areas_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(areas_triplet, add=True, update=False)


party = data_to_add['PARTY_CGMproject'].query("add_to_boundary == True").set_index("ID")

party_triplet = RDF_parser.tableview_to_triplet(party)
party_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(party_triplet, add=True, update=False)

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
    metadata = CGMES_tools.get_metadata_from_FullModel(data)
    global_zip_filename = CGMES_tools.get_filename_from_metadata(metadata, filename_mask=global_zip_filemask, file_type='zip')
    eq_zip_filename = CGMES_tools.get_filename_from_metadata(metadata, file_type='zip')

    # 11 Update version number if it already exists
    if path.exists(global_zip_filename) or path.exists(eq_zip_filename):
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

# Set namespaces for export

namespace_map = dict(cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
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
                      global_zip_filename=global_zip_filename,
                      # debug=True
                      )

# Excel triplet export
# data.export_to_excel()

# Export changes
# data.changes.to_csv("changes.csv", encoding="UTF-8")

