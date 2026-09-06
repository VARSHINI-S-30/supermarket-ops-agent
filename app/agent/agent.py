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
# AGENT SETTINGS
# ============================================================

# Maximum number of model -> tool -> model cycles
MAX_TOOL_ROUNDS = 10

# Maximum number of previous conversation messages retained.
# This prevents Telegram memory from growing indefinitely.
MAX_HISTORY_MESSAGES = 40


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
SYSTEM HEALTH
============================================================

A system health tool is available.

When the owner asks about:

- system health
- database health
- whether everything is working
- diagnostics
- stock integrity

use get_system_health.

Do not claim the system is healthy without checking
the tool result.

============================================================
OWNER PREFERENCES
============================================================

The supermarket owner has persistent preferences.

These preferences are stored in the database and are
independent of conversation memory.

Supported preferences:

- default_payment
- preferred_brand
- shop_name
- gstin

============================================================
DEFAULT PAYMENT
============================================================

If the owner says:

"Always use UPI unless I say otherwise."

Store:

default_payment = upi

When finalizing a bill:

- If the owner explicitly specifies payment mode,
  use the explicitly specified mode.
- If the owner does not specify payment mode,
  use the saved default_payment preference.
- Never invent a payment preference.
- Never claim payment succeeded unless finalize_bill
  returns success=true.

Supported payment modes:

- cash
- upi
- card
- credit

If no payment mode is specified and no default payment
preference exists, ask the user to specify one.

============================================================
SHOP NAME
============================================================

If the owner says:

"Set my shop name to Sri Lakshmi Supermarket."

Use set_preference with:

preference_key = shop_name

preference_value = Sri Lakshmi Supermarket

Invoice generation automatically reads the saved shop name.

============================================================
GSTIN
============================================================

If the owner provides a GSTIN, store it using set_preference.

Never invent a GSTIN.

Invoice generation automatically reads the saved GSTIN.

============================================================
PREFERENCE PERSISTENCE
============================================================

Preferences survive:

- conversation reset
- /reset
- application restart

Conversation memory and owner preferences are separate.

If the owner asks what their preferences are,
use get_preferences.

If the owner explicitly asks to remember a preference,
use set_preference.

Do not claim that a preference was saved unless
set_preference succeeds.

============================================================
USING SAVED PREFERENCES
============================================================

Persistent preferences are operational settings.

When a saved preference is relevant to an operation,
use it.

Explicit user instructions always have priority
over saved preferences.

Example:

Saved:
default_payment = upi

User:
"Finalize bill 15 with cash."

Use cash.

Do not silently override an explicit instruction.

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
3. If exactly one product clearly matches, use it.
4. If multiple products could match, ask the user to clarify.
5. Never guess a product ID or SKU.

============================================================
STOCK
============================================================

For stock-related questions always use the appropriate inventory tool.

Never estimate inventory.

If the user asks:

"How much Maggi is left?"

Use search_products if necessary,
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
5. update_bill_item if needed
6. finalize_bill when customer is ready
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

If a bill ID has already been created in the conversation,
reuse it.

Do not create a new bill unnecessarily.

If the current conversation does not contain a bill ID,
ask for or create a bill as appropriate.

============================================================
STOCK SAFETY
============================================================

Never allow overselling.

The business tools enforce stock validation.

If a tool rejects an order because of insufficient stock,
communicate the actual available quantity.

Do not claim that the purchase succeeded if the tool failed.

============================================================
FINALIZING BILLS
============================================================

Supported payment modes:

- cash
- upi
- card
- credit

For credit:

- A customer must be associated with the bill.
- Never create credit for an unknown customer.

If payment_mode is not explicitly provided:

1. Check the saved default_payment preference.
2. If found, use it.
3. If not found, ask the user for a payment mode.

Explicit payment mode always wins.

Finalization is idempotent.

If finalize_bill reports that the bill was already finalized,
do not claim that stock was deducted again.

Never say payment succeeded unless finalize_bill succeeds.

