from RDF_parser import load_all_to_dataframe

import pandas

path_list = [r"ENTSOE_CGMES_v2.4.15_04Jul2016_RDFS/EquipmentProfileCoreOperationRDFSAugmented-v2_4_15-4Jul2016.rdf"]

data = load_all_to_dataframe(path_list)


def get_all_class_parameters(class_name):

    all_class_parameters = pandas.DataFrame()
    class_name_list = [class_name]

    for class_name in class_name_list:

        # Get parameters and add to parameter dataframe
        class_parameters = data.query("VALUE == '{}' & KEY == 'domain'".format(class_name))
        all_class_parameters = all_class_parameters.append(class_parameters)

        # Look if the class has a parent class, if yes add to further parsing
        cim_class = data.query("ID == '{}'".format(class_name))
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
                                     )[['minOccurs', 'maxOccurs', 'comment', 'dataType', 'domain', 'label']]

    return validation_data


def concrete_classes_list():
    return list(data.query("VALUE == 'http://iec.ch/TC57/NonStandard/UML#concrete'")["ID"])


#print(validation_view("#ACLineSegment"))
#print(validation_view("#PowerTransformerEnd"))


for concrete_class in concrete_classes_list():
    print(validation_view(concrete_class))