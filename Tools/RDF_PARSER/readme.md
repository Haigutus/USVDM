# RDF parser:

It parses RDF/XML data to pandas dataframe with 4 columns [ID, KEY, VALUE, INSTANCE_ID] (sort of triplestore like)

Input files can be xml or zip files (containgn one or mutiple xml files)

to get started:

```python
import pandas
import RDF_parser

path = "CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"
data = pandas.read_RDF([path])
```

Result:

![image](https://user-images.githubusercontent.com/11408965/64228384-53350500-ceef-11e9-9a8b-473ed1dc6e4d.png)


You can then query a dataframe of all same type elements and its parameters across all [EQ, SSH, TP, SV etc.] instance files, where parameters are columns and index is object ID-s

```python
data.type_tableview("ACLineSegment")
```

![image](https://user-images.githubusercontent.com/11408965/64228433-7eb7ef80-ceef-11e9-81d4-43e39ecf099d.png)


Look into examples folders for more
