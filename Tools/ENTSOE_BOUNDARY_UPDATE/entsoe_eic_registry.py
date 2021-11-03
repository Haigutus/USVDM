import requests
import pandas
from lxml import etree

pandas.set_option('display.max_columns', 20)
pandas.set_option('display.width', 1000)


def get_allocated_eic():

    allocated_eic_url = "https://www.entsoe.eu/fileadmin/user_upload/edi/library/eic/allocated-eic-codes.xml"
    allocated_eic = requests.get(allocated_eic_url)

    xml_tree = etree.fromstring(allocated_eic.content)

    eic_data_list = []

    EICs = xml_tree.iter("{*}EICCode_MarketDocument")

    for EIC in EICs:

        elements = [EIC]
        for element in elements:

            eic_dict = {}

            for field in element.getchildren():
                if len(field.getchildren()) == 0:
                    eic_dict[field.tag.split("}")[1]] = field.text
                else:
                    elements.append(field)

            eic_data_list.append(eic_dict)

    return pandas.DataFrame(eic_data_list)


def eic_table_to_triplet(data):
    return data.melt(id_vars="mRID", value_name="VALUE", var_name="KEY").rename(columns={"mRID": "ID"})

def get_allocated_eic_triplet():
    allocated_eic_url = "https://www.entsoe.eu/fileadmin/user_upload/edi/library/eic/allocated-eic-codes.xml"
    allocated_eic = requests.get(allocated_eic_url)

    xml_tree = etree.fromstring(allocated_eic.content)

    eic_data_list = []

    EICs = xml_tree.iter("{*}EICCode_MarketDocument")

    for EIC in EICs:
        ID = EIC[0].text

        elements = [{"element": EIC}]
        for element in elements:

            for field in element["element"].getchildren():

                parent_name = element.get("parent_name")
                element_name = element['element'].tag.split('}')[1]
                field_name = field.tag.split('}')[1]

                if not parent_name:
                    parent_name = element_name
                else:
                    parent_name = f"{parent_name}.{element_name}"

                name = f"{parent_name}.{field_name}"

                if len(field.getchildren()) == 0:
                    eic_data_list.append({"ID": ID, "KEY": name, "VALUE": field.text})
                else:
                    elements.append({"parent_name": parent_name, "element": field})

    return(pandas.DataFrame(eic_data_list))
