
# Purpose:
Collection of tools that helps one to use and exchange CIM based gridmodels (CIM16/CGMES) and market messages (IEC 62325)



# Tools made into python modules:
* [EDX Mades api](https://pypi.org/project/EDX) - used for subscribe and fanout like data exchange, extra level on ECP
* [ECP Mades api](https://pypi.org/project/ecp-api) - used for direct data exchange

# Tools that work but not made to python modules

* [RDF parser](https://github.com/Haigutus/USVDM/blob/master/Tools/RDF_PARSER/RDF_parser.py) - parses CIM/XML/RDF gridmodesl to pandas dataframe in a triplestore like format. Headers: [ID, KEY, VALUE, INSTANCE_ID]
* [OPDM api](https://github.com/Haigutus/USVDM/blob/master/Tools/MADES_API/OPDM_SOAP_client.py) - to exchange gridmodels
* [XML validator](https://github.com/Haigutus/USVDM/tree/master/Tools/XML_VALIDATOR) -> [https://xsd.cimtools.eu/](https://xsd.cimtools.eu/) - UI to validate XML messages - (European Market message XSD-s included: IEC62325 and EDIGAS 5)


# Tools that need to be updated

## 1.[ENTSO-E OPDM validator wrapper](https://github.com/Haigutus/USVDM/tree/master/Tools/CGMES_VALIDATOR)

#### Python support:
2.7
#### External modules:
1. OPDM validator R2.0 _30.06.2017_  - [link](https://extra.entsoe.eu/SOC/IT/OPDE_OPDM_KeyDocuments/cgmes-validation-tool-R2.0.zip) 

#### User guide:
1. Add OPDM validator to same folder with python script
2. Run python script
3. Select file(s) containing single .xml profile or zip file(s) containing zipped profiles for validation 
4. Select location for report folder
5. Check .xml files in selected report folder location
