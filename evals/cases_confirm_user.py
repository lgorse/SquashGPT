
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
valid_date = date.today()+timedelta(days=2)
invalid_date = date.today()+timedelta(days=7)

tomorrow_str = tomorrow.strftime("%B %-d")
valid_date_str = valid_date.strftime("%B %-d")
invalid_date_str = invalid_date.strftime("%B %-d")

scenario_json = [
  {
    "scenario": "Incorrect: Booking request without date or time",
    "category": "confirmation_request",
    "user_query": "Book me a court",
    "conversation_context": [],
    "expected_behavior": "Should ask for date and time, NOT call tool"
  },
  {
    "scenario": "Incorrect: Booking request without time",
    "category": "confirmation_request",
    "user_query": "Book me a court tomorrow",
    "conversation_context": [],
    "expected_behavior": "Should ask for time, NOT call tool"
  },
  {
    "scenario": "Incorrect: booking request for ineligible time",
    "category": "confirmation_request",
    "user_query": "Book a court tomorrow at 9:15 am",
    "conversation_context": [],
    "expected_behavior": "Should ask the user to correct their request. Should not return a confirmation request OR call the booking tool"
  },
  {
    "scenario": "Correct - infers the correct AM/PM of an ambiguous time request",
    "category": "confirmation_request",
    "user_query": "Book a court tomorrow at 9",
    "conversation_context": [],
    "expected_behavior": "Should confirm with the user as 9 am"
  },
  {
    "scenario": "Correct booking request - relative day",
    "category": "confirmation_request",
    "user_query": "Book a court tomorrow at 3 pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, NOT call tool yet"
  },
  {
    "scenario": "Correct booking request - specific date",
    "category": "confirmation_request",
    "user_query": "Reserve court 1 on "+str(valid_date)+" at 2:15pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, NOT call tool yet"
  },
  {
    "scenario": "Correct booking request - specific weekday",
    "category": "confirmation_request",
    "user_query": "Book a court "+valid_date.strftime("%A")+" at 3 pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, providing the matching date in the format (%B %-d). Should NOT call tool yet"
  },
  {
    "scenario": "Correct booking request with unnecessary information (court number)",
    "category": "confirmation_request",
    "user_query": "Book court 3 tomorrow at 3 pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, and not commit to a specific court. Do NOT call tool yet"
  },
  {
    "scenario": "Incorrect: Cancellation request without date",
    "category": "confirmation_request",
    "user_query": "Cancel my booking",
    "conversation_context": [],
    "expected_behavior": "Should ask which date is the booking, NOT call tool"
  },
  {
    "scenario": "Correct cancellation request - specific date",
    "category": "confirmation_request",
    "user_query": "Cancel my booking on "+str(valid_date),
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation. Should NOT call tool yet"
  },
  {
    "scenario": "Correct cancellation request - relative day",
    "category": "confirmation_request",
    "user_query": "Cancel my booking tomorrow",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, providing tomorrow's date. Should NOT call tool yet"
  },
  {
    "scenario": "Correct cancellation request - specific weekday",
    "category": "confirmation_request",
    "user_query": "Cancel my booking "+valid_date.strftime("%A"),
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, providing the matching date in the format (%B %-d). Should NOT call tool yet"
  },
  {
    "scenario": "Correct cancellation request with unnecessary information (time)",
    "category": "confirmation_request",
    "user_query": "Cancel my booking on "+str(valid_date)+" at 2:15pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, without committing to the specific time. Should NOT call tool yet"
  }
]
