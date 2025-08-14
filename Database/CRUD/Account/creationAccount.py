# Fichier: creation_compte.py

import bcrypt
import re
from mysql.connector import Error
from connexionDB import connect  # Importe la fonction de connexion


# Fonction pour vérifier si le mot de passe correspond aux informations personnelles
def password_is_personal_info(nom, prenom, username, password):
    """
    Vérifie si le mot de passe contient le nom, le prénom ou le nom d'utilisateur.
    """
    return nom.lower() in password.lower() or prenom.lower() in password.lower() or username.lower() in password.lower()


# Fonction pour hacher le mot de passe avec bcrypt
def hash_password(password):
    """
    Hache le mot de passe en utilisant l'algorithme bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


# Fonction pour demander un mot de passe valide et haché
def get_valid_password(nom, prenom, username):
    """
    Demande un mot de passe à l'utilisateur, le valide et le hache.
    """
    while True:
        password = input("Entrez votre nouveau mot de passe : ")
        confirm_password = input("Confirmez votre nouveau mot de passe : ")

        if password != confirm_password:
            print("Les mots de passe ne correspondent pas. Veuillez réessayer.")
        elif len(password) < 8:
            print("Le mot de passe doit contenir au moins 8 caractères.")
        elif password_is_personal_info(nom, prenom, username, password):
            print("Le mot de passe ne doit pas contenir votre nom, prénom ou nom d'utilisateur. Veuillez réessayer.")
        else:
            return hash_password(password)


def is_valid_email(email):
    """
    Vérifie le format d'une adresse e-mail en utilisant une expression régulière.
    """
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return re.match(email_regex, email) is not None


def creation_compte(conn):
    """
    Guide l'utilisateur dans la création d'un nouveau compte et l'insère dans la base de données.
    """
    print("\n--- Création d'un compte ---")
    nom = input("Entrez le nom : ")
    prenom = input("Entrez le prénom : ")
    while True:
        email = input("Entrez l'email : ")
        if not is_valid_email(email):
            print("L'adresse e-mail n'est pas valide. Veuillez réessayer.")
        else:
            break
    username = input("Entrez votre nom d'utilisateur : ")
    # Demander le rôle de l'utilisateur
    while True:
        role = input("Entrez le rôle (admin/utilisateur) : ").lower()
        if role in ['admin', 'utilisateur']:
            break
        else:
            print("Rôle invalide. Veuillez choisir entre 'admin' ou 'utilisateur'.")
    password = get_valid_password(nom, prenom, username)

    try:
        cursor = conn.cursor()
        query = """
                INSERT INTO Compte (nom_compte, prenom_compte, email, nom_utilisateur, mot_de_passe_hache, role_compte)
                VALUES (%s, %s, %s, %s, %s, %s) \
                """
        cursor.execute(query, (nom, prenom, email, username, password.decode('utf-8'), role))
        conn.commit()
        print("Compte créé avec succès !")
    except Error as e:
        print(f"Erreur lors de la création du compte : {e}")
        # Gérer l'erreur si l'email existe déjà
        if e.errno == 1062:  # Numéro d'erreur pour les doublons
            print("Cet email est déjà utilisé. Veuillez en choisir un autre.")
        conn.rollback()  # Annule les modifications en cas d'erreur


# Pour voir les comptes existants
def lecture_compte(conn):
    """
    Affiche tous les comptes existants dans la base de données.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_compte, nom_compte, prenom_compte, email, nom_utilisateur, role_compte FROM Compte")
        accounts = cursor.fetchall()

        if accounts:
            print("\n--- Liste des comptes ---")
            for account in accounts:
                print(
                    f"ID: {account[0]}, Nom: {account[1]}, Prénom: {account[2]}, Email: {account[3]}, Nom d'utilisateur: {account[4]}, Rôle: {account[5]}")
        else:
            print("\nAucun compte trouvé dans la base de données.")

    except Error as e:
        print(f"Erreur lors de la lecture des comptes : {e}")


