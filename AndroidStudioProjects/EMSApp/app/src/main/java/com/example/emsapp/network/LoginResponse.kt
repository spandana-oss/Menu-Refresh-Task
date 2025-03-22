package com.example.emsapp.network

import com.google.gson.annotations.SerializedName

data class LoginResponse(
    val success: Boolean,
    val message: String,
    @SerializedName("api_key") val token: String?
)
