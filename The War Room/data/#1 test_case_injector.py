# test_case_injector.py

from core.token_engine import inject_tokens
from core.case_controller import activate_case_mode, run_master_protocol
from core.section_engine import generate_section

def simulate_case_environment():
    print("Injecting test case environment...")

    test_case_id = "CASE_20250923_TEST"
    test_tokens = {
        "CASE_ID": test_case_id,
        "CLIENT_NAME": "Maria Huerta",
        "SUBJECT_NAME": "Rose Alejandra Beltran",
        "CONTRACT_DATE": "2025-05-12",
        "SURV_DAY1_DATE": "Thursday, August 21, 2025",
        "SURV_DAY1_START_ACTUAL": "07:12",
        "SURV_DAY1_END_ACTUAL": "15:24",
        "SURV_DAY1_COST": "850",
        "FINAL_REPORT_HOURS": "1.5",
        "REPORTS_PROCESSED": 0
    }

    run_master_protocol(test_case_id)
    activate_case_mode(test_case_id)
    inject_tokens(test_tokens)

    print(f"Case [{test_case_id}] activated.")
    print(f"Tokens injected: {len(test_tokens)}")

    try:
        generate_section("section_1", test_case_id)
        print("Section 1 generated successfully.")
    except Exception as e:
        print(f"Section 1 generation failed: {e}")

    try:
        generate_section("section_3", test_case_id)
        print("Section 3 generated successfully.")
    except Exception as e:
        print(f"Section 3 generation failed: {e}")

if __name__ == "__main__":
    simulate_case_environment()
