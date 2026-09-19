"""
Unit tests for the PII Sanitization and Redaction Pipeline.
"""

import pytest
from app.core.pii_sanitizer import PIISanitizer, luhn_checksum_is_valid


def test_luhn_algorithm():
    """Verify that the Luhn check distinguishes valid card patterns from random numbers."""
    # Standard Visa test number (valid Luhn)
    assert luhn_checksum_is_valid("4532015112830366") is True
    # Random invalid digits
    assert luhn_checksum_is_valid("1234567890123456") is False
    # Short string
    assert luhn_checksum_is_valid("12345") is False


def test_email_redaction():
    """Test standard and edge-case email address masking."""
    prompt = "Please send the invoice to sarah.connor@cyberdyne.org and john_doe123@gmail.com right away."
    sanitized, count, types = PIISanitizer.sanitize_text(prompt)

    assert count == 2
    assert "EMAIL" in types
    assert "sarah.connor@cyberdyne.org" not in sanitized
    assert "john_doe123@gmail.com" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized


def test_credit_card_redaction():
    """Test credit card redaction with valid Luhn numbers."""
    # Using standard test card number
    prompt = "Here is my Visa card: 4532 0151 1283 0366 for payment."
    sanitized, count, types = PIISanitizer.sanitize_text(prompt)

    assert count == 1
    assert "CREDIT_CARD" in types
    assert "4532 0151 1283 0366" not in sanitized
    assert "[REDACTED_CREDIT_CARD]" in sanitized


def test_phone_number_redaction():
    """Test phone number format masking (dashed, parenthesized, international)."""
    prompt = "Call my mobile at +1 (555) 234-5678 or office line 555-876-5432."
    sanitized, count, types = PIISanitizer.sanitize_text(prompt)

    assert count >= 1
    assert "PHONE_NUMBER" in types
    assert "+1 (555) 234-5678" not in sanitized
    assert "[REDACTED_PHONE_NUMBER]" in sanitized


def test_clean_text_untouched():
    """Ensure standard technical text without PII is completely untouched."""
    prompt = "Explain how Kubernetes StatefulSets manage persistent storage volume claims."
    sanitized, count, types = PIISanitizer.sanitize_text(prompt)

    assert count == 0
    assert len(types) == 0
    assert sanitized == prompt


def test_batch_message_sanitization():
    """Test sanitizing a full OpenAI conversation thread."""
    messages = [
        {"role": "system", "content": "You are a customer support agent."},
        {"role": "user", "content": "My email is alice@example.com and phone is 555-123-4567."},
        {"role": "assistant", "content": "Thanks Alice! How can I help?"}
    ]
    sanitized_messages, total_count, all_types = PIISanitizer.sanitize_messages(messages)

    assert total_count == 2
    assert "EMAIL" in all_types
    assert "PHONE_NUMBER" in all_types
    assert "alice@example.com" not in sanitized_messages[1]["content"]
    assert "[REDACTED_EMAIL]" in sanitized_messages[1]["content"]
