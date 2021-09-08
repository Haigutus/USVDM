# -------------------------------------------------------------------------------
# Name:        Export Referencedata
# Purpose:     Create an RDF file of all relevant reference data for CGM Process and specifically for IGM validation
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

from Tools.RDF_PARSER import RDF_parser

### Input conf ###

debug = True

# Mapping tables #
mapping_conf_path = "configurations/CGMProcess_ReferenceData_dev.xlsx"

### Output conf ###

# CGMES export
export_undefined = False
#export_type      = "xml_per_instance_zip_per_all"
#export_type = "xml_per_instance_zip_per_xml"
export_type = "xml_per_instance"
export_format = "configurations/CGMBP_extentsions.json"

## Process start

# Load configurations
data_to_add = pandas.read_excel(mapping_conf_path, sheet_name=None)

INSTANCE_ID = str(uuid4())


#ProcessTypes
data = RDF_parser.tableview_to_triplet(data_to_add['ReferenceData_Distribution'].set_index("ID"))
data["INSTANCE_ID"] = INSTANCE_ID

#CimProfiles
process_triplet = RDF_parser.tableview_to_triplet(data_to_add['ProcessType'].set_index("ID"))
process_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(process_triplet, add=True, update=False)

#CimProfiles
profiles_triplet = RDF_parser.tableview_to_triplet(data_to_add['CimProfile'].set_index("ID"))
profiles_triplet["INSTANCE_ID"] = INSTANCE_ID

data = data.update_triplet_from_triplet(profiles_triplet, add=True, update=False)


# Load export format configuration
with open(export_format, "r") as conf_file:
    rdf_map = json.load(conf_file)

# Set namespaces for export

namespace_map = dict(cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                     cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#",
                     rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                     rdfs="http://www.w3.org/2000/01/rdf-schema#",
                     dcat="http://www.w3.org/ns/dcat#",
                     dcterms="http://purl.org/dc/terms/")

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map,
                      namespace_map=namespace_map,
                      export_undefined=export_undefined,
                      export_type=export_type,
                      #global_zip_filename=global_zip_filename,
                      # debug=True
                      )
