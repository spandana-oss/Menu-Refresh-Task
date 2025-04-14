package com.example.deltasitemanager.models

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    val status: String,
    val message: String,
    val api_key: String
)

data class SiteInfoResponse(
    val status: String,
    val message: Any
)

data class SiteInfo(
    val ems_id: Int,
    val mac_id: String,
    val sub_name: String,
    val created_at: String,
    val capacity: Int,
    val ems_name: String
)
//
//data class IndividualSiteInfo(
//    val gatewayid: String,
//    val PCS_ActivePower: String,
//    val Total_SoC: String
//)
//

data class GenericResponse<T>(
    val status: String,
    val message: List<T>
)

data class IndividualSiteInfo(
    val ems_data_id: Int,
    val ems_id: Int,
    val gatewayid: String,
    val evtime: String,
    val PCS_ActivePower: Double,
    val PCS_EnergyImport_Today: Double,
    val PCS_EnergyExport_Today: Double,
    val PCS_Status: Int,
    val PCS_Control_Mode: Int,
    val PCS_EnergyImport_Lifetime: Double,
    val PCS_EnergyExport_Lifetime: Double,
    val Total_System_Charge_State: Int,
    val Total_BatteryVoltage: Double,
    val Total_BatteryCurrent: Double,
    val Total_BatteryPower: Double,
    val Total_SoC: Int,
    val Grid_CB_Status: Int,
    val DG1_CB_Status: Int,
    val DG2_CB_Status: Int,
    val Selection_Switch: Int,
    val GRID_Voltage_RY: Double,
    val GRID_Voltage_YB: Double,
    val GRID_Voltage_BR: Double,
    val GRID_Active_Power_RYB: Double,
    val GRID_Active_Total_Import: Double,
    val GRID_Active_Total_Export: Double,
    val DG1_Voltage_RY: Double,
    val DG1_Voltage_YB: Double,
    val DG1_Voltage_BR: Double,
    val DG1_Active_Power_RYB: Double,
    val DG1_Active_Total_Export: Double,
    val DG2_Voltage_RY: Double,
    val DG2_Voltage_YB: Double,
    val DG2_Voltage_BR: Double,
    val DG2_Active_Power_RYB: Double,
    val Load_Active_Power: Double,
    val PerDay_AvgLoad: Double,
    val PerDay_GridOutage_Instance: Int,
    val Grid_Export_Energy_Today: Double,
    val Grid_Import_Energy_Today: Double,
    val DG1_Export_Energy_Today: Double,
    val DG2_Export_Energy_Today: Double,
    val DG_Export_Energy_Today: Double,
    val Total_Plant_Export_Today: Double,
    val diesel_save: Double,
    val cost_diesel_save: Double,
    val co2_emission: Double,
    val GRID_Resumption: Int,
    val FW_Version_No: String,
    val Grid_outage_duration: Int,
    val created_at: String,
    val DG2_Active_Total_Export: Double,
    val PVI_Total_Active_Power: Double,
    val PVI_Curtailed_Percentage: Double,
    val PVI_Total_Gen_Today: Double,
    val PVI_Total_Gen_Lifetime: Double,
    val PVI1_Active_Power: Double,
    val PVI1_Inverter_State: Int,
    val PVI2_Active_Power: Double,
    val PVI2_Inverter_State: Int,
    val PVI3_Active_Power: Double,
    val PVI3_Inverter_State: Int,
    val PVI4_Active_Power: Double,
    val PVI4_Inverter_State: Int,
    val PVI5_Active_Power: Double,
    val PVI5_Inverter_State: Int,
    val PVI6_Active_Power: Double,
    val PVI6_Inverter_State: Int,
    val PVI7_Active_Power: Double,
    val PVI7_Inverter_State: Int,
    val charging_cycles: Double,
    val discharging_cycles: Double,
    val total_cycle_count: Double,
    val PVI_Generation_Offgrid: Double,
    val PVI_Runtime_Offgrid: Double,
    val PVI8_Active_Power: Double,
    val Inverter8_State: Int,
    val PVI9_Active_Power: Double,
    val Inverter9_State: Int,
    val PVI10_Active_Power: Double,
    val Inverter10_State: Int,
    val PVI11_Active_Power: Double,
    val Inverter11_State: Int,
    val PVI12_Active_Power: Double,
    val Inverter12_State: Int,
    val PVI13_Active_Power: Double,
    val Inverter13_State: Int,
    val PVI14_Active_Power: Double,
    val Inverter14_State: Int
)