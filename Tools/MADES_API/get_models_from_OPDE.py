#-------------------------------------------------------------------------------
# Name:        Get Data from OPDE
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     20.11.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import ftplib
import os
import paramiko
import datetime, pytz, aniso8601

import zipfile

import pandas


import OPDM_SOAP_client


# OPDM server conf

username        = ""
server_adress   = ''
key_file_dir    = ""

# Baltic FTP conf

server_ip   = ''
username    = ''
password    = ''



# Date time stuff

now = datetime.datetime.now()


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


CET             = pytz.timezone("Europe/Brussels")
UTC             = pytz.timezone("UTC")
EET             = pytz.timezone("Europe/Tallinn")

# End of datetime stuff


def create_ssh_and_sftp_connection(username, server_adress, key_file_dir):

    # Read keyfile
    private_key = paramiko.RSAKey.from_private_key_file(key_file_dir)

    # Set up SSH and SFTP connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_adress, username=username, pkey=private_key)
    sftp = ssh.open_sftp()

    return ssh, sftp


def upload_to_ftp(file_path, destination_path):

    session = ftplib.FTP(server_ip, username, password)
    session.cwd(destination_path)

    with open(file_path,'rb') as file_object:
        session.storbinary('STOR {}'.format(os.path.basename(file_path)), file_object)

    session.quit()


# Lets query for all profiles and store their metadata to a dataframe

report_dataframe = pandas.DataFrame()

start_time = get_day_start(datetime.datetime.now(CET)).astimezone(UTC) + aniso8601.parse_duration("P1DT30M")
end_time = start_time + aniso8601.parse_duration("P1D")

print(start_time.isoformat(), end_time.isoformat())

metadata_dict = {"TSO": "AST", "timeHorizon": "1D"}

while start_time <= end_time:

    metadata_dict["scenarioDate"] = start_time.isoformat()

    print metadata_dict

    response_start = datetime.datetime.now()
    response      = OPDM_SOAP_client.query_profile(metadata_dict)
    response_end = datetime.datetime.now()
    response_duration = response_end - response_start

    print(response_duration.total_seconds())


    if response.get("sm:OperationFailure", False) != False:

            print("Query failure, saving current results and trying again")

            response      = OPDM_SOAP_client.query_profile(metadata_dict)


    if response['sm:QueryResult']['sm:part'] == "py_query":

        print("No data for: " + start_time.isoformat())
        start_time = start_time + aniso8601.parse_duration("PT1H")
        continue

    response['sm:QueryResult']['sm:part'].pop(0) # Have to remove first element of response as it does not contain profile metadata

    report_dataframe = report_dataframe.append(pandas.DataFrame(response['sm:QueryResult']['sm:part'])) # Rest of response can directly be added to dataframe

    start_time = start_time + aniso8601.parse_duration("PT1H")


# Now lets get all files and upload them

ssh, sftp = create_ssh_and_sftp_connection(username, server_adress, key_file_dir)

localpath = r"C:/IGM_DOWNLOAD"

if not os.path.exists(localpath):
            os.makedirs(localpath)


for row_id, row_data in report_dataframe.iterrows():

    file_id = row_data["pmd:modelid"]
    remotepath = OPDM_SOAP_client.get_content(file_id) # See on katki, siin tuleb tagasi xml, mitte dict, aga OPDM on maas ja ei saa dictionary tagastust valmis teha, kuna ei ole xml-i

    print remotepath

    file_name = os.path.basename(row_data["pmd:content-reference"]).split(".")[0]

    xml_path = os.path.join(localpath, file_name + ".xml")
    zip_path = os.path.join(localpath, file_name + ".zip")

    sftp.get(remotepath, xml_path)

    with zipfile.ZipFile(zip_path, 'w') as zip_container:
        zip_container.write(xml_path, arcname=os.path.basename(xml_path))

    destination_path = "AST/CGM/OUT"

    upload_to_ftp(zip_path, destination_path)



 # Profile Meta example

"""
<pmd:fileName>20181024T1030Z_EMS_EQ_000.XML</pmd:fileName>
<pmd:modelid>6bfa5c34-f4fb-45f3-a909-1ae94c08d4e3</pmd:modelid>
<pmd:versionNumber>000</pmd:versionNumber>
<pmd:content-reference>CGMES/1D/EMS/20181024/103000/EQ/20181024T1030Z_EMS_EQ_000.XML</pmd:content-reference>
<pmd:isFullModel>true</pmd:isFullModel>
<pmd:timeHorizon>1D</pmd:timeHorizon>
<pmd:modelPartReference>EMS</pmd:modelPartReference>
<pmd:contentType>CGMES</pmd:contentType>
<pmd:conversationId>18240149</pmd:conversationId>
<pmd:description>Created by Transmission Network Analyzer 2.3</pmd:description>
<pmd:creationDate>2018-10-24T12:58:23.000Z</pmd:creationDate>
<pmd:TSO>EMS</pmd:TSO>
<pmd:cgmesProfile>EQ</pmd:cgmesProfile>
<pmd:modelingAuthoritySet>https://ems.rs/OperationalPlanning</pmd:modelingAuthoritySet>
<pmd:version>0</pmd:version>
<pmd:scenarioDate>2018-10-24T10:30:00.000Z</pmd:scenarioDate>
<pmd:validFrom>20181024T1030Z</pmd:validFrom>
<pmd:modelProfile>http://entsoe.eu/CIM/EquipmentCore/3/1</pmd:modelProfile>
<pmd:fullModel_ID>6bfa5c34-f4fb-45f3-a909-1ae94c08d4e3</pmd:fullModel_ID>
"""

