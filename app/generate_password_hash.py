#!/usr/bin/env python3
"""Generate a bcrypt hash for a password to use in .env."""

import sys
import bcrypt


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m app.generate_password_hash <password>")
        print("Example: python -m app.generate_password_hash mysecretpassword")
        sys.exit(1)
    
    password = sys.argv[1]
    hashed = get_password_hash(password)
    print(f"Password hash for '{password}':")
    print(hashed)
    print("\nAdd this to your .env file as:")
    print(f"ADMIN_PASSWORD_HASH={hashed}")


if __name__ == "__main__":
    main()
