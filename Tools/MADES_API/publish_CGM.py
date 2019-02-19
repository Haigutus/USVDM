#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     06.08.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import sys
import copy


import OPDM_SOAP_client as API

sys.path.append(r'C:\GIT')
import SEND_REPORT_EMAIL

from lxml import etree

import zipfile
import tempfile
from io import BytesIO

import ftplib
import pandas

import datetime
import pytz
import aniso8601


pandas.set_option("display.max_rows", 12)
pandas.set_option("display.max_columns", 10)
pandas.set_option("display.width", 1500)
pandas.set_option('display.max_colwidth', -1)

server_ip   = ""
username    = ""
password    = ""

meta_separator = "_"

# USAGE

# 1. Set correct settings above
# 2. Import to another script and use function:

# import baltic_ftp
# <your script>
# baltic_ftp.upload_to_ftp(file_path, destination_path)



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




def timestamp_range(start_date, end_date, ISO_step):

    timestamp_list = []
    timestamp = start_date

    while timestamp <= end_date:

        timestamp_list.append(timestamp)
        timestamp += aniso8601.parse_duration(ISO_step, relative = True)

    return timestamp_list


def upload_to_ftp(file_path, destination_path):

    session = ftplib.FTP(server_ip, username, password)
    session.cwd(destination_path)

    with open(file_path,'rb') as file_object:
        session.storbinary('STOR {}'.format(os.path.basename(file_path)), file_object)

    session.quit()



def metadata_from_filename(file_name):

    print(file_name)
    file_metadata = {}
    file_name, file_metadata["file_type"] = file_name.split(".")


    if "_EQ_" in file_name or "_BD_" in file_name:

        file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)
        file_metadata["process_type"] = ""

    else:

        try:
            file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)

        except:
            print ("Non CGMES file {}".format(file_name))

    return file_metadata

def filename_from_metadata(file_metadata):

    if file_metadata["profile"] == "EQ" or file_metadata["profile"] == "BD":
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    else:
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    file_name = ".".join([file_name, file_metadata["file_type"]])

    return file_name


def get_data_and_metadata_from_xml(filepath_or_fileobject):

    #parsed_xml = etree.parse(r"C:\Users\kristjan.vilgo\Desktop\IGM_hour23\IGM_hour23\20180310T2330Z_2D_ELERING_TP_001.xml")
    parsed_xml = etree.parse(filepath_or_fileobject)

    header = parsed_xml.find("{*}FullModel")
    meta_elements = header.getchildren()

    meta_list = []
    for element in meta_elements:
         meta_list.append([element.tag, element.text, element.attrib])

    xml_metadata = pandas.DataFrame(meta_list, columns = ["tag", "text", "attrib"])

    return parsed_xml, xml_metadata


def get_file_from_ftp(file_path):

    file_object = BytesIO()
    session.retrbinary('RETR {}'.format(file_path), file_object.write)
    return file_object


def unzip_single_file(file_object):

    zip_file = zipfile.ZipFile(file_object)

    file_name = zip_file.namelist()[0]

    xml_file = zip_file.open(file_name)

    return xml_file


def etree_to_zip(etree_object, file_name):

    # Independant of passed name make sure that xml and zip get correct file format
    zip_name = file_name.replace(".xml", ".zip")
    xml_name = file_name.replace(".zip", ".xml")

    file_object = BytesIO()

    file_object.name = zip_name

    out_zipped_file = zipfile.ZipFile(file_object, 'w', zipfile.ZIP_DEFLATED)
    out_zipped_file.writestr(xml_name, etree.tostring(etree_object))
    #out_zipped_file.close()



    return file_object

def profile_query_result_to_dataframe(query_result):

    if query_result.get("sm:OperationFailure", False) != False:

        print("Query failure: ")

        query_status = response["sm:OperationFailure"]["sm:part"]["opde:Error"]['opde:technical-details']['opde:technical-detail']

        print(query_status)

        return

    if type(query_result['sm:QueryResult']['sm:part']) == str:

        print("No data")

        return

    query_result['sm:QueryResult']['sm:part'].pop(0)

    query_dataframe = pandas.DataFrame(query_result['sm:QueryResult']['sm:part'])

    return query_dataframe


### GET CGM files from FTP ###


delivery_date = get_day_start() + aniso8601.parse_duration("P1D")


base_bath = "/RSC/CGM/OUT/{}/".format(delivery_date.strftime("%Y%m%d"))

print(base_bath)

boundary_eq = "1d1c30d0-dc0a-4e30-8a68-2cc7570e3308"

test_reciver_list = ["list_of_nice_emails"]

prod_reciver_list = ["list_of_nice_emails"]

reciver_list = prod_reciver_list

