import json
from Tools.RDF_PARSER.RDFS_tools import *


def get_owl_metadata(data):
    """Returns metadata about CIM profile defined in RDFS OWL Ontology"""

    return data.merge(data.query("KEY == 'type' and VALUE == 'http://www.w3.org/2002/07/owl#Ontology'").ID).set_index("KEY")["VALUE"]


#path = r"rdfs/DocumentHeaderProfile_v2_2_RDFSv2020_10May2023.rdf"
#path = r"rdfs/DocumentHeaderProfile_RDFSv2020_21Sep2022.rdf"
#path = r"rdfs/ObjectRegistryProfile_RDFSv2020_21Sep2022.rdf"
path =r"rdfs/RemedialActionProfile_v2_2_RDFSv2020_20Apr2023.rdf"


#add_header = False
add_header = True
#header_conf = "ENTSO-E_Document header vocabulary_2.1.0_2022-07-21_IEC61970-552_ED2.json"
header_conf = "ENTSO-E_Document header vocabulary_2.2.0_2023-05-10_IEC61970-552_ED2.json"

#serialisation = "IEC61970-552_ED1"
serialisation = "IEC61970-552_ED2"

serialisations = {
    "IEC61970-552_ED1": {
        "id_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID",
        "id_prefix": "_",
        "about_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",
        "about_prefix": "#_",
        "resource_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
        "resource_prefix": "#_",
        "enumeration_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
        "enumeration_prefix": ""
           },
    "IEC61970-552_ED2": {
        "id_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",
        "id_prefix": "urn:uuid:",
        "about_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",
        "about_prefix": "urn:uuid:",
        "resource_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
        "resource_prefix": "urn:uuid:",
        "enumeration_attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
        "enumeration_prefix": ""
           },
}

id_attribute = serialisations[serialisation]["id_attribute"]
id_prefix = serialisations[serialisation]["id_prefix"]

about_attribute = serialisations[serialisation]["about_attribute"]
about_prefix = serialisations[serialisation]["about_prefix"]

resource_attribute = serialisations[serialisation]["resource_attribute"]
resource_prefix = serialisations[serialisation]["resource_prefix"]

enumeration_attribute = serialisations[serialisation]["enumeration_attribute"]
enumeration_prefix = serialisations[serialisation]["enumeration_prefix"]


data = load_all_to_dataframe([path])

# Dictionary to keep all configurations
conf_dict = {}

# For each profile in loaded RDFS
profiles = data["INSTANCE_ID"].unique()

