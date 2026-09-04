import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from app.agent.tools import TOOL_REGISTRY, execute_tool


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is not set. Please add it to your .env file."
    )


# ============================================================
# OPENROUTER CLIENT
# ============================================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "openai/gpt-4o-mini"


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are Nebula Supermarket's AI operations assistant.

You operate a real Indian kirana/supermarket through tools.

Your job is to understand natural-language requests, reason about them,
select the correct tools, execute business operations, and clearly
communicate the result to the user.

IMPORTANT:
You MUST use tools whenever the answer depends on actual supermarket data.

Never invent:
- product prices
- stock quantities
- GST rates
- HSN codes
- customer balances
- bill totals
- sales figures
- reorder quantities
- invoice information

Always obtain such information from the available tools.

============================================================
BUSINESS DOMAIN
============================================================

The supermarket operates using:
- Indian Rupees (INR)
- Product SKUs
- Quantity and units
- Selling price
- Cost price
- MRP
- GST
- HSN codes
- Customer credit / khata
- Cash, UPI, card and credit payments

============================================================
PRODUCT SEARCH
============================================================

If the user gives a product name rather than a SKU:

1. Use search_products.
2. Examine the returned products.
3. If exactly one product clearly matches, use that product.
4. If multiple products could match, ask the user to clarify.
5. Never guess a SKU.

============================================================
STOCK
============================================================

For stock-related questions always use the appropriate inventory tool.

Never estimate inventory.

If the user asks:
"How much Maggi is left?"

Use search_products first if the SKU is unknown,
then check_stock.

============================================================
BILLING
============================================================

Bills are normally created as draft bills.

Typical workflow:

1. create_bill
2. identify products
3. add_item_to_bill
4. get_bill when needed
5. update_bill_item if the user wants changes
6. finalize_bill when the customer is ready to pay
7. generate_invoice after successful finalization

Never manually invent the final bill total.

============================================================
MULTI-TURN BILLING
============================================================

Users may provide orders over several messages.

Example:

User:
"I need 2 Maggi."

Then:
"Also add one Atta."

Then:
"Actually make Maggi 3."

Maintain bill context from the conversation.

If a bill ID has already been created in the conversation, reuse it.

Do not create a new bill unnecessarily.

============================================================
STOCK SAFETY
============================================================

Never allow overselling.

The business tools enforce stock validation.

If a tool rejects an order because of insufficient stock,
communicate the actual available quantity to the user.

Do not claim that the purchase succeeded if the tool returned failure.

============================================================
FINALIZING BILLS
============================================================

Supported payment modes:
- cash
- upi
- card
- credit

For credit/khata payments:
- A customer must be associated with the bill.
- Never create credit for an unknown customer.

Never say payment succeeded unless finalize_bill succeeds.

============================================================
KHATA / CREDIT
============================================================

Use get_customer_credit to check outstanding credit.

Use record_credit_payment when a customer makes a payment.

Never invent a customer's balance.

============================================================
SALES
============================================================

Use:
- get_sales_summary
- get_daily_sales
- get_daily_close

for sales-related questions.

Never invent sales numbers.

============================================================
REORDER
============================================================

When asked what needs reordering:

Use get_reorder_recommendations.

Do not invent reorder quantities.

============================================================
INVOICE
============================================================

Invoices can only be generated for finalized bills.

If the user requests an invoice:
1. Verify the bill exists.
2. Verify it is finalized.
3. Use generate_invoice.

============================================================
BUSINESS ANALYSIS
============================================================

If the user requests a business analysis, management report,
sales analysis, or presentation:

Use generate_analysis_deck.

============================================================
AMBIGUITY
============================================================

If a request is ambiguous, ask a concise clarification question.

Do not guess.

============================================================
ERROR HANDLING
============================================================

If a tool returns success = false:

Do not pretend the operation succeeded.

Instead, explain the tool's message naturally.

============================================================
RESPONSE STYLE
============================================================

Be:
- concise
- professional
- helpful
- natural
- suitable for a supermarket owner

Use INR formatting where appropriate.

Do not expose internal tool names unless useful.

Do not expose hidden reasoning or chain-of-thought.

============================================================
IMPORTANT TOOL RULE
============================================================

Tools are the source of truth for supermarket data.

Reason about the user's request, select the appropriate tool,
execute it, inspect its result, and continue if another tool is needed.

