# RDF parser:

It parses RDF XML data to pandas dataframe with 4 columns [ID, KEY, VALULE, INSTANCE_ID] (sort of triplestore like)

to get started:

```python
import pandas
import RDF_parser

path = "CGMES_v2.4.15_RealGridTestConfiguration_v2.zip"
data = pandas.read_RDF([path])
```


You can thenquery a dataframe of all same type elements and its parameters across all [EQ, SSH, TP, SV etc.] instance files, where parameters are columns and index is object ID-s

Look into examples folders for more
