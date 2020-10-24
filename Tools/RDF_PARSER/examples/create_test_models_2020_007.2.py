import sys
import pandas
import json
import datetime
from uuid import uuid4

sys.path.append("..")
import RDF_parser
import CGMES_tools


# Input settings
input_data = [r"C:\Users\kristjan.vilgo\Downloads\20201017T1330Z_1D_APG_001\20201017T1330Z_1D_APG_001.zip"]


# Set namepsaces for export

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         #cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#",
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")

# Export settings
export_undefined = False
export_type      = "xml_per_instance_zip_per_xml"

# Load export format configuration
with open(r"..\entsoe_v2.4.15_2014-08-07.json", "r") as conf_file:
    rdf_map = json.load(conf_file)

# Read data
data = pandas.read_RDF(input_data)

# Parse metadata to file header
data = CGMES_tools.update_FullModel_from_filename(data)

test_description = "Test model created for Change Request 2020_007.2. Code used for generation: https://github.com/Haigutus/USVDM/blob/master/Tools/RDF_PARSER/examples/create_test_models_2020_007.2.py"

versions = [{"HEADER": {"Model.modelingEntity": "ELERING",
                        "Model.created": f"{datetime.datetime.utcnow().isoformat()}Z",
                        "Model.scenarioTime": "2020-10-12T09:30:00Z",
                        "Model.processType": "1D",
                        "Model.modelingAuthoritySet": "http://www.elering.ee/OperationalPlanning",
                        "Model.description": test_description},
             "MODEL": ["ControlArea/IdentifiedObject.energyIdentCodeEic=10Y1001A1001A39I"]
             },
            {"HEADER": {"Model.modelingEntity": "AST",
                        "Model.created": f"{datetime.datetime.utcnow().isoformat()}Z",
                        "Model.scenarioTime": "2020-10-12T10:30:00Z",
                        "Model.processType": "2D",
                        "Model.modelingAuthoritySet": "http://www.ast.lv/OperationalPlanning",
                        "Model.description": test_description},
             "MODEL": ["ControlArea/IdentifiedObject.energyIdentCodeEic=10YLV-1001A00074"]
             },
            {"HEADER": {"Model.modelingEntity": "LITGRID",
                        "Model.created": f"{datetime.datetime.utcnow().isoformat()}Z",
                        "Model.scenarioTime": "2020-10-12T11:30:00Z",
                        "Model.processType": "2D",
                        "Model.modelingAuthoritySet": "http://www.litgrid.eu/OperationalPlanning",
                        "Model.description": test_description},
             "MODEL": ["ControlArea/IdentifiedObject.energyIdentCodeEic=10YLT-1001A0008Q"]
             }
            ]

for version in versions:

    # Update FullModel
    meta_updates = version["HEADER"]

    # Update metadata
    data = CGMES_tools.update_FullModel_from_dict(data, meta_updates)

    # Update model data

    for update in version["MODEL"]:
        object_name, attribute = update.split("/")
        attribute_name, attribute_value = attribute.split("=")

        object_ID = data.query(f"KEY == 'Type' and VALUE == '{object_name}'").iloc[0].ID

        attribute_index = data.query(f"ID == '{object_ID}' and KEY == '{attribute_name}'").index[0]

        # Update data
        data.loc[attribute_index, "VALUE"] = attribute_value



    # Update filename
    CGMES_tools.update_filename_from_FullModel(data)

    # Update uuid of each profile instance
    for INSTANCE_ID in data.query("KEY == 'Type' and VALUE == 'FullModel'").ID.unique():
        data = data.replace(INSTANCE_ID, str(uuid4()))

    # Export triplet to CGMES
    data.export_to_cimxml(rdf_map=rdf_map, namespace_map=namespace_map, export_undefined=export_undefined, export_type=export_type)