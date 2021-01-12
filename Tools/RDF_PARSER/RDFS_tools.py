from RDF_parser import load_all_to_dataframe

import pandas
import os

pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)
pandas.set_option('display.max_colwidth', None)


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


def list_of_files(path, file_extension):

    matches = []
    for filename in os.listdir(path):

        if filename.endswith(file_extension):
            matches.append(os.path.join(path, filename))
        else:
            print("Not a {} file: {}".format(file_extension, filename))

    return matches



def get_all_class_parameters(data, class_name):

    all_class_parameters = pandas.DataFrame()  # TODO, use list or tuple
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
            class_name_list.append(parent_class.to_list()[0])  # In case multiple profiles loaded together

    print("Inheritance sequence")
    print(" -> ".join(class_name_list))

    return all_class_parameters


def parameter_tableview(data, class_name):

    all_class_parameters = get_all_class_parameters(data, class_name)

    #parameter_id_list = all_class_parameters["ID"].tolist()  # TODO use merge here insetad isin method - it is faster

    #type_data = data[data.ID.isin(parameter_id_list)].drop_duplicates(["ID", "KEY"])  # There can't be duplicate ID and KEY pairs for pivot.

    type_data = all_class_parameters[["ID"]].merge(data, on="ID").drop_duplicates(["ID", "KEY"])

    data_view = type_data.pivot(index="ID", columns="KEY")["VALUE"]

    return data_view


def validation_view(data, class_name):


    data_view = parameter_tableview(data, class_name)

    validation_data = multiplicity_to_XSD_format(data_view)

    if "AssociationUsed" in validation_data.columns:
        validation_data = validation_data.query("AssociationUsed != 'No'")

    return validation_data[['minOccurs', 'maxOccurs', 'comment']] #[['minOccurs', 'maxOccurs', 'dataType', 'domain', 'label', 'comment']]


def multiplicity_to_XSD_format(data_table_view):
    """Converts multiplicity defined in extended RDFS to XSD minOccurs and maxOccurs and adds them to the table"""

    multiplicity = data_table_view.multiplicity.str.split("#M:").str[1]
    data_table_view["minOccurs"] = multiplicity.str[0]
    data_table_view["maxOccurs"] = multiplicity.str[-1].str.replace("n", "unbounded")

    return data_table_view


def get_namespace_and_name(uri, default_namespace):

    namespace, name = uri.split("#")

    if namespace == "":
        namespace = default_namespace

    return namespace, name



def parse_multiplicity(uri):
    """Converts multiplicity defined in extended RDFS to XSD minOccurs and maxOccurs"""

    multiplicity = str(uri).split("#M:")[1]

    minOccurs = multiplicity[-1].replace("n", "unbounded")
    maxOccurs = multiplicity[0]

    return minOccurs, maxOccurs


def concrete_classes_list(data):
    """Returns list of Concrete classes from Triplet"""
    return list(data.query("VALUE == 'http://iec.ch/TC57/NonStandard/UML#concrete'")["ID"])


def get_profile_metadata(data):
    """Returns metadata about CIM profile defined in RDFS"""

    profile_domain = data.query("VALUE == 'baseUML'")["ID"].to_list()[0].split(".")[0]
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

    path = r"rdfs\CGMES_2_4_15_09May2019_RDFS\UNIQUE_RDFSAugmented-v2_4_15-09May2019.zip"

    data = load_all_to_dataframe([path])

    print(validation_view(data, "#ACLineSegment"))
    print(validation_view(data, "#PowerTransformerEnd"))








#print(validation_view("#ACLineSegment"))
#print(validation_view("#PowerTransformerEnd"))