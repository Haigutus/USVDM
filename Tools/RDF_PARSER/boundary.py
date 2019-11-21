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


boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20191023T0000Z_ENTSO-E_BD_1130.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"
#boundary_path = r"/home/kristjan/Downloads/20191023T0000Z_ENTSO-E_BD_1130.zip"

# 1 Load data from CGMES boundary global ZIP, exported by NMD
data = RDF_parser.load_all_to_dataframe([boundary_path])

# DEBUG export initial data in excel
#data.export_to_excel()

# Add missing metadata form filename to FullModel
data = CGMEStools.update_FullModel_from_filename(data, parser=get_metadata_from_filename_NMD)

# Get current time, to update created DateTime and ScenarioTime
utc_now = datetime.utcnow()

# Update FullModel
meta_updates = {'Model.description':          "Official CGM boundary set",                # 2 Update description            TODO Proposal to add original BD version nr
                'Model.modelingAuthoritySet': "http://tscnet.eu/EMF",                     # 3 Update modelling AuthoritySet
                'Model.scenarioTime':         utc_now.date().isoformat() + "T00:00:00Z",  # 4 Update model Scenario Time    TODO update to 00:30 and test on OPDM
                'Model.created':              utc_now.isoformat() + "Z",                  # 5 Update model Created
                'Model.version':              "001"                                       # 6 Set model Version to 001
                }

# Update metadata
data = CGMEStools.update_FullModel_from_dict(data, meta_updates)

# 7 Update Line name and description

lines    = data.type_tableview("Line").reset_index()
cn_nodes = data.type_tableview("ConnectivityNode").reset_index()
tp_nodes = data.type_tableview("TopologicalNode").reset_index()

#TODO add name and description to ConnectivityNode and TopologicalNode?
line_and_nodes = lines.merge(cn_nodes, left_on="ID",
                                    right_on='ConnectivityNode.ConnectivityNodeContainer',
                                    suffixes=("","_ConnectivityNode"))

#line_and_nodes = line_and_nodes.merge(tp_nodes, left_on="ConnectivityNode.TopologicalNode",
#                                      right_index=True,
#                                      suffixes=("","_TopologicalNode"))

# Create new Line name
fromEndName = line_and_nodes['ConnectivityNode.fromEndName']
toEndName   = line_and_nodes['ConnectivityNode.toEndName']
line_and_nodes["IdentifiedObject.name"] = (fromEndName + " - " + toEndName).str[:32] # Limit to 32 character

# Update to have unique line name, add last char from boundary point name
#line_cb_id = line_and_nodes["IdentifiedObject.name_ConnectivityNode"].str[-1]
#line_and_nodes["IdentifiedObject.name"] = (line_cb_id +"-" + fromEndName + "-" + toEndName).str[:32] # Limit to 32 character


# Create new Line description
fromEndIsoCode = line_and_nodes['ConnectivityNode.fromEndIsoCode']
toEndIsoCode   = line_and_nodes['ConnectivityNode.toEndIsoCode']
line_and_nodes["IdentifiedObject.description"] = "AC tie line between " + fromEndIsoCode + ' and ' + toEndIsoCode

# Update Line data
data = data.update_triplet_from_tableview(line_and_nodes.set_index("ID")[["IdentifiedObject.name",
                                                                   "IdentifiedObject.description"]], add=False)



# 8 Update DC line name and description

# Update Lines
columns_to_update = ["IdentifiedObject.name", "IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic"]

HVDC_data = pandas.read_csv("HVDC_mapping.csv", index_col=0)

DC_LINES = HVDC_data.rename(columns={"Line.mRID":"ID"}).set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_LINES, add=False)

# Update ConnectivityNodes
columns_to_update = ["IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic"]
DC_CN_NODES = HVDC_data.rename(columns={"ConnectivityNode.mRID":"ID"}).set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_CN_NODES, add=False)

# Update TopologicalNodes
DC_TP_NODES = HVDC_data.merge(tp_nodes[["ID", "TopologicalNode.ConnectivityNodeContainer"]],
                              left_on='Line.mRID',
                              right_on='TopologicalNode.ConnectivityNodeContainer').set_index("ID")[columns_to_update]
data = data.update_triplet_from_tableview(DC_TP_NODES, add=False)

boundary_data = pandas.read_excel(r"C:\USVDM\Tools\RDF_PARSER\DATE_NOT_SELECTED_ENTSO-E_XLS_BD_1128_BoundaryUpgrade.xlsx", sheet="BoundaryPoints", header=1)

boundary_data = boundary_data.rename(columns={"Boundary Point Line CIM ID":"ID", "NEW Line Name ": "IdentifiedObject.name"})

#boundary_data[["Boundary Point Line CIM ID", "Line Name", "NEW Line Name "]]
#lines.merge(boundary_data, left_on="ID", right_on="Boundary Point Line CIM ID")
boundary_data["ID"] = boundary_data["ID"].str[1:]
boundary_data["IdentifiedObject.name"] = boundary_data["IdentifiedObject.name"].str[:32]
boundary_data = boundary_data.set_index("ID")
data = data.update_triplet_from_tableview(boundary_data[["IdentifiedObject.name"]], add=False)

# 9 Remove Junctions

# 10 Remove Terminals

# Add additional Areas

mapping_table = pandas.read_excel("MAP_AREA_PARTY.xlsx").dropna(how="all")
INSTANCE_ID   = data.query("VALUE == 'http://entsoe.eu/CIM/EquipmentBoundary/3/1'").INSTANCE_ID.item()


