import pandas
from Tools.RDF_PARSER import RDF_parser
from stdnum.eu import eic

base_data_path = r"C:\Users\kristjan.vilgo\Elering AS\Upgrade of planning tools - Elering Base Model\Models\EMS_ENHANCED\Export_2024-02-29.zip"
data = pandas.read_RDF([base_data_path])
data["VALID_EIC"] = data.query("KEY == 'IdentifiedObject.energyIdentCodeEic'").VALUE.apply(eic.is_valid)
print(data.merge(data.query("VALID_EIC == False").ID))