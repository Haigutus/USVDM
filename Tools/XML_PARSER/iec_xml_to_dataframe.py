#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     01.10.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas
from lxml import etree
import aniso8601


def get_text(parent_element, path):
    """Returns xml text of first element found in 'parent_element' at defined path.
       Returns empty sting if no element was found."""

    element = parent_element.find(path)

    if element is not None:
        text = element.text

    else:
        text = ""

    return text



def parse_iec_xml(file_path):
    """Parses iec xml to Pandas DataFrame, meta on the same row wit valu and start/end time
    columns = ["position", "timestamp_start_utc", "timestamp_end_utc", "value", "business_type", "from_domain", "to_domain", "line"]"""

    tree    = etree.parse(file_path)
    periods = tree.findall('.//{*}Period')


    data_list = []


    for period in periods:

        business_type = get_text(period, '../{*}businessType')
        from_domain   = get_text(period, '../{*}in_Domain.mRID')
        to_domain     = get_text(period, '../{*}out_Domain.mRID')
        line          = get_text(period, '../{*}connectingLine_RegisteredResource.mRID')


        curve_type = get_text(period, '../{*}curveType')
        resolution = aniso8601.parse_duration(period.find('.//{*}resolution').text, relative=True)
        start_time = aniso8601.parse_datetime(period.find('.//{*}start').text)
        end_time   = aniso8601.parse_datetime(period.find('.//{*}end').text)

        points = period.findall('.//{*}Point')

        for n, point in enumerate(points):
            position = int(eval(point.find("{*}position").text))
            value = float(eval(point.find("{*}quantity").text))
            timestamp_start = (start_time + resolution * (position -1)).replace(tzinfo=None)


            if curve_type == "A03":
                # This curvetype expect values to be valid until next change or until the end of period
                if n+2 <= len(points):
                    next_position = int(eval(points[n+1].find("{*}position").text))
                    timestamp_end = (start_time + resolution * (next_position -1)).replace(tzinfo=None)
                else:

                    timestamp_end = end_time.replace(tzinfo=None)

            else:
                # Else the value is on only valid during specified resolution
                timestamp_end = timestamp_start + resolution


            data_list.append((position, timestamp_start, timestamp_end, value, business_type, from_domain, to_domain, line))

            #dataframe.ix[timestamp_start.replace(tzinfo=None), "DATA"] = value


    data_frame = pandas.DataFrame(data_list, columns = ["position", "timestamp_start_utc", "timestamp_end_utc", "value", "business_type", "from_domain", "to_domain", "line"])

    #print  data_frame #DEBUG
    return data_frame




# TEST

if __name__ == '__main__':

    # File selection GUI for standalone use

    from Tkinter import *
    import ttk
    from tkFileDialog import askopenfilename


    def select_file(file_type='.*',dialogue_title="Select file"):
        """ Single file selection popup
        return: list"""

        Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
        filename = askopenfilename(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

        print filename
        return [filename] #main function takes files in a list, thus single file must aslo be passed as list


    # Pandas settings for nice tables

    pandas.options.display.max_rows = 10
    pandas.options.display.max_columns = 10
    pandas.options.display.width = None


    # Process

    file_path = r"C:\Users\kristjan.vilgo\Downloads\2018-03-22_CGMA_EDI_package\XML\Output\ReportingInformationMarketDocument\20180322_D2_ARS_10V000000000011Q_10X----------QAS_10Y---------CGMA_RID_001.xml"
    #file_path = r"C:\Users\kristjan.vilgo\Downloads\42959390.xml"
    #file_path = r"C:\Users\kristjan.vilgo\Downloads\20190418_CGM_10V1001C--00012J_10V000000000011Q_A01_002.xml"

    #file_path  = select_file(file_type='*.xml')[0]
    data_frame = parse_iec_xml(file_path)

    #data_frame.to_csv("output.csv")
    data_frame.to_excel("row_output.xlsx")


    data_frame["from_to_line"] = data_frame["from_domain"] + "_" + data_frame["to_domain"] + "_" + data_frame["line"]

    pivoted = pandas.pivot_table(data_frame, values='value', index=['timestamp_start_utc', 'timestamp_end_utc'], columns=['from_to_line'])

    pivoted.to_excel("table_output.xlsx")

