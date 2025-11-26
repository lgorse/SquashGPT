
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
valid_date = date.today()+timedelta(days=2)
invalid_date = date.today()+timedelta(days=7)

tomorrow_str = tomorrow.strftime("%B %-d")
valid_date_str = valid_date.strftime("%B %-d")
invalid_date_str = invalid_date.strftime("%B %-d")

scenario_json = [
  {
    "scenario": "get bookings",
    "category": "tool_response",
    "user_query": "What are my bookings?",
    "tool_response": "{\"status\": \"success\", \"bookings\": [{\"date\": \"2025-11-24\", \"time\": \"5:15 pm\", \"status\": null, \"court\": 8}, {\"date\": \"2025-11-25\", \"time\": \"11:15 am\", \"status\": null, \"court\": 1}, {\"date\": \"2025-11-27\", \"time\": \"10:30 am\", \"status\": null, \"court\": 3}]}",
    "expected_behavior": "Should clearly list all bookings with court, date, and time"
  },
  {
    "scenario": "Successful booking request",
    "category": "tool_response",
    "user_query": "Yes",
    "conversation_context": [
    {"role": "user", "content": "Book a court tomorrow at 6pm"},
    {"role":"assistant","content":"I'll book a court tomorrow at 6 pm"}],
    "tool_response": "{\"status\": \"success\", \"bookings\" : [{\"court\": 3, \"date\": \"" + str(tomorrow) + "\", \"time\": \"18:00\"}]}",
    "expected_behavior": "Should confirm booking with date, time"
  },
  {
    "scenario": "Failed booking request - no courts",
    "category": "tool_response",
    "user_query": "Yes",
     "conversation_context": [
    {"role": "user", "content": "Book a court tomorrow at 6pm"},
    {"role":"assistant","content":"I'll book a court tomorrow at 6 pm"}],
    "tool_response": "{\"status\": \"error\", \"message\": \"Courts not available\"}",
    "expected_behavior": "Should explain the failure"
  },
  {
     "scenario": "Failed booking request - too far ahead",
    "category": "tool_response",
     "user_query": "OK",
      "conversation_context": [
    {"role": "user", "content": "Book court 3 in 5 days at 6pm"},
    {"role":"assistant","content":"I'll book a court on "+invalid_date_str+" at 6 pm"}],
    "tool_response": "{\"status\": \"error\", \"message\": \"You cannot book a court this far into the future\"}",
    "expected_behavior": "Should explain the failure"
  },
  {
    "scenario": "Failed booking request - double booking",
    "category": "tool_response",
    "user_query": "Confirmed",
     "conversation_context": [
    {"role": "user", "content": "Book a court tomorrow at 6pm"},
    {"role":"assistant","content":"I'll book a court tomorrow "+str(valid_date)+" at 6 pm"}],
    "tool_response": "{\"status\": \"error\", \"message\": \"Courts not available\"}",
    "expected_behavior": "Should explain the failure"
  },
  {
    "scenario": "Failed Cancellation request - no booking found",
    "category": "tool_response",
   "user_query": "Yes",
     "conversation_context": [
    {"role": "user", "content": "Cancel my booking tomorrow."},
    {"role":"assistant","content":"Cancel your booking tomorrow "+tomorrow_str+" ?"}],
    "expected_behavior": "Should explain the failure"
  }
]
