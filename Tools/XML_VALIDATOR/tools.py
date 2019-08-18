import os
from lxml import etree
import pandas


def check_path(list_of_paths):  # Print paths and check if they exist

    for path in list_of_paths:
        check = os.path.exists(path)
        print("{} > path: {}".format(path, check))


def xml_path_to_str(xml_path_or_fileobject):
    """"path to xml file -> pretty xml as string"""

    xml_str = etree.tostring(etree.parse(xml_path_or_fileobject).getroot(), pretty_print = True).decode()
    return xml_str


def list_of_files(root_path,file_extension, go_deep = False):

    path_list = [root_path]

    matches = []


    for path in path_list:

        if os.path.isdir(path) == True:
            print("{} is not a path".format(path))

            for filename in os.listdir(path):

                full_path = os.path.join(path, filename)

                if filename.endswith(file_extension):
                    matches.append(full_path)

                else:
                    print ("Not a {} file: {}".format(file_extension, filename))

                    if go_deep == True:
                        print("Adding path to futher processing -> {}".format(full_path))
                        path_list.append(full_path)


    return matches


def find_all_xsds():

    file_list = list_of_files("XSD",".xsd", go_deep=True)

    xsd_list = []

    for file_path in file_list:


        single_xsd_meta = {}

        tree_object = etree.parse(file_path)

        single_xsd_meta["target_namespace"] = tree_object.getroot().attrib.get("targetNamespace", "")
        single_xsd_meta["file_path"]        = os.path.abspath(file_path)
        single_xsd_meta["file_name"]        = os.path.basename(file_path)

        xsd_list.append(single_xsd_meta)

    xsd_dataframe = pandas.DataFrame(xsd_list)

    return xsd_dataframe


def load_XML(XML_string):

    status_dict = {"type":"XML"}

    # Load XML
    print("Loading XML xml string")
    try:
        parser = etree.XMLParser(remove_comments=True, encoding='utf-8')
        xml_doc = etree.fromstring(XML_string.encode(), parser = parser)

        print("OK - XML loaded")
        status_dict["status"] = "OK - loaded"
        status_dict["errors"] = ""

    except Exception as error:

        print("ERROR - Loading XML failed")
        print(error)
        print(error.args)

        status_dict["status"] = "ERROR - Loading failed"
        status_dict["errors"] = error.args
        xml_doc = ""

    return status_dict, xml_doc



def load_XSD_file(XSD_file):

    status_dict = {"type":"XSD"}

    # Load XSD
    print("Loading XSD from")
    try:
        xml_schema_doc = etree.parse(XSD_file)
        xml_schema = etree.XMLSchema(xml_schema_doc)


        print("OK - XSD loaded")
        print(xml_schema.error_log)

        status_dict["status"] = "OK - loaded"
        status_dict["errors"] = xml_schema.error_log

    except Exception as error:
        print(error)
        print("ERROR - Loading XSD failed")

        status_dict["status"] = "ERROR - Loading failed"
        status_dict["errors"] = [error]
        xml_schema = ""

    return status_dict, xml_schema


def load_XSD_string(XSD_string):

    status_dict = {"type":"XSD"}

    # Load XSD
    print("Loading XSD")
    try:
        parser = etree.XMLParser(remove_comments=True, encoding='utf-8')
        xml_schema_doc = etree.fromstring(XSD_string.encode(), parser = parser)
        xml_schema = etree.XMLSchema(xml_schema_doc)


        print("OK - XSD loaded")
        print(xml_schema.error_log)

        status_dict["status"] = "OK - loaded"
        status_dict["errors"] = xml_schema.error_log

    except Exception as error:
        print(error)
        print("ERROR - Loading XSD failed")

        status_dict["status"] = "ERROR - Loading failed"
        status_dict["errors"] = error
        xml_schema = ""

    return status_dict, xml_schema

