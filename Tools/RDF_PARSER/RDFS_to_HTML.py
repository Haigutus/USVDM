from RDFS_tools import *
import os

files_list = list_of_files(r"rdfs\CGMES_2_4_15_09May2019_RDFS", ".rdf")

namespace_map = dict(    cim="http://iec.ch/TC57/2013/CIM-schema-cim16#",
                         cims="http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
                         entsoe="http://entsoe.eu/CIM/SchemaExtension/3/1#",
                         cgmbp="http://entsoe.eu/CIM/Extensions/CGM-BP/2020#",
                         md="http://iec.ch/TC57/61970-552/ModelDescription/1#",
                         rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                         rdfs="http://www.w3.org/2000/01/rdf-schema#",
                         xsd="http://www.w3.org/2001/XMLSchema#")

prefix_map = {v: k for k, v in namespace_map.items()}

def replace_namesapce_with_prefix(uri, default_namespace="http://iec.ch/TC57/2013/CIM-schema-cim16"):

    namespace, name = uri.split("#")

    if namespace == "":
        namespace = default_namespace

    prefix = prefix_map[f"{namespace}#"]

    return f"{prefix}:{name}"


def html_datatable(table, path):
    """Create nice formatted HTML table from pandas dataframe"""

    html = f"""
    <html>
        <body>
            <head>
                <style>
				#settings {{
					font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
					border-collapse: collapse;
					width: 100%;
				}}

				#settings td, #setting th {{
					border: 1px solid #ddd;
					padding: 8px;
				}}

				#settings tr:nth-child(even){{background-color: #f2f2f2;}}

				#settings tr:hover {{background-color: #ddd;}}

				#settings th {{
					padding-top: 12px;
					padding-bottom: 12px;
                    padding-left: 8px;
					padding-right: 12px;
					text-align: left;
					background-color: #001f3f;
					color: white;
				}}

				</style>
            </head>

            {table.to_html(index=False, index_names=False, table_id="settings")}

        </body>
    </html>

            """

    with open(path, "w") as file_object:
        file_object.write(html)

    return html


for file_path in files_list:

    path_list = [file_path]

    data = load_all_to_dataframe(path_list)


    # Packages

    packages = data.query("VALUE == 'http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory'")[["ID"]]

    # Profile metadata

    profile_metadata = get_profile_metadata(data).to_frame()

    metadata = profile_metadata["VALUE"].to_dict()

    # entsoeURI
    entsoeURI_url_list = profile_metadata[profile_metadata.index.str.contains("entsoeURI")].VALUE.tolist()

    entsoeURI_list = []

    for url in entsoeURI_url_list:
        entsoeURI_list.append(url.split("/")[-3])


    # Write to files

    #filename = "_".join([metadata["shortName"], metadata["entsoeUML"], metadata["date"]] + entsoeURI_list).replace(".", "").replace("-", "") + ".html"

    filename = ".html"

    #print(filename)


    folder = os.path.join(metadata["entsoeUML"], metadata["shortName"], "_".join(entsoeURI_list))
    if not os.path.exists(folder):
        os.makedirs(folder)

    html_datatable(profile_metadata.reset_index(), os.path.join(folder, "Profile" + filename))
    html_datatable(packages, os.path.join(folder, "Packages" + filename))
    #packages.to_html(open(os.path.join(folder, "Packages" + filename), "w"), index=False)


    for concrete_class in concrete_classes_list(data):

        namespace, name = get_namespace_and_name(concrete_class, metadata['namespaceUML'])

        path = os.path.join(folder, name + filename)
        view = validation_view(data, concrete_class)
        view.index = view.index.map(replace_namesapce_with_prefix)
        view = view.reset_index()

        html_datatable(view, path)

        #with open(path, "w") as file_object:
        #    file_object.write(html_datatable(view))
        #view.to_html(open(path, "w"), index=True)