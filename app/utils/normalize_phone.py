def normalize_phone_numbers(phone_number: str) -> str:
    if not phone_number:
        return "Invalid phone number!"

    number = ''.join(
        char for char in phone_number
        if char.isdigit()
    )

    if not 6 <= len(number) <= 15:
        return "Invalid phone number!"

    return f"+{number}"