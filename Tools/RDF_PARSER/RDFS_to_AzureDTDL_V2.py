import json
import os
from Tools.RDF_PARSER.RDFS_tools import *
#from RDFS_tools import *


def get_description(meta_dict):
    description = meta_dict.get("comment", "")
    if len(str(description)) <= 3:
        description = ""
        print(f"WARNING - {meta_dict['label']} is missing description")

    return description


data_types_map = {
 '#String': "string",
 '#Simple_Float': "float",
 '#Float': "float",
 '#Boolean': "boolean",
 '#Reactance': "float",
 '#Resistance': "float",
 '#Voltage': "float",
 '#Integer': "integer",
 '#ActivePower': "float",
 '#ReactivePower': "float",
 '#CurrentFlow': "float",
 '#AngleDegrees': "float",
 '#PerCent': "float",
 '#Conductance': "float",
 '#Susceptance': "float",
 '#PU': "float",
 '#Date': "date",
 '#Length': "float",
 '#DateTime': "dateTime",
 '#ApparentPower': "float",
 '#Seconds': "float",
 '#Inductance': "float",
 '#Money': "float",
 '#MonthDay': "integer",
 '#VoltagePerReactivePower': "float",
 '#Capacitance': "float",
 '#ActivePowerPerFrequency': "float",
 '#ResistancePerLength': "float",
 '#RotationSpeed': "float",
 '#AngleRadians': "float",
 '#InductancePerLength': "float",
 '#ActivePowerPerCurrentFlow': "float",
 '#CapacitancePerLength': "float",
 '#Decimal': "float",
 '#Frequency': "float",
 '#Temperature': "float"}


#path = r"rdfs\CGMES_2_4_15_09May2019_RDFS\EquipmentProfileCoreOperationShortCircuitRDFSAugmented-v2_4_15-09May2019.rdf"
#path = r"rdfs\RDFS_UML_FDIS06_27Jan2020.zip"
path = r"rdfs\CGMES_2_4_15_09May2019_RDFS\UNIQUE_RDFSAugmented-v2_4_15-09May2019.zip"

# https://github.com/Azure/opendigitaltwins-dtdl/blob/master/DTDL/v2/dtdlv2.md

data = load_all_to_dataframe([path])

# Dictionary to keep all configurations
conf_dict = []

# Get current profile metadata
metadata = get_profile_metadata(data).to_dict()

# Add concrete classes

cim_namespace = metadata["namespaceUML"]
rdf_namespace = metadata["namespaceRDF"]

#classes_defined_externally = profile_data.query("KEY == 'stereotype' and VALUE == 'Description'").ID.to_list()

interfaces_list = concrete_classes_list(data)

for interface_uri in interfaces_list:

    # Define class namespace
    class_namespace, class_name = get_namespace_and_name(interface_uri, default_namespace=cim_namespace)

    class_meta = data.get_object_data(interface_uri).to_dict()

    description = get_description(class_meta)



    # Add class definition
    interface = {
                "@context": "dtmi:dtdl:context;2",
                "@type": "Interface",
                "@id": f"dtmi:cim:{class_name};16",
                "displayName": class_name,
                "description": description[:511],
                #"comment": "public"/"private"  # TODO - define if class is private or public (concrete)
                #"contents": []
                }

    # Add attributes

    parameters_table, extends = parameters_tableview(data, interface_uri)


    if len(extends) > 0:
        interface["extends"] = []

        for parent_class in extends:

            if parent_class not in interfaces_list:
                interfaces_list.append(parent_class)

            namespace, name = get_namespace_and_name(parent_class, default_namespace=cim_namespace)

            interface["extends"].append(f"dtmi:cim:{name};16")

    if parameters_table is not None:
        interface["contents"] = []

        for parameter, parameter_meta in parameters_table.iterrows():  # TODO - replace with itertuples

            parameter_dict = parameter_meta.to_dict()

            association_used = parameter_dict.get("AssociationUsed", "NaN")

            # If it is association but not used, we don't export it
            if association_used == 'No':
                continue

            # If it is used association or regular parameter, then we need the name and namespace
            parameter_namespace, parameter_name = get_namespace_and_name(parameter, default_namespace=cim_namespace)

            description = get_description(parameter_dict)

            parameter_def = {
                    #"@id": f"dtmi:cim16:{parameter_name}",
                    #"name": parameter_name.replace(".", "_"),

                    "@type": "Property",
                    "name": parameter_meta["label"],
                    "displayName": parameter_name,
                    #"writable": True,
                    "description": description[:511],
                }


            # If association
            if association_used == 'Yes':

                parameter_def["@type"] = "Relationship"

                target_namespace, target_name = get_namespace_and_name(parameter_dict['range'], rdf_namespace)

                parameter_def["target"] = f"dtmi:cim:{target_name};16"  # TODO - namespace and name

            else:
                data_type = parameter_dict.get("dataType", "nan")

                # If regular parameter
                if str(data_type) != "nan":

                    parameter_def["schema"] = data_types_map[data_type]

                # If enumeration
                else:

                    parameter_def["schema"] = {
                                                "@type": "Enum",
                                                "valueSchema": "string",
                                                "enumValues": []
                                               }

                    # Add allowed values for enumeration
                    values = data.query(f"VALUE == '{parameter_dict['range']}' and KEY == 'type'").ID.tolist()

                    for value in values:

                        value_namespace, value_name = get_namespace_and_name(value, default_namespace=cim_namespace)

                        value_meta = data.get_object_data(value).to_dict()

                        description = get_description(value_meta)

                        value_def = {
                                        #"@id": f"dtmi:cim16:{value_name}",
                                        #"name": value_name.replace(".", "_"),
                                        "name": value_meta["label"],
                                        #"displayName": value_name,
                                        "enumValue": value_name,
                                        "description": description[:511],
                                    }

                        parameter_def["schema"]["enumValues"].append(value_def)

                    # Limit enumerations to 100 (Azure DT limitation)
                    if len(parameter_def["schema"]["enumValues"]) > 100:
                        parameter_def["schema"]["enumValues"] = parameter_def["schema"]["enumValues"][:100]
                        print(f"WARNING - Enumerations capped to 100 for {parameter_name}")

            # Add content to Interface
            interface["contents"].append(parameter_def)

    # Export conf
    path_name = "{entsoeUML}_{date}_DTDL_V2".format(**metadata)

    if not os.path.exists(path_name):
        os.makedirs(path_name)

    file_name = f"{class_name}.json"
    # file_name = "{profileUML}_{date}.json".format(**metadata)

    with open(os.path.join(path_name, file_name), "w") as file_object:
        json.dump(interface, file_object, indent=4)
