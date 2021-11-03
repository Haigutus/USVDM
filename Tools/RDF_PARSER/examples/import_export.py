# Purpose:     Correct input models for merging
#
# Author:      kristjan.vilgo
#
# Created:     26.02.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPLv2
#-------------------------------------------------------------------------------
from shapely.geometry import Point, MultiPoint, box
import sys
sys.path.append("..")
import RDF_parser
import CGMES_tools
import pandas
import json
from tkinter import filedialog
from tkinter import *



input_data = list(filedialog.askopenfilenames(initialdir="/", title="Select CIMXML files", filetypes=(("CIMXML", "*.zip"), ("CIMXML","*.xml"))))

# Read data
data = pandas.read_RDF(input_data)

# Parse metadata
data = CGMES_tools.update_FullModel_from_filename(data)


## EXPORT ###

# Set namepsaces for export

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         #cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#",
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")

export_undefined = False
export_type      = "xml_per_instance_zip_per_all"

# Load export format configuration
with open(r"..\entsoe_v2.4.15_2014-08-07_about_urn_uuid.json", "r") as conf_file:
    rdf_map = json.load(conf_file)

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map, namespace_map=namespace_map, export_undefined=export_undefined, export_type=export_type)


