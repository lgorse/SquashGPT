package com.example.squashgpt.data.api

import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Streaming

data class ChatRequest(
    val user_id: String,
    val message: String
)

data class ClearRequest(
    val user_id: String
)

data class ClearResponse(
    val status: String
)

interface SquashAPI {
    @POST("/chat")
    @Streaming
    fun sendMessage(@Body request: ChatRequest): Call<ResponseBody>

    @POST("/clear")
    fun clearChat(@Body request: ClearRequest): Call<ClearResponse>
}
