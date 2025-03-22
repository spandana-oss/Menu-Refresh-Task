package com.example.emsapp.network

import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Header
import retrofit2.Response
import com.google.gson.annotations.SerializedName
import retrofit2.Call
import retrofit2.http.*
// API Response Data Class
//data class LoginResponse(
//    val success: Boolean,
//    val message: String,
//    val token: String? = null
//)

// API Request Data Class
data class LoginRequest(
    @SerializedName("username") val email: String,
    @SerializedName("password") val password: String
)

// Retrofit API Service Interface


interface ApiService {
    @FormUrlEncoded
    @POST("mobileapi/login")  // Replace with actual endpoint
    fun login(
        @Header("Authorization") apiKey: String,  // If required
        @Field("username") email: String,
        @Field("password") password: String
    ): Call<LoginResponse>
}
