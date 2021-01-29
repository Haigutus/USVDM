from azure.digitaltwins.core import DigitalTwinsClient
from azure.identity import DefaultAzureCredential
import pandas
import Tools.RDF_PARSER.RDF_parser
from aniso8601 import parse_date, parse_datetime
import datetime
import concurrent

data_types_map = {
 '#String': str,
 '#Simple_Float': float,
 '#Float': float,
 '#Boolean': bool,
 '#Reactance': float,
 '#Resistance': float,
 '#Voltage': float,
 '#Integer': int,
 '#ActivePower': float,
 '#ReactivePower': float,
 '#CurrentFlow': float,
 '#AngleDegrees': float,
 '#PerCent': float,
 '#Conductance': float,
 '#Susceptance': float,
 '#PU': float,
 '#Date': parse_date,
 '#Length': float,
 '#DateTime': parse_datetime,
 '#ApparentPower': float,
 '#Seconds': float,
 '#Inductance': float,
 '#Money': float,
 '#MonthDay': int,
 '#VoltagePerReactivePower': float,
 '#Capacitance': float,
 '#ActivePowerPerFrequency': float,
 '#ResistancePerLength': float,
 '#RotationSpeed': float,
 '#AngleRadians': float,
 '#InductancePerLength': float,
 '#ActivePowerPerCurrentFlow': float,
 '#CapacitancePerLength': float,
 '#Decimal': float,
 '#Frequency': float,
 '#Temperature': float}




rdfs = pandas.read_RDF([r"rdfs\CGMES_2_4_15_09May2019_RDFS\UNIQUE_RDFSAugmented-v2_4_15-09May2019.zip"])

# Get all relations
all_data_links = rdfs.query("KEY == 'AssociationUsed' and VALUE == 'Yes'").ID.str[1:].rename("KEY")

# Get all data types
data_types = rdfs.query("KEY == 'dataType'")

# Clean ID-s
data_types["ID"] = data_types["ID"].str.split("#", expand=True)[1].str.replace(".", "_")

# Create data types lookup table
data_types_dict = data_types.replace({"VALUE": data_types_map}).set_index("ID")["VALUE"].to_dict()




input_data = [r"test_models\TestConfigurations_packageCASv2.0\MiniGrid\NodeBreaker\CGMES_v2.4.15_MiniGridTestConfiguration_BaseCase_Complete_v3.zip"]

data = pandas.read_RDF(input_data)

# DefaultAzureCredential supports different authentication mechanisms and determines the appropriate credential type based of the environment it is executing in.
# It attempts to use multiple credential types in an order until it finds a working credential.

# - AZURE_URL: The URL to the ADT in Azure
#url = os.getenv("AZURE_URL")

url = input("Please copy here your Azure DT URL")

# DefaultAzureCredential expects the following three environment variables:
# - AZURE_TENANT_ID: The tenant ID in Azure Active Directory
# - AZURE_CLIENT_ID: The application (client) ID registered in the AAD tenant
# - AZURE_CLIENT_SECRET: The client secret for the registered application
credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
service_client = DigitalTwinsClient(url, credential)

"https://docs.microsoft.com/en-us/python/api/overview/azure/digitaltwins-core-readme?view=azure-python"
# Examples
def print_all_models():

    listed_models = service_client.list_models()
    for model in listed_models:
        print(model)


def add_object(data_object):
    # Get object id
    data_id = data_object.ID.iloc[0]

    # Convert to dictionary
    data_dict = data_object.set_index("KEY")[["VALUE"]].to_dict()["VALUE"]

    # Extract and remove data/class type
    data_type = data_dict.pop("Type")

    # Convert data types
    for key, value in data_dict.items():
        data_dict[key] = data_types_dict.get(key, str)(value)

    # Add object/instance ID
    data_dict["$dtId"] = data_id

    # Create Azure TD format
    twin = {"$metadata": {"$model": f"dtmi:iec:cim:schema:{data_type};16"}}
    twin.update(data_dict)

    # Upload data
    return service_client.upsert_digital_twin(data_id, twin)


def add_relation(relation):
    twin_relation = {
        "$relationshipId": f"dtmi:iec:cim:schema:{relation.KEY.replace('.', ':')};16",
        "$sourceId": relation.ID_FROM,
        "$relationshipName": relation.KEY.replace('.', '_'),
        "$targetId": relation.ID_TO,
    }

    return service_client.upsert_relationship(twin_relation["$sourceId"], twin_relation["$relationshipId"], twin_relation)

# Trigger Azure authentication

listed_models = service_client.list_models()
print(listed_models.__next__())

input("Press Enter once Azure auth is done")


# Filter out full model and Instance ID
data = data.merge(data.query("KEY == 'Type' and VALUE != 'FullModel'").ID, on="ID")[["ID", "KEY", "VALUE"]]

# Get all relations
all_relations = data.references_all()

# Filter out all relations
data = data.merge(all_data_links, on="KEY", how="outer", indicator=True).query("_merge == 'left_only'")[["ID", "KEY", "VALUE"]]

# Replace . with _ for Azure
data.KEY = data.KEY.str.replace(".", "_")

# Convert numbers
#data.VALUE = pandas.to_numeric(data.VALUE, errors='ignore')

# Convert boolians
#data = data.replace({'VALUE': {'true': True, 'false': False}})

# Group all data by ID to objects
data_objects = data.groupby("ID")

# Create thread pool to not wait for Azure response
executor = concurrent.futures.ThreadPoolExecutor(200)

# Time process start
start_time = datetime.datetime.now()

# List to collect all thread results
submitted_relations = []

# Add objects
number_of_objects = len(data_objects)
for count, _data in enumerate(data_objects):

    data_id, data_object = _data

    submitted_relations.append(executor.submit(add_object, data_object))

    print(f"INFO - {count+1}/{number_of_objects} - Added {data_id}")


# Add relations
number_of_relations = len(all_relations)
for count, relation in enumerate(all_relations.itertuples()):

    #add_relation(relation)
    submitted_relations.append(executor.submit(add_relation, relation))

    print(f"INFO - {count+1}/{number_of_relations} - Submitted: {relation.KEY}")

_, start_time = Tools.RDF_PARSER.RDF_parser.print_duration(f"INFO - {number_of_objects} objects and {number_of_relations} relations sent to Azure TD, waiting for submission confirmations", start_time)

concurrent.futures.wait(submitted_relations)

_, start_time = Tools.RDF_PARSER.RDF_parser.print_duration(f"INFO - Submissions confirmed", start_time)



