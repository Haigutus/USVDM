Short explanation how my RDF parser works:

It parses all the data to pandas dataframe with 4 columns [ID, KEY, VALULE, INSTANCE_ID] (sort of triplestore like)
path = "CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"
data = load_all_to_dataframe([path])


You can then ask a dataframe of all same type elements and its parameters across all [EQ, SSH, TP, SV etc.] instance files, where parameters are columns and index is object ID-s

Look into exaples folders for more details
