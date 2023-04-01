from datetime import datetime
import sys
import pandas
from uuid import uuid4

sys.path.append("..")
import RDF_parser

source_excel_file = r"ObjectRegistry.xlsx"

types_to_convert = ["FullModel", "IdentifiedObject", "Name"]
source_data = pandas.read_excel(source_excel_file, sheet_name=types_to_convert)

# Convert to triplets
triplet_data_list = []
for type_name, type_data in source_data.items():
    triplet_data_list.append(type_data.set_index("ID").tableview_to_triplet())


# Add Distribution data for filename definition
DIST_ID = str(uuid4())
triplet_data_list.append(pandas.DataFrame(
        [
            # Distribution part, needed for filename
            (DIST_ID, "Type", "Distribution"),
            (DIST_ID, "label", "ObjectRegistry.rdf"), # Change this to change filename

        ],
        columns=["ID", "KEY", "VALUE"]
    )
)

# Concat all converted triplets
data = pandas.concat(triplet_data_list, ignore_index=True)

# Set Converter version
data.set_VALUE_at_KEY("Model.applicationSoftware", "ObjectRegistryConverter_0.0.1_2023-04-01")

# Add instance ID
data["INSTANCE_ID"] = str(uuid4())

# Export
data.export_to_cimxml(rdf_map=r"../ENTSO-E_Object Registry vocabulary_2.1.0_2022-07-21.json",
                      export_undefined=False,
                      export_type="xml_per_instance",
                      debug=False)




