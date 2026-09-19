"""
Zero-dependency test runner to verify core gateway logic.
Can be executed directly via: python backend/tests/run_tests.py
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.pii_sanitizer import PIISanitizer, luhn_checksum_is_valid
from app.core.cache_manager import CacheManager
from app.core.cost_calculator import CostCalculator


def run_all_tests():
    print("================================================================")
    print(" >>> RUNNING AI GATEWAY VERIFICATION SUITE")
    print("================================================================\n")

    # Test 1: Luhn Algorithm
    print("[1/5] Testing Credit Card Luhn Formula...")
    assert luhn_checksum_is_valid("4532015112830366") is True, "Failed valid Luhn check"
    assert luhn_checksum_is_valid("1234567890123456") is False, "Failed invalid Luhn check"
    print("      [PASS] Luhn algorithm correctly isolates valid card numbers.")

    # Test 2: PII Redaction
    print("[2/5] Testing Automated PII Redaction Pipeline...")
    raw_prompt = (
        "Send invoice to john.doe@cyberdyne.com, call +1-555-234-5678, "
        "and bill card 4532 0151 1283 0366."
    )
    cleaned, count, types = PIISanitizer.sanitize_text(raw_prompt)
    assert count == 3, f"Expected 3 redactions, got {count}"
    assert "EMAIL" in types, "EMAIL type missing"
    assert "PHONE_NUMBER" in types, "PHONE_NUMBER type missing"
    assert "CREDIT_CARD" in types, "CREDIT_CARD type missing"
    assert "john.doe@cyberdyne.com" not in cleaned
    assert "[REDACTED_EMAIL]" in cleaned
    assert "[REDACTED_CREDIT_CARD]" in cleaned
    assert "[REDACTED_PHONE_NUMBER]" in cleaned
    print("      [PASS] Emails, Credit Cards, and Phone Numbers sanitized cleanly.")

    # Test 3: Prompt Hashing
    print("[3/5] Testing Deterministic SHA-256 Prompt Hashing...")
    msgs = [{"role": "user", "content": "Explain quantum computing."}]
    h1 = CacheManager.generate_prompt_hash("gpt-4o", msgs, temperature=0.7)
    h2 = CacheManager.generate_prompt_hash("gpt-4o", msgs, temperature=0.7)
    h3 = CacheManager.generate_prompt_hash("gemini-1.5-flash", msgs, temperature=0.7)
    assert h1 == h2, "Hashes for identical prompt must match"
    assert h1 != h3, "Hashes for different models must diverge"
    assert len(h1) == 64, "Hash length must be 64 chars"
    print(f"      [PASS] Deterministic SHA-256 generated ({h1[:16]}...).")

    # Test 4: Financial Cost Calculator
    print("[4/5] Testing Token & Latency Cost Calculator...")
    cost = CostCalculator.calculate_cost("gpt-4o", 1000, 1000)
    expected_cost = (1000 / 1_000_000 * 5.0) + (1000 / 1_000_000 * 15.0)
    assert abs(cost - expected_cost) < 0.000001
    print(f"      [PASS] 2,000 tokens evaluated accurately at ${cost:.6f} USD.")

    # Test 5: Message Batch Sanitization
    print("[5/5] Testing Multi-turn Chat Conversation Sanitizer...")
    chat_thread = [
        {"role": "system", "content": "You are a customer service assistant."},
        {"role": "user", "content": "Hello my email is alice@corp.net"},
        {"role": "assistant", "content": "Hello! How can I help?"},
        {"role": "user", "content": "My phone is (555) 987-6543"}
    ]
    cleaned_thread, total_redactions, detected_types = PIISanitizer.sanitize_messages(chat_thread)
    assert total_redactions == 2
    assert "alice@corp.net" not in cleaned_thread[1]["content"]
    assert "(555) 987-6543" not in cleaned_thread[3]["content"]
    print("      [PASS] Full multi-turn dialog history redacted successfully.")

    print("\n================================================================")
    print(" >>> ALL 5 TEST SUITES PASSED! CORE BACKEND PIPELINE VERIFIED.")
    print("================================================================")


if __name__ == "__main__":
    run_all_tests()
