package com.example.squashgpt4a

data class Message(
    val text: String,
    val isUser: Boolean,
    val timestamp: Long = System.currentTimeMillis(),
    val isLoading: Boolean = false,
    val loadingType: LoadingType? = null
)

enum class LoadingType {
    SQUASHGPT,
    API
}
