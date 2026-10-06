"""
Classifier test script — runs against the SRM KTR training dataset.
Tests both image+text and text-only inputs, prints results and accuracy.

Run from /backend:  python scripts/test_classifier.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_classifier import classify_report

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "training_data")
LABELS_FILE = os.path.join(DATASET_DIR, "labels.json")

# ANSI colours
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


async def run_tests():
    with open(LABELS_FILE) as f:
        labels = json.load(f)

    all_samples = (
        [(s, "train") for s in labels["train"]] +
        [(s, "test")  for s in labels["test"]]
    )

    print(f"\n{BOLD}{'='*65}{RESET}")
    print(f"{BOLD}  SRM KTR Campus Hazard Classifier — Dataset Accuracy Test{RESET}")
    print(f"{BOLD}{'='*65}{RESET}")
    print(f"  Model: Gemini 1.5 Flash  |  Samples: {len(all_samples)} (16 train + 10 test)\n")

    correct_hazard = 0
    correct_severity_exact = 0
    correct_severity_close = 0   # within ±1
    correct_critical = 0
    total = 0

    for sample, split in all_samples:
        img_path = os.path.join(DATASET_DIR, split, sample["file"])
        if not os.path.exists(img_path):
            print(f"  {YELLOW}SKIP{RESET} {sample['file']} — file not found")
            continue

        result = await classify_report(img_path, sample["description"])

        hazard_match    = result["hazard_type"] == sample["hazard_type"]
        sev_exact       = result["severity"] == sample["severity"]
        sev_close       = abs(result["severity"] - sample["severity"]) <= 1
        critical_match  = result["is_safety_critical"] == sample["is_safety_critical"]

        correct_hazard        += hazard_match
        correct_severity_exact += sev_exact
        correct_severity_close += sev_close
        correct_critical       += critical_match
        total += 1

        status = f"{GREEN}✓{RESET}" if hazard_match else f"{RED}✗{RESET}"
        sev_tag = f"{GREEN}exact{RESET}" if sev_exact else (f"{YELLOW}±1{RESET}" if sev_close else f"{RED}off{RESET}")

        print(f"  {status} [{split:5s}] {sample['file']:20s}  "
              f"expected={sample['hazard_type']:22s} got={result['hazard_type']:22s}  "
              f"sev {sample['severity']}→{result['severity']} ({sev_tag})  "
              f"conf={result['confidence']:.2f}")

    print(f"\n{BOLD}{'─'*65}{RESET}")
    print(f"{BOLD}  Results  ({total} samples){RESET}")
    print(f"{'─'*65}")
    print(f"  Hazard type accuracy  : {BOLD}{correct_hazard}/{total} "
          f"({100*correct_hazard//total}%){RESET}")
    print(f"  Severity exact match  : {correct_severity_exact}/{total} "
          f"({100*correct_severity_exact//total}%)")
    print(f"  Severity within ±1    : {correct_severity_close}/{total} "
          f"({100*correct_severity_close//total}%)")
    print(f"  Safety-critical match : {correct_critical}/{total} "
          f"({100*correct_critical//total}%)")
    print(f"{'─'*65}\n")

    # Quick 5-sample smoke test with text-only inputs
    print(f"{BOLD}  Text-only smoke tests (no image){RESET}")
    print(f"{'─'*65}")
    smoke = [
        ("Water accumulated near entrance after rain making path slippery", "waterlogging"),
        ("Street light near the gate is not working, area is dark at night", "lighting_issue"),
        ("Pothole on internal campus road — vehicles swerving to avoid it",  "infrastructure_issue"),
        ("Plastic waste and litter left after cultural event at amphitheatre","cleanliness_issue"),
        ("Someone left a suspicious bag near the parking lot entrance",       "suspicious_activity"),
    ]
    for text, expected in smoke:
        r = await classify_report(None, text)
        match = r["hazard_type"] == expected
        sym = f"{GREEN}✓{RESET}" if match else f"{RED}✗{RESET}"
        print(f"  {sym}  expected={expected:25s} got={r['hazard_type']:25s} conf={r['confidence']:.2f}")
        print(f"       \"{text[:70]}\"")

    print(f"\n{BOLD}Done.{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