for profile in profiles:
    profile_data = data.query(f"INSTANCE_ID == '{profile}'")

    # Get current profile metadata
    metadata = get_owl_metadata(profile_data).to_dict()
    metadata["serialisation"] = serialisation
    profile_name = metadata["keyword"]

    # Get namspace map
    namespace_map = data.merge(data.query("KEY == 'Type' and VALUE == 'NamespaceMap'").ID).set_index("KEY")["VALUE"].to_dict()
    namespace_map.pop("Type", None)
    namespace_map.pop("xml_base", None)

    # Dictionary to keep current profile schema
    conf_dict[profile_name] = {}
    conf_dict[profile_name]["NamespaceMap"] = namespace_map

    # Add concrete classes

    cim_namespace = namespace_map["cim"]
    rdf_namespace = namespace_map["rdf"]

    classes_defined_externally = profile_data.query("KEY == 'stereotype' and VALUE == 'Description'").ID.to_list()

    for concrete_class in concrete_classes_list(profile_data):

        # Define class namespace
        class_namespace, class_name = concrete_class.split("#")

        class_meta = profile_data.get_object_data(concrete_class).to_dict()

        if class_namespace == "":
            class_namespace = cim_namespace
        else:
            class_namespace = class_namespace + "#"

        # Define class ID attribute
        class_ID_attribute = id_attribute
        class_ID_prefix = id_prefix

        if concrete_class in classes_defined_externally:
            class_ID_attribute = about_attribute
            class_ID_prefix = about_prefix

        # Add class definition
        conf_dict[profile_name][class_name] = {
                                                "attrib": {
                                                            "attribute": class_ID_attribute,
                                                            "value_prefix": class_ID_prefix
                                                         },
                                                "namespace": class_namespace,
                                                "description": class_meta.get("comment", ""),
                                                "parameters": []
                                                }

        # Add attributes

        for parameter, parameter_meta in parameters_tableview_all(profile_data, concrete_class).iterrows():

            parameter_dict = parameter_meta.to_dict()

            association_used = parameter_dict.get("AssociationUsed", "NaN")

            # If it is association but not used, we don't export it
            if association_used == 'No':
                continue

            # If it is used association or regular parameter, then we need the name and namespace
            parameter_namespace, parameter_name = parameter.split("#")

            if parameter_namespace == "":
                parameter_namespace = cim_namespace

            else:
                parameter_namespace = parameter_namespace + "#"

            parameter_def = {
                "description": parameter_dict.get("comment", ""),
                "multiplicity": parameter_dict["multiplicity"].split("#M:")[1],
                "namespace": parameter_namespace
            }

            parameter_def["xsd:minOccours"], parameter_def["xsd:maxOccours"] = parse_multiplicity(parameter_dict["multiplicity"])

            # If association
            if association_used == 'Yes':
                parameter_def["attrib"] = {
                                               "attribute": resource_attribute,
                                               "value_prefix": resource_prefix
                                          }

                parameter_def["type"] = "Association"
                parameter_def["range"] = parameter_dict["range"]

            else:
                data_type = parameter_dict.get("dataType", "nan")

                # If regular parameter
                if str(data_type) != "nan":

                    data_type_namespace, data_type_name = data_type.split("#")

                    data_type_meta = data.get_object_data(data_type).to_dict()

                    if data_type_namespace == "":
                        data_type_namespace = cim_namespace

                    data_type_def = {
                        "description": data_type_meta.get("comment", ""),
                        "type": data_type_meta.get("stereotype", ""),
                        "namespace": data_type_namespace
                    }

                    parameter_def["type"] = data_type_name
                    conf_dict[profile_name][data_type_name] = data_type_def

                # If enumeration
                else:
                    parameter_def["attrib"] = {
                                                  "attribute": enumeration_attribute,
                                                  "value_prefix": enumeration_prefix
                                              }
                    parameter_def["type"] = "Enumeration"
                    parameter_def["range"] = parameter_dict["range"].replace("#", "")
                    parameter_def["values"] = []

                    # Add allowed values
                    values = profile_data.query(f"VALUE == '{parameter_dict['range']}' and KEY == 'type'").ID.tolist()

                    for value in values:

                        value_namespace, value_name = value.split("#")
                        value_meta = data.get_object_data(value).to_dict()

                        if value_namespace == "":
                            value_namespace = cim_namespace

                        value_def = {
                            "description": value_meta.get("comment", ""),
                            "namespace": value_namespace
                        }

                        parameter_def["values"].append(value_name)
                        conf_dict[profile_name][value_name] = value_def





            # Add parameter definition
            conf_dict[profile_name][parameter_name] = parameter_def

            # Add to class
            conf_dict[profile_name][class_name]["parameters"].append(parameter_name)


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

if add_header:
    with open(header_conf, "r") as file_object:
        new_fullmodel_conf = json.load(file_object)["DH"]

    for profile_name in conf_dict:
        conf_dict[profile_name].update(new_fullmodel_conf)

# Export conf

file_name = "{publisher}_{title}_{versionInfo}_{modified}_{serialisation}.json".format(**metadata)
#file_name = "{entsoeUML}_{date}.json".format(**metadata)
#file_name = "{profileUML}_{date}.json".format(**metadata)

with open(file_name, "w") as file_object:
    json.dump(conf_dict, file_object, indent=4)
    print(f"Configuration Generated: {file_name}")