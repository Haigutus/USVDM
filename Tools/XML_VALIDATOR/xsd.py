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


def validate_XML_string(XML_string, XSD_string = False):

    # Create list to keep all processing messages
    status_list = []

    # Load XML
    XML_status, xml_doc = load_XML(XML_string)
    status_list.append(XML_status)

    # In case of XML error, return
    if xml_doc == "":
        return status_list

    # If no XSD is provided, look fo one and loade it
    if XSD_string == False:
        # Find XML root namespace and corresponding XSD

        root_namespace = xml_doc.nsmap.get(None)
        xsd_dataframe = find_all_xsds()
        XSD_path_list = xsd_dataframe.query("target_namespace == '{}'".format(root_namespace))["file_path"].tolist()


        if len(XSD_path_list) == 1:
            status_list.append({"type":"XSD_used", "status":os.path.basename(XSD_path_list[0]), "errors":""})

            # Load XSD
            XSD_status, xml_schema = load_XSD_file(XSD_path_list[0])

        else:
            status_list.append({"type":"XSD_used", "status":"ERROR - No XSD provided", "errors":["XML has no or wrong reference to XSD in root 'target_namespace' attribute"]})
            return status_list

    # Just load XSD if one was provided
    else:
        #Load XSD
        status_list.append({"type":"XSD_used", "status":"Using provided XSD", "errors":""})
        XSD_status, xml_schema = load_XSD_string(XSD_string)

    status_list.append(XSD_status)

    # In case of XSD error return
    if xml_schema == "":
        return status_list


    # Create dict to keep all valdaiton data
    status_dict = {"type":"Validation"}

    # Validate XML
    try:
        xml_schema.validate(xml_doc)

    except Exception as error:
        print("Validation failed")
        status_dict["status"] = "ERROR - Validation failed"
        status_dict["errors"] = error

        status_list.append(status_dict)

        return status_list

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

    for error in xml_schema.error_log:

        error_dict = {}
        for error_parameter in error_parametres_list:

            error_dict[error_parameter] = getattr(error, error_parameter, "")

        error_list.append(error_dict)


    status_dict["errors"] = error_list
    status_dict["status"] = "{} errors found in XML".format(len(error_list))
    status_list.append(status_dict)

    return status_list


# TEST - this will only run if this file is executed on its own, will not run when this module is imported
if __name__ == "__main__":


    XML = r"""example.xml"""


    check_path([XML]) # DEBUG

    XML_string = open(XML,"r").read()
    status_list = validate_XML_string(XML_string)

    for line in status_list: print(line)