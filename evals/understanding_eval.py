from openai import OpenAI
import os
from dotenv import load_dotenv
import json


AGENT_MODEL = 'gpt-5-mini'
EVALUATOR_MODEL = 'gpt-5'
EVAL_TITLE = "SquashGPT understanding eval"

load_dotenv()
client = OpenAI(api_key=os.getenv('openai_api_key'))

# Read your system prompt from file
script_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(script_dir, "gpt_prompt.txt")
tools_path = os.path.join(script_dir, "tools.json")
test_cases_path = os.path.join(script_dir, "test_cases.json")

with open(prompt_path, "r") as f:
    YOUR_SYSTEM_PROMPT = f.read()

with open(tools_path, "r") as f:
    TOOLS = json.load(f)

with open(test_cases_path, "r") as f:
    TEST_CASES = json.load(f)

print(f"Loaded prompt from: {prompt_path}")
print(f"Prompt length: {len(YOUR_SYSTEM_PROMPT)} characters\n")

print(f"Loaded Tools json from {tools_path}")
print(f"Loaded test cases from {test_cases_path}")

# Step 1: Create the eval
print("Creating eval...")
eval_result = client.evals.create(
    name=EVAL_TITLE,
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "user_query": {"type": "string"},
                "conversation_context": {"type": "array"},  # For multi-turn conversations
                "tool_response": {"type": "string"}  # For tool response scenarios
            },
            "required": ["user_query"]
        },
        "include_sample_schema": True,
    },
    testing_criteria=[
        {
            "type": "score_model",
            "name": EVAL_TITLE,
            "model": EVALUATOR_MODEL,
            "input": [
                {
                    "role": "system",
                    "content": """You are evaluating if the assistant makes correct tool call decisions and communicates tool results properly.

FIRST, review the assistant's system prompt to understand what it's supposed to do:
---
""" + YOUR_SYSTEM_PROMPT + """
---

Based on the system prompt above, evaluate the assistant's behavior.

There are FOUR scenarios:

SCENARIO 1: Missing information (e.g., "Book me a court")
- The assistant MUST ask for missing required information
- For bookings: needs date AND time (and optionally court)
- For deletions: needs date/time or booking identifier
- Score 5: Asks for ALL missing required info clearly, NO tool call made
- Score 4: Asks for some but not all missing info, NO tool call made
- Score 3: Asks unclear questions OR makes a tool call when shouldn't
- Score 2: Makes wrong tool call or doesn't ask for missing info
- Score 1: Gives error or unhelpful response

SCENARIO 2: Complete info, FIRST message (e.g., "Book court 3 tomorrow at 5pm")
- The assistant MUST ask for confirmation before making the tool call
- Score 5: Asks for clear confirmation, NO tool call made yet
- Score 4: Asks for confirmation but unclear, NO tool call made
- Score 3: Makes tool call immediately without asking for confirmation
- Score 2: Asks for more info that was already provided
- Score 1: Gives error or unhelpful response

SCENARIO 3: User confirmed (e.g., user says "Yes" or "Confirm" after being asked)
- The assistant MUST now call the appropriate tool
- Expected tools are listed in the tools arguments of the eval
- Score 5: Calls CORRECT tool with appropriate arguments
- Score 4: Calls correct tool but arguments could be better
- Score 3: Calls WRONG tool
- Score 2: Doesn't call any tool when it should
- Score 1: Gives error or unhelpful response

SCENARIO 4: Tool response received (check if tool_response field is present in item data)
- The assistant received a response from the booking API and must communicate it clearly
- Score 5: Clearly states success/failure with all key details (time, date)
- Score 4: States result clearly but missing 1-2 minor details
- Score 3: Communicates the result but could be clearer or more complete
- Score 2: Vague or confusing communication of the result
- Score 1: Doesn't communicate the result properly or gives wrong information

To check: Look at the full assistant response including tool_calls array.

Return just the number."""
                },
                {
                    "role": "user",
                    "content": """Conversation history:
{{item.conversation_context}}

Current user message: {{item.user_query}}

Tool response (if applicable): {{item.tool_response}}

Full assistant response:
{{sample.choices[0].message}}

Score this (1-5):"""
                }
            ],
            "range": [1, 5],
            "pass_threshold": 4.0,
        }
    ],
)

