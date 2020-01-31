from lxml import etree
from collections import OrderedDict
import json
import pandas
from lxml.builder import ElementMaker




def ODprint(_OrderedDict):

    print json.dumps(_OrderedDict,indent=4)


pandas.set_option("display.max_rows", 20)
pandas.set_option("display.max_columns", 6)
pandas.set_option("display.width", 1000)


def create_conf_from_XSD(xsd_path):


    xsd_tree = etree.parse(open(xsd_path))

    target_namespace    = xsd_tree.getroot().attrib['targetNamespace']

    root_elements            = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}element")
    root_elements_dictionary = OrderedDict()

    complex_types            = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}complexType")
    complex_types_dictionary = OrderedDict()


    # Not used
    attributes               = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}attribute")
    simple_types             = xsd_tree.findall("{http://www.w3.org/2001/XMLSchema}simpleType")





    for element in root_elements:

        element_name = element.attrib['name']

        root_elements_dictionary[element_name] = {"namespace": target_namespace}

        # Attributes
        element_attributes = []

        for attribute in element.findall('.//{http://www.w3.org/2001/XMLSchema}attribute'):

            attribute_name = attribute.attrib['name']

            element_attributes.append(attribute_name)

        root_elements_dictionary[element_name]["attributes"] = element_attributes


    for element in complex_types:

        element_name = element.attrib['name']

        children = pandas.DataFrame()

        for child_element in element.findall('.//{http://www.w3.org/2001/XMLSchema}element'):

            child_name = child_element.attrib["name"]
            children = children.append(pandas.DataFrame([child_element.attrib.values()], columns = child_element.attrib.keys()))

        complex_types_dictionary[element_name] = children.reset_index(drop = True)



    return root_elements_dictionary, complex_types_dictionary


def recursively_empty(e):
   if e.text:
       return False
   return all((recursively_empty(c) for c in e.iterchildren()))









def recursively_empty(e):
   if e.text:
       return False
   return all((recursively_empty(c) for c in e.iterchildren()))



def create_message(xsd_path, root_name, header_meta_dict, data, debug = False):



    root_elements_dictionary, complex_types_dictionary = create_conf_from_XSD(xsd_path)


    # root

    namespace = root_elements_dictionary[root_name]["namespace"]

    E = ElementMaker(namespace=namespace, nsmap={None:namespace})
    root = E(root_name)

    # Complex elements

    parent_elements = [(root_name, root)]

    for parent in parent_elements:

        parent_name = parent[0]
        parent_element = parent[1]

        for _, row in complex_types_dictionary[parent_name].iterrows():

            element = E(row["name"])
            parent_element.append(element)

            children = complex_types_dictionary.get(row["name"],"")

            if len(children) >0:
                parent_elements.append((row["name"], element))





##    for key in header_meta_dict:
##        element = root.find(key)
##
##        if element is not None:
##            value = header_meta_dict[key]
##
##            if type(value) is str:
##                element.text = header_meta_dict[key]
##
##            if type(value) is dict:
##                element.text    = value["text"]
##                element.attrib.update(value["attributes"])
##
##        else:
##            print("WARNING - '{}' not found in  in XSD".format(key))
##
##
##    for _, row in data["dataframe"].iterrows():
##
##        insertion_point = root.find(data["insert_to"])
##        initial_parent = E(data["parent"])
##
##        for key in row.keys():
##
##            parent = initial_parent
##            elements = key.split("/")
##
##            for element_name in elements:
##                element = parent.find("./{*}" + element_name)
##
##                if element is None:
##                    element = E(element_name)
##
##
##                parent.append(element)
##                parent = element
##
##            element.text = str(row[key])
##            insertion_point.append(initial_parent)

    if debug == True:
        print "Full XML structure"
        print etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')

##    context = etree.iterwalk(root)
##    for action, elem in context:
##        parent = elem.getparent()
##        if recursively_empty(elem):
##            parent.remove(elem)
##
##    final_xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
##
##    if debug == True:
##        print "Final XML"
##        print final_xml
##
##        xmlschema_doc = etree.parse(xsd_path)
##        xmlschema = etree.XMLSchema(xmlschema_doc)
##
##        print " XML is valid -> {}".format(xmlschema.validate(root))
##        print xmlschema.error_log
##
##
##    return final_xml



# Test
if __name__ == '__main__':

    from uuid import uuid4
    #import pandas
    from datetime import datetime

    now = datetime.utcnow()

    test_data_dict = {'end_time_utc':   {1L: '2019-05-03T15:00Z', 2L: '2019-05-04T15:00Z'},
                      'start_time_utc': {1L: '2019-05-02T15:00Z', 2L: '2019-05-03T15:00Z'},
                      'Price/type':           {1L: 'Z10', 2L: 'Z11'},
                      'Price/amount':          {1L: "10", 2L: "20"}}

    dataframe = pandas.DataFrame(test_data_dict)

    dataframe["timeInterval"] = dataframe["start_time_utc"] + "/" + dataframe["end_time_utc"]


    header_meta_dict = {"./{*}identification":str(uuid4())[:35],
                        "./{*}version":"1",
                        "./{*}type":"94G",
                        "./{*}creationDateTime":now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "./{*}validityPeriod":"{}/{}".format(dataframe["start_time_utc"].iloc[0], dataframe["end_time_utc"].iloc[-1]),
                        "./{*}issuer_MarketParticipant.identification":{"text":"10X1001A1001A39W", "attributes":{"codingScheme":"305"}},
                        "./{*}issuer_MarketParticipant.marketRole.code":"ZSO",
                        "./{*}recipient_MarketParticipant.identification":{"text":"10X1001A1001A39W", "attributes":{"codingScheme":"305"}},
                        "./{*}recipient_MarketParticipant.marketRole.code":"ZSO",
                        "./{*}Account/{*}identification":{"text":"BalancingGas", "attributes":{"codingScheme":"ZSO"}},
                        "./{*}Account/{*}type": "ZOF",
                        "./{*}Account/{*}accountTso": {"text":"10X1001A1001A39W", "attributes":{"codingScheme":"305"}},
                        "./{*}Account/{*}TimeSeries/{*}type": "Z40",
                        "./{*}Account/{*}TimeSeries/{*}measureUnit.code": "KWH",
                        "./{*}Account/{*}TimeSeries/{*}currency.code": "EUR",
                        #"./{*}Account/{*}TimeSeries/{*}Period/{*}timeInterval": "{}/{}".format(dataframe["start_time_utc"].iloc[0], dataframe["end_time_utc"].iloc[-1]),
                        #"./{*}Account/{*}TimeSeries/{*}Period/{*}Price/{*}amount": "10",
                        #"./{*}Account/{*}TimeSeries/{*}Period/{*}Price/{*}type": "Z10" , # Z10 - Marginal buy price, Z11 - Marginal sell price
                        }


    data = {"insert_to": "./{*}Account/{*}TimeSeries",
            "parent" : "Period",
            "dataframe": dataframe[['timeInterval', 'Price/amount', 'Price/type']]}


    root_name = 'ReserveBid_MarketDocument'

    xsd_path = r"C:\USVDM\Tools\XML_VALIDATOR\XSD\CIM_2019-09-17\iec62325-451-7-reservebiddocument_v7_1.xsd"

    create_message(xsd_path, root_name, header_meta_dict, data, debug = True)