# Fonction pour mettre à jour un compte
def update_compte(conn):
    """
    Met à jour un compte existant dans la base de données.
    """
    print("\n--- Mise à jour d'un compte ---")
    account_id = input("Entrez l'ID du compte à mettre à jour : ")
    # On pourrait ici vérifier que l'ID existe avant de continuer

    # Récupérer les informations actuelles du compte pour la validation du mot de passe
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nom_compte, prenom_compte, nom_utilisateur FROM Compte WHERE id_compte = %s",
                       (account_id,))
        current_data = cursor.fetchone()
        if not current_data:
            print("Aucun compte trouvé avec cet ID.")
            return
        nom_actuel, prenom_actuel, username_actuel = current_data

    except Error as e:
        print(f"Erreur lors de la récupération des données du compte : {e}")
        return

    nom = input(f"Nouveau nom (actuel: {nom_actuel}, laissez vide pour ne pas modifier) : ") or nom_actuel
    prenom = input(f"Nouveau prénom (actuel: {prenom_actuel}, laissez vide pour ne pas modifier) : ") or prenom_actuel
    email = input(f"Nouvel email (laissez vide pour ne pas modifier) : ")
    while email and not is_valid_email(email):
        print("L'adresse e-mail n'est pas valide. Veuillez réessayer.")
        email = input(f"Nouvel email (laissez vide pour ne pas modifier) : ")

    username = input(
        f"Nouveau nom d'utilisateur (actuel: {username_actuel}, laissez vide pour ne pas modifier) : ") or username_actuel

    password = input("Nouveau mot de passe (laissez vide pour ne pas modifier) : ")
    password_hashed = None
    if password:
        password_hashed = get_valid_password(nom, prenom, username)

    try:
        cursor = conn.cursor()
        updates = []
        params = []

        if nom != nom_actuel:
            updates.append("nom_compte = %s")
            params.append(nom)
        if prenom != prenom_actuel:
            updates.append("prenom_compte = %s")
            params.append(prenom)
        if email:
            updates.append("email = %s")
            params.append(email)
        if username != username_actuel:
            updates.append("nom_utilisateur = %s")
            params.append(username)
        if password_hashed:
            updates.append("mot_de_passe_hache = %s")
            params.append(password_hashed.decode('utf-8'))

        if updates:
            query = f"UPDATE Compte SET {', '.join(updates)} WHERE id_compte = %s"
            params.append(account_id)
            cursor.execute(query, tuple(params))
            conn.commit()
            print("Compte mis à jour avec succès !")
        else:
            print("Aucune modification apportée.")
    except Error as e:
        print(f"Erreur lors de la mise à jour du compte : {e}")
        conn.rollback()


def suppression_compte(conn):
    """
    Supprime un compte après confirmation par le mot de passe administrateur.
    """
    print("\n--- Suppression d'un compte ---")
    account_id = input("Entrez l'ID du compte à supprimer : ")
    admin_password = input("Entrez le mot de passe d'un compte administrateur pour confirmer : ")

    try:
        cursor = conn.cursor()
        # On vérifie si le mot de passe admin est correct
        cursor.execute("SELECT mot_de_passe_hache FROM Compte WHERE role_compte = 'admin'")
        admin_passwords = cursor.fetchall()

        is_admin_password_correct = False
        for hashed_password in admin_passwords:
            if bcrypt.checkpw(admin_password.encode('utf-8'), hashed_password[0].encode('utf-8')):
                is_admin_password_correct = True
                break

        if is_admin_password_correct:
            cursor.execute("DELETE FROM Compte WHERE id_compte = %s", (account_id,))
            conn.commit()
            print("Compte supprimé avec succès !")
        else:
            print("Mot de passe administrateur incorrect. Suppression annulée.")
    except Error as e:
        print(f"Erreur lors de la suppression du compte : {e}")
        conn.rollback()


# Menu principal
def main():
    """
    Point d'entrée principal du programme, gère le menu et les appels de fonctions.
    """
    conn = connect()
    if not conn:
        print("Le programme ne peut pas continuer sans connexion à la base de données.")
        return

    while True:
        print("\n--- Menu Principal ---")
        print("1. Créer un compte")
        print("2. Lister les comptes")
        print("3. Mettre à jour un compte")
        print("4. Supprimer un compte")
        print("5. Quitter")
        choice = input("Choisissez une option : ")

        if choice == '1':
            creation_compte(conn)
        elif choice == '2':
            lecture_compte(conn)
        elif choice == '3':
            update_compte(conn)
        elif choice == '4':
            suppression_compte(conn)
        elif choice == '5':
            break
        else:
            print("Option invalide. Veuillez réessayer.")

    conn.close()
    print("Déconnexion de la base de données.")


if __name__ == "__main__":
    main()
