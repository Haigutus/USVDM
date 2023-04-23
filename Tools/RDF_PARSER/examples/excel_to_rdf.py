from datetime import datetime
import sys
import pandas
from uuid import uuid4

sys.path.append("..")
import RDF_parser

version = "0.0.2_2023-04-23"


def convert_excel_to_rdf(rdf_conf_path, source_excel_path, types_to_convert,
                         destination_rdf_path=None,
                         export_type="xml_per_instance"
                         ):

    # TODO - maybe add send to EDX functionality
    # TODO - maybe add filename form metadata creation
    if not destination_rdf_path:
        destination_rdf_path = f"excel_to_rdf_export_{datetime.now():%Y-%m-%dT%H%M}.rdf"

    print(f"INFO loading {types_to_convert} from {source_excel_path}")
    source_data = pandas.read_excel(source_excel_path, sheet_name=types_to_convert)

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
                (DIST_ID, "label", destination_rdf_path),
            ],
            columns=["ID", "KEY", "VALUE"]
        )
    )

    # Concat all converted triplets
    data = pandas.concat(triplet_data_list, ignore_index=True)

    # Set Converter version
    data.set_VALUE_at_KEY("Model.applicationSoftware", f"ExcelToRDFConverter_{version}")

    # Add instance ID
    data["INSTANCE_ID"] = str(uuid4())

    # Export
    data.export_to_cimxml(rdf_map=rdf_conf_path,
                          export_undefined=False,
                          export_type=export_type,
                          debug=False)


if __name__ == "__main__":
    source_excel_path = r"ObjectRegistry.xlsx"

    types_to_convert = ["FullModel", "IdentifiedObject", "Name"]

    rdf_conf = r"../ENTSO-E_Object Registry vocabulary_2.1.0_2022-07-21_about_urn_uuid.json"

    convert_excel_to_rdf(rdf_conf, source_excel_path, types_to_convert)





