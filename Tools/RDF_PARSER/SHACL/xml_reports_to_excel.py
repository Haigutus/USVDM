# MIT License
#
# Copyright (c) 2021 Kristjan Vilgo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Change history
#Date	    By	Description
#2021-05-14 LOO Change history added
#2021-05-14 LOO File paths updated with hardcoded locations
#2021-05-17 LOO Use of arguments generated from library.xml added
#2021-05-21 LOO Updated version from Kristjan used
#2021-05-26 KV  Updated parse_children_to_dict to pick up all children and all attributes, add per TSO name excel sheet, with validation results, added additional logging
#2021-06-02 LOO Four arguments are delivered, arg0 is the path to the script location.
#2021-06-22 KV  Check if there is sourcingTSO defined in metadata before doing aggregations per TSO; Check if any input data is provided and log invalid paths; improve xml parsing speed

import pandas, sys
from lxml import etree
from datetime import datetime
import os

def parse_children_to_dict(parent):
    """Parses all children to flat dictionary.
    If attribs are present then first is assigned as value, else the text"""

    result_dict = {}

    children = parent.getchildren()

    for child in children:
        child_namespace, child_name = child.tag.split("}")

        if len(child.getchildren()) > 0:
            children.extend(child.getchildren())

        if len(child.attrib) > 0:

            for attribute in child.attrib.items():
                attribute, attribute_value = attribute
                attribute_namespace, attribute_name = attribute.split("}")

            result_dict[f"{child_name}_{attribute_name}"] = attribute_value

        if child.text and child.text.strip():
            result_dict[child_name] = child.text.strip()

    return result_dict

# Get list of report files

file_reports = ""
model_reports = ""
output = ""

# If we got arguments use them, otherwise assume a folder structure relative current working directory
# TODO - put output to the first position and any number of input paths as a list
    
if len(sys.argv) == 4:
    file_reports    = sys.argv[1]
    model_reports   = sys.argv[2]
    output          = sys.argv[3]
else:
    base_path       = os.getcwd()
    file_reports    = os.path.join(base_path, "workspace/output/temp/preproReports")
    model_reports   = os.path.join(base_path, "workspace/output/temp/modelReport")
    output          = os.path.join(base_path, "workspace/output/report")

output_name = os.path.join(output, f'ExcelValidationReport_{datetime.now():%Y%m%d_%H%M%S}.xlsx')


# Create the list of input files

input_files = []

for input_path in [file_reports, model_reports]:

    if os.path.exists(input_path):
        input_files.extend(os.path.join(input_path, file_path) for file_path in os.listdir(input_path))

    else:
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [ERROR  ] Path not existing -> {input_path}")

if len(input_files) == 0:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [WARNING] No SHACL reports provided -> exiting script, no report will be generated")
    exit()


# Create dictionary to store all reports
validation_report_name = "Validations"
reports = {validation_report_name: []}


# Read in all reports
parser = etree.XMLParser(remove_comments=True, collect_ids=False, remove_blank_text=True)  # Improve parsing speed
for path in input_files:

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [INFO   ] Parsing report {path}")

    report_xml = etree.parse(path, parser=parser)

    # Extract all metadata
    models_meta_objects = report_xml.findall(".//{*}Report.MetaData/{*}FullModel")
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
severity = report_data.resultSeverity_resource.value_counts()

# Number of warning per Rule
rule_warnings = report_data.query("resultSeverity_resource == '#WARNING'").sourceShape_resource.value_counts()

# Number of errors per Rule
rule_errors = report_data.query("resultSeverity_resource == '#ERROR'").sourceShape_resource.value_counts()


# Export to excel
print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [INFO   ] All reports imported, starting to create Excel report")
with pandas.ExcelWriter(output_name, options={'strings_to_urls': False}) as writer:

    # Raw reports
    for report_name, report in reports.items():
        pandas.DataFrame(report).to_excel(writer, sheet_name=report_name)

    # Validation statistics
    severity.to_excel(writer, sheet_name='Overall Severity')
    rule_warnings.to_excel(writer, sheet_name='Warnings by Rule')
    rule_errors.to_excel(writer, sheet_name='Errors by Rule')

    # Additional statistics if sourcingTSO is present in metadata
    if "Model.sourcingTSO" in report_data.columns:

        # Number of errors per TSO
        report_data.query("resultSeverity_resource == '#WARNING'")["Model.sourcingTSO"].value_counts().to_excel(writer, sheet_name='Warnings by TSO')

        # Number of errors per TSO
        report_data.query("resultSeverity_resource == '#ERROR'")["Model.sourcingTSO"].value_counts().to_excel(writer, sheet_name='Errors by TSO')

        # Report per TSO if more than one TSO present
        TSOs = report_data["Model.sourcingTSO"].unique()
        if len(TSOs) > 2:
            for TSO in TSOs:
                report_data[report_data["Model.sourcingTSO"] == TSO].to_excel(writer, sheet_name=f"{validation_report_name}_{TSO}")

print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [INFO   ] Excel report created -> {output_name}")



