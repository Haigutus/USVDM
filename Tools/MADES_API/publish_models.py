#-------------------------------------------------------------------------------
# Name:        publish_modles.py
# Purpose:     Upload IGM-s to OPDE
#
# Author:      kristjan.vilgo
#
# Created:     06.08.2018
# Copyright:   (c) kristjan.vilgo 2018
# Licence:     GPL2
#-------------------------------------------------------------------------------
import os
from lxml import etree
import zipfile
import OPDM      # python -m pip install opdm-api


MODELLING_TOOL_NAME =  "Neplan"
MODELLING_TOOL_VERSION =  "10.8.6.2"

source_path      = "Generated Cases"
destination_path = "Generated Cases Archive"

upload_to_pro = True
OPDM_PRO_URL = ""
OPDM_PRO_USERNAME = ""
OPDM_PRO_PASSWORD = ""

upload_to_acc = True
OPDM_ACC_URL = ""
OPDM_ACC_USERNAME = ""
OPDM_ACC_PASSWORD = ""


if upload_to_acc:
    try:
        OPDE_acceptance = OPDM.create_client(OPDM_ACC_URL, username=OPDM_ACC_USERNAME, password=OPDM_ACC_PASSWORD)
    except:
        print("Could not connect to OPDM Acceptance ENV")

if upload_to_pro:
    try:
        OPDE_production = OPDM.create_client(OPDM_PRO_URL, username=OPDM_PRO_USERNAME, password=OPDM_PRO_PASSWORD)
    except:
        print("Could not connect to OPDM Production ENV")



def list_of_files(path,file_extension):

    matches = []
    for filename in os.listdir(path):

        if filename.endswith(file_extension):
            #logging.info("Processing file:"+filename)
            matches.append(path + "//" + filename)
        else:
            print("Not a {} file: {}".format(file_extension, filename))
            #logging.warning("Not a {} file: {}".format(file_extension,file_text[0]))

    print(matches)
    return matches

meta_separator = "_"

def metadata_from_filename(file_name):

    file_metadata = {} # Meta container

    file_name, file_metadata["file_type"] = file_name.split(".")
    meta_list = file_name.split(meta_separator)



    if len(meta_list) == 4:   #try: #if "_EQ_" in file_name or "_BD_" in file_name:

        file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = meta_list
        file_metadata["process_type"] = ""


    elif len(meta_list) == 5:

        file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"] = meta_list


    else:
        print("Parsing error, number of allowed meta in filename is 4 or 5 separated by '_' -> {} ".format(file_name))

    return file_metadata

def filename_from_metadata(file_metadata):

    #if file_metadata["profile"] == "EQ" or file_metadata["profile"] == "BD":
    #    file_name = meta_separator.join([file_metadata["date_time"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    #else:
    file_name = meta_separator.join([file_metadata["date_time"], file_metadata["process_type"], file_metadata["model_authority"], file_metadata["profile"], file_metadata["version"]])

    file_name = ".".join([file_name, file_metadata["file_type"]])

    return file_name

def get_xml_from_zip(zip_file_path):

    zipfile_object    = zipfile.ZipFile(zip_file_path)
    xml_file_name     = zipfile_object.namelist()[0]
    file_unzipped     = zipfile_object.open(xml_file_name, mode="r")
    xml_tree_object   = etree.parse(file_unzipped)

    return xml_tree_object

def zip_xml_file(xml_etree_object, file_metadata, destination_bath):

    # Get meta and path
    file_metadata["file_type"] = "zip"
    zip_file_name = filename_from_metadata(file_metadata)

    file_metadata["file_type"] = "xml"
    xml_file_name = filename_from_metadata(file_metadata)

    zip_file_path = os.path.join(destination_bath, zip_file_name)

    # Create and save ZIP
    out_zipped_file = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    out_zipped_file.writestr(xml_file_name, etree.tostring(xml_etree_object, pretty_print=True, xml_declaration=True, encoding='UTF-8'))#, pretty_print=True))
    out_zipped_file.close()

    return zip_file_path


# Get alla files to be uploaded
list_of_source_files = list_of_files(source_path, ".zip")

# Start upload process
for file_path in list_of_source_files:

    file_name = os.path.basename(file_path)
    print(file_path)

    if "_BD_" in file_name:
        print ("Warning - boundary will not be uploaded")
        continue

    # Parse meta from filename
    file_metadata = metadata_from_filename(file_name)

    # Get XML file
    instance_xml = get_xml_from_zip(file_path)

    # Add data confidentiality
    root = instance_xml.getroot()
    root.addprevious(etree.Comment('OPDE Confidential'))

    # Replace process type
    if file_metadata["process_type"] == "ID":

        file_metadata["process_type"] = "23"  #TODO - calcualte number of hours drom creation date to scenario date and use that as process type

    #if file_metadata["profile"] == "SV":
    #    # Add reference to random node
    #    topological_island = instance_xml.find("{*}TopologicalIsland")
    #    random_node = topological_island.find("{*}TopologicalIsland.TopologicalNodes").attrib.values()[0]
    #
    #    angle_ref = etree.Element("{http://iec.ch/TC57/2013/CIM-schema-cim16#}TopologicalIsland.AngleRefTopologicalNode")
    #    angle_ref.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"] = random_node
    #
    #    topological_island.append(angle_ref)


    # Add correct metadata to description
    instance_xml.find(".//{*}Model.description").text = f"""
<MDE>
    <BP>{file_metadata["process_type"]}</BP>
    <TOOL>{MODELLING_TOOL_NAME}_V{MODELLING_TOOL_VERSION}</TOOL>
</MDE>
"""


    # Get filename form meta
    new_file_name = filename_from_metadata(file_metadata)

    # New filepath
    new_path      = os.path.join(destination_path, new_file_name)

    # If file allready exist rise version number
    while os.path.exists(new_path) == True:

        print("File allready exists: {}".format(new_path))
        print("Raising version number")

        #Raise version by one
        current_version          = int(file_metadata["version"])
        file_metadata["version"] = "{:03d}".format(current_version + 1)

        instance_xml.find(".//{*}Model.version").text = file_metadata["version"]


        print("File will be written with new version number {}".format(file_name))

        # Get filename form meta
        new_file_name = filename_from_metadata(file_metadata)

        # New filepath
        new_path      = os.path.join(destination_path, new_file_name)


    # Save zip file
    new_path = zip_xml_file(instance_xml, file_metadata, destination_path)


    if os.path.exists(new_path):

        if upload_to_pro:
            try:
                print("Uploading to OPDM Production")
                response = OPDE_production.publication_request(new_path)
                print(etree.tostring(response, pretty_print = True).decode())  #DEBUG
            except Exception as e:
                print(e)
                print("Unable to upload to OPDM Production, disabeling upload")
                upload_to_pro = False

        if upload_to_acc:
            try:
                print("Uploading to OPDM Acceptance")
                response = OPDE_acceptance.publication_request(new_path)
                print(etree.tostring(response, pretty_print = True).decode())  #DEBUG
            except Exception as e:
                print(e)
                print("Unable to upload to OPDM Acceptance, disabeling upload")
                upload_to_acc = False

    else:
        print("Path not found, skipping -> {}".format(new_path))
