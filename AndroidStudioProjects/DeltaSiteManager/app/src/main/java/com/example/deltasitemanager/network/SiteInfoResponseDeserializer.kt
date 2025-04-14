package com.example.deltasitemanager.network

import com.example.deltasitemanager.models.SiteInfo
import com.example.deltasitemanager.models.SiteInfoResponse
import com.google.gson.*
import com.google.gson.reflect.TypeToken
import java.lang.reflect.Type

class SiteInfoResponseDeserializer : JsonDeserializer<SiteInfoResponse> {
    override fun deserialize(
        json: JsonElement,
        typeOfT: Type,
        context: JsonDeserializationContext
    ): SiteInfoResponse {
        val jsonObject = json.asJsonObject
        val status = jsonObject["status"].asString
        val messageElement = jsonObject["message"]

        val message: Any = if (messageElement.isJsonArray) {
            val listType = object : TypeToken<List<SiteInfo>>() {}.type
            context.deserialize<List<SiteInfo>>(messageElement, listType)
        } else {
            messageElement.asString
        }

        return SiteInfoResponse(status, message)
    }
}
