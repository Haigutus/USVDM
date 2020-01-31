#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     05.11.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from lxml import etree
import pandas

def get_all_children_with_text(parent):

    root_children = parent.getchildren()
    children_with_text = {}

    for child in root_children:
        if len(child.getchildren()) == 0:
            children_with_text[etree.QName(child.tag).localname] = child.text
    return children_with_text


# Define path
path = r"C:\Users\kristjan.vilgo\Downloads\V2_GRID_OPERATOR_CUSTOMER_report (6)"

xml = etree.parse(path).getroot()

periods = xml.findall("{*}ConnectionPoint/{*}Account/{*}TimeSeries/{*}Period")

periods_data = []
for period in periods:
    period_data = {}
    start, end = period.find("{*}timeInterval").text.split("/")
    period_data["timeInterval.start"] = start
    period_data["timeInterval.end"] = end
    period_data["direction.code"] = period.find("{*}Quantity/{*}direction.code").text
    period_data["amount"] = period.find("{*}Quantity/{*}amount").text

    # Timeseries metadata
    timeseries = period.getparent()
    period_data.update(get_all_children_with_text(timeseries))

    # Account metadata
    account = timeseries.getparent()
    period_data.update(get_all_children_with_text(account))

    # Add to data list
    periods_data.append(period_data)

# Convert to dataframe and export, print
data = pandas.DataFrame(periods_data)
data.to_csv(r"report.csv", encoding="UTF-8")
print(data)