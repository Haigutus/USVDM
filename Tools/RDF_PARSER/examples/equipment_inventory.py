import sys
sys.path.append("..")
import pandas
import json
import uuid
import RDF_parser

input_data = [r"C:\Users\kristjan.vilgo\Downloads\QoCDC_v3.2.1_test_models\test.zip"]

items = ['Line',
 'ACLineSegment',
 'GeneratingUnit',
 'NuclearGeneratingUnit',
 'ThermalGeneratingUnit',
 'WindGeneratingUnit',
 'SolarGeneratingUnit',
 'HydroGeneratingUnit',
 'HydroPump',
 'SynchronousMachine',
 'AsynchronousMachine',
 'ConformLoad',
 'NonConformLoad',
 'StationSuply',
 'BusbarSection',
 'LinearShuntCompensator',
 'NonLinearShuntCompensator',
 'SeriesCompensator',
 'StaticVarCompensator',
 'DCLineSegment',
 'Substation',
 'PowerTransformer',
 'identifiedObject.Name',
 'identifiedObject.Description',
 'IdentifiedObject.mRID',
 'IdentifiedObject.energyIdentCodeEic',
 'IdentifiedObject.shortName',
 'Equipment.EquipmentContainer',
 'VoltageLevel.Substation',
 'ConductingEquipment.BaseVoltage']


# Create profile definition for export
with open(r"..\entsoe_v2.4.15_2014-08-07.json", "r") as conf_file:
    rdf_map = json.load(conf_file)
rdf_map["EQINV"] = {}
for key, value in rdf_map["EQ"].items():

    if key in items:
        if value.get("parameters"):
            value["parameters"] = [parameter for parameter in value["parameters"] if parameter in items]

        rdf_map["EQINV"][key] = value

# Load data
data = pandas.read_RDF(input_data)

# Filter out old headers
data = data.merge(data.query("KEY == 'Type' and VALUE != 'FullModel' and VALUE != 'Distribution'").ID)

# Create new ID-s
INSTANCE_ID = str(uuid.uuid4())
header_id = str(uuid.uuid4())
distribution_id = str(uuid.uuid4())

# Define export
export_conf = [
    (distribution_id, "Type", "Distribution", INSTANCE_ID),
    (distribution_id, "label", "equipment_inventory_example.xml", INSTANCE_ID),
    (distribution_id, "Model.messageType", "EQINV", INSTANCE_ID),
]
data = pandas.concat([data, pandas.DataFrame(export_conf, columns=["ID", "KEY", "VALUE", "INSTANCE_ID"])])

data["INSTANCE_ID"] = INSTANCE_ID

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
export_type      = "xml_per_instance_zip_per_xml"

# Export triplet to CGMES
data.export_to_cimxml(rdf_map=rdf_map, namespace_map=namespace_map, export_undefined=export_undefined, export_type=export_type, debug=True)