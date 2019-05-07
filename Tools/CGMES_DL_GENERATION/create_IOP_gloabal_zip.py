#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     05.09.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import datetime
from pytz import timezone
import os
import zipfile


meta_separator = "_"

def metadata_from_filename(file_name):

    file_metadata = {}
    file_name, file_metadata["file_type"] = file_name.split(".")

    if "_EQ_" in file_name or "_BD_" in file_name:

        file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)
        file_metadata["process_type"] = ""

    else:

        file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)

    return file_metadata

def filename_from_metadata(file_metadata):

    if file_metadata["profile"] == "EQ" or file_metadata["profile"] == "BD":
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    else:
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    file_name = ".".join([file_name, file_metadata["file_type"]])

    return file_name



source_bath = "//elering.sise/teenused/NMM/data/ACG/Generated Cases Archive"
destination_bath = "C:/IOPs"


IOP_date = "13.02.2019"





IOP_CET_day = timezone("Europe/Brussels").localize(datetime.datetime.strptime(IOP_date,"%d.%m.%Y"))

CET_first_model_timestamp   = IOP_CET_day + datetime.timedelta(minutes=30) # All models are for HH:30 timestamp
CET_last_model_timestamp    = IOP_CET_day + datetime.timedelta(days=1, minutes=-30)

UTC_first_model_timestamp   = CET_first_model_timestamp.astimezone(timezone('UTC'))
UTC_last_model_timestamp    = CET_last_model_timestamp.astimezone(timezone('UTC'))


# Create folder for IOP if not allready present

IOP_folder_name = "IOP{:%d%m%y}".format(IOP_CET_day)
destination_bath = os.path.join(destination_bath, IOP_folder_name)

if not os.path.exists(destination_bath):
    os.makedirs(destination_bath)


global_zip_name_template = "BA02_BD{busines_day:%d%m%Y}_{process_type}_Elering_001_NodeBreaker.zip"

file_metadata = {'date_time': '',
                 'file_type': 'zip',
                 'model_authority': 'ELERING',
                 'process_type': '',
                 'profile': '',
                 'version': '001'}


list_of_processtypes = ["2D", "1D"]
list_of_profiles     = ["EQ", "SSH", "TP", "SV"]


for process_type in list_of_processtypes:

    file_metadata["process_type"] = process_type

    zip_file_name = global_zip_name_template.format(busines_day=IOP_CET_day, process_type=process_type)
    zip_file_path = os.path.join(destination_bath, zip_file_name)

    out_zipped_file = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)

    print os.path.normpath(zip_file_path).replace("\\","/")



    model_timestamp = UTC_first_model_timestamp

    while model_timestamp <= UTC_last_model_timestamp:

        file_metadata["date_time"] = "{:%Y%m%dT%H%MZ}".format(model_timestamp)

        for profile in list_of_profiles:

            file_metadata["profile"] = profile

            if file_metadata["profile"] == "EQ" and file_metadata["process_type"] == "1D":
                file_metadata["version"]= "002"

            else:
                file_metadata["version"]= "001"

            file_name = filename_from_metadata(file_metadata)

            file_path = os.path.join(source_bath, file_name)

            file_exsists = os.path.exists(file_path)

            print file_path, file_exsists

            if file_exsists:

                out_zipped_file.write(file_path, file_name)

        model_timestamp = model_timestamp + datetime.timedelta(hours=1)


    out_zipped_file.close()





