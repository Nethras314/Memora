import hashlib
import hmac

def hash_pin(pin: str) -> str:
    """
    Hashes a 4-digit PIN using SHA-256 with a static application salt.
    """
    salt = "memora_salt_key_2026"
    return hashlib.sha256(f"{salt}{pin}".encode("utf-8")).hexdigest()

def verify_pin(plain_pin: str, stored_hash: str) -> bool:
    """
    Verifies a plain 4-digit PIN against its stored hash or stored PIN.
    Uses timing-safe comparison to prevent timing attacks.
    """
    if not plain_pin or not stored_hash:
        return False
    
    # 1. Compare against calculated salted SHA-256 hash
    calculated = hash_pin(plain_pin)
    if hmac.compare_digest(calculated, stored_hash):
        return True
        
    # 2. Support database records where PIN was stored as plain 4-digit string
    if hmac.compare_digest(plain_pin, stored_hash):
        return True
        
    return False

