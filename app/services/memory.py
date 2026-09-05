import json
from datetime import datetime

from app.database.db import SessionLocal
from app.database.models import TelegramSession


# ============================================================
# CONFIGURATION
# ============================================================

MAX_CONVERSATION_MESSAGES = 60


# ============================================================
# GET CONVERSATION
# ============================================================

def get_conversation(telegram_user_id):

    db = SessionLocal()

    try:

        session = (
            db.query(TelegramSession)
            .filter(
                TelegramSession.telegram_user_id
                == str(telegram_user_id)
            )
            .first()
        )

        if not session:
            return []

        try:

            conversation = json.loads(
                session.conversation_json
            )

        except (json.JSONDecodeError, TypeError):

            return []

        if not isinstance(
            conversation,
            list
        ):

            return []

        return conversation

    except Exception as e:

        print(
            f"Error loading conversation: {e}"
        )

        return []

    finally:

        db.close()


# ============================================================
# SAVE CONVERSATION
# ============================================================

def save_conversation(
    telegram_user_id,
    conversation
):

    db = SessionLocal()

    try:

        telegram_user_id = str(
            telegram_user_id
        )

        # Keep only the most recent messages.
        # This prevents the conversation from becoming
        # unnecessarily large over time.

        if len(conversation) > MAX_CONVERSATION_MESSAGES:

            conversation = conversation[
                -MAX_CONVERSATION_MESSAGES:
            ]

        conversation_json = json.dumps(
            conversation,
            ensure_ascii=False,
            default=str
        )

        session = (
            db.query(TelegramSession)
            .filter(
                TelegramSession.telegram_user_id
                == telegram_user_id
            )
            .first()
        )

        if session:

            session.conversation_json = (
                conversation_json
            )

            session.updated_at = (
                datetime.utcnow()
            )

        else:

            session = TelegramSession(
                telegram_user_id=telegram_user_id,
                conversation_json=conversation_json,
                updated_at=datetime.utcnow()
            )

            db.add(session)

        db.commit()

        return {
            "success": True,
            "message": (
                "Conversation saved successfully."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error saving conversation: {str(e)}"
            )
        }

    finally:

        db.close()


# ============================================================
# CLEAR CONVERSATION
# ============================================================

def clear_conversation(
    telegram_user_id
):

    db = SessionLocal()

    try:

        session = (
            db.query(TelegramSession)
            .filter(
                TelegramSession.telegram_user_id
                == str(telegram_user_id)
            )
            .first()
        )

        if not session:

            return {
                "success": True,
                "message": (
                    "No conversation memory existed."
                )
            }

        session.conversation_json = "[]"

        session.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        return {
            "success": True,
            "message": (
                "Conversation memory cleared."
            )
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Error clearing conversation: {str(e)}"
            )
        }

    finally:

        db.close()


# ============================================================
# CHECK WHETHER MEMORY EXISTS
# ============================================================

def has_conversation(
    telegram_user_id
):

    db = SessionLocal()

    try:

        session = (
            db.query(TelegramSession)
            .filter(
                TelegramSession.telegram_user_id
                == str(telegram_user_id)
            )
            .first()
        )

        if not session:
            return False

        try:

            conversation = json.loads(
                session.conversation_json
            )

            return (
                isinstance(conversation, list)
                and len(conversation) > 0
            )

        except Exception:

            return False

    finally:

        db.close()