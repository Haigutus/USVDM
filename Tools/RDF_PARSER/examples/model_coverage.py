### Simple script to see how much of standard is used by model(s)

import pandas
from Tools.RDF_PARSER import RDF_parser

#data = pandas.read_RDF([r"C:\Users\kristjan.vilgo\Downloads\CAS 3.0.0.zip"])
data = pandas.read_RDF([r"C:\Users\kristjan.vilgo\Downloads\RealGrid V9 (2).zip"])
schema_data = pandas.read_RDF([r"..\rdfs\RDFS_UML_FDIS06_27Jan2020.zip"])

classes = schema_data.query("KEY == 'domain'").VALUE.value_counts()
attributes = schema_data.query("KEY == 'domain'").ID.value_counts()

class_data = data.query("KEY == 'Type'").VALUE.value_counts()
attribute_data = data.query("KEY != 'Type' and KEY != 'label'").KEY.value_counts()

class_coverage = len(class_data) / len(classes)
attribute_coverage = len(attribute_data) / len(attributes)
overall = (len(class_data) + len(attribute_data)) / (len(classes) + len(attributes))

print(f"Overall coverage {overall:.2f}; class coverage {class_coverage:.2f}; attribute coverage {attribute_coverage:.2f}")

reports = {"Classes in Model": class_data,
           "Attributes in Model": attribute_data}

# Export reports to excel
with pandas.ExcelWriter("coverage_report.xlsx") as writer:

    # Raw reports
    for report_name, report in reports.items():
        pandas.DataFrame(report).to_excel(writer, sheet_name=report_name)