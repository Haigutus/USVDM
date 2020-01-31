#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     30.08.2019
# Copyright:   (c) kristjan.vilgo 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import RDF_parser
import pandas

data = RDF_parser.load_all_to_dataframe([
r"C:\IOPs\IOP050619\BA02_BD05062019_1D_Elering_001_NodeBreaker\20190604T2230Z_1D_ELERING_SSH_001.zip",
r"C:\IOPs\IOP050619\BA02_BD05062019_1D_Elering_001_NodeBreaker\20190604T2230Z_1D_ELERING_SV_001.zip",
r"C:\IOPs\IOP050619\BA02_BD05062019_1D_Elering_001_NodeBreaker\20190604T2230Z_1D_ELERING_TP_001.zip",
r"C:\IOPs\IOP050619\BA02_BD05062019_1D_Elering_001_NodeBreaker\20190604T2230Z_ELERING_EQ_002.zip"])

synchrouns_machines  = data.type_tableview("SynchronousMachine")
generating_units     = data.type_tableview("GeneratingUnit")


join = synchrouns_machines.merge(generating_units, left_on = "RotatingMachine.GeneratingUnit", right_index = True)

join[u'RotatingMachine.p'] = join[u'RotatingMachine.p'] * -1

print(join[(join[u'RotatingMachine.p'] < join[u'GeneratingUnit.minOperatingP'])][[u'RotatingMachine.p', u'GeneratingUnit.minOperatingP', u'IdentifiedObject.name_x', u'IdentifiedObject.name_y']])
print(join[(join[u'RotatingMachine.p'] > join[u'GeneratingUnit.maxOperatingP'])][[u'RotatingMachine.p', u'GeneratingUnit.minOperatingP', u'IdentifiedObject.name_x', u'IdentifiedObject.name_y']])
