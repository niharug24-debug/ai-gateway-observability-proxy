"""
PII Sanitization & Data Masking Engine.
Detects and redacts sensitive data (Emails, Credit Cards, Phone Numbers)
prior to transit to external LLM providers.
"""

import re
from typing import Tuple, List, Dict, Any


def luhn_checksum_is_valid(card_number_str: str) -> bool:
    """
    Validates a credit card candidate using the Luhn checksum algorithm (Mod 10).
    Ensures arbitrary 16-digit numbers or serial codes aren't mistakenly marked as cards.
    """
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += digit
            
    return (checksum % 10) == 0


class PIISanitizer:
    """
    High-performance Regex pattern interceptor for sensitive PII data masking.
    """
    # Email pattern
    EMAIL_REGEX = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        re.IGNORECASE
    )

    # Phone Number pattern (matches E.164, standard US/international with brackets, dashes, spaces)
    # Examples: +1-555-123-4567, (555) 123-4567, 555.123.4567, +44 20 7946 0958
    PHONE_REGEX = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'
    )

    # Credit card pattern candidates: 13-19 digits, possibly separated by spaces or hyphens
    CREDIT_CARD_CANDIDATE_REGEX = re.compile(
        r'\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b'
    )

    @classmethod
    def sanitize_text(cls, text: str) -> Tuple[str, int, List[str]]:
        """
        Scans and sanitizes a single string of text.
        
        Returns:
            Tuple containing:
            - sanitized_text (str): The transformed text with [REDACTED_*] markers.
            - total_redactions (int): Count of sensitive items redacted.
            - detected_types (List[str]): List of categories found (e.g. ['EMAIL', 'CREDIT_CARD']).
        """
        if not text:
            return text, 0, []

        sanitized = text
        redacted_count = 0
        types_detected = set()

        # 1. Redact Emails
        email_matches = list(cls.EMAIL_REGEX.finditer(sanitized))
        if email_matches:
            types_detected.add("EMAIL")
            redacted_count += len(email_matches)
            sanitized = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", sanitized)

        # 2. Redact Credit Cards (with Luhn validation check)
        def replace_card(match: re.Match) -> str:
            nonlocal redacted_count
            candidate = match.group(0)
            cleaned_digits = re.sub(r'\D', '', candidate)
            if luhn_checksum_is_valid(cleaned_digits):
                types_detected.add("CREDIT_CARD")
                redacted_count += 1
                return "[REDACTED_CREDIT_CARD]"
            return candidate

        sanitized = cls.CREDIT_CARD_CANDIDATE_REGEX.sub(replace_card, sanitized)

        # 3. Redact Phone Numbers
        # We ensure phone regex doesn't match redacted tags
        def replace_phone(match: re.Match) -> str:
            nonlocal redacted_count
            candidate = match.group(0)
            digits_only = re.sub(r'\D', '', candidate)
            # Valid phones typically have 7 to 15 digits
            if 7 <= len(digits_only) <= 15:
                types_detected.add("PHONE_NUMBER")
                redacted_count += 1
                return "[REDACTED_PHONE_NUMBER]"
            return candidate

        sanitized = cls.PHONE_REGEX.sub(replace_phone, sanitized)

        return sanitized, redacted_count, sorted(list(types_detected))

    @classmethod
    def sanitize_messages(
        cls, messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """
        Sanitizes a list of OpenAI-formatted chat messages.
        
        Returns:
            Tuple containing:
            - sanitized_messages (List[Dict]): Clone of messages with sanitized content.
            - total_redactions (int): Total count across all messages.
            - detected_types (List[str]): All PII categories found.
        """
        sanitized_messages = []
        total_redactions = 0
        all_detected_types = set()

        for msg in messages:
            msg_copy = dict(msg)
            content = msg_copy.get("content")
            if isinstance(content, str):
                cleaned_content, count, types = cls.sanitize_text(content)
                msg_copy["content"] = cleaned_content
                total_redactions += count
                all_detected_types.update(types)
            sanitized_messages.append(msg_copy)

        return sanitized_messages, total_redactions, sorted(list(all_detected_types))
