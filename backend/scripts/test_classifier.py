"""
CLI test for the AI classifier.
Run: python backend/scripts/test_classifier.py
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from app.services.ai_classifier import classify_report

SAMPLES = [
    (None, "Electrical wire hanging loose near the socket in lab, sparking when you get close"),
    (None, "There is a huge pothole near the library gate causing bike damage every day"),
    (None, "Suspicious person loitering near the hostel block after midnight"),
    (None, "Ceiling is leaking water in the library first floor near the study area"),
    (None, "My lunch was delicious today at the canteen, had biryani"),  # NOT a hazard
]


async def main():
    print("=" * 60)
    print("S.O.S. Classifier Test — 5 Samples")
    print("=" * 60)
    for i, (image_path, text) in enumerate(SAMPLES, 1):
        print(f"\n[{i}] Input: {text[:70]}...")
        result = await classify_report(image_path, text)
        print(f"    hazard_type : {result['hazard_type']}")
        print(f"    category    : {result['category']}")
        print(f"    severity    : {result['severity']}/5")
        print(f"    critical    : {result['is_safety_critical']}")
        print(f"    summary     : {result['summary']}")
        print(f"    confidence  : {result['confidence']}")
        print(f"    reasoning   : {result['reasoning'][:100]}...")
    print("\n" + "=" * 60)
    print("Test complete.")


if __name__ == "__main__":
    asyncio.run(main())
