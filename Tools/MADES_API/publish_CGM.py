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

import OPDM_SOAP_client as API
import os
from lxml import etree

import zipfile
import tempfile
from StringIO import StringIO

import ftplib
import os

import pandas

pandas.set_option("display.max_rows", 10)
pandas.set_option("display.max_columns", 10)
pandas.set_option("display.width", 1500)

server_ip   = '185.7.252.111'
username    = 'Elering_baltic-rsc.eu'
password    = '8CHmWzWZ'

meta_separator = "_"

# USAGE

# 1. Set correct settings above
# 2. Import to another script and use function:

# import baltic_ftp
# <your script>
# baltic_ftp.upload_to_ftp(file_path, destination_path)

def upload_to_ftp(file_path, destination_path):

    session = ftplib.FTP(server_ip, username, password)
    session.cwd(destination_path)

    with open(file_path,'rb') as file_object:
        session.storbinary('STOR {}'.format(os.path.basename(file_path)), file_object)

    session.quit()



def get_metadata_from_filename(file_name):

    file_metadata = {}
    file_name, file_metadata["file_type"] = file_name.split(".")

    if "_EQ_" in file_name or "_BD_" in file_name:

        file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)
        file_metadata["process_type"] = ""

    else:

        file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = file_name.split(meta_separator)

    return file_metadata

def set_filename_from_metadata(file_metadata):

    if file_metadata["profile"] == "EQ" or file_metadata["profile"] == "BD":
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    else:
        file_name = meta_separator.join([file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    file_name = ".".join([file_name, file_metadata["file_type"]])

    return file_name


def get_metadata_from_xml(filepath_or_fileobject):

    #parsed_xml = etree.parse(r"C:\Users\kristjan.vilgo\Desktop\IGM_hour23\IGM_hour23\20180310T2330Z_2D_ELERING_TP_001.xml")
    parsed_xml = etree.parse(filepath_or_fileobject)

    header = parsed_xml.find("{*}FullModel")
    meta_elements = header.getchildren()

    meta_list = []
    for element in meta_elements:
         meta_list.append([element.tag, element.text, element.attrib])

    metadata = pandas.DataFrame(meta_list, columns = ["tag", "text", "attrib"])

    return metadata


def get_file_from_ftp(file_path):

    file_object = StringIO()
    session.retrbinary('RETR {}'.format(file_path), file_object.write)
    return file_object


def unzip_single_file(file_object):

    zip_file = zipfile.ZipFile(file_object)

    file_name = zip_file.namelist()[0]

    xml_file = zip_file.open(file_name)

    return xml_file


session = ftplib.FTP(server_ip, username, password)

base_bath = "/RSC/CGM/OUT/20181122/"

session.cwd(base_bath)

files_list = session.nlst()

meta_list = []

for file_name in files_list:

    meta = get_metadata_from_filename(file_name)

    meta["file_path"] = os.path.join(base_bath, file_name)

    meta_list.append(meta)

data = pandas.DataFrame(meta_list)

timestamps = data["date_time"].unique()

timestamp = timestamps[0]

sorted = data[(data["date_time"]==timestamp)]

##for file_name in files_list:
##
##    file_object = get_file_from_ftp(os.path.join(base_bath, file_name))
##
##    xml_file = unzip_single_file(file_object)
##
##    xml_metadata = get_metadata_from_xml(xml_file)
##
##    meta = get_metadata_from_filename(xml_file.name)
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


