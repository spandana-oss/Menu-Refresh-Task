package com.example.deltasitemanager.network

import com.example.deltasitemanager.models.IndividualSiteInfo
import com.google.gson.GsonBuilder
import com.google.gson.reflect.TypeToken
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {
    private const val BASE_URL = "https://pqr.deltaww.com/BESS/mobileapi/"

    @Volatile
    var apiKey: String? = null

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .build()

    // 👇 Register the generic deserializer for GenericResponse<IndividualSiteInfo>
    private val gson = GsonBuilder()
        .registerTypeAdapter(
            TypeToken.getParameterized(GenericResponse::class.java, IndividualSiteInfo::class.java).type,
            GenericResponseDeserializer(IndividualSiteInfo::class.java)
        )
        .create()

    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(ApiService::class.java)
    }
}
