def format_phone_number(raw_phone: str) -> str:
    return "38" + "".join(el for el in raw_phone if el.isdigit())
