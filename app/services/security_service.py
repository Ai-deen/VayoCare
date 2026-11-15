import hashlib
import os
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple

class SecurityService:
    def __init__(self):
        # In-memory tracking cache: {identifier: (fail_count, lock_until_timestamp)}
        self._failed_attempts: Dict[str, Tuple[int, float]] = {}
        self.MAX_ATTEMPTS = 5
        self.LOCKOUT_DURATION_SECONDS = 900  # 15 minutes lockout

    def hash_passcode(self, passcode: str, salt: bytes = None) -> str:
        """PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations."""
        if salt is None:
            salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', passcode.encode('utf-8'), salt, 100000)
        return f"{salt.hex()}${key.hex()}"

    def verify_passcode(self, passcode: str, hashed_passcode: str) -> bool:
        """Safely verifies a passcode against stored hash using constant-time comparison."""
        if not hashed_passcode:
            return False
        # If legacy plain-text (for migration), check directly
        if "$" not in hashed_passcode:
            return hmac.compare_digest(passcode, hashed_passcode)
        try:
            salt_hex, key_hex = hashed_passcode.split("$")
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            new_key = hashlib.pbkdf2_hmac('sha256', passcode.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(new_key, expected_key)
        except Exception:
            return False

    def is_locked_out(self, identifier: str) -> Tuple[bool, int]:
        """Checks if account or IP is currently locked out in DB or memory cache."""
        clean = "".join(c for c in identifier if c.isdigit())
        now = time.time()

        # 1. Check DB first if available
        try:
            from app.db.session import SessionLocal
            from app.db.models import User
            with SessionLocal() as session:
                user = session.query(User).filter(User.phone == clean).first()
                if user and user.lockout_until:
                    lock_ts = user.lockout_until.timestamp()
                    if now < lock_ts:
                        return True, int(lock_ts - now)
                    elif now >= lock_ts and user.failed_attempts >= self.MAX_ATTEMPTS:
                        user.failed_attempts = 0
                        user.lockout_until = None
                        session.commit()
                        if identifier in self._failed_attempts:
                            del self._failed_attempts[identifier]
                        return False, 0
        except Exception:
            pass

        # 2. In-memory cache fallback
        record = self._failed_attempts.get(identifier)
        if not record:
            return False, 0
        count, lock_until = record
        if now < lock_until:
            return True, int(lock_until - now)
        elif count >= self.MAX_ATTEMPTS and now >= lock_until:
            del self._failed_attempts[identifier]
            return False, 0
        return False, 0

    def record_failed_attempt(self, identifier: str) -> int:
        """Increments failed attempt count and applies lockout after 5 fails in DB and memory."""
        now = time.time()
        record = self._failed_attempts.get(identifier, (0, 0))
        count = record[0] + 1
        lock_until = record[1]
        if count >= self.MAX_ATTEMPTS:
            lock_until = now + self.LOCKOUT_DURATION_SECONDS
        self._failed_attempts[identifier] = (count, lock_until)

        # Persist to DB
        try:
            from app.db.session import SessionLocal
            from app.db.models import User
            clean = "".join(c for c in identifier if c.isdigit())
            with SessionLocal() as session:
                user = session.query(User).filter(User.phone == clean).first()
                if user:
                    user.failed_attempts = count
                    if count >= self.MAX_ATTEMPTS:
                        user.lockout_until = datetime.fromtimestamp(lock_until)
                    session.commit()
        except Exception:
            pass

        return count

    def reset_failed_attempts(self, identifier: str):
        """Clears lockout and fail counts upon successful authentication."""
        if identifier in self._failed_attempts:
            del self._failed_attempts[identifier]

        # Reset in DB
        try:
            from app.db.session import SessionLocal
            from app.db.models import User
            clean = "".join(c for c in identifier if c.isdigit())
            with SessionLocal() as session:
                user = session.query(User).filter(User.phone == clean).first()
                if user:
                    user.failed_attempts = 0
                    user.lockout_until = None
                    session.commit()
        except Exception:
            pass

security_service = SecurityService()
