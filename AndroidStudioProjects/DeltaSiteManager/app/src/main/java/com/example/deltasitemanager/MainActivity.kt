package com.example.deltasitemanager

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.*
import androidx.navigation.NavType
import androidx.navigation.compose.*
import com.example.deltasitemanager.ui.*
import com.example.deltasitemanager.viewmodel.AuthViewModel
import com.example.deltasitemanager.ui.theme.DeltaSiteManagerTheme
import androidx.navigation.navArgument

class MainActivity : ComponentActivity() {
    private val authViewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            DeltaSiteManagerTheme {
                val navController = rememberNavController()
                var isLoggedIn by remember { mutableStateOf(false) }

                NavHost(
                    navController = navController,
                    startDestination = if (isLoggedIn) Screen.Dashboard.route else Screen.Login.route
                ) {
                    composable(Screen.Login.route) {
                        LoginScreen(
                            onLoginSuccess = {
                                isLoggedIn = true
                                navController.navigate(Screen.Dashboard.route) {
                                    popUpTo(Screen.Login.route) { inclusive = true }
                                }
                            },
                            authViewModel = authViewModel
                        )
                    }

                    composable(Screen.Dashboard.route) {
                        DashboardScreen(
                            navController = navController,
                            authViewModel = authViewModel
                        )
                    }

                    composable(
                        route = Screen.SiteDetail.route,
                        arguments = listOf(navArgument("macId") { type = NavType.StringType })
                    ) { backStackEntry ->
                        val macId = backStackEntry.arguments?.getString("macId") ?: ""
                        SiteDetailScreen(
                            macId = macId,
                            navController = navController,
                            authViewModel = authViewModel
                        )
                    }

                    composable(Screen.Analytics.route) {
                        AnalyticsScreen(navController = navController)
                    }
                }
            }
        }
    }
}
