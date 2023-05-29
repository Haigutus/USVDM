
# Purpose:
Collection of tools that helps one to use and exchange CIM based gridmodels (CIM16/CGMES) and market messages (IEC 62325)



# Tools made into python modules:
* [EDX Mades api](https://pypi.org/project/EDX) - used for subscribe and fanout like data exchange, extra level on ECP
* [ECP Mades api](https://pypi.org/project/ecp-api) - used for direct data exchange
* [OPDM api](https://pypi.org/project/opdm-api/) - used for Gridmodel Exchanges in Europe (IGM, CGM, BDS) 

# Tools that work but not made to python modules

* [RDF parser](https://github.com/Haigutus/USVDM/blob/master/Tools/RDF_PARSER) - parses CIM/XML/RDF gridmodesl to pandas dataframe in a triplestore like format. Headers: [ID, KEY, VALUE, INSTANCE_ID]
* [XML validator](https://github.com/Haigutus/USVDM/tree/master/Tools/XML_VALIDATOR) -> [https://xsd.cimtools.eu/](https://xsd.cimtools.eu/) - UI to validate XML messages - (European Market message XSD-s included: IEC62325 and EDIGAS 5)
