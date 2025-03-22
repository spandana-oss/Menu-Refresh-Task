package com.example.emsapp.network

import retrofit2.Call
import retrofit2.http.*

interface EMSApiService {
    @FormUrlEncoded // ✅ Ensures form-data instead of JSON
    @POST("mobileapi/login") // ✅ Replace with actual API endpoint
    fun login(
        @Field("username") username: String,  // ✅ Matches form-data keys
        @Field("password") password: String
    ): Call<LoginResponse>
}