##if __name__ == '__main__':
##    reciver_list = test_reciver_list

session = ftplib.FTP(server_ip, username, password)


TSOs = ['ELERING', 'LITGRID', 'AST'] #SSH_data["model_authority"].tolist()


try:
    session.cwd(base_bath)

except:
    message = "CGM process error - CGM is not available at {}".format(base_bath)
    print(message)
    SEND_REPORT_EMAIL.send_report_email("Error - D-1 CGM submission", "CGM submission report", message, reciver_list,[])
    sys.exit()



files_list = session.nlst()

if len(files_list)==0:
    message = "CGM process error - CGM is not available at {}".format(base_bath)
    print(message)
    SEND_REPORT_EMAIL.send_report_email("Error - D-1 CGM submission", "CGM submission report", message, reciver_list,[])
    sys.exit()


meta_list = []

for n, file_name in enumerate(files_list):

    print(file_name)

    if ".zip" in file_name:

        meta = metadata_from_filename(file_name)
        meta["file_path"] = os.path.join(base_bath, file_name)
        meta_list.append(meta)

    else:
        print("Un supported file {}".format(file_name))

cgm_profiles = pandas.DataFrame(meta_list)

cgm_profiles.replace("LV", "AST", inplace = True)  # Name error in CGM export


timestamps = cgm_profiles["date_time"].unique()


missing_SV =[]

for timestamp in timestamps:

    print(timestamp)

    ### GET IGM meta from OPDE ###


    #time_horizon = SSH_data["process_type"].tolist()[0]

    published_profiles = pandas.DataFrame()

    for TSO in TSOs:

        query_id, query_result = API.query_object(object_type = "IGM", metadata_dict = {'pmd:TSO': TSO, 'pmd:validFrom': timestamp})

        try:
            profile_list = query_result['sm:QueryResult']['sm:part'][1]['opdm:OPDMObject']["opde:Component"]
        except:
            print("No profiles returned")
            continue

        for profile in profile_list:
            published_profiles = published_profiles.append(pandas.DataFrame(profile['opdm:Profile']), ignore_index = True)


##    query_result_copy = copy.deepcopy(query_result['sm:QueryResult']['sm:part'])
##    for collection in query_result_copy:
##
##        if type(result) != str:
##           del collection['opdm:OPDMObject']["opde:Component"]
##           collection_data = pandas.DataFrame(collection['opdm:OPDMObject'])


    CGM_SSH_DATA = cgm_profiles[(cgm_profiles["date_time"]==timestamp) & (cgm_profiles["profile"]=="SSH") & cgm_profiles.model_authority.isin(TSOs)]
    CGM_SV_DATA  = cgm_profiles[(cgm_profiles["date_time"]==timestamp) & (cgm_profiles["profile"]=="SV")]

    if CGM_SV_DATA.empty:
        print("Missing merged SV for {}".format(timestamp))
        missing_SV.append(timestamp)
        continue

    IGM_SSH_DATA = published_profiles[(published_profiles["pmd:cgmesProfile"]=="SSH")]
    IGM_EQ_DATA  = published_profiles[(published_profiles["pmd:cgmesProfile"]=="EQ")]
    IGM_TP_DATA  = published_profiles[(published_profiles["pmd:cgmesProfile"]=="TP")]


    SV_references_list = []


