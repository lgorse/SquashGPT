
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
valid_date = date.today()+timedelta(days=2)
invalid_date = date.today()+timedelta(days=7)

tomorrow_str = tomorrow.strftime("%B %-d")
valid_date_str = valid_date.strftime("%B %-d")
invalid_date_str = invalid_date.strftime("%B %-d")

scenario_json = [
  {
    "scenario": "Call booking function for correct booking request on relative date",
    "category": "tool_request",
    "user_query": "Yes, please book it",
    "conversation_context": [
      {"role": "user", "content": "Book court 3 tomorrow at 3 pm"},
      {"role": "assistant", "content": "I'll book a court "+str(tomorrow_str)+" at 3 PM. Should I proceed with this booking?"}
    ],
    "expected_behavior": "Should call book_court tool with correct parameters"
  },
  {
    "scenario": "Call booking function for correct booking request on fixed date",
    "category": "tool_request",
    "user_query": "Yes, please book it",
    "conversation_context": [
      {"role": "user", "content": "Book a court "+str(valid_date)+" at 3 pm"},
      {"role": "assistant", "content": "I'll book a court "+valid_date_str+" at 3 PM. Should I proceed with this booking?"}
    ],
    "expected_behavior": "Should call book_court tool with correct parameters"
  },
  {
    "scenario": "Call booking function for correct booking request on weekday",
    "category": "tool_request",
    "user_query": "Yes, please book it",
    "conversation_context": [
      {"role": "user", "content": "Book a court "+valid_date.strftime("%A")+" at 1:30pm"},
      {"role": "assistant", "content": "I'll book a court "+valid_date_str+" at 1:30PM. Should I proceed with this booking?"}
    ],
    "expected_behavior": "Should call book_court tool with correct parameters"
  },
  {
    "scenario": "Get user's bookings",
    "category": "tool_request",
    "user_query": "Get my bookings",
    "conversation_context": [],
    "expected_behavior": "Should call the get_bookings function"
  },
  {
    "scenario": "Call cancel function for cancellation request on specific date",
    "category": "tool_request",
    "user_query": "Yes",
    "conversation_context": [
      {"role": "user", "content": "Cancel my booking on "+str(valid_date)+" at 5:15pm"},
      {"role": "assistant", "content": "I'll cancel your booking for "+valid_date_str+". Should I proceed?"}
    ],
    "expected_behavior": "Should call delete_booking tool with correct date"
  },
  {
    "scenario": "Call cancel function for correct cancellation request on relative date",
    "category": "tool_request",
    "user_query": "Confirm",
    "conversation_context": [
      {"role": "user", "content": "Cancel my booking tomorrow"},
      {"role": "assistant", "content": "I'll cancel your booking for "+tomorrow_str+". Should I proceed?"}
    ],
    "expected_behavior": "Should call delete_booking tool with correct date"
  },
  {
    "scenario": "Call cancel function for correct booking request on weekday",
    "category": "tool_request",
    "user_query": "Confirmed",
    "conversation_context": [
      {"role": "user", "content": "Cancel my court on "+valid_date.strftime("%A")},
      {"role": "assistant", "content": "I'll cancel your court on "+valid_date_str+". Please confirm"}
    ],
    "expected_behavior": "Should call book_court tool with correct parameters"
  }

]
