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



def unzip_all_files(file_object):

    list_of_all_files = []

    zip_file = zipfile.ZipFile(file_object)

    for file_name in zip_file.namelist():

        new_file_object = BytesIO(zip_file.open(file_name))
        new_file_object.name = file_name

        list_of_all_files.append(new_file_object)

    return  list_of_all_files

def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):



        if filename.endswith(file_extension):
            #logging.info("Processing file:"+filename)
            matches.append(path + "//" + filename)
        else:
            print("Not a {} file: {}".format(file_extension, filename))
            #logging.warning("Not a {} file: {}".format(file_extension,file_text[0]))

    print(matches)
    return matches


source_bath = r"\\elering.sise\teenused\NMM\data\IOP"

list_of_source_files = list_of_files(source_bath, ".zip")

zip_list = unzip_all_files(list_of_source_files[0])


#result = API.publication_request("CGMES", new_zip)

#print("Uploaded -> {}".format(new_zip.name))



