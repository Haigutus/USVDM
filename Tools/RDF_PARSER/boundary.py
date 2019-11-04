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


#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20191023T0000Z_ENTSO-E_BD_1130.zip"
#boundary_path = r"C:\Users\kristjan.vilgo\Downloads\20190304T0000Z_ENTSO-E_BD_001.zip"
boundary_path = r"/home/kristjan/Downloads/20191023T0000Z_ENTSO-E_BD_1130.zip"

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

lines = data.type_tableview("Line").reset_index()
nodes = data.type_tableview("ConnectivityNode").reset_index()

#TODO filter out AC and DC lines
line_and_nodes = lines.merge(nodes, left_on="ID",
                                    right_on='ConnectivityNode.ConnectivityNodeContainer',
                                    suffixes=("","_node"))

# Update name
fromEndName = line_and_nodes['ConnectivityNode.fromEndName']
toEndName   = line_and_nodes['ConnectivityNode.toEndName']
line_and_nodes["IdentifiedObject.name"] = fromEndName + " - " + toEndName


# Update description
fromEndIsoCode = line_and_nodes['ConnectivityNode.fromEndIsoCode']
toEndIsoCode   = line_and_nodes['ConnectivityNode.toEndIsoCode']
line_and_nodes["IdentifiedObject.description"] = "AC tie line between " + fromEndIsoCode + ' and ' + toEndIsoCode

data.update_triplet_from_tableview(line_and_nodes.set_index("ID")[["IdentifiedObject.name",
                                                                   "IdentifiedObject.description"]], add=False)



# 8 Update DC line name and description
columns_to_update = ["IdentifiedObject.name", "IdentifiedObject.description", "IdentifiedObject.energyIdentCodeEic"]

HVDC_data = pandas.read_csv("HVDC_mapping.csv", index_col=0)

DC_LINES = HVDC_data.rename(columns={"Line.mRID":"ID"}).set_index("ID")[columns_to_update]
data.update_triplet_from_tableview(DC_LINES, add=False)

DC_NODES = HVDC_data.rename(columns={"ConnectivityNode.mRID":"ID"}).set_index("ID")[columns_to_update]
data.update_triplet_from_tableview(DC_NODES, add=False)

# 9 Remove Junctions

# 10 Remove Terminals

# 13 Remove empty EIC
# TODO make report on lines without EIC
# TODO make report on line EIC not in CIO tool

data.query("KEY=='IdentifiedObject.energyIdentCodeEic'")

# 11 Update version number if it already exists

# 12 Export the boundary



"Exports to RDF all data with same INSTACE_ID and if label element exists for it. Each Type is put to a sheet"
# TODO add specific folder path
# TODO set some nice properties - https://xlsxwriter.readthedocs.io/workbook.html#workbook-set-properties

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")



rdf_map = {"FullModel":                                 {"namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#", "attrib":{"attribute":"{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",       "value_prefix":"urn:uuid:"}},
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
           "ConnectivityNode.TopologicalNode":          {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
           "ConnectivityNode.toEndIsoCode":             {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
           "ConnectivityNode.toEndName":                {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
           "ConnectivityNode.toEndNameTso":             {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
           "ConnectivityNode.fromEndIsoCode":           {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
           "ConnectivityNode.fromEndName":              {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
           "ConnectivityNode.fromEndNameTso":           {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
           "ConnectivityNode.boundaryPoint":            {"namespace": "http://entsoe.eu/CIM/SchemaExtension/3/1#",        "text": ""},
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
           "Line":                                      {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
           "Line.Region":                               {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
           "BaseVoltage":                               {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
           "BaseVoltage.nominalVoltage":                {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "text": ""},
           "EnergySchedulingType":                      {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
           "GeographicalRegion":                        {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
           "SubGeographicalRegion":                     {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",         "value_prefix": "_"}},
           "SubGeographicalRegion.Region":              {"namespace": "http://iec.ch/TC57/2013/CIM-schema-cim16#",        "attrib":{"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",   "value_prefix": "#_"}},
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

