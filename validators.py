import re
import uuid

def is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is a valid UUID"""
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string
    except (ValueError, AttributeError):
        return False

def validate_message(message: str) -> tuple[bool, str]:
    """Validate user message"""
    if not message or message.isspace():
        return False, "Message cannot be empty"
    
    if len(message) < 10:
        return False, "Message is too short. Please provide more details"
    
    if len(message) > 1000:
        return False, "Message is too long. Please keep it under 1000 characters"
    
    # Basic inappropriate content check
    inappropriate_patterns = [
        r'\b(hack|crack|steal|illegal|drugs?)\b',
        r'\b(password|credit.?card)\b'
    ]
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, message.lower()):
            return False, "Sorry, I cannot assist with potentially inappropriate or illegal content"
    
    return True, ""
