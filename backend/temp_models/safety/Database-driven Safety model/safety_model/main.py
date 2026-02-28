from __future__ import annotations

from typing import Optional

from colorama import Fore, Style, init as colorama_init

from .safety_agent import SafetyAgent
from .seed_data import init_db


def parse_dosage(input_str: str) -> Optional[int]:
    input_str = input_str.strip()
    if not input_str:
        return None
    try:
        value = int(input_str)
        if value < 0:
            return None
        return value
    except ValueError:
        return None


def main() -> None:
    colorama_init(autoreset=True)

    # Ensure DB schema exists (does not reseed data)
    init_db()

    agent = SafetyAgent()

    print(Fore.CYAN + "=== Database-driven Medicine Safety Checker ===" + Style.RESET_ALL)
    print("Type 'quit' at any time to exit.\n")

    while True:
        name = input("Medicine name: ").strip()
        if name.lower() in {"quit", "exit"}:
            break

        dosage_input = input("Requested daily dosage (mg, blank if unknown): ")
        dosage_mg = parse_dosage(dosage_input)

        assessment = agent.assess(name, dosage_mg)
        if assessment is None:
            print(Fore.YELLOW + "No information found for that medicine in the database.\n")
            continue

        header_color = Fore.GREEN if assessment.is_safe else Fore.RED
        print(header_color + f"\nAssessment for {assessment.medicine_name}:" + Style.RESET_ALL)
        print(f"- Requires prescription: {assessment.requires_prescription}")
        print(f"- Controlled level: {assessment.controlled_level}")
        print(f"- Max daily dosage (mg): {assessment.max_daily_dosage_mg}")
        print(f"- Requested daily dosage (mg): {assessment.requested_daily_dosage_mg}")
        print(f"- Considered safe: {assessment.is_safe}")

        if assessment.reasons:
            print("Reasons / notes:")
            for idx, reason in enumerate(assessment.reasons, start=1):
                print(f"  {idx}. {reason}")

        print()  # blank line between queries


if __name__ == "__main__":
    main()

