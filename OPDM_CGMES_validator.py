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

from Tkinter import Tk
from tkFileDialog import askopenfilename
from tkFileDialog import askopenfilenames
from tkFileDialog import askdirectory
import subprocess
import sys
import zipfile
import os



def select_file(file_type='.*',dialogue_title="Select file"):
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the path to the selected file

    return [filename] #main function takes files in a list, thus single file must aslo be passed as list

def select_files(file_type='.*' ,dialogue_title="Select file(s)"):
    """ Multiple files selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filenames = askopenfilenames(title=dialogue_title,filetypes=[('{} file'.format(file_type),'*{}'.format(file_type))]) # show an "Open" dialog box and return the paths to selected files
##    print filenames #[DEBUG]
    return filenames


def select_folder(dialogue_title="Select Folder"):
    """Folder selection popup
    return: string"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    directory = askdirectory(title=dialogue_title) # show an "Open" dialog box and return the path to the selected folder

    return directory


def command_line(cmd):
    """
    Handle the command line call
    keyword arguments:
    cmd: list
    return:  0 if error
    """
    try:

        cmd_process = subprocess.Popen(cmd)
##        print subprocess.list2cmdline(cmd) # To see the command that was passed  [DEBUG]
##

    except subprocess.CalledProcessError:
        print "Error"
        return 0

##if sys.platform == 'darwin':
##    def open_folder(path):
##        command_line(['open', '--', path])
##elif sys.platform == 'linux2':
##    def open_folder(path):
##        command_line(['xdg-open', '--', path])
##elif sys.platform == 'win32':
##    def open_folder(path):
##        command_line(['explorer', path])

def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):

        file_text=filename.split(".")

        if filename.endswith(file_extension):
            #logging.info("Processing file:"+filename)
            matches.append(path + "//" + file_text[0] + file_extension)
        else:
            print "Not a {} file: {}".format(file_extension,file_text[0])
            #logging.warning("Not a {} file: {}".format(file_extension,file_text[0]))

    print matches
    return matches

def unzip_file(file, to_directory):

    check_path([file, to_directory])

    original_zip=zipfile.ZipFile(file,"r")
    original_zip.extractall(to_directory)
    original_zip.close()

def check_path(list_of_paths): #Print paths an check if exsist

    for path in list_of_paths:
        print (path)
        check=os.path.exists(path)
        message="Path exsits: {}".format(check)
        print message
        #logging.info(path)
        #logging.info(message)



def create_paths(w_paths): #Check if path exsit, if not create one
    """input: list of paths to be created"""

    for path in w_paths:

        if not os.path.exists(path):
            os.makedirs(path)
            #logging.info("New path added: "+path)

def list_of_zip_in_zip(zip_file):

    """Tests if zip file contains folders. Input: .zip file path Return: list of folders"""
    file = zipfile.ZipFile(zip_file)

    list_of_zip = []

    for zipinfo in file.filelist:

        #print zipinfo.filename

        if zipinfo.filename.endswith('.zip'): ##Inside .zip folders all allways seperated with /

            list_of_zip.append(zipinfo.filename)

    #print list_of_folders

    return list_of_zip

def validate_CGMES(parameters,CGMES_files,report_folder):


    for file in CGMES_files:
        print "Processing: " + file

        command=['java', '-jar', 'validation-command.jar', parameters, file, report_folder]
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


