import sys
import argparse
from excel_to_rdf import convert_excel_to_rdf, version

parser = argparse.ArgumentParser(description="""Convert EXCEL representation of RDF data to RDF/XML""",
                                 epilog=f"""Copyright (c): Baltic RCC OÜ 2023;
                                           Creator: kristjan.vilgo@baltic-rcc.eu;
                                           Licence: GPL 2.0;
                                           Version: {version}""",
                                 prog="convert_excel_to_rdf")

parser.add_argument('--conf', type=str, help='RDF Export Configuration Path', required=True)
parser.add_argument('--input', type=str, help='Input EXCEL full path', required=True)
parser.add_argument('--output', type=str, help='Output RDF/XML full path, if not provided default filename will be used ./excel_to_rdf_export_YYYY-MM-DDTHHMM.rdf')
parser.add_argument('--export_type', type=str, help='How the export is to be packaged',
                    choices=["xml_per_instance", "xml_per_instance_zip_per_all", "xml_per_instance_zip_per_xml"],
                    default="xml_per_instance")
parser.add_argument('--sheets', type=str, nargs='+', help='Names of Excel Sheets to be exported', required=True)

arg = parser.parse_args()

convert_excel_to_rdf(rdf_conf_path=arg.conf,
                     source_excel_path=arg.input,
                     types_to_convert=arg.sheets,
                     destination_rdf_path=arg.output,
                     export_type=arg.export_type,
                    )

# Example Use
#convert_excel_to_rdf.py --conf "../ENTSO-E_Object Registry vocabulary_2.1.0_2022-07-21_about_urn_uuid.json" --input "ObjectRegistry.xlsx" --sheets FullModel IdentifiedObject Name --output "ObjectRegistry.rdf"


# Command to create executable
#python -m PyInstaller convert_excel_to_rdf.py --add-data="../RDF_parser.py;excel_to_rdf.py" --hidden-import lxml --hidden-import pandas --hidden-import openpyxl --onefile

# Example cmd commands
#convert_excel_to_rdf --conf "../ENTSO-E_Object Registry vocabulary_2.1.0_2022-07-21_old.json" --input "ObjectRegistry.xlsx" --sheets FullModel IdentifiedObject Name --output "ObjectRegistry_old.rdf"
#convert_excel_to_rdf --conf "../ENTSO-E_Object Registry vocabulary_2.1.0_2022-07-21_about_urn_uuid.json" --input "ObjectRegistry.xlsx" --sheets FullModel IdentifiedObject Name --output "ObjectRegistry.rdf"


