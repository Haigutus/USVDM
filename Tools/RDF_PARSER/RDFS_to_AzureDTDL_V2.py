import json
import os
from Tools.RDF_PARSER.RDFS_tools import *
#from RDFS_tools import *


def get_description(meta_dict):
    """Parse description"""

    max_lenght = 512
    description = meta_dict.get("comment", "")
    description_length = len(str(description))

    # If description is missing
    if description_length <= 3:
        description = ""
        print(f"WARNING - {meta_dict['label']} is missing description")

    # If description exceeds max length
    if description_length > max_lenght:
        description = description[:max_lenght]
        print(f"WARNING - {meta_dict['label']} description is truncated to {max_lenght} from {description_length}")

    return description


URI_map = {
    "http://iec.ch/TC57/2013/CIM-schema-cim16#": {"path": "iec:cim:schema",
                                                  "version": 16},
    "http://entsoe.eu/CIM/SchemaExtension/3/1#": {"path": "eu:cim:extension",
                                                  "version": 31}

}


def URI_to_DTMI(uri, default_namespace):
    """Convert URI to DTMI
    URI  -> https://www.w3.org/Addressing/URL/uri-spec.html
    DTMI -> https://github.com/Azure/digital-twin-model-identifier"""

    namespace, name = get_namespace_and_name(uri, default_namespace)

    clean_name      = name.replace(".", ":")
    #clean_namespace = namespace.split("//")[1].replace("/", "_").replace(".", ":").replace("-", "__").replace("#", "")
    clean_namespace = URI_map[f"{namespace}#"]

    return f"dtmi:{clean_namespace['path']}:{clean_name};{clean_namespace['version']}"




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

concrete_interfaces_list = concrete_classes_list(data)

interfaces_list = []
interfaces_list.extend(concrete_interfaces_list)

for interface_uri in interfaces_list:

    # Define class namespace
    class_namespace, class_name = get_namespace_and_name(interface_uri, default_namespace=cim_namespace)

    # Get class meta
    class_meta = data.get_object_data(interface_uri).to_dict()

    # Create class definition
    interface = {
                "@context": "dtmi:dtdl:context;2",
                "@type": "Interface",
                "@id": URI_to_DTMI(interface_uri, cim_namespace),
                "displayName": class_name,
                "description": get_description(class_meta),
                }

    # Check and mark if interface/class is public/concrete
    if interface_uri in concrete_interfaces_list:
        interface["comment"] = "concrete"

    # Get parameters and parents
    parameters_table, extends = parameters_tableview(data, interface_uri)

    # Add parent classes (extended) to processing (if present)
    if len(extends) > 0:
        interface["extends"] = []

        for parent_class in extends:

            if parent_class not in interfaces_list:
                interfaces_list.append(parent_class)

            interface["extends"].append(URI_to_DTMI(parent_class, cim_namespace))

    # Add attributes
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

            parameter_def = {
                    "@id": URI_to_DTMI(parameter, cim_namespace),
                    "@type": "Property",
                    "name": parameter_name.replace(".", "_"),
                    "displayName": parameter_name,
                    "description": get_description(parameter_dict),
                }

            # Get parameter min and max occurrences
            maxOccurs, minOccurs = parse_multiplicity(parameter_dict["multiplicity"])

            # If association
            if association_used == 'Yes':

                parameter_def["@type"] = "Relationship"
                parameter_def["target"] = URI_to_DTMI(parameter_dict['range'], cim_namespace)

                # Add max relations (min relations available, but not added as when defining objects not all relations, parameters might be available)
                if str(maxOccurs) != "unbounded":
                    parameter_def["maxMultiplicity"] = int(maxOccurs)

            else:
                data_type = parameter_dict.get("dataType", "nan")

                if maxOccurs == "unbounded" or int(maxOccurs) > 1:
                    print(f"WARNING - array input not implemented for {parameter_name}")
                    # TODO - Implement array in case multiple parameters of same type allowed (Needed for Header)

                # If regular parameter
                if str(data_type) != "nan":

                    parameter_def["schema"] = data_types_map[data_type]
                    # TODO - introduce units that Azure TD supports and can be mapped to CIM

                # If enumeration
                else:

                    # TODO - Azure enumerations do not work, switched all enumeration to string for now. Issue - https://github.com/Azure-Samples/digital-twins-explorer/issues/91

                    parameter_def["schema"] = "string"

                    # parameter_def["schema"] = {
                    #                             "@type": "Enum",
                    #                             "valueSchema": "string",
                    #                             "enumValues": []
                    #                            }
                    #
                    # # Add allowed values for enumeration
                    # values = data.query(f"VALUE == '{parameter_dict['range']}' and KEY == 'type'").ID.tolist()
                    #
                    # for value in values:
                    #
                    #     value_namespace, value_name = get_namespace_and_name(value, default_namespace=cim_namespace)
                    #
                    #     value_meta = data.get_object_data(value).to_dict()
                    #
                    #     value_def = {
                    #                     #"@id": URI_to_DTMI(value, cim_namespace),
                    #                     "name": value_name.replace(".", "_"),
                    #                     "displayName": value_name,
                    #                     "enumValue": f"{value_namespace}#{value_name}",
                    #                     "description": get_description(value_meta),
                    #                 }
                    #
                    #     parameter_def["schema"]["enumValues"].append(value_def)
                    #
                    # # Limit enumerations to 100 (Azure DT limitation)
                    # if len(parameter_def["schema"]["enumValues"]) > 100:
                    #     parameter_def["schema"]["enumValues"] = parameter_def["schema"]["enumValues"][:100]
                    #     print(f"WARNING - Enumerations capped to 100 for {parameter_name}")

            # Add content to Interface
            interface["contents"].append(parameter_def)

    # Export conf
    path_name = "{entsoeUML}_{date}_DTDL_V2".format(**metadata)

    if not os.path.exists(path_name):
        os.makedirs(path_name)

    file_name = f"{class_name}.json"

    with open(os.path.join(path_name, file_name), "w") as file_object:
        json.dump(interface, file_object, indent=4)
