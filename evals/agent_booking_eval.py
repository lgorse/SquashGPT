"""
Simple SquashGPT Eval - Tests if assistant asks for missing information
Run this once to create the eval, then view results in the dashboard

"""

from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv('openai_api_key'))
GPT_VERSION = 'gpt-5-mini'

# Read your system prompt from file
script_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(script_dir, "gpt_prompt.txt")
test_cases_path = os.path.join(script_dir, "test_cases.json")

with open(prompt_path, "r") as f:
    YOUR_SYSTEM_PROMPT = f.read()

with open(test_cases_path, "r") as f:
    TEST_CASES = json.load(f)

print(f"Loaded prompt from: {prompt_path}")
print(f"Prompt length: {len(YOUR_SYSTEM_PROMPT)} characters")
print(f"Loaded test cases from {test_cases_path}\n")

# Step 1: Create the eval
eval_result = client.evals.create(
    name="SquashGPT Tool Response Communication",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "user_query": {"type": "string"},
                "tool_response": {"type": "string"}
            },
            "required": ["user_query", "tool_response"]
        },
        "include_sample_schema": True,
    },
    testing_criteria=[
        {
            "type": "score_model",
            "name": "Tool Response Communication Grader",
            "model": "gpt-5",
            "input": [
                {
                    "role": "system",
                    "content": """You are evaluating how well the assistant communicates booking results to users.

The assistant received a response from the booking API and must communicate it clearly.

Score as follows:
5 - Excellent: Clearly states success/failure with all key details (booking ID, court, time, date)
4 - Good: States result clearly but missing 1-2 minor details
3 - Adequate: Communicates the result but could be clearer or more complete
2 - Poor: Vague or confusing communication of the result
1 - Failed: Doesn't communicate the result properly or gives wrong information

Key things to check:
- Does it clearly say if the booking succeeded or failed?
- For success: Does it mention the court number, time, and date?
- For failure: Does it explain why and offer to help?
- Is the tone appropriate (friendly, professional)?

Return just the number."""
                },
                {
                    "role": "user",
                    "content": """User requested: {{item.user_query}}

Tool returned: {{item.tool_response}}

Assistant responded: {{sample.output_text}}

Score this (1-5):"""
                }
            ],
            "range": [1, 5],
            "pass_threshold": 4.0,
        }
    ],
)

print(f"✓ Eval created with ID: {eval_result.id}\n")

# Step 2: Pre-generate conversations with tool responses
# This is where you actually run the full conversation flow
print("Generating test conversations with tool responses...")

def run_conversation_with_tool(user_query, tool_response_data):
    """
    Simulates a full conversation: user request → tool call → tool response → agent response
    Returns the final agent response text
    """
    
    # Simulate the conversation
    messages = [
        {"role": "system", "content": YOUR_SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
        # Simulate assistant making a tool call
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "get_bookings",
                        "arguments": '{}'
                    }
                }
            ]
        },
        # Simulate tool response
        {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "content": tool_response_data
        }
    ]
    
    # Now get the agent's final response
    response = client.chat.completions.create(
        model=GPT_VERSION,
        messages=messages,
    )
    
    return response.choices[0].message.content


# Step 3: Filter test cases for this eval
# This eval only tests tool response communication
test_scenarios = [
    {
        "user_query": tc["user_query"],
        "tool_response": tc["tool_response"]
    }
    for tc in TEST_CASES
    if tc["category"] == "tool_response"
]

# Generate the actual responses
test_data = []
for scenario in test_scenarios:
    print(f"  - Testing: {scenario['user_query'][:50]}...")
    
    agent_response = run_conversation_with_tool(
        scenario["user_query"],
        scenario["tool_response"]
    )
    
    test_data.append({
        "item": {
            "user_query": scenario["user_query"],
            "tool_response": scenario["tool_response"]
        },
        "sample": {
            "model": GPT_VERSION,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": agent_response
                    },
                    "finish_reason": "stop"
                }
            ],
            "output_text": agent_response
        }
    })

print(f"\n✓ Generated {len(test_data)} test conversations\n")

# Step 4: Run the eval on pre-generated data
print("Running eval on generated conversations...")
run_result = client.evals.runs.create(
    name="Tool Response Test",
    eval_id=eval_result.id,
    data_source={
        "type": "jsonl",
        "source": {
            "type": "file_content",
            "content": test_data
        }
    }
)

print(f"✓ Run created with ID: {run_result.id}")

# Step 5: Show dashboard link
dashboard_url = f"https://platform.openai.com/evaluations/{eval_result.id}"
print(f"\n{'='*70}")
print(f"🎉 Done! View your results here:")
print(f"\n{dashboard_url}\n")
print(f"{'='*70}")
print(f"\nThis eval tests:")
print(f"  • Success message clarity (2 cases)")
print(f"  • Failure message handling (2 cases)")
print(f"  • Whether agent communicates all key details")
print(f"  • Appropriate tone and helpfulness")