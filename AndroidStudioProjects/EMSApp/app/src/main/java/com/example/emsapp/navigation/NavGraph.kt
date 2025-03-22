package com.example.emsapp.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.emsapp.ui.theme.LoginScreen
import com.example.emsapp.ui.theme.DashboardScreen

@Composable
fun NavGraph() {
    val navController = rememberNavController() // ✅ Define navController inside Composable
    NavHost(navController = navController, startDestination = "login") {
        composable("login") { LoginScreen(navController) }
        composable("dashboard") { DashboardScreen() }
    }
}
