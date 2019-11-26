#-------------------------------------------------------------------------------
# Name:        Profile size query
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     26.11.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     GPL v2
#-------------------------------------------------------------------------------

import OPDM_SOAP_client

metadata_dict = {'pmd:scenarioDate': '2019-11-27T09:30:00', 'pmd:timeHorizon':"1D" } # ,'pmd:TSO': 'CGMBA' ,'pmd:cgmesProfile': 'EQ', 'pmd:TSO': 'APG',}
message_id, response =   query_profile(metadata_dict)
print(json.dumps(response, indent = 4))
response['sm:QueryResult']['sm:part'].pop(0)
print(pandas.DataFrame(response['sm:QueryResult']['sm:part']))