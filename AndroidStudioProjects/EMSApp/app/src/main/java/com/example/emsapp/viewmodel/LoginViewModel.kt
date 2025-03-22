package com.example.emsapp.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.emsapp.network.RetrofitClient
import com.example.emsapp.network.LoginResponse
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginViewModel : ViewModel() {

    fun login(username: String, password: String, onResult: (Boolean, String?) -> Unit) {
        val call = RetrofitClient.apiService.login(username, password)

        call.enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                val loginResponse = response.body()
                Log.d("RawAPIResponse", "Received: $loginResponse")

                if (response.isSuccessful && loginResponse != null) {
                    // FIX: If token exists, consider login successful
                    if (loginResponse.success || loginResponse.token != null) {
                        Log.d("LoginSuccess", "Login successful: ${loginResponse.message}")
                        onResult(true, "Login successful!")
                    } else {
                        Log.e("LoginError", "Login failed: ${loginResponse.message}")
                        onResult(false, loginResponse.message ?: "Unknown error")
                    }
                } else {
                    Log.e("LoginError", "Server error: ${response.errorBody()?.string()}")
                    onResult(false, "Server error")
                }
            }



            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                Log.e("LoginError", "API call failed: ${t.message}")
                onResult(false, "API call failed: ${t.localizedMessage}")
            }
        })
    }
}