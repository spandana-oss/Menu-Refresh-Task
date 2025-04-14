package com.example.deltasitemanager.network

import com.example.deltasitemanager.models.LoginResponse
import com.example.deltasitemanager.models.SiteInfoResponse
import okhttp3.RequestBody
import retrofit2.http.*
import retrofit2.Response
import com.example.deltasitemanager.models.GenericResponse
import com.example.deltasitemanager.models.IndividualSiteInfo
interface ApiService {

    @Multipart
    @POST("login")
    suspend fun login(
        @Part("username") username: RequestBody,
        @Part("password") password: RequestBody
    ): LoginResponse

    @FormUrlEncoded
    @POST("getsiteinfo")
    suspend fun getSiteInfo(
        @Field("Authorization") apiKey: String
    ): Response<SiteInfoResponse>

    @FormUrlEncoded
    @POST("getindividualsiteinfo")
    suspend fun getIndividualSiteInfo(
        @Field("Authorization") apiKey: String,
        @Field("macid") macId: String
    ): Response<GenericResponse<IndividualSiteInfo>>

}
