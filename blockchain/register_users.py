"""
Ответственность:
Точка входа для регистрации новых пользователей.
"""

from users import UserManager, UserAlreadyExists, InvalidEmail

def register_new_user():
    print("=== Регистрация нового пользователя ===")

    name = input("Введите ваше имя: ").strip()
    email = input("Введите email: ").strip()
    password = input("Введите пароль: ").strip()
    confirm_password = input("Подтвердите пароль: ").strip()

    if password != confirm_password:
        print("[ERROR] Пароли не совпадают.")
        return

    if "@" not in email:
        print("[ERROR] Некорректный email.")
        return

    user_manager = UserManager()

    try:
        user_manager.register_user(name, email, password)
        print("\n✅ Регистрация успешна!")
        print(f"Приветствуем, {name}!")
    except UserAlreadyExists as e:
        print(f"[ERROR] Не удалось зарегистрироваться: {e}")
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")

if __name__ == "__main__":
    register_new_user()