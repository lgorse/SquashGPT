#!/usr/bin/env python3

import requests
import json
import sys

'''BASE_URL = "http://localhost:5000"'''
BASE_URL = "https://squashgpt.up.railway.app/"
USER_ID = "test_user_interactive"

def chat(message):
    """Send a message and display the streaming response."""
    print(f"\n🎾 You: {message}")
    print("─" * 60)
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "user_id": USER_ID,
            "message": message
        },
        stream=True
    )
    
    print("💬 Assistant: ", end='', flush=True)
    accumulated_text = ""
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data:'):
                data_str = line[5:].strip()
                if data_str:
                    try:
                        data = json.loads(data_str)
                        status = data.get('status')
                        
                        if status == 'api_processing':
                            pass  # Silent
                        elif status == 'calling_openai':
                            pass  # Silent
                        elif status == 'streaming':
                            text = data.get('text', '')
                            accumulated_text += text
                            print(text, end='', flush=True)
                        elif status == 'tool_call':
                            tool = data.get('tool')
                            args = data.get('arguments')
                            print(f"\n🔧 [Calling tool: {tool} with {args}]")
                            print("💬 Assistant: ", end='', flush=True)
                        elif status == 'tool_executed':
                            tool = data.get('tool')
                            result = data.get('result')
                            print(f"\n✅ [Tool {tool} executed: {result.get('success', False)}]")
                            print("💬 Assistant: ", end='', flush=True)
                        elif status == 'executing_tools':
                            print(f"\n⚙️  [Executing tools...]")
                            print("💬 Assistant: ", end='', flush=True)
                        elif status == 'getting_final_response':
                            print(f"\n🤔 [Getting final response...]")
                            print("💬 Assistant: ", end='', flush=True)
                        elif status == 'complete':
                            print()
                        elif status == 'error':
                            print(f"\n❌ Error: {data.get('message')}")
                    except json.JSONDecodeError:
                        pass
    
    print()
    return accumulated_text

def main():
    print("=" * 60)
    print("🎾 SquashGPT Interactive Chat")
    print("=" * 60)
    print("Type your messages and press Enter.")
    print("Commands: 'clear' to reset conversation, 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            # Get user input
            user_input = input("\n🎾 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                response = requests.post(
                    f"{BASE_URL}/clear",
                    json={"user_id": USER_ID}
                )
                print("🗑️  Conversation cleared!")
                continue
            
            # Send message
            print("─" * 60)
            
            response = requests.post(
                f"{BASE_URL}/chat",
                json={
                    "user_id": USER_ID,
                    "message": user_input
                },
                stream=True
            )
            
            print("💬 Assistant: ", end='', flush=True)
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        data_str = line[5:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                status = data.get('status')
                                
                                if status == 'streaming':
                                    text = data.get('text', '')
                                    print(text, end='', flush=True)
                                elif status == 'tool_call':
                                    tool = data.get('tool')
                                    args = data.get('arguments')
                                    print(f"\n🔧 [Tool call: {tool}({args})]")
                                    print("💬 Assistant: ", end='', flush=True)
                                elif status == 'tool_executed':
                                    print(f"\n✅ [Tool executed]")
                                    print("💬 Assistant: ", end='', flush=True)
                                elif status == 'complete':
                                    print()
                                elif status == 'error':
                                    print(f"\n❌ Error: {data.get('message')}")
                            except json.JSONDecodeError:
                                pass
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()