column_map    = {column:column.split("_")[1] for column in mapping_table.columns if "AREA" in column}
areas         = mapping_table[list(column_map.keys())].rename(columns=column_map).drop_duplicates("ID").set_index("ID")
areas["Type"] = "GeographicalRegion"

areas_triplet = RDF_parser.tableview_to_triplet(areas)
areas_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(areas_triplet, add=True, update=False)

# Add Party

party_column_map    = {column:column.split("_")[1] for column in mapping_table.columns if "PARTY" in column}
party               = mapping_table[list(party_column_map.keys())].rename(columns=column_map).drop_duplicates("ID").set_index("ID")

party_column_map["Party.Region"] = "AREA_ID"
party["Type"]       = "Party"

party_triplet = RDF_parser.tableview_to_triplet(party)
party_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(party_triplet, add=True, update=False)


# 13 Remove empty EIC
# TODO make report on lines without EIC
# TODO make report on line EIC not in CIO tool

#data.query("KEY=='IdentifiedObject.energyIdentCodeEic'")

# 11 Update version number if it already exists

# 12 Export the boundary



"Exports to RDF all data with same INSTACE_ID and if label element exists for it. Each Type is put to a sheet"
# TODO add specific folder path
# TODO set some nice properties - https://xlsxwriter.readthedocs.io/workbook.html#workbook-set-properties

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         cgm= 'http://entsoe.eu/CIM/Extensions/CGM/2019#',
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")



rdf_map = {"EQBD":{"FullModel":                                 {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "attrib":{"attribute":"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",       "value_prefix":"urn:uuid:"}},
                   "Model.created":                             {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.version":                             {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.description":                         {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.modelingAuthoritySet":                {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.profile":                             {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.scenarioTime":                        {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.DependentOn":                         {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "attrib":{"attribute":"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",    "value_prefix":"urn:uuid:"}},
                   "IdentifiedObject.name":                     {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "text": ""},
                   "IdentifiedObject.description":              {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "text": ""},
                   "IdentifiedObject.shortName":                {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "IdentifiedObject.energyIdentCodeEic":       {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode":                          {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "ConnectivityNode.ConnectivityNodeContainer":{"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
                   "ConnectivityNode.toEndIsoCode":             {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode.toEndName":                {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode.toEndNameTso":             {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode.fromEndIsoCode":           {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode.fromEndName":              {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode.fromEndNameTso":           {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode.boundaryPoint":            {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "Line":                                      {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "Line.Region":                               {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
                   "BaseVoltage":                               {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "BaseVoltage.nominalVoltage":                {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "text": ""},
                   "EnergySchedulingType":                      {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "GeographicalRegion":                        {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "SubGeographicalRegion":                     {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "SubGeographicalRegion.Region":              {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
                   "Party":                                     {"namespace": 'http://entsoe.eu/CIM/Extensions/CGM/2019#',        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "Party.Region":                              {"namespace": 'http://entsoe.eu/CIM/Extensions/CGM/2019#',        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},

            },

            "TPBD": { "FullModel":                              {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "attrib":{"attribute":"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",       "value_prefix":"urn:uuid:"}},
                   "Model.created":                             {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.version":                             {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.description":                         {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.modelingAuthoritySet":                {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.profile":                             {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.scenarioTime":                        {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "text": ""},
                   "Model.DependentOn":                         {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "attrib":{"attribute":"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",    "value_prefix":"urn:uuid:"}},
                   "IdentifiedObject.name":                     {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "text": ""},
                   "IdentifiedObject.description":              {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "text": ""},
                   "IdentifiedObject.shortName":                {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "IdentifiedObject.energyIdentCodeEic":       {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode":                           {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
                   "TopologicalNode.BaseVoltage":               {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
                   "TopologicalNode.ConnectivityNodeContainer": {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
                   "TopologicalNode.toEndIsoCode":              {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode.toEndName":                 {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode.toEndNameTso":              {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode.fromEndIsoCode":            {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode.fromEndName":               {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode.fromEndNameTso":            {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "TopologicalNode.boundaryPoint":             {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
                   "ConnectivityNode":                          {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",      "value_prefix": "#_"}},
                   "ConnectivityNode.TopologicalNode":          {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
            }
}



### EXPORT ###

# Update single xml file names kept in label tag and generate global zip name
instance_filemask   = "{scenarioTime:%Y%m%dT%H%MZ}_{processType}_{modelingEntity}_{messageType}_{version:03d}"
global_zip_filemask = "{scenarioTime:%Y%m%dT%H%MZ}_{processType}_{modelingEntity}_BD_{version:03d}"

# Set file names for single cimxml
data = CGMEStools.update_filename_from_FullModel(data, instance_filemask)

# Generate filename for global zip
metadata            = CGMEStools.get_metadata_from_FullModel(data)
global_zip_filename = CGMEStools.get_filename_from_metadata(metadata, filename_mask=global_zip_filemask, file_type='zip')

existing_instance_ID = data.query("KEY == 'Model.messageType'").set_index("VALUE")["ID"].to_dict()
updated_instance_ID  = CGMEStools.generate_instances_ID()


from os import path

print("Does global zip exist - " + str(path.exists(global_zip_filename)))

# CGMES export
export_undefined = False
export_type      = "xml_per_instance_zip_per_all"
#export_type     = "xml_per_instance_zip_per_xml"
#export_type     = "xml_per_instance"

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map, namespace_map=namespace_map, export_undefined=export_undefined,
                                                                    export_type=export_type,
                                                                    global_zip_filename=global_zip_filename)

# Excel triplet export
data.export_to_excel()

# Export changes
data.changes.to_csv("changes.csv", encoding="UTF-8")

