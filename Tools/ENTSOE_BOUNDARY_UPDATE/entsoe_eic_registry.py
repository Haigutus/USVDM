import requests
import pandas
from lxml import etree


def get_allocated_eic():

    allocated_eic_url = "https://www.entsoe.eu/fileadmin/user_upload/edi/library/eic/allocated-eic-codes.xml"
    allocated_eic = requests.get(allocated_eic_url)

    xml_tree = etree.fromstring(allocated_eic.content)

    eic_data_list = []

    for EIC in xml_tree.iter("{*}EICCode_MarketDocument"):
        eic_dict = {}

        for field in EIC.getchildren():
            eic_dict[field.tag.split("}")[1]] = field.text

        eic_data_list.append(eic_dict)

    return pandas.DataFrame(eic_data_list)
