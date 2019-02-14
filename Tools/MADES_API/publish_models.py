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
import StringIO

meta_separator = "_"

API.client.debug = False

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


def raise_version_number(file_path):

    zip_file_name = os.path.basename(file_path)
    base_path = os.path.dirname(file_path)


    # ZIP filename version number update
    zip_file_meta = metadata_from_filename(zip_file_name)

    if zip_file_meta["profile"] == "BD":

        print "Warning - Do not update boundary file"
        new_zip_file_path = file_path

    else:
        zip_file_meta["version"] = "{:03d}".format(int(zip_file_meta["version"]) + 1) #Raise version by one

        new_zip_file_name = filename_from_metadata(zip_file_meta)
        new_zip_file_path = os.path.join(base_path, new_zip_file_name)


        # XML element version number update
        zipfile_object = zipfile.ZipFile(file_path)

        # XML filename version number update
        xml_file_name = zipfile_object.namelist()[0]
        xml_file_meta = metadata_from_filename(xml_file_name)
        xml_file_meta["version"] = zip_file_meta["version"]
        new_xml_file_name = filename_from_metadata(xml_file_meta)


        file_unzipped  = zipfile_object.open(xml_file_name, mode="r")

        loaded_profile = etree.parse(file_unzipped)
        loaded_profile.find(".//{http://iec.ch/TC57/61970-552/ModelDescription/1#}Model.version").text = xml_file_meta["version"]



        # Write new files

        out_zipped_file = zipfile.ZipFile(new_zip_file_path, 'w', zipfile.ZIP_DEFLATED)
        out_zipped_file.writestr(new_xml_file_name, etree.tostring(loaded_profile))
        out_zipped_file.close()


    #Finally
    return new_zip_file_path

def change_process_type(file_path, new_process_type):

    zip_file_name = os.path.basename(file_path)
    base_path = os.path.dirname(file_path)


    # ZIP filename version number update
    zip_file_meta = metadata_from_filename(zip_file_name)
    zip_file_meta["process_type"] = new_process_type

    new_zip_file_name = filename_from_metadata(zip_file_meta)
    new_zip_file_path = os.path.join(base_path, new_zip_file_name)


    # XML element version number update
    zipfile_object = zipfile.ZipFile(file_path)

    # XML filename version number update
    xml_file_name = zipfile_object.namelist()[0]
    print xml_file_name
    xml_file_meta = metadata_from_filename(xml_file_name)
    xml_file_meta["process_type"] = new_process_type
    new_xml_file_name = filename_from_metadata(xml_file_meta)


    file_unzipped  = zipfile_object.open(xml_file_name, mode="r")


    # Write new files

    out_zipped_file = zipfile.ZipFile(new_zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    out_zipped_file.writestr(new_xml_file_name, file_unzipped.read())
    out_zipped_file.close()


    #Finally
    return new_zip_file_path







#source_bath = "//elering.sise/teenused/NMM/data/ACG/Generated Cases"
source_bath = r"C:\IOPs\2019_YR"
destination_bath = "//elering.sise/teenused/NMM/data/ACG/Generated Cases Archive"

list_of_source_files = API.list_of_files(source_bath, ".zip")

for file_path in list_of_source_files:

    print file_path

    file_name = os.path.basename(file_path)

    if "_BD_" in file_name:
        print "Warning - boundary will not be uploaded"
        continue


    new_path  = os.path.join(destination_bath, file_name)
    file_metadata   = metadata_from_filename(file_name)

    if file_metadata["process_type"] == "ID":

        new_process_type = "23"
        file_path  = change_process_type(file_path, new_process_type)
        file_name = os.path.basename(file_path)
        new_path  = os.path.join(destination_bath, file_name)


    while os.path.exists(new_path) == True:

        print "File allready exists: {}".format(new_path)
        print "rasing version"

        file_path = raise_version_number(file_path)
        file_name = os.path.basename(file_path)
        new_path  = os.path.join(destination_bath, file_name)

        print "File will be written with new version number {}".format(file_name)



    os.rename(file_path, new_path)
    response = API.publication_request("CGMES", new_path)

    #with open(new_path,'rb') as file_object:
    #    session.storbinary('STOR 20181107T2230Z_ELERING_EQ_001.zip'.format(file_name), file_object)     # send the file


