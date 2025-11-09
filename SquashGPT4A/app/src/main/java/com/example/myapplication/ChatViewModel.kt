package com.example.squashgpt4a

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aallam.openai.client.OpenAI
import com.aallam.openai.client.OpenAIConfig
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlin.coroutines.cancellation.CancellationException

class ChatViewModel : ViewModel() {

    private val config = OpenAIConfig(
        token = "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",
        headers = mapOf("OpenAI-Beta" to "assistants=v2")
    )
    private val openAI = OpenAI(config)

    private val repository = OpenAIRepository(openAI).apply {
        // Set up the callback to handle loading state changes
        onLoadingStateChanged = { loadingType ->
            updateLoadingMessage(loadingType)
        }
    }

    private val _messages = MutableStateFlow<List<Message>>(emptyList())
    val messages: StateFlow<List<Message>> = _messages

    private var currentJob: Job? = null

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading


    fun sendMessage(text: String) {
        if (text.isBlank()) return

        // Add user message
        val userMessage = Message(text = text, isUser = true)
        _messages.value = _messages.value + userMessage

        // Show loading
        _isLoading.value = true

        // Send to OpenAI
        currentJob = viewModelScope.launch {
            try {
                val response = repository.sendMessage(text)

                // Add assistant response
                val assistantMessage = Message(text = response, isUser = false)
                _messages.value = _messages.value + assistantMessage
            }catch (e: CancellationException) {
                // Remove loading messages on cancellation
                _messages.value = _messages.value.filterNot { it.isLoading }

                val cancelMessage = Message(text = "Request cancelled", isUser = false)
                _messages.value = _messages.value + cancelMessage
            } finally {
                // Hide loading
                _isLoading.value = false
            }

        }

    }

    private fun updateLoadingMessage(loadingType: LoadingType?) {
        // Remove any existing loading messages
        _messages.value = _messages.value.filterNot { it.isLoading }

        // Add new loading message if needed
        if (loadingType != null) {
            val loadingMessage = Message(
                text = "",
                isUser = false,
                isLoading = true,
                loadingType = loadingType
            )
            _messages.value = _messages.value + loadingMessage
        }
    }

    fun stopProcessing() {
        viewModelScope.launch {
            repository.cancelCurrentRun()  // Cancel on OpenAI's side
            currentJob?.cancel()
            currentJob = null
            _messages.value = _messages.value.filterNot { it.isLoading }
            _isLoading.value = false
        }
    }

    fun clearConversation() {
        repository.clearThread()
        _messages.value = emptyList()
    }



}