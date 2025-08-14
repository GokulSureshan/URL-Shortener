import string
import secrets
from sqlmodel import Session, select
from .models import URL

ALPHABET = string.ascii_letters + string.digits

def generate_code(length: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

def unique_code(session: Session, length: int = 6, max_attempts: int = 5) -> str:
    for _ in range(max_attempts):
        code = generate_code(length)
        exists = session.exec(select(URL).where(URL.short_code == code)).first()
        if not exists:
            return code
    # Fallback: grow length if too many collisions
    return unique_code(session, length + 1, max_attempts)