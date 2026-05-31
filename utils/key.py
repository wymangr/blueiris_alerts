import hmac
import hashlib


def encode(key: str, clear: str) -> str:
    return hmac.new(key.encode(), clear.encode(), hashlib.sha256).hexdigest()
