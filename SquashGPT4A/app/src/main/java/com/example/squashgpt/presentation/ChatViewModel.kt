package com.example.squashgpt.presentation

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.squashgpt.data.api.ChatRequest
import com.example.squashgpt.data.api.ClearRequest
import com.example.squashgpt.data.api.SquashAPI
import com.example.squashgpt.domain.model.ChatMessage
import com.example.squashgpt.domain.model.LoadingState
import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.BufferedReader

class ChatViewModel(
    private val api: SquashAPI,
    private val userId: String
) : ViewModel() {

    private val _messages = MutableLiveData<List<ChatMessage>>(emptyList())
    val messages: LiveData<List<ChatMessage>> = _messages

    private val _loadingState = MutableLiveData<LoadingState>(LoadingState.Idle)
    val loadingState: LiveData<LoadingState> = _loadingState

    private val gson = Gson()

    fun sendMessage(message: String) {
        if (message.isBlank()) return

        // Add user message
        addMessage(ChatMessage(text = message, isUser = true))

        // Send to backend
        viewModelScope.launch {
            try {
                _loadingState.value = LoadingState.ApiProcessing

                val response = withContext(Dispatchers.IO) {
                    api.sendMessage(ChatRequest(userId, message)).execute()
                }

                if (response.isSuccessful) {
                    response.body()?.let { responseBody ->
                        withContext(Dispatchers.IO) {
                            parseSSEStream(responseBody.byteStream().bufferedReader())
                        }
                    }
                } else {
                    _loadingState.value = LoadingState.Error("Network error: ${response.code()}")
                    removeStreamingMessage()
                }
            } catch (e: Exception) {
                _loadingState.value = LoadingState.Error("Error: ${e.message}")
                removeStreamingMessage()
            }
        }
    }

    fun clearChat() {
        viewModelScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    api.clearChat(ClearRequest(userId)).execute()
                }
                _messages.value = emptyList()
                _loadingState.value = LoadingState.Idle
            } catch (e: Exception) {
                _loadingState.value = LoadingState.Error("Failed to clear chat: ${e.message}")
            }
        }
    }

    private suspend fun parseSSEStream(reader: BufferedReader) {
        var accumulatedText = ""
        var hasStreamingMessage = false

        try {
            reader.use {
                var line: String?
                while (it.readLine().also { line = it } != null) {
                    if (line?.startsWith("data:") == true) {
                        val jsonString = line!!.substring(5).trim()
                        if (jsonString.isNotEmpty()) {
                            try {
                                val json = gson.fromJson(jsonString, JsonObject::class.java)
                                val status = json.get("status")?.asString

                                // Debug logging
                                println("SSE Event - Status: $status, JSON: $jsonString")

                                withContext(Dispatchers.Main) {
                                    when (status) {
                                        "api_processing" -> {
                                            _loadingState.value = LoadingState.ApiProcessing
                                        }
                                        "calling_openai" -> {
                                            _loadingState.value = LoadingState.CallingOpenAI
                                        }
                                        "streaming" -> {
                                            val text = json.get("text")?.asString ?: ""
                                            accumulatedText += text
                                            _loadingState.value = LoadingState.StreamingResponse(accumulatedText)

                                            if (!hasStreamingMessage) {
                                                addMessage(ChatMessage(
                                                    text = accumulatedText,
                                                    isUser = false,
                                                    isStreaming = true
                                                ))
                                                hasStreamingMessage = true
                                            } else {
                                                updateStreamingMessage(accumulatedText)
                                            }

                                            // Small delay to smooth out rendering
                                            delay(5)
                                        }
                                        "tool_call", "executing_tools", "tool_executed",
                                        "tool_error", "tool_not_found", "getting_final_response",
                                        "tool_complete" -> {
                                            // Tool events - keep showing processing
                                            _loadingState.value = LoadingState.ApiProcessing
                                        }
                                        "complete" -> {
                                            if (hasStreamingMessage) {
                                                replaceStreamingMessage(accumulatedText)
                                            } else if (accumulatedText.isNotEmpty()) {
                                                addMessage(ChatMessage(
                                                    text = accumulatedText,
                                                    isUser = false,
                                                    isStreaming = false
                                                ))
                                            }
                                            _loadingState.value = LoadingState.Success(accumulatedText)
                                            _loadingState.value = LoadingState.Idle
                                        }
                                        "error" -> {
                                            val errorMessage = json.get("message")?.asString ?: "Unknown error"
                                            _loadingState.value = LoadingState.Error(errorMessage)
                                            removeStreamingMessage()
                                        }
                                    }
                                }
                            } catch (e: Exception) {
                                // Skip malformed JSON
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            withContext(Dispatchers.Main) {
                _loadingState.value = LoadingState.Error("Stream error: ${e.message}")
                removeStreamingMessage()
            }
        }
    }

    private fun addMessage(message: ChatMessage) {
        val currentMessages = _messages.value.orEmpty().toMutableList()
        currentMessages.add(message)
        _messages.value = currentMessages
    }

    private fun updateStreamingMessage(text: String) {
        val currentMessages = _messages.value.orEmpty().toMutableList()
        val lastIndex = currentMessages.indexOfLast { it.isStreaming }
        if (lastIndex != -1) {
            currentMessages[lastIndex] = currentMessages[lastIndex].copy(text = text)
            _messages.value = currentMessages
        }
    }

    private fun replaceStreamingMessage(text: String) {
        val currentMessages = _messages.value.orEmpty().toMutableList()
        val lastIndex = currentMessages.indexOfLast { it.isStreaming }
        if (lastIndex != -1) {
            currentMessages[lastIndex] = currentMessages[lastIndex].copy(
                text = text,
                isStreaming = false
            )
            _messages.value = currentMessages
        }
    }

    private fun removeStreamingMessage() {
        val currentMessages = _messages.value.orEmpty().toMutableList()
        currentMessages.removeAll { it.isStreaming }
        _messages.value = currentMessages
    }
}
