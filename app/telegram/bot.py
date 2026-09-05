import os
import json
import logging

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.agent.agent import run_agent

from app.services.memory import (
    get_conversation,
    save_conversation,
    clear_conversation,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# ARTIFACT EXTRACTION
# ============================================================

def extract_generated_files(
    conversation
):
    """
    Find newly generated PDF/PPTX files from
    the current request only.
    """

    generated_files = []

    if not conversation:
        return generated_files

    for message in conversation:

        if message.get("role") != "tool":
            continue

        content = message.get(
            "content",
            ""
        )

        try:

            result = json.loads(
                content
            )

        except Exception:

            continue

        if not isinstance(
            result,
            dict
        ):
            continue

        if not result.get(
            "success"
        ):
            continue

        filepath = result.get(
            "filepath"
        )

        filename = result.get(
            "filename"
        )

        if not filepath:
            continue

        if not os.path.exists(
            filepath
        ):
            continue

        extension = (
            os.path.splitext(
                filepath
            )[1]
            .lower()
        )

        if extension not in {
            ".pdf",
            ".pptx"
        }:
            continue

        generated_files.append(
            {
                "filepath": filepath,
                "filename": (
                    filename
                    or os.path.basename(
                        filepath
                    )
                ),
            }
        )

    return generated_files


# ============================================================
# SEND GENERATED FILE
# ============================================================

async def send_generated_file(
    update,
    filepath,
    filename
):

    try:

        if not os.path.exists(
            filepath
        ):

            await update.message.reply_text(
                "The generated file could not be found."
            )

            return

        extension = (
            os.path.splitext(
                filepath
            )[1]
            .lower()
        )

        if extension == ".pdf":

            caption = (
                "📄 Invoice generated successfully\n"
                f"File: {filename}"
            )

        elif extension == ".pptx":

            caption = (
                "📊 Business analysis generated successfully\n"
                f"File: {filename}"
            )

        else:

            caption = (
                f"Generated file: {filename}"
            )

        with open(
            filepath,
            "rb"
        ) as document:

            await update.message.reply_document(
                document=document,
                filename=filename,
                caption=caption
            )

    except Exception:

        logger.exception(
            "Error sending generated file."
        )

        await update.message.reply_text(
            "The file was generated, but I "
            "could not send it through Telegram."
        )


# ============================================================
# /START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    welcome_message = (
        f"Hello {user.first_name}! 👋\n\n"

        "Welcome to Nebula Supermarket Ops Agent.\n\n"

        "I can help you manage supermarket operations "
        "directly through Telegram.\n\n"

        "You can ask me things like:\n"
        "• How much Maggi is left?\n"
        "• Do we have Aashirvaad Atta?\n"
        "• Show low-stock products\n"
        "• What needs reordering?\n"
        "• What are today's sales?\n"
        "• Create a bill\n"
        "• Add 2 Maggi to the bill\n"
        "• Add one Atta\n"
        "• Change Maggi quantity to 3\n"
        "• Finalize the bill using UPI\n"
        "• Check customer khata\n"
        "• Record a credit payment\n"
        "• Generate an invoice\n"
        "• Generate business analysis\n\n"

        "Just send your request naturally."
    )

    await update.message.reply_text(
        welcome_message
    )


# ============================================================
# /HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    help_message = (
        "🛒 NEBULA SUPERMARKET OPS AGENT\n\n"

        "📦 INVENTORY\n"
        "• Check stock of Maggi\n"
        "• Search for Atta\n"
        "• Show low-stock items\n"
        "• What should I reorder?\n\n"

        "🧾 BILLING\n"
        "• Create a bill\n"
        "• Add 2 Maggi\n"
        "• Add one Atta\n"
        "• Change Maggi quantity to 3\n"
        "• Remove Atta\n"
        "• Show my bill\n"
        "• Finalize bill with UPI\n\n"

        "💳 KHATA\n"
        "• Check customer 1 credit\n"
        "• Record ₹500 payment for customer 1\n\n"

        "📊 SALES\n"
        "• Today's sales\n"
        "• Daily close\n\n"

        "📄 REPORTS\n"
        "• Generate invoice for bill 9\n"
        "• Generate business analysis deck\n\n"

        "⚙️ COMMANDS\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/reset - Clear conversation memory"
    )

    await update.message.reply_text(
        help_message
    )


