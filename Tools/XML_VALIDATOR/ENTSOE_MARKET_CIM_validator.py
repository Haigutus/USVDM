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

from lxml import etree
import os

def validate_XML(XML_path,XSD_path):

    #Load XSD
    print "Loading XSD at {}".format(XSD_path)
    try:
        xmlschema_doc = etree.parse(XSD_path)
        print "XSD loaded"
    except etree.XMLSyntaxError as error:
        print error
        print "Loading XSD failed"

    print "Loading XML at {}".format(XML_path)
    try:
        xmlschema = etree.XMLSchema(xmlschema_doc)
        print xmlschema.error_log
        #Validate XML

        xml_doc = etree.parse(XML_path)
        xmlschema.validate(xml_doc)
        print "Loaded and validation done"
    except etree.XMLSyntaxError as error:
        print error
        print error.args
        print "Loading XML failed"

    #Print errors
    print xmlschema.error_log

    pass

def check_path(list_of_paths): #Print paths an check if exsist

    for path in list_of_paths:
        print (path)
        check=os.path.exists(path)
        message="Path exsits: {}".format(check)
        print message

#XSD = "C:\CIMDesk\CIMdesk\profile\entsoe\entsoe_2_4\equipment.xsd"
XSD = r"""C:\Users\kristjan.vilgo\Downloads\Day-Ahead-Public-master\Day-Ahead-Public-master\urn-ediel-org-neg-spotmarket-biddocument-2-0.xsd"""
#XML = r"""C:\USVDM\XSD\CIM_2017-05-30\20170503T2230Z_ELERING_EQ_001.xml"""
#XML = r"""H:\PROJECTS\BHT 2\CGMA\CGMA_templates\20170103_CGMA_PPD_10X1001A1001A55Y_10YLT-1001A0008Q_LITGRID.xml"""
XML = r"""C:\Users\kristjan.vilgo\Downloads\Day-Ahead-Public-master\Day-Ahead-Public-master\Elering_for_11XNORDPOOLSPOT2_120720182200.xml"""
check_path([XML,XSD])

validate_XML(XML,XSD)