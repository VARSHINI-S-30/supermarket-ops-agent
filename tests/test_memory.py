from app.database.db import engine, Base
from app.database.models import TelegramSession

from app.services.memory import (
    get_conversation,
    save_conversation,
    clear_conversation,
    has_conversation,
)


# ============================================================
# DATABASE TABLE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


print("=" * 60)
print("STEP 13 - PERSISTENT MEMORY TEST")
print("=" * 60)


TEST_USER_ID = "step13_test_user_123"


# ============================================================
# TEST 1 - CLEAR OLD TEST MEMORY
# ============================================================

print("\n--- TEST 1: CLEAR OLD MEMORY ---")

result = clear_conversation(
    TEST_USER_ID
)

print(result)


# ============================================================
# TEST 2 - EMPTY MEMORY
# ============================================================

print("\n--- TEST 2: CHECK EMPTY MEMORY ---")

conversation = get_conversation(
    TEST_USER_ID
)

print("Conversation:", conversation)

assert conversation == []

print("Empty memory test passed.")


# ============================================================
# TEST 3 - SAVE CONVERSATION
# ============================================================

print("\n--- TEST 3: SAVE CONVERSATION ---")

test_conversation = [
    {
        "role": "system",
        "content": "You are a supermarket assistant."
    },
    {
        "role": "user",
        "content": "How much Maggi is left?"
    },
    {
        "role": "assistant",
        "content": "There are 39 packets of Maggi left."
    }
]

result = save_conversation(
    TEST_USER_ID,
    test_conversation
)

print(result)

assert result["success"] is True

print("Conversation saved successfully.")


# ============================================================
# TEST 4 - CHECK MEMORY
# ============================================================

print("\n--- TEST 4: CHECK MEMORY ---")

exists = has_conversation(
    TEST_USER_ID
)

print("Memory exists:", exists)

assert exists is True

print("Memory existence test passed.")


# ============================================================
# TEST 5 - LOAD CONVERSATION
# ============================================================

print("\n--- TEST 5: LOAD CONVERSATION ---")

loaded_conversation = get_conversation(
    TEST_USER_ID
)

print("Loaded conversation:")

for message in loaded_conversation:
    print(message)

assert loaded_conversation == test_conversation

print("Conversation loaded successfully.")


# ============================================================
# TEST 6 - CLEAR MEMORY
# ============================================================

print("\n--- TEST 6: CLEAR MEMORY ---")

result = clear_conversation(
    TEST_USER_ID
)

print(result)

assert result["success"] is True


# ============================================================
# TEST 7 - VERIFY CLEAR
# ============================================================

print("\n--- TEST 7: VERIFY MEMORY CLEARED ---")

final_conversation = get_conversation(
    TEST_USER_ID
)

print(
    "Conversation after clear:",
    final_conversation
)

assert final_conversation == []

print("Memory clear test passed.")


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 60)
print("STEP 13 TEST COMPLETED SUCCESSFULLY")
print("=" * 60)