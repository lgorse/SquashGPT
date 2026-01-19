from openai import OpenAI
from flask import Flask, Response, request, jsonify, stream_with_context
import json
import time
import os
import squash
import court
import perf_logger
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()
client = OpenAI(api_key=os.getenv('openai_api_key'))

# Store conversation history per user
user_conversations = {}

# Your prompt ID from OpenAI dashboard
PROMPT_ID = os.getenv("openai_prompt_id")

AVAILABLE_TOOLS=["get_bookings", "delete_booking", "book_court"]


def stream(request):
    data = request.json
    user_id = data['user_id']
    user_message = data['message']

    previous_response_id = user_conversations.get(user_id)
    today_date = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")

    def generate():
        stream_start = perf_logger.log_perf_start("gpt.stream", user_id)

        yield f"data: {json.dumps({'status': 'api_processing'})}\n\n"
        time.sleep(0.1)

        yield f"data: {json.dumps({'status': 'calling_openai'})}\n\n"
        openai_start = perf_logger.log_perf_start("openai.responses.create", user_id)

        try:
            stream = client.responses.create(
                prompt={"id": PROMPT_ID},
                input=[
                    {"role": "system", "content": f"Today's date is {today_date}."},
                    {"role": "user", "content": user_message}
                ],
                previous_response_id=previous_response_id,
                stream=True
            )
            
            response_id = None
            full_response = ""
            tool_calls = []
            first_event_logged = False


            for event in stream:
                if not first_event_logged and hasattr(event, 'type'):
                    perf_logger.log_perf_end("openai.responses.create", openai_start, user_id)
                    first_event_logged = True
                if not hasattr(event, 'type'):
                    continue
                if event.type == "response.output_text.delta":
                    text_delta = event.delta if hasattr(event, 'delta') else ""
                    full_response += text_delta
                    yield f"data: {json.dumps({'status': 'streaming', 'text': text_delta})}\n\n"
                
                 # Handle tool calls
                elif event.type == "response.output_item.done":
                    if hasattr(event, 'item') and hasattr(event.item, 'type'):
                        if event.item.type == "function_call":
                            # Get the call_id from event.item
                            call_id = event.item.call_id if hasattr(event.item, 'call_id') else event.item.id

                            tool_call = {
                                "id": call_id,
                                "name": event.item.name,
                                "arguments": json.loads(event.item.arguments) if hasattr(event.item, 'arguments') else {}
                            }
                            tool_calls.append(tool_call)
                            yield f"data: {json.dumps({
                                'status': 'tool_call',
                                'tool': tool_call['name'],
                                'arguments': tool_call['arguments']
                            })}\n\n"

                elif event.type == "response.completed":
                    if hasattr(event, 'response'):
                        response_id = event.response.id
                    else:
                        print("DEBUG - response.completed event but no response attribute")

           ## print(f"DEBUG - After stream loop, response_id: {response_id}, tool_calls: {len(tool_calls)}")

            if tool_calls:
                yield f"data: {json.dumps({'status': 'executing_tools'})}\n\n"
                tools_start = perf_logger.log_perf_start("execute_squash", user_id)
                # Execute tools and get final response by yielding from the generator
                for event in execute_squash(tool_calls, response_id, user_id):
                    yield event
                    # Check if this is the final response with the response_id
                    if 'final_response_id' in event:
                        event_data = json.loads(event.split('data: ')[1].strip())
                        if 'final_response_id' in event_data:
                            final_response_id = event_data['final_response_id']
                            user_conversations[user_id] = final_response_id
                            response_id = final_response_id
                perf_logger.log_perf_end("execute_squash", tools_start, user_id)

            elif response_id:
                user_conversations[user_id] = response_id
                print(response_id)
            
            yield f"data: {json.dumps({'status': 'complete', 'response_id': response_id})}\n\n"
            perf_logger.log_perf_end("gpt.stream", stream_start, user_id)

        except Exception as e:
            perf_logger.log_perf_end("gpt.stream", stream_start, user_id)
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )

def clear_chat(request):
    user_id = request.json['user_id']
    user_conversations.pop(user_id, None)
    return jsonify({"status": "cleared"})

def execute_squash(tool_calls, response_id, user_id):

    tool_results = []

    for tool_call in tool_calls:
        tool_name = tool_call['name']

        tool_args = tool_call['arguments']
        # Execute the tool
        if tool_name in AVAILABLE_TOOLS:
            try:
                result = None
                tool_start = perf_logger.log_perf_start(f"tool:{tool_name}", user_id)
                if tool_name == "get_bookings":
                    result = court.my_reservations()
                elif tool_name == "book_court":
                    print(f"tool arguments{tool_args}")
                    result = court.book_courts(tool_args)
                elif tool_name == "delete_booking":
                    result = court.delete_booking(tool_args)
                perf_logger.log_perf_end(f"tool:{tool_name}", tool_start, user_id)
                 
                tool_results.append({
                    "type": "function_call_output",
                    "call_id": tool_call['id'],
                    "output": json.dumps(result)
                })
                
                yield f"data: {json.dumps({
                    'status': 'tool_executed',
                    'tool': tool_name,
                    'result': result
                })}\n\n"
                
            except Exception as e:
                tool_results.append({
                    "type": "function_call_output",
                    "call_id": tool_call['id'],
                    "output": json.dumps({"error": str(e)})
                })
                yield f"data: {json.dumps({
                    'status': 'tool_error',
                    'tool': tool_name,
                    'error': str(e)
                })}\n\n"
        else:
            yield f"data: {json.dumps({
                'status': 'tool_not_found',
                'tool': tool_name
            })}\n\n"

    # Send tool results back to OpenAI for final response (after all tools are executed)
    yield f"data: {json.dumps({'status': 'getting_final_response'})}\n\n"

    final_openai_start = perf_logger.log_perf_start("openai.final_response", user_id)
    # Submit tool outputs by creating a new response with the tool results
    # tool_results is already in the correct format: [{"type": "function_call_output", "call_id": "...", "output": "..."}]
    final_stream = client.responses.create(
        prompt={"id": PROMPT_ID},
        input=tool_results,
        previous_response_id=response_id,
        stream=True
    )


    final_response = ""
    final_response_id = None
    final_first_event = False

    for event in final_stream:
        if not final_first_event and hasattr(event, 'type'):
            perf_logger.log_perf_end("openai.final_response", final_openai_start, user_id)
            final_first_event = True
        if not hasattr(event, 'type'):
            continue

        if event.type == "response.output_text.delta":
            text_delta = event.delta if hasattr(event, 'delta') else ""
            final_response += text_delta
            yield f"data: {json.dumps({'status': 'streaming', 'text': text_delta})}\n\n"

        elif event.type == "response.completed":
            if hasattr(event, 'response'):
                final_response_id = event.response.id

    yield f"data: {json.dumps({'status': 'tool_complete', 'final_response_id': final_response_id})}\n\n"