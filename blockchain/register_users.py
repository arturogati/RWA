"""
Responsibilities:
Entry point for new user registration.
"""

from users import UserManager, UserAlreadyExists, InvalidEmail

def register_new_user():
    print("=== New User Registration ===")

    name = input("Enter your name: ").strip()
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()
    confirm_password = input("Confirm password: ").strip()

    if password != confirm_password:
        print("[ERROR] Passwords don't match.")
        return

    if "@" not in email:
        print("[ERROR] Invalid email format.")
        return

    user_manager = UserManager()

    try:
        user_manager.register_user(name, email, password)
        print("\n✅ Registration successful!")
        print(f"Welcome, {name}!")
    except UserAlreadyExists as e:
        print(f"[ERROR] Registration failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    register_new_user()