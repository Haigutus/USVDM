#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     20.07.2017
# Copyright:   (c) kristjan.vilgo 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from Tkinter import Tk
from Tkinter import *
import ttk
from tkFileDialog import askopenfilename
from tkFileDialog import askopenfilenames
from tkFileDialog import askdirectory
import subprocess
import sys
import zipfile
import os
from lxml import etree
import logging

def get_XML_namespace(element_tag):

    #print element_tag

    namespace = ""

    if element_tag[0] == "{":
        namespace, element = element_tag[1:].split("}")

    return namespace

def get_XML_element(element_tag):

    element = element_tag

    if element_tag[0] == "{":
        namespace, element = element_tag[1:].split("}")

    return element

def get_meta_from_string(meta_string, meta_separator):
    return meta_string.split(meta_separator)

def init_logging(log_name):
    logging.basicConfig(log_name + ".log",level=logging.DEBUG,format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

def check_path(list_of_paths): #Print paths an check if exsist

    for path in list_of_paths:
        print (path)
        check=os.path.exists(path)
        message="Path exsits: {}".format(check)
        print message
        #logging.info(path)
        #logging.info(message)
        return check


def loadXMLs (file_paths):

    XML_trees=[]

    check_path(file_paths)

    for file in file_paths:

        loaded_xml = etree.parse(file)

        XML_trees.append(loaded_xml)

    return XML_trees



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

    return

def xml_to_dic(XML_tree):

    """ Convert lxml XML tree object to dictionary and returns it"""

    items_dic={}


    #print XML_tree.docinfo.root_name

    doc_dic={}

    for atribute in dir(XML_tree.docinfo):
        if atribute[0] != "_" and atribute != "clear":
            doc_dic[atribute] = getattr(XML_tree.docinfo,atribute)

    #print doc_dic

    items_dic[-1] = {"DATA":{"element":"__DOC__" ,"atribute":doc_dic},"PARENT":""}


    #define message and root of XML

    root = XML_tree.getroot()

    element_list=[]
    #element_list.append([doc_dic,""])
    element_list.append([root,""])


    for n, (element, parent) in enumerate(element_list):

        if isinstance(element.tag, basestring):


            data={}
            data["namespace"] = get_XML_namespace(element.tag)
            data["element"]=get_XML_element(element.tag)
            data["atribute"]=element.attrib
            data["text"]=element.text

            item={}
            item["PARENT"] = parent
            item["DATA"] = data

            #print item

            items_dic[n]= item


            for child in element.getchildren():

                element_list.append([child,n])

        else:
            print("Unexpected element [not imported!]:")# {} - {}".format(element, element.text))

    return items_dic