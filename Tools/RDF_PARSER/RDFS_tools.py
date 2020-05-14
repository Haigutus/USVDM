from RDF_parser import load_all_to_dataframe

import pandas
import os

pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)
pandas.set_option('display.max_colwidth', -1)

#data.query("KEY == 'multiplicity'").VALUE

def list_of_files(root_path,file_extension, go_deep = False):

    path_list = [root_path]

    matches = []

    for path in path_list:

        if os.path.isdir(path) == True:
            print("{} is not a path".format(path))

            for filename in os.listdir(path):

                full_path = os.path.join(path, filename)

                if filename.endswith(file_extension):
                    matches.append(full_path)

                else:
                    print ("Not a {} file: {}".format(file_extension, filename))

                    if go_deep == True:
                        print("Adding path to futher processing -> {}".format(full_path))
                        path_list.append(full_path)





def get_all_class_parameters(data, class_name):

    all_class_parameters = pandas.DataFrame()
    class_name_list = [class_name]

    for class_name in class_name_list:

        # Get parameters and add to parameter dataframe
        class_parameters = data.query("VALUE == '{}' & KEY == 'domain'".format(class_name))
        all_class_parameters = all_class_parameters.append(class_parameters)
        #print all_class_parameters

        # Look if the class has a parent class, if yes add to further parsing
        cim_class = data.query("ID == '{}'".format(class_name))
        #print cim_class
        parent_class = cim_class.query("KEY == 'subClassOf'")["VALUE"]

        if parent_class.empty == False:
            class_name_list.append(parent_class.item())

    print("Inheritance sequence")
    print(" -> ".join(class_name_list))

    return all_class_parameters


def parameter_tableview(data, class_name):

    all_class_parameters = get_all_class_parameters(data, class_name)

    parameter_id_list = all_class_parameters["ID"].tolist()  # TODO use merge here insetad isin method - it is faster

    type_data = data[data.ID.isin(parameter_id_list)].drop_duplicates(["ID", "KEY"])  # There can't be duplicate ID and KEY pairs for pivot.
    data_view = type_data.pivot(index="ID", columns="KEY")["VALUE"]

    return data_view


def validation_view(data, class_name):


    data_view = parameter_tableview(data, class_name)

    validation_data = data_view.join(data_view['multiplicity'].
                                     str.split("#M:", expand=True)[1].
                                     str.split(r".", expand=True)[[0, 2]].
                                     rename({0:"minOccurs", 2:"maxOccurs"}, axis = "columns")
                                     )[['minOccurs', 'maxOccurs', 'domain', 'label', 'comment']] #[['minOccurs', 'maxOccurs', 'dataType', 'domain', 'label', 'comment']]

    return validation_data


def concrete_classes_list(data):
    return list(data.query("VALUE == 'http://iec.ch/TC57/NonStandard/UML#concrete'")["ID"])


def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):

        if filename.endswith(file_extension):
            matches.append(os.path.join(path, filename))
        else:
            print("Not a {} file: {}".format(file_extension, filename))

    return matches

def get_profile_metadata(data):
    """Returns metadata about CIM profile defined in RDFS"""

    profile_domain = data.query("VALUE == 'baseUML'")["ID"].item().split(".")[0]
    profile_metadata = data[data.ID.str.contains(profile_domain)].query("KEY == 'isFixed'").copy(deep=True)

    profile_metadata["ID"] = profile_metadata.ID.str.split("#", expand=True)[1].str.split(".", expand=True)[1]

    return profile_metadata.set_index("ID")["VALUE"]

# Full Model class is missing in RDFS, thus added here manually # TODO add Supersedes
fullmodel_conf = { "FullModel": {
                        "attrib": {
                            "attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",
                            "value_prefix": "urn:uuid:"
                            },
                            "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"},

                    "Model.DependentOn": {
                        "attrib": {
                            "attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                            "value_prefix": "urn:uuid:"
                        },
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },

                    "Model.Supersedes": {
                        "attrib": {
                            "attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                            "value_prefix": "urn:uuid:"
                        },
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },

                    "Model.created": {
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },
                    "Model.description": {
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },
                    "Model.messageType": {
                        "namespace": "http://entsoe.eu/CIM/Extensions/CGM-BP/2020#"
                    },
                    "Model.modelingAuthoritySet": {
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },
                    "Model.modelingEntity": {
                        "namespace": "http://entsoe.eu/CIM/Extensions/CGM-BP/2020#"
                    },
                    "Model.processType": {
                        "namespace": "http://entsoe.eu/CIM/Extensions/CGM-BP/2020#"
                    },
                    "Model.profile": {
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },
                    "Model.scenarioTime": {
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    },
                    "Model.version": {
                        "namespace": "http://iec.ch/TC57/61970-552/ModelDescription/1#"
                    }}

