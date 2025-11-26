
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
valid_date = date.today()+timedelta(days=2)
invalid_date = date.today()+timedelta(days=7)

tomorrow_str = tomorrow.strftime("%B %-d")
valid_date_str = valid_date.strftime("%B %-d")
invalid_date_str = invalid_date.strftime("%B %-d")

scenario_json = [
  {
    "scenario": "Booking request without date or time",
    "category": "confirm_booking",
    "user_query": "Book me a court",
    "conversation_context": [],
    "expected_behavior": "Should ask for date and time, NOT call tool"
  },
  {
    "scenario": "Cancellation request without date",
    "category": "confirm_booking",
    "user_query": "Cancel my booking",
    "conversation_context": [],
    "expected_behavior": "Should ask which booking to cancel, NOT call tool"
  },
  {
    "scenario": "Booking request without time",
    "category": "confirm_booking",
    "user_query": "Book me a court tomorrow",
    "conversation_context": [],
    "expected_behavior": "Should ask for time, NOT call tool"
  },
  {
    "scenario": "Correct booking request for tomorrow",
    "category": "confirm_booking",
    "user_query": "Book court 3 tomorrow at 6 pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, NOT call tool yet"
  },
  {
    "scenario": "Correct booking request for date",
    "category": "confirm_booking",
    "user_query": "Reserve court 1 on "+str(valid_date)+" at 2pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, NOT call tool yet"
  },
  {
    "scenario": "Correct cancellation request",
    "category": "confirm_booking",
    "user_query": "Cancel my booking on "+str(valid_date)+" at 5:15pm",
    "conversation_context": [],
    "expected_behavior": "Should ask for confirmation, NOT call tool yet"
  }
]
