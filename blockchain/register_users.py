"""
Responsabilité :
Point d'entrée pour l'enregistrement de nouveaux utilisateurs.
"""

from users import UserManager, UserAlreadyExists, InvalidEmail

def register_new_user():
    print("=== Enregistrement d'un nouvel utilisateur ===")

    name = input("Entrez votre nom : ").strip()
    email = input("Entrez votre email : ").strip()
    password = input("Entrez votre mot de passe : ").strip()
    confirm_password = input("Confirmez votre mot de passe : ").strip()

    if password != confirm_password:
        print("[ERREUR] Les mots de passe ne correspondent pas.")
        return

    if "@" not in email:
        print("[ERREUR] Email invalide.")
        return

    user_manager = UserManager()

    try:
        user_manager.register_user(name, email, password)
        print("\n✅ Enregistrement réussi !")
        print(f"Bienvenue, {name} !")
    except UserAlreadyExists as e:
        print(f"[ERREUR] Échec de l'enregistrement : {e}")
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue : {e}")

if __name__ == "__main__":
    register_new_user()