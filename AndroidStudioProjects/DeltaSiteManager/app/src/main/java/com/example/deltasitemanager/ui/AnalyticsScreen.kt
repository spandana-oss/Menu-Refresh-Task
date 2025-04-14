package com.example.deltasitemanager.ui
import android.app.DatePickerDialog
import android.widget.DatePicker
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.navigation.NavController
import com.github.mikephil.charting.charts.LineChart
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun AnalyticsScreen(navController: NavController) {
    val context = LocalContext.current

    var selectedDevice by remember { mutableStateOf("PCS") }
    var selectedParameter by remember { mutableStateOf("") }
    var selectedDate by remember { mutableStateOf(Calendar.getInstance()) }
    val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
    val selectedDateString = remember { mutableStateOf(dateFormat.format(selectedDate.time)) }

    var displayType by remember { mutableStateOf("Graph") }
    var showData by remember { mutableStateOf(false) }

    val parameterOptions = when (selectedDevice) {
        "PCS" -> listOf("PCS Active Power", "PCS Import Energy", "PCS Export Energy")
        "Battery" -> listOf("Battery Voltage", "Battery Current", "Battery Power", "Battery SOC")
        "Load" -> listOf("Load Active Power", "Load Import Energy", "Average Load")
        "Grid" -> listOf("Grid Active Power", "Grid Import Energy", "Grid Export Energy", "Grid Outage")
        "DG" -> listOf("DG1 Active Power", "DG2 Active Power", "DG Export Energy")
        else -> emptyList()
    }

    var entries by remember { mutableStateOf(emptyList<Entry>()) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Analytics") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(modifier = Modifier.padding(padding).padding(16.dp)) {

            // Device selection
            DropdownMenuSelector("Device", selectedDevice, listOf("PCS", "Battery", "Load", "Grid", "DG")) {
                selectedDevice = it
                selectedParameter = ""
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Parameter selection
            DropdownMenuSelector("Parameter", selectedParameter, parameterOptions) {
                selectedParameter = it
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Date picker
            Button(onClick = {
                val now = Calendar.getInstance()
                DatePickerDialog(
                    context,
                    { _: DatePicker, year: Int, month: Int, day: Int ->
                        selectedDate.set(year, month, day)
                        selectedDateString.value = dateFormat.format(selectedDate.time)
                    },
                    now.get(Calendar.YEAR),
                    now.get(Calendar.MONTH),
                    now.get(Calendar.DAY_OF_MONTH)
                ).show()
            }) {
                Text("Select Date: ${selectedDateString.value}")
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Display type toggle
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("View As: ")
                Spacer(modifier = Modifier.width(8.dp))
                Button(onClick = { displayType = "Table" }) { Text("Table") }
                Spacer(modifier = Modifier.width(8.dp))
                Button(onClick = { displayType = "Graph" }) { Text("Graph") }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Go button to generate data
            Button(onClick = {
                // Generate dummy data (replace with API later)
                entries = (0..23).map { hour ->
                    Entry(hour.toFloat(), (10..100).random().toFloat())
                }
                showData = true
            }) {
                Text("Go")
            }

            Spacer(modifier = Modifier.height(16.dp))

            if (showData && selectedParameter.isNotBlank()) {
                if (displayType == "Graph") {
                    AndroidView(factory = { context ->
                        LineChart(context).apply {
                            val dataSet = LineDataSet(entries, selectedParameter).apply {
                                color = android.graphics.Color.BLUE
                                valueTextColor = android.graphics.Color.BLACK
                                lineWidth = 2f
                                setDrawCircles(false)
                            }
                            data = LineData(dataSet)
                            xAxis.position = XAxis.XAxisPosition.BOTTOM
                            description.isEnabled = false
                            axisRight.isEnabled = false
                            invalidate()
                        }
                    }, modifier = Modifier.fillMaxWidth().height(300.dp))
                } else {
                    // Table View
                    Column {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Color.LightGray)
                                .padding(8.dp)
                        ) {
                            Text("Hour", modifier = Modifier.weight(1f))
                            Text("Value", modifier = Modifier.weight(1f))
                            Text("Unit", modifier = Modifier.weight(1f))
                        }
                        entries.forEachIndexed { hour, entry ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .border(0.5.dp, Color.Gray)
                                    .padding(8.dp)
                            ) {
                                Text("$hour", modifier = Modifier.weight(1f))
                                Text("${entry.y.toInt()}", modifier = Modifier.weight(1f))
                                Text(getUnit(selectedParameter), modifier = Modifier.weight(1f))
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun DropdownMenuSelector(label: String, selected: String, options: List<String>, onSelect: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }

    Column {
        Text(label)
        Box {
            Button(onClick = { expanded = true }) {
                Text(selected.ifEmpty { "Select $label" })
            }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                options.forEach { option ->
                    DropdownMenuItem(onClick = {
                        onSelect(option)
                        expanded = false
                    }) {
                        Text(option)
                    }
                }
            }
        }
    }
}

// Helper to return unit based on parameter
fun getUnit(param: String): String {
    return when {
        param.contains("Power", true) -> "kW"
        param.contains("Energy", true) -> "kWh"
        param.contains("Voltage", true) -> "V"
        param.contains("Current", true) -> "A"
        param.contains("SOC", true) -> "%"
        param.contains("Load", true) -> "kW"
        else -> ""
    }
}
