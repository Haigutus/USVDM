from RDF_parser import load_all_to_dataframe

import pandas
import urlparse
import os

pandas.set_option("display.max_rows", 15)
pandas.set_option("display.max_columns", 8)
pandas.set_option("display.width", 1000)
#pandas.set_option('display.max_colwidth', -1)

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





def get_all_class_parameters(class_name):

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


def parameter_tableview(class_name):

    all_class_parameters = get_all_class_parameters(class_name)

    parameter_id_list = all_class_parameters["ID"].tolist()

    type_data = data[data.ID.isin(parameter_id_list)].drop_duplicates(["ID", "KEY"])  # There can't be duplicate ID and KEY pairs for pivot.
    data_view = type_data.pivot(index="ID", columns="KEY")["VALUE"]

    return data_view


def validation_view(class_name):


    data_view = parameter_tableview(class_name)

    validation_data = data_view.join(data_view['multiplicity'].
                                     str.split("#M:", expand=True)[1].
                                     str.split(r".", expand=True)[[0, 2]].
                                     rename({0:"minOccurs", 2:"maxOccurs"}, axis = "columns")
                                     )[['minOccurs', 'maxOccurs', 'domain', 'label', 'comment']] #[['minOccurs', 'maxOccurs', 'dataType', 'domain', 'label', 'comment']]

    return validation_data


def concrete_classes_list():
    return list(data.query("VALUE == 'http://iec.ch/TC57/NonStandard/UML#concrete'")["ID"])


def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):

        if filename.endswith(file_extension):
            matches.append(os.path.join(path, filename))
        else:
            print("Not a {} file: {}".format(file_extension, filename))

    return matches



files_list = list_of_files(r"C:\USVDM\Tools\RDF_PARSER\ENTSOE_CGMES_v2.4.15_04Jul2016_RDFS", ".rdf")

for file_path in files_list:

    path_list = [file_path]

    data = load_all_to_dataframe(path_list)

    # Packages

    packages = data.query("VALUE == 'http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory'")[["ID"]]

    # Profile metadata

    profile_domain = data.query("VALUE == 'baseUML'")["ID"].item().split(".")[0]

    profile_metadata = data[data.ID.str.contains(profile_domain)].query("KEY == 'isFixed'")[["ID", "VALUE"]]
    simple_profile_metadata = profile_metadata.copy(deep=True)
    simple_profile_metadata["ID"] = simple_profile_metadata.ID.str.split("#", expand = True)[1].str.split(".", expand = True)[1]
    #simple_profile_metadata = simple_profile_metadata[["ID", "VALUE"]]

    metadata = simple_profile_metadata.set_index("ID")["VALUE"].to_dict()




    entsoeURI_url_list = profile_metadata[profile_metadata.ID.str.contains("entsoeURI")].VALUE.tolist()

    entsoeURI_list = []

    for url in entsoeURI_url_list:
         entsoeURI_list.append(urlparse.urlparse(url).path.split("/")[2])


    #filename = "_".join([metadata["shortName"], metadata["entsoeUML"], metadata["date"]] + entsoeURI_list).replace(".", "").replace("-", "") + ".html"

    filename = ".html"

    #print filename


    folder = os.path.join(metadata["entsoeUML"], metadata["shortName"], "_".join(entsoeURI_list))
    if not os.path.exists(folder):
        os.makedirs(folder)

    simple_profile_metadata.to_html(open(os.path.join(folder, "Profile" + filename), "w"),index = False)
    packages.to_html(open(os.path.join(folder, "Packages" + filename), "w"),index = False)


    for concrete_class in concrete_classes_list():

        path = os.path.join(folder, concrete_class + filename)
        validation_view(concrete_class).to_html(open(path, "w"),index = True)


#print(validation_view("#ACLineSegment"))
#print(validation_view("#PowerTransformerEnd"))