package com.example.emsapp.ui.theme

import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun DashboardScreen() {
    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Dashboard") })
        }
    ) { paddingValues -> // ✅ Fix: Use 'paddingValues' parameter
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues) // ✅ Apply padding
        ) {
            Text(
                text = "Welcome to Dashboard",
                modifier = Modifier.padding(16.dp)
            )
        }
    }
}
