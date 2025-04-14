package com.example.deltasitemanager.network

import com.google.gson.*
import java.lang.reflect.Type

// Generic response class (you can also put this in a separate file if needed)
data class GenericResponse<T>(
    val status: String,
    val message: List<T>
)

// Custom deserializer to handle both single object and array in 'message' field
class GenericResponseDeserializer<T>(private val clazz: Class<T>) : JsonDeserializer<GenericResponse<T>> {
    override fun deserialize(
        json: JsonElement,
        typeOfT: Type,
        context: JsonDeserializationContext
    ): GenericResponse<T> {
        val jsonObject = json.asJsonObject
        val status = jsonObject.get("status").asString
        val messageElement = jsonObject.get("message")

        val messageList: List<T> = when {
            messageElement.isJsonArray -> {
                messageElement.asJsonArray.map { context.deserialize<T>(it, clazz) }
            }
            messageElement.isJsonObject -> {
                listOf(context.deserialize(messageElement, clazz))
            }
            else -> {
                emptyList()
            }
        }

        return GenericResponse(status, messageList)
    }
}
