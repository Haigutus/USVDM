
# Purpose:
Collection of tools that helps one to use and exchange CIM based gridmodels (CIM16/CGMES) and market messages (IEC 62325)



# Tools made into python modules:
* [EDX Mades api](https://pypi.org/project/EDX) - used for subscribe and fanout like data exchange, extra level on ECP
* [ECP Mades api](https://pypi.org/project/ecp-api) - used for direct data exchange
* [OPDM api](https://pypi.org/project/opdm-api/) - used for Gridmodel Exchanges in Europe (IGM, CGM, BDS)
* [triplets](https://pypi.org/project/triplets/) Import and Export CIM/XML/RDF gridmodesl to pandas dataframe in a triplestore like format. Headers: [ID, KEY, VALUE, INSTANCE_ID] packaged and updated version of [RDF parser](https://github.com/Haigutus/USVDM/blob/master/Tools/RDF_PARSER)

# Tools that work but not made to python modules

* [XML validator](https://github.com/Haigutus/xml-validator) (git submodule at `Tools/XML_VALIDATOR`) → [https://xsd.cimtools.eu/](https://xsd.cimtools.eu/) — UI to validate market XML (IEC 62325 / ESMP and Edig@s); clone with `git clone --recurse-submodules` or `git submodule update --init`


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
