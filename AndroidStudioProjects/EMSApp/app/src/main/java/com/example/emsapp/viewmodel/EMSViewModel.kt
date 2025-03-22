package com.example.emsapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.emsapp.network.LoginRequest
import com.example.emsapp.network.LoginResponse
import com.example.emsapp.network.RetrofitClient
import kotlinx.coroutines.launch
import retrofit2.Response
import android.util.Log

class EMSViewModel : ViewModel() {

    // Function to get API Key (Replace with actual secure storage)
    private fun getApiKey(): String {
        return "Bearer cf0663c5bec627741b32"  // Replace with actual API key handling
    }

    // Function to perform login
    fun login(username: String, password: String, onResult: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            var response: Response<LoginResponse>? = null  // Declare response outside try

            try {
                val apiKey = getApiKey()
                Log.d("LoginDebug", "Sending username: $username, password: $password")

                response = RetrofitClient.apiService.login(username, password).execute() // Execute synchronously

                if (response.isSuccessful) {
                    val loginResponse = response.body()
                    Log.d("LoginSuccess", "Message: ${loginResponse?.message}, Token: ${loginResponse?.token}")

                    if (loginResponse?.success == true) {
                        onResult(true, loginResponse.token)
                    } else {
                        Log.e("LoginError", "Login failed: ${loginResponse?.message}")
                        onResult(false, loginResponse?.message)
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e("LoginError", "Server error: $errorBody")
                    onResult(false, "Server error: $errorBody")
                }
            } catch (e: Exception) {
                Log.e("LoginException", "Unexpected error", e) // ✅ Prints full stack trace
                onResult(false, "Unexpected error: ${e.localizedMessage}")
            } finally {
                response?.errorBody()?.close() // Close response body safely
            }
        }
    }

}