print(f"✓ Eval created with ID: {eval_result.id}")

"""# Step 2: Filter test cases for this eval
# This eval only tests input understanding (missing_information, needs_confirmation, user_confirmed)
test_cases = [
    {
        "user_query": tc["user_query"],
        "conversation_context": tc.get("conversation_context", [])
    }
    for tc in TEST_CASES
    if tc["category"] in ["missing_information", "needs_confirmation", "user_confirmed"]
]"""

# Step 3: Actually run conversations and generate responses
print("\nGenerating test responses...")

def run_conversation(test_case):
    """Run a conversation with the agent and return the response"""
    # Build messages with conversation history
    messages = [{"role": "system", "content": YOUR_SYSTEM_PROMPT}]

    # Add conversation history if it exists
    if test_case.get("conversation_context"):
        for msg in test_case["conversation_context"]:
            messages.append(msg)

    # Add current user query
    messages.append({"role": "user", "content": test_case["user_query"]})

    # If this is a tool_response scenario, simulate the tool call flow
    if test_case.get("tool_response"):
        # First get the agent's initial response (which should make a tool call)
        initial_response = client.chat.completions.create(
            model=AGENT_MODEL,
            messages=messages,
            tools=TOOLS
        )

        # Add the assistant's tool call to messages
        assistant_msg = {
            "role": "assistant",
            "content": initial_response.choices[0].message.content
        }

        # Only add tool_calls if they exist (don't use empty array)
        if initial_response.choices[0].message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": "call_test123",
                    "type": "function",
                    "function": {
                        "name": "booking_tool",
                        "arguments": '{}'
                    }
                }
            ]

            messages.append(assistant_msg)

            # Add the simulated tool response
            messages.append({
                "role": "tool",
                "tool_call_id": "call_test123",
                "content": test_case["tool_response"]
            })

            # Get the agent's final response after receiving tool output
            response = client.chat.completions.create(
                model=AGENT_MODEL,
                messages=messages,
                tools=TOOLS
            )

            return response.choices[0].message
        else:
            # If no tool call was made, just return the initial response
            return initial_response.choices[0].message
    else:
        # Normal flow for non-tool-response scenarios
        response = client.chat.completions.create(
            model=AGENT_MODEL,
            messages=messages,
            tools=TOOLS
        )

        return response.choices[0].message

# Generate responses for all test cases
eval_data = []
for i, test_case in enumerate(TEST_CASES):
    print(f"  - Testing case {i+1}/{len(TEST_CASES)}: {test_case['user_query'][:50]}...")

    agent_message = run_conversation(test_case)

    # Convert tool_calls to dict if they exist
    tool_calls_dict = None
    if agent_message.tool_calls:
        tool_calls_dict = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            }
            for tc in agent_message.tool_calls
        ]

    # Build item with only schema-compliant fields
    item_data = {
        "user_query": test_case["user_query"],
        "conversation_context": test_case.get("conversation_context", []),
        "tool_response": test_case.get("tool_response", "")
    }

    eval_data.append({
        "item": item_data,
        "sample": {
            "model": AGENT_MODEL,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": agent_message.content,
                        "tool_calls": tool_calls_dict
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    })

print(f"\n✓ Generated {len(eval_data)} test responses\n")

# Step 4: Run the eval on pre-generated responses
print("Running eval on generated responses...")
run_result = client.evals.runs.create(
    name= EVAL_TITLE,
    eval_id=eval_result.id,
    data_source={
        "type": "jsonl",
        "source": {
            "type": "file_content",
            "content": eval_data
        }
    }
)

print(f"✓ Run created with ID: {run_result.id}")

# Step 5: Show dashboard link
dashboard_url = f"https://platform.openai.com/evaluations/{eval_result.id}"
print(f"\n🎉 Done! View your results here:")
print(f"\n{dashboard_url}\n")