Do not answer prematurely if a tool is required.
"""


# ============================================================
# OPENAI / OPENROUTER TOOL SCHEMA
# ============================================================

def build_openai_tools():

    tools = []

    for tool_name, tool_info in TOOL_REGISTRY.items():

        description = tool_info.get(
            "description",
            f"Execute the {tool_name} supermarket operation."
        )

        parameters = tool_info.get(
            "parameters",
            {}
        )

        properties = {}
        required = []

        for parameter_name, parameter_info in parameters.items():

            properties[parameter_name] = {
                "type": parameter_info.get("type", "string"),
                "description": parameter_info.get(
                    "description",
                    parameter_name
                )
            }

            if parameter_info.get("required", False):
                required.append(parameter_name)

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": False
                    }
                }
            }
        )

    return tools


# ============================================================
# SERIALIZE TOOL RESULT
# ============================================================

def serialize_tool_result(result):

    try:
        return json.dumps(
            result,
            ensure_ascii=False,
            default=str
        )

    except Exception:

        return json.dumps(
            {
                "success": False,
                "message": str(result)
            },
            ensure_ascii=False
        )


# ============================================================
# CONVERSATION NORMALIZATION
# ============================================================

def normalize_conversation(conversation):

    if conversation is None:
        return []

    if not isinstance(conversation, list):
        raise ValueError(
            "conversation must be a list."
        )

    return conversation.copy()


# ============================================================
# AGENT FUNCTION
# ============================================================

def run_agent(user_message, conversation=None):

    if not user_message or not user_message.strip():

        return {
            "success": False,
            "message": "Please enter a message.",
            "response": "Please enter a message.",
            "conversation": conversation or []
        }

    messages = normalize_conversation(conversation)

    # --------------------------------------------------------
    # Add system prompt
    # --------------------------------------------------------

    has_system_message = any(
        message.get("role") == "system"
        for message in messages
    )

    if not has_system_message:

        messages.insert(
            0,
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        )

    # --------------------------------------------------------
    # Add user message
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_message.strip()
        }
    )

    tools = build_openai_tools()

    # --------------------------------------------------------
    # Agent control loop
    # --------------------------------------------------------

    max_tool_rounds = 5

    for _ in range(max_tool_rounds):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0
            )

        except Exception as e:

            error_message = (
                "I couldn't connect to the AI service. "
                f"Error: {str(e)}"
            )

            return {
                "success": False,
                "message": error_message,
                "response": error_message,
                "conversation": messages
            }

        if not response.choices:

            error_message = (
                "The AI service returned no response."
            )

            return {
                "success": False,
                "message": error_message,
                "response": error_message,
                "conversation": messages
            }

        assistant_message = response.choices[0].message

        # ----------------------------------------------------
        # Add assistant message to conversation
        # ----------------------------------------------------

        assistant_dict = {
            "role": "assistant"
        }

        if assistant_message.content is not None:

            assistant_dict["content"] = (
                assistant_message.content
            )

        if assistant_message.tool_calls:

            assistant_dict["tool_calls"] = []

            for tool_call in assistant_message.tool_calls:

                assistant_dict["tool_calls"].append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                )

        messages.append(assistant_dict)

        # ----------------------------------------------------
        # Final answer
        # ----------------------------------------------------

        if not assistant_message.tool_calls:

            final_response = (
                assistant_message.content
                if assistant_message.content
                else "I couldn't generate a response."
            )

            return {
                "success": True,
                "message": final_response,
                "response": final_response,
                "conversation": messages
            }

        # ----------------------------------------------------
        # Execute tools
        # ----------------------------------------------------

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            raw_arguments = tool_call.function.arguments

            # ------------------------------------------------
            # Check tool
            # ------------------------------------------------

            if tool_name not in TOOL_REGISTRY:

                tool_result = {
                    "success": False,
                    "message": (
                        f"Unknown tool requested: {tool_name}"
                    )
                }

            else:

                # --------------------------------------------
                # Parse arguments
                # --------------------------------------------

                try:

                    arguments = json.loads(
                        raw_arguments
                    )

                    if not isinstance(arguments, dict):

                        raise ValueError(
                            "Tool arguments must be a JSON object."
                        )

                except Exception as e:

                    tool_result = {
                        "success": False,
                        "message": (
                            f"Invalid arguments for tool "
                            f"'{tool_name}': {str(e)}"
                        )
                    }

                else:

                    # ----------------------------------------
                    # Execute business tool
                    # ----------------------------------------

                    try:

                        tool_result = execute_tool(
                            tool_name,
                            arguments
                        )

                    except Exception as e:

                        tool_result = {
                            "success": False,
                            "message": (
                                f"Tool '{tool_name}' failed: "
                                f"{str(e)}"
                            )
                        }

            # ------------------------------------------------
            # Send result back to model
            # ------------------------------------------------

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": serialize_tool_result(
                        tool_result
                    )
                }
            )

    # ========================================================
    # MAXIMUM TOOL ROUNDS
    # ========================================================

    error_message = (
        "I was unable to complete the request within "
        "the allowed number of operations."
    )

    return {
        "success": False,
        "message": error_message,
        "response": error_message,
        "conversation": messages
    }


# ============================================================
# DIRECT CLI TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEBULA SUPERMARKET AI AGENT")
    print("=" * 60)

    print("\nType 'exit' to stop.\n")

    conversation = []

    while True:

        user_input = input("You: ").strip()

        if user_input.lower() in {
            "exit",
            "quit",
            "q"
        }:
            print("Goodbye!")
            break

        if not user_input:
            continue

        result = run_agent(
            user_input,
            conversation
        )

        print("\nAgent:")

        print(result["message"])

        conversation = result["conversation"]

        print()