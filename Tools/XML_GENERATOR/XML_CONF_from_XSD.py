from lxml import etree
from pprint import pprint


def create_conf_from_XSD(xsd_path):

    xsd_tree = etree.parse(open(xsd_path))

    target_namespace    = xsd_tree.getroot().attrib['targetNamespace']

    elements            = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}element")
    attributes          = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}attribute")
    complex_variables   = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}complexType")
    simple_variables    = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}simpleType")


    variables_dictionary = {}
    atributes_dictionary = {}
    elements_dictionary = {}
    complex_variables_dictionary = {}
    simple_variables_dictionary = {}


    for element in elements:

        ID = 0

        element_name = element.attrib['name']

        elements_dictionary[element_name] = {}
        elements_dictionary[element_name][str(ID)] = {'PARENT': '', 'DATA': {'element': "{{{0}}}{1}".format(target_namespace, element_name)}}

        # Attributes
        element_attributes = {}

        for attribute in element.findall('.//{http://www.w3.org/2001/XMLSchema}attribute'):
            attribute_name = attribute.attrib['name']
            print(attribute_name)
            element_attributes[attribute_name] = '{{{}}}'.format(attribute_name)

            variables_dictionary[attribute_name] = element.attrib

        elements_dictionary[element_name][str(ID)]["attributes"] = element_attributes


        # Child elements
        for child_element in element.findall('.//{http://www.w3.org/2001/XMLSchema}element'):

            ID += 1

            child_name = child_element.attrib['name']
            elements_dictionary[element_name][str(ID)] = {'PARENT': str(0), 'DATA': {'element': child_name, 'text': '{{{}}}'.format(child_name)}}
            variables_dictionary[child_name] = child_element.attrib





    for variable in complex_variables:

        ID = 0

        # Main parent element
        variable_name = variable.attrib['name']
        complex_variables_dictionary[variable_name] = {}
        complex_variables_dictionary[variable_name][str(ID)] = {'PARENT': '', 'DATA': {'element': variable_name}}

        # Add attributes

        complex_element_attributes = {}

        for attribute in variable.findall('.//{http://www.w3.org/2001/XMLSchema}attribute'):
            attribute_name = attribute.attrib['name']
            complex_element_attributes[attribute_name] = '{{{}}}'.format(attribute_name)
            variables_dictionary[attribute_name] = attribute.attrib

        complex_variables_dictionary[variable_name][str(ID)]["attributes"] = complex_element_attributes

        # Add children elements
        for child_element in variable.findall('.//{http://www.w3.org/2001/XMLSchema}element'):

            ID += 1

            child_name = child_element.attrib['name']
            complex_variables_dictionary[variable_name][str(ID)] = {'PARENT': str(0), 'DATA': {'element': child_name, 'text': '{{{}}}'.format(child_name)}}
            variables_dictionary[child_name] = child_element.attrib


    for variable in simple_variables:

        variable_name = variable.attrib['name']

        enumeration = variable.findall('.//{http://www.w3.org/2001/XMLSchema}enumeration')

        enumeration_list = []
        for item in enumeration:
            enumeration_list.append(item.attrib)

        variables_dictionary[variable_name] = enumeration_list

    #pprint(elements_dictionary)


    return elements_dictionary, complex_variables_dictionary, variables_dictionary


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





##
##print(etree.tostring(error_message))
##
##file = open("test.xml", "w")
##file.write(etree.tostring(error_message, pretty_print="true").decode("UTF-8"), )
##file.close()
