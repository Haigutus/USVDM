#-------------------------------------------------------------------------------
# Name:        OPDM CGMES validation tool wrapper
# Purpose:
#
# Author:      Kristjan Vilgo
# Contributors:
#
# Created:     01.07.2017
# Copyright:   (c) kristjan.vilgo 2017
# Licence:     Free to use, modify and distribute "as is", no warranty is provided. Author and contributors names must be kept.
#-------------------------------------------------------------------------------
import sys

sys.path.append("../")

from ToolBox import *

def validate_CGMES(parameters,CGMES_files,report_folder):


    for file in CGMES_files:
        print "Processing: " + file

        command=['java', '-jar', 'local-quality-service-2.5.0.878.jar', parameters, file, report_folder]
        output = command_line(command)

        if output == 0:

            print "Error " + file

        else:
            print "OK"


        #open_folder(str(report_folder)) #does not work, should open folder with quality files when done

file_extentsion = ".zip"
select_file_dialogue = "Choose .zip file(s), all child directories will be unzipped if present"
select_folder_dialogue = "Choose root folder for .xml report files"

lis_of_selceted_files = select_files(file_extentsion,select_file_dialogue)
report_directory = select_folder(select_folder_dialogue)

list_of_validation_files = []

for file in lis_of_selceted_files:
    if list_of_zip_in_zip(file) == []:
        list_of_validation_files.append(file)
    else:
        path=file[:-len(file_extentsion)]
        create_paths([path])
        unzip_file(file,path)
        list_of_validation_files.extend(list_of_files(path,".zip"))

print validate_CGMES("--report-only",list_of_validation_files,report_directory)


