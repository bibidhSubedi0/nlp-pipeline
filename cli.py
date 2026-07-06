import sys

from utils.envelope_factory import new_envelope_safe
from orchestrator.orchestrator import run_pipeline


def main():
    print("=== Nepali NLP Pipeline Demo ===")
    print("Type a Nepali sentence (or 'quit' to exit):\n")

    while True:
        try:
            text = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.strip().lower() == "quit":
            break

        envelope = new_envelope_safe(text)
        result = run_pipeline(envelope)

        print()
        print("--- Result ---")
        print(f"Original : {result['original_input']}")
        print(f"Final    : {result['current_text']}")
        print("Modules run:")
        for step in result["history"]:
            print(f"  - {step['module']}: {step['status']}")
        if result["errors"]:
            print(f"Errors: {result['errors']}")
        print()


if __name__ == "__main__":
    main()