============================================================
KHATA / CUSTOMER CREDIT
============================================================

When the user wants to use credit:

1. A valid customer must be associated with the bill.
2. Never invent a customer.
3. Use customer tools to identify the customer.
4. Only then finalize the credit bill.

When the user asks how much a customer owes,
use get_customer_credit or get_customer_credit_summary.

When recording a credit payment,
use record_credit_payment.

Never claim that a credit payment succeeded unless
the tool succeeds.

============================================================
CUSTOMER MANAGEMENT
============================================================

Customers are persistent database records.

Use customer tools when the user wants to:

- add a customer
- find a customer
- search for a customer
- check customer credit
- record a credit payment

If the user gives a customer name but not an ID:

1. Use search_customers.
2. If exactly one clear customer matches, use it.
3. If multiple customers match, ask for clarification.
4. Never randomly choose between customers.

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
DAILY CLOSE
============================================================

When the owner asks:

"Close the day"

or:

"Today's close"

or:

"Give me the daily closing summary"

use get_daily_close.

Do not claim that accounting data changed unless
a tool actually performs a write operation.

============================================================
BUSINESS HEALTH
============================================================

For questions such as:

"How is the store doing?"

"Give me a business summary."

"How are sales and stock?"

use get_business_health.

Recommendations must be grounded in actual tool results.

============================================================
REORDER
============================================================

When asked what needs reordering:

use get_reorder_recommendations.

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

If the user requests:

- business analysis
- management report
- sales analysis
- presentation
- PPT
- PowerPoint

use generate_analysis_deck.

============================================================
AMBIGUITY
============================================================

If a request is ambiguous, ask a concise clarification question.

Do not guess.

============================================================
ERROR HANDLING
============================================================

If a tool returns:

success = false

do not pretend the operation succeeded.

Explain the tool's message naturally.

============================================================
TOOL EXECUTION
============================================================

Tools are the source of truth for supermarket data.

For a business operation:

1. Understand the user's request.
2. Select the appropriate tool.
3. Execute the tool.
4. Inspect its result.
5. If another tool is needed, continue.
6. Only provide the final answer after the required
   operations are complete.

