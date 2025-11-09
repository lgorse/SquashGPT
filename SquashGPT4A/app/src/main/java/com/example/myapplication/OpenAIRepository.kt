//asst_aA9PbdNVLRxjGwm6Ge6DGaKr

package com.example.squashgpt4a

import com.aallam.openai.api.BetaOpenAI
import com.aallam.openai.api.assistant.AssistantId
import com.aallam.openai.api.chat.ToolId
import com.aallam.openai.api.core.Role
import com.aallam.openai.api.core.Status
import com.aallam.openai.api.message.MessageContent
import com.aallam.openai.api.message.MessageRequest
import com.aallam.openai.api.run.RunId
import com.aallam.openai.api.run.RunRequest
import com.aallam.openai.api.run.ToolOutput
import com.aallam.openai.api.thread.ThreadId
import com.aallam.openai.api.thread.ThreadRequest
import com.aallam.openai.client.OpenAI
import kotlinx.coroutines.delay
import kotlinx.coroutines.yield
import kotlinx.serialization.json.*
import java.time.LocalDate
import kotlin.coroutines.cancellation.CancellationException

@OptIn(BetaOpenAI::class)
class OpenAIRepository(private val openAI: OpenAI) {

    private var currentThreadId: ThreadId? = null
    private val assistantId = AssistantId("asst_aA9PbdNVLRxjGwm6Ge6DGaKr")
    private val bookingAPI = BookingAPIService()
    private val today = LocalDate.now().toString()

    private var cancellationHandler: (suspend () -> Unit)? = null

    var onLoadingStateChanged: ((LoadingType?) -> Unit)? = null


    suspend fun sendMessage(userMessage: String): String {
        return try {
            // Signal SquashGPT processing started
            onLoadingStateChanged?.invoke(LoadingType.SQUASHGPT)

            // Create thread if needed
            if (currentThreadId == null) {
                val thread = openAI.thread(request = ThreadRequest())
                currentThreadId = thread.id

                // Check if cancelled
                yield()

                openAI.message(
                    threadId = currentThreadId!!,
                    request = MessageRequest(
                        role = Role.User,
                        content = userMessage
                    )
                )
            } else {
                openAI.message(
                    threadId = currentThreadId!!,
                    request = MessageRequest(
                        role = Role.User,
                        content = userMessage
                    )
                )
            }

            yield()

            // Run the assistant
            var run = openAI.createRun(
                threadId = currentThreadId!!,
                request = RunRequest(
                    assistantId = assistantId,
                    instructions = "Today is $today. You always specify weekdays when mentioning bookings.")
            )

            // Set up cancellation handler for this run
            val threadId = currentThreadId!!
            val runId = run.id
            cancellationHandler = {
                try {
                    openAI.cancel(threadId = threadId, runId = runId)
                } catch (e: Exception) {
                    // Ignore errors
                }
            }

            // Check if cancelled right after setting handler
            yield()

            // Poll until completion or action required
            while (run.status == Status.Queued ||
                run.status == Status.InProgress ||
                run.status == Status.RequiresAction) {

                // Check if cancelled
                yield()

                // Handle function calls
                if (run.status == Status.RequiresAction && run.requiredAction != null) {

                    // Signal API processing when tool calls are detected
                    onLoadingStateChanged?.invoke(LoadingType.API)

                    // Get run steps to access tool calls
                    val steps = openAI.runSteps(threadId = currentThreadId!!, runId = run.id)
                    val toolOutputs = mutableListOf<ToolOutput>()

                    // Check if cancelled before each API call
                    yield()

                    for (step in steps) {
                        val stepDetails = step.stepDetails
                        if (stepDetails is com.aallam.openai.api.run.ToolCallStepDetails) {
                            val toolCalls = stepDetails.toolCalls
                            if (toolCalls != null) {
                                for (toolCall in toolCalls) {
                                    if (toolCall is com.aallam.openai.api.run.ToolCallStep.FunctionTool) {
                                        val functionName = toolCall.function.name
                                        val arguments = toolCall.function.arguments

                                        // Execute the function
                                        val result = executeFunctionCall(functionName, arguments)

                                        toolOutputs.add(
                                            ToolOutput(
                                                toolCallId = ToolId(toolCall.id.id),
                                                output = result
                                            )
                                        )
                                    }
                                }
                            }
                        }
                    }

                    if (toolOutputs.isNotEmpty()) {

                        // Back to SquashGPT processing after API calls complete
                        onLoadingStateChanged?.invoke(LoadingType.SQUASHGPT)

                        // Submit tool outputs
                        openAI.submitToolOutput(
                            threadId = currentThreadId!!,
                            runId = run.id,
                            output = toolOutputs
                        )
                    }
                }

                delay(1000)
                run = openAI.getRun(threadId = currentThreadId!!, runId = run.id)
            }

            cancellationHandler = null

            // Clear loading state
            onLoadingStateChanged?.invoke(null)

            if (run.status != Status.Completed) {
                return "Error: Run status is ${run.status}"
            }

            // Get response
            val messagesList = openAI.messages(threadId = currentThreadId!!)
            val lastMessage = messagesList.firstOrNull()

            if (lastMessage != null) {
                val content = lastMessage.content.firstOrNull()
                if (content is MessageContent.Text) {
                    return content.text.value
                }
            }

            return "No response received"
        } catch (e: CancellationException) {
            cancellationHandler?.invoke()
            cancellationHandler = null
            onLoadingStateChanged?.invoke(null)
            throw e // Re-throw to propagate cancellation
        } catch (e: Exception) {
            cancellationHandler = null
            onLoadingStateChanged?.invoke(null)
            "Error: ${e.message}"
        }
    }

    /**
     * Routes function calls to appropriate API methods
     */
    private suspend fun executeFunctionCall(functionName: String, arguments: String): String {
        return try {
            val json = Json.parseToJsonElement(arguments).jsonObject

            when (functionName) {
                "get_bookings" -> {
                    bookingAPI.getBookings()
                }

                "book_court" -> {
                    val date = json["date"]?.jsonPrimitive?.content
                        ?: return """{"error": "Missing date"}"""
                    val time = json["time"]?.jsonPrimitive?.content
                        ?: return """{"error": "Missing time"}"""

                    bookingAPI.createBooking(date, time)
                }

                "delete_booking" -> {
                    val date = json["date"]?.jsonPrimitive?.content
                        ?: return """{"error": "Missing date"}"""

                    bookingAPI.deleteBooking(date)
                }

                else -> {
                    """{"error": "Unknown function: $functionName"}"""
                }
            }

        } catch (e: Exception) {
            """{"error": "Function execution failed: ${e.message}"}"""
        }
    }

    suspend fun cancelCurrentRun() {
        cancellationHandler?.invoke()
        cancellationHandler = null
        onLoadingStateChanged?.invoke(null)
    }



    fun clearThread() {
        currentThreadId = null
    }

    fun cleanup() {
        bookingAPI.close()
    }
}
