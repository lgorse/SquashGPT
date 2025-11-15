from openai import OpenAI
from flask import Flask, Response, request, jsonify, stream_with_context
import json
import time
import squash
import court

client = OpenAI(api_key="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")

# Store conversation history per user
user_conversations = {}

# Your prompt ID from OpenAI dashboard
PROMPT_ID = "pmpt_6909acbc497c8195b8b7a10c35d163160154a643cd7833f5"

AVAILABLE_TOOLS=["get_bookings", "delete_booking", "book_court"]


def stream(request):
    data = request.json
    user_id = data['user_id']
    user_message = data['message']
    
    previous_response_id = user_conversations.get(user_id)

    def generate():
        yield f"data: {json.dumps({'status': 'api_processing'})}\n\n"
        time.sleep(0.1)
        
        yield f"data: {json.dumps({'status': 'calling_openai'})}\n\n"
        
        try:
            stream = client.responses.create(
                prompt={"id": PROMPT_ID},
                input=[{"role": "user", "content": user_message}],
                previous_response_id=previous_response_id,
                stream=True
            )
            
            response_id = None
            full_response = ""
            tool_calls = []

            
            for event in stream:
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
                    
            elif response_id:
                user_conversations[user_id] = response_id
                print(response_id)
            
            yield f"data: {json.dumps({'status': 'complete', 'response_id': response_id})}\n\n"
            
        except Exception as e:
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
                if tool_name == "get_bookings":
                    result = court.my_reservations()
                elif tool_name == "book_court":
                    print(f"tool arguments{tool_args}")
                    result = court.book_courts(tool_args)
                elif tool_name == "delete_booking":
                    result = court.delete_booking(tool_args)
                 
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

    for event in final_stream:
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