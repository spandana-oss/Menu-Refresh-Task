package com.example.deltasitemanager.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.example.deltasitemanager.viewmodel.AuthViewModel

@Composable
fun DashboardScreen(
    navController: NavHostController,
    authViewModel: AuthViewModel = viewModel()
) {
    val siteInfo by authViewModel.siteInfo.collectAsState()
    val error by authViewModel.error.collectAsState()

    LaunchedEffect(Unit) {
        authViewModel.getSiteInfo()
    }

    Column(modifier = Modifier
        .fillMaxSize()
        .padding(16.dp)) {

        Text(text = "Site Information", style = MaterialTheme.typography.h6)
        Spacer(modifier = Modifier.height(16.dp))

        LazyColumn {
            siteInfo?.let { list ->
                items(list) { site ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(8.dp)
                            .clickable {
                                navController.navigate(Screen.SiteDetail.createRoute(site.mac_id))
                            },
                        elevation = 4.dp
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("EMS Name: ${site.ems_name}")
                            Text("Sub Name: ${site.sub_name}")
                            Text("Capacity: ${site.capacity}")
                        }
                    }
                }
            }
        }

        error?.let {
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = "Error: $it", color = MaterialTheme.colors.error)
        }
    }
}
