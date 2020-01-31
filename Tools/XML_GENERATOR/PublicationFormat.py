#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     03.05.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from lxml.builder import ElementMaker
from lxml import etree
import pandas

from datetime import datetime
import aniso8601
import pytz


def create_message(meta_dict, dataframe, print_message = False):

    now = datetime.utcnow()
    E = ElementMaker()

    # Complex elements
    PublicationFormat = E("PublicationFormat")
    timeseries = E("timeseries")
    meta = E("meta")

    # Elements
    data_items = [u'start_time_utc', u'end_time_utc', u'value', u'unit'] # To ensure correct order

    # Create root element
    PublicationFormat.append(timeseries)

    # Create timeseries element (we use only single one per message, format allows more)
    timeseries.append(meta)

    # Add meta to timeseries
    for parameter in meta_dict:

        if meta_dict[parameter] == None:
            meta.append(E(str(parameter)))

        else:
            meta.append(E(str(parameter), meta_dict[parameter]))


    # Add data to timeseries
    for _,row in dataframe.iterrows():

        data = E("data")
        data.append(E("updated_time_utc", now.strftime("%Y-%m-%dT%H:%M:%SZ")))

        for item_name in data_items:

            data.append(E(str(item_name), str(row[item_name])))

        timeseries.append(data)

    if print_message == True:
        print etree.tostring(PublicationFormat, pretty_print=True, xml_declaration=True, encoding='UTF-8') # Debug

    return etree.tostring(PublicationFormat, pretty_print=True, xml_declaration=True, encoding='UTF-8')


# Test
if __name__ == '__main__':

    meta_dict = {"message_type":"A12",
                "receiver_role":"A04",
                "process_type":"A06",
                "domain":"10Y1001A1001A94A",
                "document_status":"A02",
                "business_type":"Z21",
                "in_area":"10YLV-1001A00074",
                "currency":"EUR/MWh",
                "direction":"A01",
                "object_aggregation":"A01",
                "resolution":"PT1H"}


    test_data_dict = {'end_time_utc':   {1L: '2019-05-03T15:00:00Z', 2L: '2019-05-04T15:00:00Z'},
                      'start_time_utc': {1L: '2019-05-02T15:00:00Z', 2L: '2019-05-03T15:00:00Z'},
                      'unit':           {1L: 'MWh', 2L: 'MWh'},
                      'value':          {1L: "10", 2L: "20"}}

    dataframe = pandas.DataFrame(test_data_dict)

    create_message(meta_dict, dataframe, print_message = True)

