package com.example.deltasitemanager.ui

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Dashboard : Screen("dashboard")

    object SiteDetail : Screen("siteDetail?macId={macId}") {
        fun createRoute(macId: String): String = "siteDetail?macId=$macId"
    }

    object Analytics : Screen("analytics")
}
