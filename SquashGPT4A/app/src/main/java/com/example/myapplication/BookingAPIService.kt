// ==========================================
// BookingAPIService.kt
// Handles all HTTP calls to your booking API
// ==========================================
package com.example.squashgpt4a

import io.ktor.client.*
import io.ktor.client.engine.android.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json

class BookingAPIService {

    private val httpClient = HttpClient(Android) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                prettyPrint = true
            })
        }
    }

    /**
     * Get all bookings
     * Returns: {"response_data": "[{...}]", "status_code": 200}
     */
    suspend fun getBookings(): String {
        return try {
            val response: HttpResponse = httpClient.get(BookingAPIConfig.GET_BOOKINGS) {
                contentType(ContentType.Application.Json)
            }

            response.bodyAsText()

        } catch (e: Exception) {
            """{"error": "Failed to get bookings: ${e.message}"}"""
        }
    }

    /**
     * Create a new booking
     * Your API expects: {"bookings": [{"date": "2025-11-08", "time": "18:00", "status": null}]}
     */
    suspend fun createBooking(
        date: String,
        time: String
    ): String {
        return try {
            val response: HttpResponse = httpClient.post(BookingAPIConfig.CREATE_BOOKING) {
                contentType(ContentType.Application.Json)
                setBody("""
                    {
                        "bookings": [
                            {
                                "date": "$date",
                                "time": "$time",
                                "status": null
                            }
                        ]
                    }
                """.trimIndent())
            }

            response.bodyAsText()

        } catch (e: Exception) {
            """{"error": "Failed to create booking: ${e.message}"}"""
        }
    }

    /**
     * Create multiple bookings at once
     */
    suspend fun createMultipleBookings(bookings: List<Pair<String, String>>): String {
        return try {
            val bookingsJson = bookings.joinToString(",") { (date, time) ->
                """{"date": "$date", "time": "$time", "status": null}"""
            }

            val response: HttpResponse = httpClient.post(BookingAPIConfig.CREATE_BOOKING) {
                contentType(ContentType.Application.Json)
                setBody("""{"bookings": [$bookingsJson]}""")
            }

            response.bodyAsText()

        } catch (e: Exception) {
            """{"error": "Failed to create bookings: ${e.message}"}"""
        }
    }

    /**
     * Delete a booking by date
     * Uses POST method with: {"params": {"date": "2025-11-08"}}
     */
    suspend fun deleteBooking(date: String): String {
        return try {
            val response: HttpResponse = httpClient.post(BookingAPIConfig.DELETE_BOOKING) {
                contentType(ContentType.Application.Json)
                setBody("""
                    {
                            "date": "$date"
                    }
                """.trimIndent())
            }

            response.bodyAsText()

        } catch (e: Exception) {
            """{"error": "Failed to delete booking: ${e.message}"}"""
        }
    }

    fun close() {
        httpClient.close()
    }
}