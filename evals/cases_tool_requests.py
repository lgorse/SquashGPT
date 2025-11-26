
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
valid_date = date.today()+timedelta(days=2)
invalid_date = date.today()+timedelta(days=7)

tomorrow_str = tomorrow.strftime("%B %-d")
valid_date_str = valid_date.strftime("%B %-d")
invalid_date_str = invalid_date.strftime("%B %-d")

scenario_json = [
  {
    "scenario": "Call booking function for correct booking request",
    "category": "tool_request",
    "user_query": "Yes, please book it",
    "conversation_context": [
      {"role": "user", "content": "Book court 3 tomorrow at 6 pm"},
      {"role": "assistant", "content": "I'll book court 3 "+str(tomorrow_str)+" at 6 PM. Should I proceed with this booking?"}
    ],
    "expected_behavior": "Should call book_court tool with correct parameters"
  },
  {
    "scenario": "Call cancel function for correct cancellation request",
    "category": "tool_request",
    "user_query": "Confirm",
    "conversation_context": [
      {"role": "user", "content": "Cancel my booking on "+str(valid_date)+" at 5:15pm"},
      {"role": "assistant", "content": "I'll cancel your booking for "+valid_date_str+" at 5:15 PM. Should I proceed?"}
    ],
    "expected_behavior": "Should call delete_booking tool with correct date"
  }
]
