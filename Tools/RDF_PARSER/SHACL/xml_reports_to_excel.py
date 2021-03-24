import pandas
from lxml import etree
from datetime import datetime
import os

def parse_children_to_dict(parent):
    """Parses all parent direct children to dictionary.
    If attrib is present then that is assigned as value, else the text"""

    result_dict = {}
    for child in parent.getchildren():
        child_name = child.tag.split("}")[1]

        if len(child.attrib) > 0:
            result_dict[child_name] = child.attrib.values()[0]
        else:
            result_dict[child_name] = child.text

    return result_dict

# Get list of report files
current_directory = os.getcwd()
#xml_report_dir = r"temp\preproReports"
#input_files = os.listdir(os.path.join(current_directory, xml_report_dir))

# Sample how to give single path
input_files = [r"ReportExample.xml"]

# Create dictionary to store all reports
validation_report_name = "Validations"
reports = {validation_report_name: []}


# Read in all reports
for path in input_files:

    report_xml = etree.parse(os.path.join(current_directory, path))

    # Extract all metadata
    models_meta_objects = report_xml.findall(".//{*}FullModel")
    models_meta = {}
    for model in models_meta_objects:

        model_id = model.attrib.values()[0]
        model_meta = parse_children_to_dict(model)
        model_meta["identification"] = model_id
        models_meta[model_id] = model_meta

    # Get all validation results
    validation_results_objects = report_xml.findall(".//{*}ValidationResult")

    for result in validation_results_objects:
        result_data = parse_children_to_dict(result)
        meta_id = result.getparent().getparent().find("{*}ValidationReport.Model").attrib.values()[0]
        result_data.update(models_meta[meta_id])
        reports[validation_report_name].append(result_data)

    # Get statistics Report Objects
    statistics_report_objects = report_xml.findall(".//{*}ReportObject")

    for statistics_report in statistics_report_objects:

        report_name = statistics_report.find("../../{*}IdentifiedReport.name").text

        report_values = statistics_report.findall("{*}ReportObject.ReportValue/{*}ReportValue")

        report_values_dict = {}
        for value in report_values:
            report_values_dict[value[0].text] = value[3].text

        if not reports.get(report_name):
            reports[report_name] = []

        reports[report_name].append(report_values_dict)


# Create one big table
report_data = pandas.DataFrame(reports[validation_report_name])

# Number of severity
severity = report_data.resultSeverity.value_counts()

# Number of warning per Rule
rule_warnings = report_data.query("resultSeverity == '#WARNING'").sourceShape.value_counts()

# Number of errors per Rule
rule_errors = report_data.query("resultSeverity == '#ERROR'").sourceShape.value_counts()

# Number of errors per TSO
tso_warnings = report_data.query("resultSeverity == '#WARNING'")["Model.sourcingTSO"].value_counts()

# Number of errors per TSO
tso_errors = report_data.query("resultSeverity == '#ERROR'")["Model.sourcingTSO"].value_counts()

# Export to excel
file_name = f'Report_{datetime.now():%Y%m%d_%H%M%S}.xlsx'
with pandas.ExcelWriter(file_name) as writer:

    # Raw reports
    for report_name, report in reports.items():
        pandas.DataFrame(report).to_excel(writer, sheet_name=report_name)

    # Validation statistics
    severity.to_excel(writer, sheet_name='Overall Severity')
    rule_warnings.to_excel(writer, sheet_name='Warnings by Rule')
    rule_errors.to_excel(writer, sheet_name='Errors by Rule')
    tso_warnings.to_excel(writer, sheet_name='Warnings by TSO')
    tso_errors.to_excel(writer, sheet_name='Errors by TSO')


print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [INFO   ] Excel report created -> {file_name}")



