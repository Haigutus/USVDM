import pandas
import triplets
import pypowsybl
import uuid


PROVIDER_PARAMETERS = {
    #'loadPowerFactorConstant': 'False',  # cim:PowerFlowSettings.loadVoltageDependency "false"
    #'maxOuterLoopIterations': '20',  # eumd:PowerFlowSettings.maxIterationNumber "20"
    #'lowImpedanceThreshold': '1.0E-5',  # cim:PowerFlowSettings.impedanceThreshold "1e-05" ;
    #'newtonRaphsonStoppingCriteriaType': 'PER_EQUATION_TYPE_CRITERIA',
    #'maxActivePowerMismatch': '0.1',  # cim:PowerFlowSettings.activePowerTolerance "0.1"
    #'maxReactivePowerMismatch': '0.1',  # cim:PowerFlowSettings.reactivePowerTolerance "0.1"
    #'maxVoltageMismatch': '1.0E-4',  # cim:PowerFlowSettings.voltageTolerance "0.0001" ;
    #'maxAngleMismatch': '1.0E-5',  # cim:PowerFlowSettings.voltageAngleLimit "10"
    'slackBusPMaxMismatch': '0.1',  # To fulfill QOCDC SV_INJECTION_LIMIT = 0.1
}

LOADFLOW_PARAMETERS = pypowsybl.loadflow.Parameters(
    #voltage_init_mode=pypowsybl._pypowsybl.VoltageInitMode.UNIFORM_VALUES,  # cim:PowerFlowSettings.flatStart "true"
    #transformer_voltage_control_on=True,  # cim:PowerFlowSettings.transformerRatioTapControlPriority "1" ;
    #no_generator_reactive_limits=False,  # cim:PowerFlowSettings.respectReactivePowerLimits "true" ;
    #phase_shifter_regulation_on=True,  # cim:PowerFlowSettings.transformerPhaseTapControlPriority "1" ;
    #twt_split_shunt_admittance=None,
    #simul_shunt=True,  # cim:PowerFlowSettings.switchedShuntControlPriority "2" ;
    #read_slack_bus=True,
    #write_slack_bus=True,
    #distributed_slack=True,  #cim:PowerFlowSettings.slackDistributionKind cim:SlackDistributionKind.generationDistributionParticipationFactor ;
    #balance_type=pypowsybl._pypowsybl.BalanceType.PROPORTIONAL_TO_GENERATION_PARTICIPATION_FACTOR, #cim:PowerFlowSettings.slackDistributionKind cim:SlackDistributionKind.generationDistributionParticipationFactor ;
    #dc_use_transformer_ratio=None,
    #countries_to_balance=None,
    #connected_component_mode=pypowsybl._pypowsybl.ConnectedComponentMode.MAIN,
    provider_parameters=PROVIDER_PARAMETERS,
)

loads = []

lines = []

network = pypowsybl.network.load("Export.zip")
print("Imported to powsybl")
analysis = pypowsybl.sensitivity.create_ac_analysis()



analysis.add_branch_flow_factor_matrix(branches_ids=[line["ID"] for line in lines], variables_ids=[load["mRID"] for load in loads])
result = analysis.run(network)
#result.get_reference_matrix()
result.get_sensitivity_matrix()


#loadflow_result = pypowsybl.loadflow.run_ac(network=network, parameters=LOADFLOW_PARAMETERS)
#print("Loadflow done")
#print(loadflow_result)

#loadflow_result_path = f"after_lf_export_{uuid.uuid4()}.zip"



export = network.save_to_binary_buffer(
                          format="CGMES",
                          parameters={
                               #"iidm.export.cgmes.modeling-authority-set": "http://www.elering.ee/OperationalPlanning",
                               #"iidm.export.cgmes.base-name": f"{scenario['scenario_time'].replace(':','').replace('-','')}_{process_type}_ELERING",
                               #"iidm.export.cgmes.profiles": "SV,TP,SSH",
                               "iidm.export.cgmes.naming-strategy": "cgmes",  # identity, cgmes, cgmes-fix-all-invalid-ids
                                      })
export.name = "export.zip"

print("2. Export done")

#Load solved data
solved_data = pandas.read_RDF([export])
#print("Imported data form powsybl")