Do not stop after an intermediate tool result if
the user's request still requires another operation.

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
"""


# ============================================================
# BUILD OPENAI TOOL SCHEMAS
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
                "type": parameter_info.get(
                    "type",
                    "string"
                ),
                "description": parameter_info.get(
                    "description",
                    parameter_name
                )
            }

            if parameter_info.get(
                "required",
                False
            ):
                required.append(
                    parameter_name
                )

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

    if not isinstance(
        conversation,
        list
    ):
        raise ValueError(
            "conversation must be a list."
        )

    cleaned = []

    for message in conversation:

        if not isinstance(
            message,
            dict
        ):
            continue

        role = message.get("role")

        # ----------------------------------------------------
        # NORMAL USER MESSAGE
        # ----------------------------------------------------

        if role == "user":

            content = message.get(
                "content",
                ""
            )

            if content is None:
                content = ""

            cleaned.append(
                {
                    "role": "user",
                    "content": str(content)
                }
            )

        # ----------------------------------------------------
        # SYSTEM MESSAGE
        # ----------------------------------------------------

        elif role == "system":

            content = message.get(
                "content",
                ""
            )

            cleaned.append(
                {
                    "role": "system",
                    "content": str(content)
                }
            )

        # ----------------------------------------------------
        # ASSISTANT MESSAGE
        # ----------------------------------------------------

        elif role == "assistant":

            assistant_message = {
                "role": "assistant"
            }

            if "content" in message:

                assistant_message["content"] = (
                    message.get("content")
                )

            # IMPORTANT:
            # Preserve tool_calls because a following
            # role="tool" message is only valid when the
            # preceding assistant message contains the
            # corresponding tool call.
            if message.get("tool_calls"):

                valid_tool_calls = []

                for tool_call in message["tool_calls"]:

                    if not isinstance(
                        tool_call,
                        dict
                    ):
                        continue

                    tool_call_id = tool_call.get(
                        "id"
                    )

                    function = tool_call.get(
                        "function"
                    )

                    if not tool_call_id:
                        continue

                    if not isinstance(
                        function,
                        dict
                    ):
                        continue

                    function_name = function.get(
                        "name"
                    )

                    function_arguments = function.get(
                        "arguments",
                        "{}"
                    )

                    if not function_name:
                        continue

                    valid_tool_calls.append(
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": function_arguments
                            }
                        }
                    )

                if valid_tool_calls:

                    assistant_message[
                        "tool_calls"
                    ] = valid_tool_calls

            # Only keep assistant messages that actually
            # contain content or tool calls.
            if (
                assistant_message.get("content") is not None
                or assistant_message.get("tool_calls")
            ):

                cleaned.append(
                    assistant_message
                )

        # ----------------------------------------------------
        # TOOL MESSAGE
        # ----------------------------------------------------

        elif role == "tool":

            tool_call_id = message.get(
                "tool_call_id"
            )

            content = message.get(
                "content",
                ""
            )

            # We temporarily store tool messages.
            # They will be validated below.
            if tool_call_id:

                cleaned.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": str(content)
                    }
                )

    # --------------------------------------------------------
    # REPAIR TOOL MESSAGE SEQUENCES
    # --------------------------------------------------------
    #
    # OpenAI-compatible APIs require:
    #
    # assistant(tool_calls=[...])
    # tool(tool_call_id=...)
    #
    # A standalone tool message is invalid.
    #
    # This removes orphaned tool messages that may have been
    # stored by an older version of the application.
    # --------------------------------------------------------

    repaired = []

    pending_tool_ids = set()

    for message in cleaned:

        role = message.get("role")

        if role == "assistant":

            tool_calls = message.get(
                "tool_calls",
                []
            )

            if tool_calls:

                pending_tool_ids = {
                    tool_call.get("id")
                    for tool_call in tool_calls
                    if tool_call.get("id")
                }

            else:

                pending_tool_ids = set()

            repaired.append(
                message
            )

        elif role == "tool":

            tool_call_id = message.get(
                "tool_call_id"
            )

            if tool_call_id in pending_tool_ids:

                repaired.append(
                    message
                )

                pending_tool_ids.discard(
                    tool_call_id
                )

            else:

                # Orphan tool result.
                # Do NOT send it to OpenRouter.
                continue

        else:

            # A new user/system message means any unfinished
            # previous tool sequence is no longer safe to reuse.
            if role in {
                "user",
                "system"
            }:
                pending_tool_ids = set()

            repaired.append(
                message
            )

    # --------------------------------------------------------
    # LIMIT HISTORY
    # --------------------------------------------------------

    system_messages = [
        message
        for message in repaired
        if message.get("role") == "system"
    ]

    non_system_messages = [
        message
        for message in repaired
        if message.get("role") != "system"
    ]

    non_system_messages = non_system_messages[
        -MAX_HISTORY_MESSAGES:
    ]

    return (
        system_messages[:1]
        + non_system_messages
    )


# ============================================================
# SAFE APPEND ASSISTANT MESSAGE
# ============================================================

def create_assistant_message(
    assistant_message
):

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

    return assistant_dict


# ============================================================
# EXECUTE ONE TOOL CALL
# ============================================================

def execute_agent_tool(tool_call):

    tool_name = tool_call.function.name

    raw_arguments = (
        tool_call.function.arguments
    )

    # --------------------------------------------------------
    # CHECK TOOL
    # --------------------------------------------------------

    if tool_name not in TOOL_REGISTRY:

        return {
            "success": False,
            "message": (
                f"Unknown tool requested: {tool_name}"
            )
        }

    # --------------------------------------------------------
    # PARSE ARGUMENTS
    # --------------------------------------------------------

    try:

        arguments = json.loads(
            raw_arguments
        )

        if not isinstance(
            arguments,
            dict
        ):

            raise ValueError(
                "Tool arguments must be a JSON object."
            )

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Invalid arguments for tool "
                f"'{tool_name}': {str(e)}"
            )
        }

    # --------------------------------------------------------
    # EXECUTE BUSINESS TOOL
    # --------------------------------------------------------

    try:

        result = execute_tool(
            tool_name,
            arguments
        )

        if result is None:

            return {
                "success": False,
                "message": (
                    f"Tool '{tool_name}' returned no result."
                )
            }

        return result

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Tool '{tool_name}' failed: "
                f"{str(e)}"
            )
        }


# ============================================================
# MAIN AGENT FUNCTION
# ============================================================

def run_agent(
    user_message,
    conversation=None
):

    # --------------------------------------------------------
    # VALIDATE USER MESSAGE
    # --------------------------------------------------------

    if (
        not user_message
        or not user_message.strip()
    ):

        return {
            "success": False,
            "message": "Please enter a message.",
            "response": "Please enter a message.",
            "conversation": conversation or []
        }

    # --------------------------------------------------------
    # NORMALIZE / REPAIR OLD CONVERSATION
    # --------------------------------------------------------

    try:

        messages = normalize_conversation(
            conversation
        )

    except Exception as e:

        messages = []

    # --------------------------------------------------------
    # SYSTEM PROMPT
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
    # ADD USER MESSAGE
    # --------------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": user_message.strip()
        }
    )

    # --------------------------------------------------------
    # BUILD TOOLS
    # --------------------------------------------------------

    tools = build_openai_tools()

    # --------------------------------------------------------
    # AGENT CONTROL LOOP
    # --------------------------------------------------------

    for round_number in range(
        MAX_TOOL_ROUNDS
    ):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0
            )

        except Exception as e:

            error_text = str(e)

            # ------------------------------------------------
            # FRIENDLY ERROR FOR INVALID HISTORY
            # ------------------------------------------------

            if (
                "role 'tool'" in error_text
                or "preceding message with 'tool_calls'" in error_text
                or "tool_call_id" in error_text
            ):

                error_message = (
                    "The previous conversation state was invalid. "
                    "Please send the request again."
                )

            else:

                error_message = (
                    "I couldn't connect to the AI service. "
                    f"Error: {error_text}"
                )

            return {
                "success": False,
                "message": error_message,
                "response": error_message,
                "conversation": messages
            }

        # ----------------------------------------------------
        # CHECK RESPONSE
        # ----------------------------------------------------

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

        assistant_message = (
            response.choices[0].message
        )

        # ----------------------------------------------------
        # CREATE VALID ASSISTANT MESSAGE
        # ----------------------------------------------------

        assistant_dict = create_assistant_message(
            assistant_message
        )

        messages.append(
            assistant_dict
        )

        # ----------------------------------------------------
        # FINAL ANSWER
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
        # EXECUTE ALL TOOL CALLS
        # ----------------------------------------------------

        for tool_call in assistant_message.tool_calls:

            tool_result = execute_agent_tool(
                tool_call
            )

            # IMPORTANT:
            #
            # Every tool call MUST have a matching
            # role="tool" message with the exact
            # tool_call_id.
            #
            # This fixes the OpenRouter 400 error.
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
    # MAX TOOL ROUNDS REACHED
    # ========================================================

    error_message = (
        "I was unable to complete the request within "
        f"the allowed {MAX_TOOL_ROUNDS} tool operations. "
        "Please try the request again."
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

    print(
        f"\nMaximum tool rounds: {MAX_TOOL_ROUNDS}"
    )

    print("\nType 'exit' to stop.\n")

    conversation = []

    while True:

        user_input = input(
            "You: "
        ).strip()

        if user_input.lower() in {
            "exit",
            "quit",
            "q"
        }:

            print(
                "Goodbye!"
            )

            break

        if not user_input:
            continue

        result = run_agent(
            user_input,
            conversation
        )

        print("\nAgent:")

        print(
            result["message"]
        )

        conversation = result[
            "conversation"
        ]

        print()