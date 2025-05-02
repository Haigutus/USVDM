#from Tools.RDF_PARSER.RDF_parser import get_diff, load_all_to_dataframe
import sys
import argparse

sys.path.append("..")
from RDF_parser import print_triplet_diff, load_all_to_dataframe

parser = argparse.ArgumentParser(description="""Create diff in Unified format for XML RDF CIM files. Diff is per object (ID KEY VALUE) not per XML line in file. The input can be xml, zip(xml), zip(zip(xml))""",
                                 epilog="""Copyright (c) Kristjan Vilgo 2021; Licence: GPL 2.0""",
                                 prog="cim-diff")
parser.add_argument('original_file', type=str, help='Original file path')
parser.add_argument('changed_file', type=str, help='Changed file path')
parser.add_argument('-ex', '--exclude_objects', nargs='+', help='Names of rdf:Description rdf:type-s without namespace or prefix to be excluded from diff')

arg = parser.parse_args()

print_triplet_diff(load_all_to_dataframe([arg.original_file]), load_all_to_dataframe([arg.changed_file]), exclude_objects=arg.exclude_objects)

# Example Use
# python cim-diff.py K:\PROJEKT\ER_EJK_FSYSTEM\TSM_models\eq\20210512T2330Z_ELERING_EQ_001.zip K:\PROJEKT\ER_EJK_FSYSTEM\TSM_models\eq\20210516T2330Z_ELERING_EQ_001.zip

# Command to create executable
# pyinstaller cim-diff.py --add-data="../RDF_parser.py;." --hidden-import lxml --hidden-import pandas --onefile


