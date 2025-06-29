from django.core.exceptions import ValidationError
import re


def validate_formatted_phone(value: str) -> None:
    pattern = r"^380\d{9}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "Phone number must be in format: 380505050505"
        )
