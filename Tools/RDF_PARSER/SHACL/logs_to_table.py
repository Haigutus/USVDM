import pandas
import json
import glob
import datetime

path_to_log_files = r"C:\Users\kristjan.vilgo\Downloads\OPDM_VALIDATOR_LOGS"

input_files = glob.glob(f"{path_to_log_files}\*.json")

parsed_data_list = []

# Parse json files to tables
for log_file in input_files:
    parsed_data_list.append(pandas.json_normalize(json.load(open(log_file, "r"))))

# Merge results and save as excel
pandas.concat(parsed_data_list, ignore_index=True).to_excel(f"logs_in_table_{datetime.datetime.now():%Y-%m-%dT%H%M%S}.xlsx")