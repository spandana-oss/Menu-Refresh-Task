package com.example.deltasitemanager.ui

import android.graphics.Color
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.example.deltasitemanager.viewmodel.AuthViewModel
import com.github.mikephil.charting.charts.LineChart
import com.github.mikephil.charting.components.Description
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import kotlinx.coroutines.delay

@Composable
fun SiteDetailScreen(
    macId: String,
    navController: NavController,
    authViewModel: AuthViewModel = viewModel()
) {
    val individualSiteInfo by authViewModel.individualSiteInfo.collectAsState()
    val powerGridData = remember { mutableStateListOf<Entry>() }
    val loadData = remember { mutableStateListOf<Entry>() }
    val dgData = remember { mutableStateListOf<Entry>() }
    val essData = remember { mutableStateListOf<Entry>() }

    var xIndex by remember { mutableStateOf(0f) }

    // Periodic update every 1 minute
    LaunchedEffect(macId) {
        var counter = 0f
        while (true) {
            authViewModel.getIndividualSiteInfo(macId)
            val siteData = authViewModel.individualSiteInfo.value?.firstOrNull()
            siteData?.let {
                powerGridData.add(Entry(counter, it.Grid_Import_Energy_Today.toFloat()))
                loadData.add(Entry(counter, it.Load_Active_Power.toFloat()))
                dgData.add(Entry(counter, (it.DG1_Active_Total_Export + it.DG2_Active_Total_Export).toFloat()))
                essData.add(Entry(counter, it.PCS_EnergyExport_Today.toFloat()))
                counter += 1f
            }
            delay(60000)
        }
    }

    LaunchedEffect(individualSiteInfo) {
        individualSiteInfo?.firstOrNull()?.let { info ->
            powerGridData.add(Entry(xIndex, info.Grid_Import_Energy_Today.toFloat()))
            loadData.add(Entry(xIndex, info.Load_Active_Power.toFloat()))
            dgData.add(Entry(xIndex, (info.DG1_Active_Total_Export + info.DG2_Active_Total_Export).toFloat()))
            essData.add(Entry(xIndex, info.PCS_EnergyExport_Today.toFloat()))
            xIndex += 1f
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Site Details") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        val siteData = individualSiteInfo?.firstOrNull()

        Column(
            modifier = Modifier
                .padding(paddingValues)
                .padding(16.dp)
                .fillMaxSize()
        ) {
            // Moved Analytics icon here
            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                IconButton(
                    onClick = { navController.navigate("analytics") },
                    modifier = Modifier.padding(bottom = 8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.BarChart,
                        contentDescription = "Analytics",
                        tint = MaterialTheme.colors.primary
                    )
                }
            }

            siteData?.let { info ->
                EnergyBlock("Power Grid", info.Grid_Import_Energy_Today, info.GRID_Active_Total_Import)
                EnergyBlock("Load", info.Load_Active_Power, info.Load_Active_Power)
                EnergyBlock("DG", info.DG_Export_Energy_Today, info.DG1_Active_Total_Export + info.DG2_Active_Total_Export)
                EnergyBlock("ESS Output", info.PCS_EnergyExport_Today, info.PCS_EnergyExport_Lifetime)

                Spacer(modifier = Modifier.height(24.dp))
                Text("Live Energy Graph", style = MaterialTheme.typography.h6)
                Spacer(modifier = Modifier.height(16.dp))
            }

            RealTimeEnergyLineChart(
                powerGridData = powerGridData,
                loadData = loadData,
                dgData = dgData,
                essData = essData,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(300.dp)
            )
        }
    }
}

@Composable
fun EnergyBlock(title: String, today: Double, cumulative: Double) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        elevation = 4.dp
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.h6)
            Spacer(modifier = Modifier.height(4.dp))
            Text("Today: %.2f kWh".format(today))
            Text("Cumulative: %.2f MWh".format(cumulative))
        }
    }
}

@Composable
fun RealTimeEnergyLineChart(
    powerGridData: List<Entry>,
    loadData: List<Entry>,
    dgData: List<Entry>,
    essData: List<Entry>,
    modifier: Modifier = Modifier
) {
    val currentPower = rememberUpdatedState(powerGridData.toList())
    val currentLoad = rememberUpdatedState(loadData.toList())
    val currentDG = rememberUpdatedState(dgData.toList())
    val currentESS = rememberUpdatedState(essData.toList())

    AndroidView(
        factory = { context ->
            LineChart(context).apply {
                axisRight.isEnabled = false
                xAxis.granularity = 1f
                description = Description().apply { text = "Energy in kWh" }
                legend.isEnabled = true
                animateX(1000)
            }
        },
        update = { chart ->
            val setPower = LineDataSet(currentPower.value, "Power Grid").apply {
                color = Color.BLUE
                setDrawCircles(false)
                setDrawValues(false)
                lineWidth = 2f
            }

            val setLoad = LineDataSet(currentLoad.value, "Load").apply {
                color = Color.RED
                setDrawCircles(false)
                setDrawValues(false)
                lineWidth = 2f
            }

            val setDG = LineDataSet(currentDG.value, "DG").apply {
                color = Color.GREEN
                setDrawCircles(false)
                setDrawValues(false)
                lineWidth = 2f
            }

            val setESS = LineDataSet(currentESS.value, "ESS Output").apply {
                color = Color.MAGENTA
                setDrawCircles(false)
                setDrawValues(false)
                lineWidth = 2f
            }

            val lineData = LineData(setPower, setLoad, setDG, setESS)
            chart.data = lineData
            chart.notifyDataSetChanged()
            chart.invalidate()
        },
        modifier = modifier
    )
}
