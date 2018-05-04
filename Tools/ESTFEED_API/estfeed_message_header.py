from lxml import etree
from pprint import pprint


def create_conf_from_XSD(xsd_path):

    xsd_tree = etree.parse(open("estfeed-1.0.xsd"))

    target_namespace = xsd_tree.getroot().attrib['targetNamespace']
    global_elements = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}element")
    global_variables = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}complexType")

    global_elements_dictionary = {}
    global_variables_dictionary = {}
    variables_dictionary = {}


    for element in global_elements:

        ID = 0

        element_name = element.attrib['name']

        global_elements_dictionary[element_name] = {}
        global_elements_dictionary[element_name][str(ID)] = {'PARENT': '', 'DATA': {'element': "{{{0}}}{1}".format(target_namespace, element_name)}}

        for child_element in element.findall('.//{http://www.w3.org/2001/XMLSchema}element'):

            ID += 1

            child_name = child_element.attrib['name']
            global_elements_dictionary[element_name][str(ID)] = {'PARENT': str(0), 'DATA': {'element': child_name, 'text': '{{{}}}'.format(child_name)}}
            variables_dictionary[child_name] = child_element.attrib


    for variable in global_variables:

        ID = 0

        variable_name = variable.attrib['name']
        global_variables_dictionary[variable_name] = {}
        global_variables_dictionary[variable_name][str(ID)] = {'PARENT': '', 'DATA': {'element': variable_name}}

        for child_element in variable.findall('.//{http://www.w3.org/2001/XMLSchema}element'):

            ID += 1

            child_name = child_element.attrib['name']
            global_variables_dictionary[variable_name][str(ID)] = {'PARENT': str(0), 'DATA': {'element': child_name, 'text': '{{{}}}'.format(child_name)}}
            variables_dictionary[child_name] = child_element.attrib

    return global_elements_dictionary, global_variables_dictionary, variables_dictionary


def create_XML_from_conf(conf_dic):
    """Create XML file from dictionary conf input"""
    end_key       = len(conf_dic)-1
    current_key   = 0

    xml_elements_dic = {}

    while current_key <= end_key:

        element_name = conf_dic[str(current_key)]["DATA"]["element"]

        #print (element_name) #DEBUG

        #Create Element
        #CHECK if root element
        if (current_key == 0):
            element = etree.Element(element_name)

        else:
            parent_name  = xml_elements_dic[conf_dic[str(current_key)]["PARENT"]]

            #print (element_name, parent_name) #DEBUG

            element = etree.SubElement(parent_name, element_name)

            #Set Element attributes

        if "attributes" in conf_dic[str(current_key)]["DATA"]:

            for attrib_key in conf_dic[str(current_key)]["DATA"]["attributes"]:

                element.attrib[attrib_key] = conf_dic[str(current_key)]["DATA"]["attributes"][attrib_key]

        #Set Element text value

        element.text = conf_dic[str(current_key)]["DATA"].get("text", "")



        #Add current Element to element list

        xml_elements_dic[str(current_key)] = element

        #Move to next element
        current_key+=1

    xml_file = etree.tostring(xml_elements_dic["0"], pretty_print=True)
    return xml_file.decode('UTF-8')
    #return xml_elements_dic["0"]


def append_XML_object(root, message_template_dictionary, variables_dictionary):
    parser = etree.XMLParser(remove_blank_text=True)

    if root == "create_root":

        root = etree.XML(create_XML_from_conf(message_template_dictionary).format(**variables_dictionary), parser = parser)
        return root

    else:

        root.append(etree.XML(create_XML_from_conf(message_template_dictionary).format(**variables_dictionary), parser = parser))


def remove_root(text_xml):
    without_root = text_xml[text_xml.find('>')+1:text_xml.rfind('<')]
    return without_root


append_XML_object('create_root', global_elements_dictionary['error'], variables_dictionary)