if __name__ == '__main__':

    import json

    #path = r"rdfs\CGMES_2_4_15_09May2019_RDFS\EquipmentProfileCoreOperationShortCircuitRDFSAugmented-v2_4_15-09May2019.rdf"
    #path = r"rdfs\RDFS_UML_FDIS06_27Jan2020.zip"
    path = r"rdfs\CGMES_2_4_15_09May2019_RDFS\UNIQUE_RDFSAugmented-v2_4_15-09May2019.zip"

    data = load_all_to_dataframe([path])

    # Dictionary to keep all configurations
    conf_dict = {}

    # For each profile in loaded RDFS
    profiles = data["INSTANCE_ID"].unique()

    for profile in profiles:
        profile_data = data.query(f"INSTANCE_ID == '{profile}'")

        # Get current profile metadata
        metadata = get_profile_metadata(profile_data).to_dict()
        profile_name = metadata["shortName"].replace("_", "")

        # Dictionary to keep current profile metadata
        conf_dict[profile_name] = {}

        # Add concrete classes

        cim_namespace = metadata["namespaceUML"]
        rdf_namespace = metadata["namespaceRDF"]

        classes_defined_externally = profile_data.query("KEY == 'stereotype' and VALUE == 'Description'").ID.to_list()

        for concrete_class in concrete_classes_list(profile_data):

            # Define class namespace
            class_namespace, class_name = concrete_class.split("#")

            if class_namespace == "":
                class_namespace = cim_namespace
            else:
                class_namespace = class_namespace + "#"

            # Define class ID attribute #TODO add conf for this, foreseen to change in CGMES 3.0, use rdf:about everywhere
            class_ID_attribute = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}ID"
            class_ID_prefix = "_"

            if concrete_class in classes_defined_externally:
                class_ID_attribute = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"
                class_ID_prefix = "#_"

            # Add class definition
            conf_dict[profile_name][class_name] = {"attrib": {"attribute": class_ID_attribute,
                                                              "value_prefix": class_ID_prefix},
                                                   "namespace": class_namespace}

            # Add attributes

            for parameter, parameter_meta in parameter_tableview(profile_data, concrete_class).iterrows():

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

                # If association
                if association_used == 'Yes':
                    conf_dict[profile_name][parameter_name] = {"attrib": {"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                                                                          "value_prefix": "#_"},
                                                               "namespace": parameter_namespace}

                # If regular parameter
                else:
                    data_type = parameter_dict.get("dataType", "nan")

                    if str(data_type) != "nan":
                        conf_dict[profile_name][parameter_name] = {"namespace": parameter_namespace}

                    else:
                        conf_dict[profile_name][parameter_name] = {
                            "attrib": {"attribute": "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource",
                                       "value_prefix": ""},
                            "namespace": parameter_namespace}


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

    for profile_name in conf_dict:
        conf_dict[profile_name].update(fullmodel_conf)

    # Export conf

    file_name = "{entsoeUML}_{date}.json".format(**metadata)
    #file_name = "{profileUML}_{date}.json".format(**metadata)

    with open(file_name, "w") as file_object:
        json.dump(conf_dict, file_object, indent=4)





#files_list = list_of_files(r"C:\USVDM\Tools\RDF_PARSER\ENTSOE_CGMES_v2.4.15_04Jul2016_RDFS", ".rdf")

##for file_path in files_list:
##
##    path_list = [file_path]
##
##    data = load_all_to_dataframe(path_list)


##
##    # Packages
##
##    packages = data.query("VALUE == 'http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory'")[["ID"]]
##
##    # Profile metadata
##
##    metadata = get_profile_metadata(data).to_dict()
##
##    # entsoeURI
##    entsoeURI_url_list = profile_metadata[profile_metadata.ID.str.contains("entsoeURI")].VALUE.tolist()
##
##    entsoeURI_list = []
##
##    for url in entsoeURI_url_list:
##         entsoeURI_list.append(urlparse.urlparse(url).path.split("/")[2])
##
##
##    # Write to files
##
##    #filename = "_".join([metadata["shortName"], metadata["entsoeUML"], metadata["date"]] + entsoeURI_list).replace(".", "").replace("-", "") + ".html"
##
##    filename = ".html"
##
##    #print filename
##
##
##    folder = os.path.join(metadata["entsoeUML"], metadata["shortName"], "_".join(entsoeURI_list))
##    if not os.path.exists(folder):
##        os.makedirs(folder)
##
##    simple_profile_metadata.to_html(open(os.path.join(folder, "Profile" + filename), "w"),index = False)
##    packages.to_html(open(os.path.join(folder, "Packages" + filename), "w"),index = False)
##
##
##    for concrete_class in concrete_classes_list():
##
##        path = os.path.join(folder, concrete_class + filename)
##        validation_view(concrete_class).to_html(open(path, "w"),index = True)


#print(validation_view("#ACLineSegment"))
#print(validation_view("#PowerTransformerEnd"))