# ============================================================
# /RESET
# ============================================================

async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    result = clear_conversation(
        user_id
    )

    if result.get(
        "success"
    ):

        await update.message.reply_text(
            "Conversation memory has been cleared. 🔄"
        )

    else:

        await update.message.reply_text(
            "I couldn't clear the conversation memory."
        )


# ============================================================
# NORMAL TEXT MESSAGE
# ============================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user_message = update.message.text

    if not user_message:
        return

    user_id = update.effective_user.id

    logger.info(
        "Message from user %s: %s",
        user_id,
        user_message
    )

    try:

        # ----------------------------------------------------
        # Typing indicator
        # ----------------------------------------------------

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # ----------------------------------------------------
        # LOAD PERSISTENT MEMORY
        # ----------------------------------------------------

        conversation = get_conversation(
            user_id
        )

        # ----------------------------------------------------
        # Remember old conversation length
        # ----------------------------------------------------

        old_conversation_length = len(
            conversation
        )

        # ----------------------------------------------------
        # RUN AI AGENT
        # ----------------------------------------------------

        result = run_agent(
            user_message=user_message,
            conversation=conversation
        )

        # ----------------------------------------------------
        # AI RESPONSE
        # ----------------------------------------------------

        response_message = result.get(
            "message",
            "I couldn't process your request."
        )

        # ----------------------------------------------------
        # NEW CONVERSATION
        # ----------------------------------------------------

        new_conversation = result.get(
            "conversation",
            conversation
        )

        # ----------------------------------------------------
        # SAVE TO SQLITE
        # ----------------------------------------------------

        save_result = save_conversation(
            user_id,
            new_conversation
        )

        if not save_result.get(
            "success"
        ):

            logger.warning(
                "Conversation could not be saved: %s",
                save_result.get(
                    "message"
                )
            )

        # ----------------------------------------------------
        # SEND AI RESPONSE
        # ----------------------------------------------------

        await update.message.reply_text(
            response_message
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Only inspect messages created during this request.
        #
        # This prevents old PDF/PPTX files from being sent
        # again for future questions.
        # ----------------------------------------------------

        new_messages = new_conversation[
            old_conversation_length:
        ]

        generated_files = (
            extract_generated_files(
                new_messages
            )
        )

        # ----------------------------------------------------
        # SEND NEWLY GENERATED FILES
        # ----------------------------------------------------

        for file_info in generated_files:

            await send_generated_file(
                update,
                file_info["filepath"],
                file_info["filename"]
            )

    except Exception:

        logger.exception(
            "Error while processing Telegram message."
        )

        await update.message.reply_text(
            "Something went wrong while processing "
            "your request. Please try again."
        )


# ============================================================
# UNKNOWN COMMAND
# ============================================================

async def unknown_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Unknown command. Use /help to see available options."
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Telegram bot error:",
        exc_info=context.error
    )


# ============================================================
# START TELEGRAM BOT
# ============================================================

def run_telegram_bot():

    print("=" * 60)
    print("NEBULA SUPERMARKET TELEGRAM BOT")
    print("=" * 60)

    print(
        "\nStarting Telegram bot..."
    )

    print(
        "Persistent conversation memory: ENABLED"
    )

    print(
        "Press CTRL+C to stop.\n"
    )

    application = (
        Application.builder()
        .token(
            TELEGRAM_BOT_TOKEN
        )
        .build()
    )

    # --------------------------------------------------------
    # Commands
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "reset",
            reset_command
        )
    )

    # --------------------------------------------------------
    # Normal text messages
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            handle_message
        )
    )

    # --------------------------------------------------------
    # Unknown commands
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.COMMAND,
            unknown_command
        )
    )

    # --------------------------------------------------------
    # Error handler
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # --------------------------------------------------------
    # Start polling
    # --------------------------------------------------------

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_telegram_bot()