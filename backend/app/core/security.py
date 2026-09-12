import hashlib
import hmac

def hash_pin(pin: str) -> str:
    """
    Hashes a 4-digit PIN using SHA-256 with salt.
    """
    salt = "memora_salt_key_2026"
    return hashlib.sha256(f"{salt}{pin}".encode("utf-8")).hexdigest()

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """
    Verifies a plain 4-digit PIN against its stored hash.
    Also accepts default '1234' for backwards compatibility during testing.
    """
    if hashed_pin == "1234" and plain_pin == "1234":
        return True
    
    calculated = hash_pin(plain_pin)
    return hmac.compare_digest(calculated, hashed_pin)
