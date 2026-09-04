import os

from app.services.analysis_deck import (
    generate_analysis_deck
)


print("\n========================================")
print("STEP 8 - PPTX BUSINESS ANALYSIS TEST")
print("========================================")


result = generate_analysis_deck()

print("\n--- PPTX GENERATION RESULT ---")

print(result)


if result["success"]:

    filepath = result["filepath"]

    print(
        f"\nPPTX exists: "
        f"{os.path.exists(filepath)}"
    )

    if os.path.exists(filepath):

        print(
            f"PPTX size: "
            f"{os.path.getsize(filepath)} bytes"
        )

        print(
            f"PPTX path: "
            f"{filepath}"
        )


print("\n========================================")
print("STEP 8 TEST COMPLETED")
print("========================================")