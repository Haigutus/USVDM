#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     22.06.2017
# Copyright:   (c) kristjan.vilgo 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from tools import *

def validate_XML_string(XML_string, XSD_path = ""):


    # Load XML
    print("Loading XML xml string")
    try:
        parser = etree.XMLParser(remove_comments=True, encoding='utf-8')
        xml_doc = etree.fromstring(XML_string.encode(), parser = parser)
        print("XML loaded")

    except etree.XMLSyntaxError as error:

        print("Loading XML failed")
        print(error)
        print(error.args)

        return error.args


    if XSD_path == "":
        # Find XML root namespace and corresponding XSD

        root_namespace = xml_doc.nsmap.get(None)
        xsd_dataframe = find_all_xsds()
        XSD_path = xsd_dataframe.query("target_namespace == '{}'".format(root_namespace))["file_path"].item()

    # Load XSD
    print("Loading XSD from {}".format(XSD_path))
    try:
        xmlschema_doc = etree.parse(XSD_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        print("XSD loaded")
        print(xmlschema.error_log)

    except etree.XMLSyntaxError as error:
        print(error)
        print("Loading XSD failed")

        return error



    # Validate XML
    try:
        xmlschema.validate(xml_doc)

    except:
        print("Validation failed")
        return False

    #Print errors and return dataframe of errors

    error_list = []
    error_parametres_list =  ['column',
                              'domain',
                              'domain_name',
                              'filename',
                              'level',
                              'level_name',
                              'line',
                              'message',
                              'path',
                              'type',
                              'type_name']

    for error in xmlschema.error_log:

        print(error) # DEBUG
        error_dict = {}

        for error_parameter in error_parametres_list:

            error_dict[error_parameter] = getattr(error, error_parameter, "")

        error_list.append(error_dict)

    print(error_list)
    return error_list


# TEST - this will only run if this file is executed on its own, will not run when this module is imported
if __name__ == "__main__":



    XSD = r"""internal_EN16931.xsd"""
    XML = r"""converted.xml"""

    check_path([XML,XSD]) # DEBUG
    validation_error_list = validate_XML_file(XML,XSD)

    print(validation_error_list)