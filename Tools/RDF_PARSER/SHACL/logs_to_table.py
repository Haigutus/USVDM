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

import pandas
import json
import glob
import datetime
import aniso8601

path_to_log_files = r"C:\Users\kristjan.vilgo\Downloads\OPDM_VALIDATOR_LOGS"

input_files = glob.glob(f"{path_to_log_files}\*.json")

parsed_data_list = []

# Parse json files to tables
for log_file in input_files:
    parsed_data_list.append(pandas.json_normalize(json.load(open(log_file, "r"))))

# Merge results
data = pandas.concat(parsed_data_list, ignore_index=True)

# Get duration statistics
duration_statistics = data.dropna(subset=["source.proc-alive"]).copy()
duration_statistics["source.proc-alive"] = duration_statistics["source.proc-alive"].apply(aniso8601.parse_duration)
durations_pivot = pandas.pivot_table(duration_statistics, index=['source.source'], columns=['source.log-command'], aggfunc="sum", values=["source.proc-alive"])
print(durations_pivot)

# Define reports and names
file_name = f"logs_in_table_{datetime.datetime.now():%Y-%m-%dT%H%M%S}.xlsx"
reports = {"log_table": data,
           "duration_statistics": durations_pivot}

# Export reports to excel
with pandas.ExcelWriter(file_name, datetime_format='hh:mm:ss.000') as writer:

    # Raw reports
    for report_name, report in reports.items():
        pandas.DataFrame(report).to_excel(writer, sheet_name=report_name)

print(f"INFO - created file: {file_name}")

#data[['source.timestamp', 'source.log-message', 'source.source', 'source.log-command', 'source.proc-alive']]