// ==========================================
// BookingAPIConfig.kt
// Configure your API endpoints here
// ==========================================
package com.example.squashgpt4a

object BookingAPIConfig {
    const val BASE_URL = "https://squashgpt.up.railway.app"

    // Endpoints
    const val GET_BOOKINGS = "$BASE_URL/reservations"
    const val CREATE_BOOKING = "$BASE_URL/book-courts"
    const val DELETE_BOOKING = "$BASE_URL/booking/delete"
}

