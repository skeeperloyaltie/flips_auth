import base64

def encode_to_base64(string):
    """Encodes a given string to base64."""
    base64_bytes = base64.urlsafe_b64encode(string.encode('utf-8'))
    return base64_bytes.decode('utf-8')

def decode_from_base64(base64_string):
    """Decodes a given base64 string."""
    base64_bytes = base64_string.encode('utf-8')
    return base64.urlsafe_b64decode(base64_bytes).decode('utf-8')