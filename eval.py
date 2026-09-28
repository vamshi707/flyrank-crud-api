import requests

URL = "http://127.0.0.1:8000/triage"

cases = [
    {
        "text": "My card was charged twice for the same order.",
        "category": "billing",
    },
    {
        "text": "The payment failed but money was deducted from my account.",
        "category": "billing",
    },
    {
        "text": "The app crashes whenever I open the settings page.",
        "category": "bug",
    },
    {
        "text": "The login button does nothing when I click it.",
        "category": "bug",
    },
    {
        "text": "Please add dark mode to the application.",
        "category": "feature",
    },
    {
        "text": "It would be useful to have an option to export reports as PDF.",
        "category": "feature",
    },
    {
        "text": "I really like the application.",
        "category": "other",
    },
    {
        "text": "Can someone tell me more about your company?",
        "category": "other",
    },
]


passed = 0

for number, case in enumerate(cases, start=1):
    response = requests.post(
        URL,
        json={"text": case["text"]},
        timeout=35,
    )

    result = response.json()

    actual = result.get("category")
    expected = case["category"]

    if actual == expected:
        passed += 1
        status = "PASS"
    else:
        status = "FAIL"

    print(f"{number}. {status}")
    print(f"   Input:    {case['text']}")
    print(f"   Expected: {expected}")
    print(f"   Actual:   {actual}")
    print()


score = (passed / len(cases)) * 100

print("=" * 40)
print(f"Score: {passed}/{len(cases)} = {score:.0f}%")
print("=" * 40)