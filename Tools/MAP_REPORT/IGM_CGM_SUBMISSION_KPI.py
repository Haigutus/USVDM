#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Kristjan.Vilgo
#
# Created:     08.11.2018
# Copyright:   (c) Kristjan.Vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas


import datetime
import pytz
import aniso8601

import sys
sys.path.append(r'C:\GIT\USVDM\Tools\MADES_API')


import OPDM_SOAP_client


#pandas.set_option('display.height', 1000)
pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.width', 1000)

#metadata_dict = dict(TSO = "AST", cgmesProfile = "SV", validFrom = "20181024T1030Z")

CET = pytz.timezone("Europe/Brussels")
now = datetime.datetime.now(CET)

def get_year_start(date_time = now):

    year_start = date_time.replace(month = 1, day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)

    return year_start


def get_month_start(date_time = now):

    month_start = date_time.replace(day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)

    return month_start


def get_week_start(date_time = now):

    weekday = date_time.weekday()

    day_start = get_day_start(date_time)

    week_start = day_start - datetime.timedelta(days = weekday)

    return week_start


def get_day_start(date_time = now):

    day_start =  date_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

    return day_start


def get_hour_start(date_time = now):

    hour_start =  date_time.replace(minute = 0, second = 0, microsecond = 0)

    return hour_start


report_configs = [#dict(time_horizon = "1D", reference_time = get_day_start(), delta_start_time = "P0DT30M", delta_end_time = "P1D")
                  #dict(time_horizon = "YR", reference_time = get_year_start(), delta_start_time = "P1Y", delta_end_time = "P2Y"),
                  #dict(report_name = "M+1 D-2 submission", time_horizon = "2D", reference_time = get_month_start(), delta_start_time = "P-1MT30M", delta_end_time = "P0DT30M"),
                  #dict(report_name = "M+1 D-1 submission", time_horizon = "1D", reference_time = get_month_start(), delta_start_time = "P-1MT30M", delta_end_time = "P0DT30M"),
                  dict(report_name = "D0 D-1 submission", time_horizon = "1D", reference_time = get_day_start(), delta_start_time = "P0DT30M", delta_end_time = "P1DT30M"),
                  #dict(report_name = "D+1 D-1 submission", time_horizon = "1D", reference_time = get_day_start(), delta_start_time = "P-1DT30M", delta_end_time = "P0DT30M"),
                  #dict(report_name = "W+1 D-1 submission", time_horizon = "1D", reference_time = get_week_start(), delta_start_time = "P-7DT30M", delta_end_time = "P0DT30M"),



                  ]


#report_dataframe = pandas.DataFrame(columns = ["YR","1D", "2D"])
report_dataframe = pandas.DataFrame()

logging_data = []
logging_columns = ["query_id", "sceanrio_time", "query",  "query_start", "query_end", "query_duration", "query_status"]

loging_dataframe = pandas.DataFrame()


for config in report_configs:

    metadata_dict = {'pmd:timeHorizon' : config["time_horizon"],
                     'pmd:cgmesProfile' : "SV"}


    period_start_time  = config["reference_time"] + aniso8601.parse_duration(config["delta_start_time"], relative = True)

    period_end_time    = config["reference_time"] + aniso8601.parse_duration(config["delta_end_time"], relative = True)


    print(period_start_time.isoformat(), period_end_time.isoformat())

    start_time = period_start_time

    while start_time <= period_end_time:

        metadata_dict['pmd:scenarioDate'] = start_time.isoformat()

        print(metadata_dict['pmd:scenarioDate'])

        response_start = datetime.datetime.now()
        query_id, response = OPDM_SOAP_client.query_profile(metadata_dict)
        response_end = datetime.datetime.now()
        response_duration = response_end - response_start

        print(response_duration.total_seconds())


        query_status = "OK"

        if response.get("sm:OperationFailure", False) != False:

                print("Query failure, continuing")
                #report_dataframe.to_csv("result.csv")

                query_status = response["sm:OperationFailure"]["sm:part"]["opde:Error"]['opde:technical-details']['opde:technical-detail']

                start_time = start_time + aniso8601.parse_duration("PT1H")


                logging_data.append([query_id,  start_time,  str(metadata_dict) ,  response_start,  response_end, response_duration.total_seconds(), query_status])

                #loging_dataframe = loging_dataframe.append(pandas.DataFrame([{"query_id" : "nan", "sceanrio_time" : start_time, "query":  str(metadata_dict) , "query_start" : response_start, "query_end" : response_end, "query_duration" : response_duration.total_seconds(), "query_status" : query_status}]))

                #print(response)

                continue

        if type(response['sm:QueryResult']['sm:part']) == str:

            print("No data for: " + start_time.isoformat())
            start_time = start_time + aniso8601.parse_duration("PT1H")
            continue

        #print(response)

        response['sm:QueryResult']['sm:part'].pop(0) # Have to remove first element before parsing results to dataframe, contains just query id

        print(len(response['sm:QueryResult']['sm:part']))



        result_dataframe = pandas.DataFrame(response['sm:QueryResult']['sm:part'])

        report_dataframe = report_dataframe.append(result_dataframe)

        logging_data.append([query_id,  start_time,  str(metadata_dict) ,  response_start,  response_end, response_duration.total_seconds(), query_status])

        #loging_dataframe = loging_dataframe.append(pandas.DataFrame([{"query_id" : query_id, "sceanrio_time" : start_time, "query":  str(metadata_dict),  "query_start" : response_start, "query_end" : response_end, "query_duration" : response_duration.total_seconds(), "query_status" : query_status}]))



        start_time = start_time + aniso8601.parse_duration("PT1H")



report_dataframe.set_index("pmd:fullModel_ID", inplace = True)
report_dataframe["pmd:scenarioDate"] = pandas.to_datetime(report_dataframe["pmd:scenarioDate"])

loging_dataframe = pandas.DataFrame(logging_data, columns = logging_columns)
loging_dataframe.set_index("query_id", inplace = True)

print(report_dataframe)

report_dataframe.to_csv("query_result_{period_start:%Y%m%d_%H%M}_{period_end:%Y%m%d_%H%M}_{query_time:%Y%m%d_%H%M%S}.csv".format(period_start = period_start_time, period_end = period_end_time, query_time = response_end))

loging_dataframe.to_csv("query_log_{query_time:%Y%m%d_%H%M%S}.csv".format(query_time = response_end))


print(period_start_time.isoformat(), period_end_time.isoformat())

print(report_dataframe["pmd:TSO"].value_counts())

print(pandas.pivot_table(report_dataframe,index=['pmd:scenarioDate'], columns = ["pmd:TSO"], aggfunc = "count", values = "pmd:version"))