##    try:
##        boundary_EQ_ID = query_result['sm:QueryResult']['sm:part'][1]['opdm:OPDMObject']['opde:Context']['opde:Active-Official-BDS']['opde:Component'][1]['opdm:Profile']['pmd:modelid']
##        SV_references_list.append(boundary_EQ_ID)
##
##    except:
##        print("No BD references returned")
##        continue



    SV_references_list.append(boundary_eq)  # Above code did not work so well, lets just add eq BD manually



    for _, CGM_SSH in CGM_SSH_DATA.iterrows():

        TSO = CGM_SSH["model_authority"]

        file_path = CGM_SSH["file_path"]
        file_meta = CGM_SSH.to_dict()
        zip_file  = get_file_from_ftp(file_path)
        xml_file  = unzip_single_file(zip_file)

        data, metadata = get_data_and_metadata_from_xml(xml_file)

        # Record ID for SV

        SV_references_list.append(data.find(".//{*}FullModel").attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about'].replace("urn:uuid:", ""))

        # Update SSH version number

        version = "{:03d}".format(int(pandas.to_numeric(IGM_SSH_DATA[(IGM_SSH_DATA["pmd:TSO"]==TSO)]["pmd:versionNumber"]).max() + 1))

        data.find(".//{*}Model.version").text = version
        file_meta["version"] = version

        # Update EQ reference

        EQ_dependancy = IGM_EQ_DATA[(IGM_EQ_DATA["pmd:TSO"]==TSO)]["pmd:modelid"].item()
        data.find(".//{*}Model.DependentOn").attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"] = 'urn:uuid:' + EQ_dependancy

        SSH_name = filename_from_metadata(file_meta)

        new_zip = etree_to_zip(data, SSH_name)

    ##    with open(SSH_name, 'wb') as f:
    ##        f.write(new_zip.getvalue())

        result = API.publication_request("CGMES", new_zip)

        print("Uploaded -> {}".format(new_zip.name))




    #Load SV data

    file_path = CGM_SV_DATA["file_path"].item()
    file_meta = CGM_SV_DATA.iloc[0].to_dict()
    zip_file  = get_file_from_ftp(file_path)
    xml_file  = unzip_single_file(zip_file)

    data, metadata = get_data_and_metadata_from_xml(xml_file)


    # Update SSH references to SV and TP

    SV_references_list.extend(IGM_TP_DATA["pmd:modelid"].tolist())
    reference_objects = data.findall(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.DependentOn")

    parent = reference_objects[0].getparent()

    for reference in reference_objects:
        parent.remove(reference)

    for SV_reference in SV_references_list:
        element = etree.Element("{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.DependentOn")
        element.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"] = 'urn:uuid:' + SV_reference
        parent.append(element)

    # Update SV model authority

    file_meta["model_authority"] = "CGMBA"
    data.find(".//{*}Model.modelingAuthoritySet").text =  r"http://www.baltic-rsc.eu/OperationalPlanning/CGMBA"


    SV_name = filename_from_metadata(file_meta)

    new_zip = etree_to_zip(data, SV_name)


    result = API.publication_request("CGMES", new_zip)

    print("Uploaded -> {}".format(new_zip.name))




SEND_REPORT_EMAIL.send_report_email("D-1 CGM submission", "CGM submission report", "CGM has been uploaded to OPDE and is avaiable on FTP at {}".format(base_bath), reciver_list,[])

##for TSO in TSOs:
##
##    metadata = {"pmd:TSO": TSO, "pmd:validFrom": timestamp, "pmd:cgmesProfile": "EQ"}# "pmd:timeHorizon": time_horizon}
##
##    query_id, query_result = API.query_profile(metadata)
##
##    #query_result_dataframe = query_result_to_dataframe(query_result)
##
##    published_profiles = published_profiles.append(query_result_to_dataframe(query_result), ignore_index = True)
##
##print(published_profiles[["pmd:TSO","pmd:modelid", "pmd:cgmesProfile", "pmd:version"]])
#pandas.DataFrame(query_result[1]['sm:QueryResult']['sm:part'])[["pmd:TSO","pmd:modelid", "pmd:cgmesProfile"]]



#published_profiles = published_profiles.append(query_result_to_dataframe(query_result), ignore_index = True)




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

##for file_name in files_list:
##
##    file_object = get_file_from_ftp(os.path.join(base_bath, file_name))
##
##    xml_file = unzip_single_file(file_object)
##
##    xml_metadata = get_metadata_from_xml(xml_file)
##
##    meta = metadata_from_filename(xml_file.name)
##    meta["cim_fullmodel"] = xml_metadata
##    meta["file_path"] = os.path.join(base_bath, file_name)
##
##    meta_list.append(meta)


##source_bath = "//elering.sise/teenused/NMM/data/ACG/Generated Cases"
##destination_bath = "//elering.sise/teenused/NMM/data/ACG/Generated Cases Archive"
##
##list_of_source_files = API.list_of_files(source_bath, ".zip")
##
##for file_path in list_of_source_files:
##
##    print file_path
##
##    file_name = os.path.basename(file_path)
##
##    if "_BD_" in file_name:
##        print "Warning - boundary will not be uploaded"
##        continue
##
##
##    new_path  = os.path.join(destination_bath, file_name)
##    file_metadata   = metadata_from_filename(file_name)
##
##    if file_metadata["process_type"] == "ID":
##
##        new_process_type = "23"
##        file_path  = change_process_type(file_path, new_process_type)
##        file_name = os.path.basename(file_path)
##        new_path  = os.path.join(destination_bath, file_name)
##
##
##    while os.path.exists(new_path) == True:
##
##        print "File allready exists: {}".format(new_path)
##        print "rasing version"
##
##        file_path = raise_version_number(file_path)
##        file_name = os.path.basename(file_path)
##        new_path  = os.path.join(destination_bath, file_name)
##
##        print "File will be written with new version number {}".format(file_name)
##
##
##
##    os.rename(file_path, new_path)
##    response = API.publication_request("CGMES", new_path)


