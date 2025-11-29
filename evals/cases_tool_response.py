
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
valid_date = date.today()+timedelta(days=2)
invalid_date = date.today()+timedelta(days=7)

tomorrow_str = tomorrow.strftime("%B %-d")
valid_date_str = valid_date.strftime("%B %-d")
invalid_date_str = invalid_date.strftime("%B %-d")

scenario_json = [
  {
    "scenario": "Success: get bookings has courts",
    "category": "tool_response",
    "user_query": "What are my bookings?",
    "tool_response": "{\"status\": \"success\", \"bookings\": [{\"date\": \""+str(tomorrow)+"\", \"time\": \"5:15 pm\", \"status\": null, \"court\": 8}, {\"date\": \""+str(valid_date)+"\", \"time\": \"11:15 am\", \"status\": null, \"court\": 1}]}",
    "expected_behavior": "Should clearly list all bookings with court, date, and time"
  },
  {
    "scenario": "Failure: get bookings has no courts",
    "category": "tool_response",
    "user_query": "What are my bookings?",
    "tool_response": "{\"status\": \"error\", \"message\": \"No slots found\"}",
    "expected_behavior": "Should convey that there are no bookings upcoming."
  },
  {
    "scenario": "Successful booking request",
    "category": "tool_response",
    "user_query": "Yes",
    "conversation_context": [
    {"role": "user", "content": "Book a court tomorrow at 6pm"},
    {"role":"assistant","content":"I'll book a court tomorrow at 6 pm"}],
    "tool_response": "[{\"court\": 3, \"date\": \"" + str(tomorrow) + "\", \"time\": \"18:00\", \"status\" : \"confirmed\"}]",
    "expected_behavior": "Should confirm booking with date, time"
  },
  {
    "scenario": "Failed booking request - no courts",
    "category": "tool_response",
    "user_query": "Yes",
     "conversation_context": [
    {"role": "user", "content": "Book a court tomorrow at 6pm"},
    {"role":"assistant","content":"I'll book a court "+tomorrow_str+" at 6 pm"}],
    "tool_response": "[{\"court\": 3, \"date\": \"" + str(tomorrow) + "\", \"time\": \"18:00\", \"status\" : \"Slots not found\"}]",
    "expected_behavior": "Should explain the failure"
  },
  {
     "scenario": "Failed booking request - too far ahead",
    "category": "tool_response",
     "user_query": "OK",
      "conversation_context": [
    {"role": "user", "content": "Book a court on "+str(invalid_date)+" at 6pm"},
    {"role":"assistant","content":"I'll book a court on "+invalid_date_str+" at 6 pm"}],
    "tool_response": "[{\"court\": 3, \"date\": \"" + str(invalid_date) + "\", \"time\": \"18:00\", \"status\" : \"The reservation you're trying to book is too far ahead in the future\"}]",
    "expected_behavior": "Should explain the failure"
  },
  {
    "scenario": "Failed booking request - double booking",
    "category": "tool_response",
    "user_query": "Confirmed",
     "conversation_context": [
    {"role": "user", "content": "Book a court "+str(valid_date)+" at 6pm"},
    {"role":"assistant","content":"I'll book a court on "+valid_date_str+" at 6 pm"}],
    "tool_response": "[{\"court\": 3, \"date\": \"" + str(valid_date) + "\", \"time\": \"18:00\", \"status\" : \"You have reached your maximum number of courts for this day\"}]",
    "expected_behavior": "Should explain the failure"
  },
  {
    "scenario": "Successful cancellation request",
    "category": "tool_response",
    "user_query": "Yes",
    "conversation_context": [
    {"role": "user", "content": "Cancel my court tomorrow at 6pm"},
    {"role":"assistant","content":"I'll cancel your court tomorrow."}],
    "tool_response": "{\"court\": 3, \"date\": \"" + str(tomorrow) + "\", \"time\": \"18:00\", \"court\": 1, \"status\": \"Cancellation Confirmed\"}",
    "expected_behavior": "Should inform the user that the cancellation was successful."
  },
  {
    "scenario": "Failed Cancellation request - no booking found",
    "category": "tool_response",
   "user_query": "Yes",
     "conversation_context": [
    {"role": "user", "content": "Cancel my booking tomorrow."},
    {"role":"assistant","content":"Cancel your booking tomorrow "+tomorrow_str+" ?"}],
    "tool_response": "{\"status\": \"error\", \"message\": \"slot not found\"}",
    "expected_behavior": "Should explain the failure"
  }
]
