package com.example.emsapp.network

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    private const val BASE_URL = "https://pqr.deltaww.com/BESS/"  // ✅ Replace with actual API base URL

    val apiService: EMSApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create()) // ✅ Converts JSON responses
            .build()
            .create(EMSApiService::class.java)
    }
}