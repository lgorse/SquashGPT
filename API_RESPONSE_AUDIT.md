# SquashGPT API Response Audit

## Current Behavior (as of 2026-05-24)

### 1. **CREATE: `/book-courts` (POST)**

**Success scenarios - ALL return HTTP 200:**
- ✅ Slot found, no toast error → `status: "Booking Confirmed"` (line 167)
- ✅ Slot found, timeout (no toast) → `status: "Booking successful"` (line 174)

**Failure scenarios - ALL return HTTP 200:**
- ❌ No slot found → `status: "No slots found"` (line 243)
- ❌ Toast error (back-to-back, max bookings, etc.) → `status: "<toast text>"` (line 170)
- ❌ Unexpected error → `status: "<error message>"` (line 177, 180)

**Exception scenario - returns HTTP 500:**
- ❌ Python exception → `{"status": "error", "message": "<exception>"}` (line 269)

**Problem:** Success and failures both return 200. Client must parse `status` text to determine outcome.

---

### 2. **READ: `/reservations` (GET)**

**Success - returns HTTP 200:**
- ✅ Returns array of bookings (even if empty array)

**Failure - returns HTTP 500:**
- ❌ Exception → `{"status": "error", "message": "<exception>"}` (line 291)

**This one is correct** - only returns 200 on success.

---

### 3. **DELETE: `/booking/delete` (DELETE/POST)**

**Success scenarios - ALL return HTTP 200:**
- ✅ Booking found and deleted, no toast → `status: "Cancellation Confirmed"` (line 383)
- ✅ Booking found and deleted, timeout → `status: "Cancellation successful"` (line 389)

**Failure scenarios:**
- ❌ Booking not found → **HTTP 500** `{"status": "error", "message": "slot not found"}` (line 348)
- ❌ Toast error → **HTTP 200** `status: "<toast text>"` (line 386)
- ❌ Delete element not found/timeout → **HTTP 200** `status: "Delete element <error>"` (line 394)
- ❌ Other error → **HTTP 200** `status: "<error message>"` (line 398)
- ❌ Exception → **HTTP 500** `{"status": "error", "message": "<exception>"}` (line 351)

**Problem:** Mix of 200 and 500 for different failure types. Inconsistent.

---

## Recommended HTTP Status Codes

### CREATE (`/book-courts`)
- **200** - Booking succeeded
- **404** - No slots available at requested time
- **409** - Conflict (toast errors: back-to-back, max bookings, prime time issues)
- **500** - Server error (exceptions, timeouts)

### READ (`/reservations`)
- **200** - Success (even if empty array) ✅ Already correct
- **500** - Server error ✅ Already correct

### DELETE (`/booking/delete`)
- **200** - Cancellation succeeded
- **404** - Booking not found
- **409** - Cannot cancel (toast errors: too close to start time, etc.)
- **500** - Server error (exceptions, timeouts)

---

## Implementation Plan

### Phase 1: Add `success` boolean to responses (backward compatible)
```python
# In reserve_slot()
return True, "Booking Confirmed"   # Success
return False, "No slots found"      # Failure

# In book_courts()
confirmations = book_slots(bookings, driver)
for confirmation in confirmations:
    confirmation.success = booking_status[0]  # Add boolean field

# Update Booking.to_dict()
def to_dict(self):
    return {
        "date": self.date,
        "time": self.time,
        "status": self.status,
        "court": self.court,
        "success": self.success  # NEW FIELD
    }
```

### Phase 2: Return proper HTTP codes (breaking change)
```python
# In book_slots(), track success/failure types
if not slot:
    return (False, "No slots found", 404)
if toast_error:
    return (False, toast_text, 409)

# In book_courts()
if any failure is 404:
    return response, 404
if any failure is 409:
    return response, 409
if all success:
    return response, 200
```

---

## Implementation Status

**✅ Phase 1 Complete (May 24, 2026):**
- Added `success: boolean` field to Booking class
- Updated `book_slots()` to store success boolean from tuple
- Updated `book_courts()` to return proper HTTP codes:
  - 200: All bookings succeeded
  - 404: All failures are "No slots found"
  - 409: Any toast errors or mixed failures
  - 500: Exception occurred
- Updated `delete_booking()` to return proper HTTP codes:
  - 200: Cancellation succeeded
  - 404: Booking not found
  - 409: Cannot cancel (toast error/element issue)
  - 500: Exception occurred

**Response format now includes:**
```json
{
  "date": "2026-05-27",
  "time": "6:00 pm",
  "status": "Booking Confirmed",
  "court": null,
  "success": true
}
```

**Next Steps:**
- Update MCP server to check `success` boolean instead of parsing status text
- Test all scenarios (success, no slots, toast errors, not found)
