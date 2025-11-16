package com.example.squashgpt.domain.model

sealed class LoadingState {
    object Idle : LoadingState()
    object ApiProcessing : LoadingState()
    object CallingOpenAI : LoadingState()
    data class StreamingResponse(val text: String) : LoadingState()
    data class Success(val text: String) : LoadingState()
    data class Error(val message: String) : LoadingState()
}
