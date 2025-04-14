package com.example.deltasitemanager.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.deltasitemanager.models.IndividualSiteInfo
import com.example.deltasitemanager.models.SiteInfo
import com.example.deltasitemanager.network.ApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaType

class AuthViewModel : ViewModel() {
    private val _apiKey = MutableStateFlow<String?>(null)
    val apiKey: StateFlow<String?> = _apiKey

    private val _siteInfo = MutableStateFlow<List<SiteInfo>?>(null)
    val siteInfo: StateFlow<List<SiteInfo>?> = _siteInfo

    private val _individualSiteInfo = MutableStateFlow<List<IndividualSiteInfo>?>(null)
    val individualSiteInfo: StateFlow<List<IndividualSiteInfo>?> = _individualSiteInfo

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    fun login(username: String, password: String) {
        viewModelScope.launch {
            try {
                val usernamePart = username.toRequestBody("text/plain".toMediaType())
                val passwordPart = password.toRequestBody("text/plain".toMediaType())

                val response = ApiClient.apiService.login(usernamePart, passwordPart)
                if (response.status == "success") {
                    ApiClient.apiKey = response.api_key
                    _apiKey.value = response.api_key
                } else {
                    _error.value = response.message
                }
            } catch (e: Exception) {
                _error.value = "Login failed: ${e.localizedMessage}"
            }
        }
    }

    fun getSiteInfo() {
        viewModelScope.launch {
            val key = _apiKey.value
            if (key.isNullOrBlank()) {
                _error.value = "API Key is missing"
                return@launch
            }

            try {
                val response = ApiClient.apiService.getSiteInfo(apiKey = key)

                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null && body.status == "success") {
                        val message = body.message

                        // Try parsing manually using Gson
                        val gson = com.google.gson.Gson()
                        val jsonElement = gson.toJsonTree(message)

                        if (jsonElement.isJsonArray) {
                            val siteList: List<SiteInfo> = gson.fromJson(
                                jsonElement,
                                object : com.google.gson.reflect.TypeToken<List<SiteInfo>>() {}.type
                            )
                            _siteInfo.value = siteList
                        } else {
                            _error.value = "No site data available"
                        }
                    } else {
                        _error.value = "Failed: ${body?.message ?: "Unknown error"}"
                    }
                } else {
                    _error.value = "API call failed: ${response.code()}"
                }
            } catch (e: Exception) {
                _error.value = "Error fetching site info: ${e.localizedMessage}"
            }
        }
    }

    fun getIndividualSiteInfo(macId: String) {
        viewModelScope.launch {
            val key = _apiKey.value
            if (key.isNullOrBlank()) {
                _error.value = "API Key is missing"
                return@launch
            }

            try {
                val response = ApiClient.apiService.getIndividualSiteInfo(apiKey = key, macId = macId)
                if (response.isSuccessful && response.body()?.status == "success") {
                    val data = response.body()?.message
                    if (data is List<*>) {
                        _individualSiteInfo.value = data.filterIsInstance<IndividualSiteInfo>()
                    } else {
                        _error.value = "Invalid data format in response"
                    }
                } else {
                    _error.value = "Error: ${response.body()?.message}"
                }
            } catch (e: Exception) {
                _error.value = "Exception: ${e.localizedMessage}"
            }
        }
    }

}
