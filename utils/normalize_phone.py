def normalize_phone_numbers(phone_number: str) -> str:
    if not phone_number or not 5 < len(phone_number) < 15:
        return 'Invalid phone number!'
    
    number = ''.join(d for d in phone_number if d.isdigit())
    
    return f'+{number}'
    