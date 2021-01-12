import json
import os
from RDFS_tools import *

def get_description(meta_dict):
    description = meta_dict.get("comment", "")
    if len(str(description)) <= 3:
        description = ""
        print(f"WARNING - {meta_dict['label']} is missing description")

    return description


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

for concrete_class in concrete_classes_list(data):

    # Define class namespace
    class_namespace, class_name = get_namespace_and_name(concrete_class, default_namespace=cim_namespace)

    class_meta = data.get_object_data(concrete_class).to_dict()

    description = get_description(class_meta)



    # Add class definition
    interface = {
                                            "@context": "dtmi:dtdl:context;2",
                                            "@type": "Interface",
                                            "@id": f"dtmi:cim:{class_name};16",

                                            "displayName": class_name,
                                            "description": description[:511],

                                            "contents": []
                                            }

    # Add attributes

    for parameter, parameter_meta in parameter_tableview(data, concrete_class).iterrows():

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
                "name": parameter_name.replace(".", "_"),
                "displayName": parameter_name,
                #"writable": True,
                "description": description[:511],
            }


        # If association
        if association_used == 'Yes':

            parameter_def["@type"] = "Relationship"
            parameter_def["target"] = f"dtmi:cim:{parameter_dict['range'].replace('#', '')};16"

        else:
            data_type = parameter_dict.get("dataType", "nan")

            # If regular parameter
            if str(data_type) != "nan":

                parameter_def["@type"] = "Property"
                parameter_def["schema"] = "string"



                # data_type_namespace, data_type_name = data_type.split("#")
                #
                # data_type_meta = data.get_object_data(data_type).to_dict()
                #
                # if data_type_namespace == "":
                #     data_type_namespace = cim_namespace
                #
                # data_type_def = {
                #     "description": data_type_meta.get("comment", ""),
                #     "type": data_type_meta.get("stereotype", ""),
                #     "namespace": data_type_namespace
                # }
                #
                # parameter_def["type"] = data_type_name
                #conf_dict[profile_name][data_type_name] = data_type_def

            # If enumeration
            else:

                parameter_def["@type"] = "Property"
                parameter_def["schema"] = { "@type": "Enum",
                                            "valueSchema": "string",
                                            "enumValues": []
                }


                # Add allowed values
                values = data.query(f"VALUE == '{parameter_dict['range']}' and KEY == 'type'").ID.tolist()

                for value in values:

                    value_namespace, value_name = get_namespace_and_name(value, default_namespace=cim_namespace)

                    value_meta = data.get_object_data(value).to_dict()

                    description = get_description(value_meta)

                    value_def = {
                                    #"@id": f"dtmi:cim16:{value_name}",
                                    "name": value_name.replace(".", "_"),
                                    #"displayName": value_name,
                                    "enumValue": value_name,
                                    "description": description[:511],
                                }


                    parameter_def["schema"]["enumValues"].append(value_def)



        # Add parameter definition
        #conf_dict[profile_name][parameter_name] = parameter_def

        # Add content to Interface
        interface["contents"].append(parameter_def)

    # Add Interface to def
    #conf_dict.append(interface)

    # Export conf

    path_name = "{entsoeUML}_{date}_DTDL_V2".format(**metadata)

    if not os.path.exists(path_name):
        os.makedirs(path_name)

    file_name = f"{class_name}.json"
    # file_name = "{profileUML}_{date}.json".format(**metadata)

    with open(os.path.join(path_name, file_name), "w") as file_object:
        json.dump(interface, file_object, indent=4)


            # range = parameter_dict.get("range", None)
            # stereotype = parameter_dict.get("stereotype", None)
            #
            # if range is not pandas.np.nan and stereotype is not pandas.np.nan:
            #     conf_dict[profile_name][parameter_name] = {"attrib": {"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
            #                                                         "value_prefix": ""},
            #                                                         "namespace": parameter_namespace}
            #
            # else:
            #     conf_dict[profile_name][parameter_name] = {"namespace": parameter_namespace}

# Add FullModel definiton

#for profile_name in conf_dict:
#    conf_dict[profile_name].update(fullmodel_conf)

