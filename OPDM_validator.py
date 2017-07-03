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




def select_file():
    """ Single file selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file

    return [filename] #main function takes files in as list, thus single file must aslo be passed as list

def select_files():
    """ Multiple files selection popup
    return: list"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filenames = askopenfilenames() # show an "Open" dialog box and return the paths to selected files
##    print filenames #[DEBUG]
    return filenames


def select_folder():
    """Folder selection popup
    return: string"""

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    directory = askdirectory() # show an "Open" dialog box and return the path to the selected folder

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


print validate_CGMES("--report-only",select_files(),select_folder())


