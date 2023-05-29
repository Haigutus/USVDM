#-------------------------------------------------------------------------------
# Name:        Download QAS reports
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     27.11.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPL v2
#-------------------------------------------------------------------------------

from QAS_API import *

import os


# PROCESS START

query_id_mask = "py_QAS_API_001_{UUID}"
server = "https://test-opde.elering.sise"

# Neede only if basic auth is set up for UI
username = ""  #raw_input("UserName")
password = "" #raw_input("PassWord")

service = create_client(server, username, password, debug = False)




report_configs = [##dict(report_name = "M+1 D-2 submission", time_horizon = "2D", reference_time = get_month_start(), delta_start_time = "P-1MT30M", delta_end_time = "P0DT-30M"),
                  ##dict(report_name = "M+1 D-1 submission", time_horizon = "1D", reference_time = get_month_start(), delta_start_time = "P-1MT30M", delta_end_time = "P0DT-30M"),
                  dict(report_name = "D0 D-1 submission", time_horizon = "1D", reference_time = get_day_start(), delta_start_time = "P0DT30M", delta_end_time = "PT23H30M"),
                  #dict(report_name = "D-1 submission", time_horizon = "1D", reference_time = get_day_start(), delta_start_time = "P1DT30M", delta_end_time = "P2DT-30M"),
                  #dict(report_name = "D-2 submission", time_horizon = "2D", reference_time = get_day_start(), delta_start_time = "P2DT30M", delta_end_time = "P3DT-30M"),


                  ]



#TSOs = ["AST", "ELERING", "Litgrid"]
TSOs = tso_list

query_counter = 0
max_querys = 20 #Empty responses
querymessage_list = []
queryresponse_list = []
error_list = []
meta_list = []



# Make querys
for config in report_configs:



    period_start_time  = config["reference_time"] + aniso8601.parse_duration(config["delta_start_time"])
    period_end_time    = config["reference_time"] + aniso8601.parse_duration(config["delta_end_time"])

    report_path =  "QAS_REPORTS_{:%Y%m%dT%H%M}_{:%Y%m%dT%H%M}".format(period_start_time, period_end_time)

    if not os.path.exists(report_path):
        os.mkdir(report_path)


    print(period_start_time.isoformat(), period_end_time.isoformat())


    timestamp_list = timestamp_range(period_start_time, period_end_time, "P1D")

    print(timestamp_list)

    for start_time in timestamp_list:
        pass


        for TSO in TSOs:

            query_message = IGM_query_message(processType=config["time_horizon"], tso=TSO, scenarioDate="{:%Y-%m-%d}".format(start_time))#, scenarioTime="09:30:00")

            message_ID = service.send_message("SERVICE-QAS", "ENTSOE-QAS-Query", query_message)

            query_meta = {"message_id":message_ID, "Party":TSO}
            print(query_meta)

            querymessage_list.append(query_meta)

            ##status = service.check_message_status(message_ID)

            query_counter += 1

        for RSC in RSCname_list:
            for CGM in CGMType_list:

                query_message = CGM_query_message(processType=config["time_horizon"], RSCName=RSC.upper(), CGMType=CGM.upper(), scenarioDate="{:%Y-%m-%d}".format(start_time))

                message_ID = service.send_message("SERVICE-QAS", "ENTSOE-QAS-Query", query_message)

                query_meta = {"message_id":message_ID, "Party":RSC, "Area":CGM}
                print(query_meta)

                querymessage_list.append(query_meta)

                ##status = service.check_message_status(message_ID)

                query_counter += 1


### Recive responses
message = service.receive_message("ENTSOE-QAS-QueryResult", False)

while query_counter > 0 or message['remainingMessagesCount'] > 0:

    error   = False
    message = service.receive_message("ENTSOE-QAS-QueryResult")

    print("Remaining querys {}, number of messages in que {}".format(query_counter, message['remainingMessagesCount']))

    if message.receivedMessage:

        #print(message)

        try:

            error_message = parse_error_message(message)
            error = True

            error_dict = {}
            error_dict["error_message"]   = error_message
            error_dict["message_id"]      = message['receivedMessage']['messageID']
            error_dict["conversation_id"] = message['receivedMessage']['baCorrelationID']

            error_list.append(error_dict)

            print(error_dict)

            print("Removing from que")

            service.confirm_received_message(message['receivedMessage']['messageID'])


            query_counter -= 1

            continue


        except:
            pass


        if error == False:


            response_dict = {}
            response_dict["message_id"]      = message['receivedMessage']['messageID']

            queryresponse_list.append(response_dict)



            zip_file = parse_zip_attachment(message)
            zip_file.extractall(report_path)
            #print(zip_file.namelist())

            raw_files = [zip_file.read(name) for name in zip_file.namelist()]


            for xml_string in raw_files:

                report = parse_QAReport(xml_string)
                del report["violations"] #To reduce the amount of data sent to elastic

                opde_id       = report.get("opde_id","")
                model_type    = report.get("type","")

                alternative_id = "_".join([opde_id, model_type])
                #print(etree.tostring(etree.fromstring(xml_string), pretty_print = True).decode())
                meta_list.append(report)

            #print(pandas.DataFrame(meta_list))#.drop(columns=["violations", "ERRORS_INFO", "WARNINGS_INFO"]))

        #pandas.DataFrame(meta_list)#.drop(columns=["violations"]).to_csv("C:\Users\kristjan.vilgo\Downloads\example_data.csv")


            service.confirm_received_message(message['receivedMessage']['messageID'])
            query_counter -= 1

    else:

        max_querys -= 1

        if max_querys <= 0:
            break

        time.sleep(1)

reports = {"query":querymessage_list, "response":queryresponse_list, "error":error_list, "meta":meta_list}

for report in reports:
    pandas.DataFrame(reports[report]).to_csv(os.path.join(report_path, report + ".csv"))

