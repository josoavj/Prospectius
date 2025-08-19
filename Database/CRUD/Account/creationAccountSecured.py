import bcrypt
import re
import hashlib
import secrets
import datetime
from mysql.connector import Error
from Database.CRUD.connexionDB import connect


# =====================================================
# FONCTIONS DE VALIDATION ET SÉCURITÉ
# =====================================================

def password_is_personal_info(nom, prenom, username, password):
    """
    Vérifie si le mot de passe contient le nom, le prénom ou le nom d'utilisateur.
    """
    return nom.lower() in password.lower() or prenom.lower() in password.lower() or username.lower() in password.lower()


def hash_password_with_salt(password):
    """
    Hache le mot de passe en utilisant SHA256 + salt personnalisé (compatible avec la DB)
    """
    # Générer un salt aléatoire de 32 caractères
    salt = secrets.token_hex(16)  # 32 caractères hexadécimaux

    # Combiner le mot de passe et le salt, puis hacher avec SHA256
    password_salt_combo = password + salt
    hashed_password = hashlib.sha256(password_salt_combo.encode()).hexdigest()

    return hashed_password, salt


def verify_password(password, stored_hash, stored_salt):
    """
    Vérifie si un mot de passe correspond au hash stocké
    """
    password_salt_combo = password + stored_salt
    computed_hash = hashlib.sha256(password_salt_combo.encode()).hexdigest()
    return computed_hash == stored_hash


def is_password_complex(password):
    """
    Vérifie la complexité du mot de passe (nouvelle règle renforcée)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."

    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule."

    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule."

    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."

    return True, "Mot de passe valide."


def get_valid_password(nom, prenom, username):
    """
    Demande un mot de passe à l'utilisateur, le valide et le hache.
    """
    while True:
        password = input("Entrez votre nouveau mot de passe : ")
        confirm_password = input("Confirmez votre nouveau mot de passe : ")

        if password != confirm_password:
            print("Les mots de passe ne correspondent pas. Veuillez réessayer.")
            continue

        is_complex, message = is_password_complex(password)
        if not is_complex:
            print(message)
            continue

        if password_is_personal_info(nom, prenom, username, password):
            print("Le mot de passe ne doit pas contenir votre nom, prénom ou nom d'utilisateur. Veuillez réessayer.")
            continue

        return hash_password_with_salt(password)


def is_valid_email(email):
    """
    Vérifie le format d'une adresse e-mail en utilisant une expression régulière renforcée.
    """
    email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(email_regex, email) is not None


def is_valid_phone(phone):
    """
    Vérifie le format d'un numéro de téléphone
    """
    phone_regex = r'^[0-9+\-\s()]+$'
    return re.match(phone_regex, phone) is not None and len(
        phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) >= 8


# =====================================================
# GESTION DES COMPTES (VERSION OPTIMISÉE)
# =====================================================

def creation_compte(conn, created_by_id=None):
    """
    Guide l'utilisateur dans la création d'un nouveau compte avec la nouvelle structure.
    """
    print("\n--- Création d'un compte ---")
    nom = input("Entrez le nom : ").strip()
    prenom = input("Entrez le prénom : ").strip()

    while True:
        email = input("Entrez l'email : ").strip()
        if not is_valid_email(email):
            print("L'adresse e-mail n'est pas valide. Veuillez réessayer.")
        else:
            break

    username = input("Entrez votre nom d'utilisateur : ").strip()

    # Demander le rôle de l'utilisateur (avec le nouveau rôle manager)
    while True:
        print("Rôles disponibles : admin, user, manager")
        role = input("Entrez le rôle : ").lower()
        if role in ['admin', 'user', 'manager']:
            break
        else:
            print("Rôle invalide. Veuillez choisir entre 'admin', 'user' ou 'manager'.")

    hashed_password, salt = get_valid_password(nom, prenom, username)

    try:
        cursor = conn.cursor()

        # Utiliser la procédure stockée mise à jour avec le salt
        cursor.callproc('sp_creer_compte', [nom, prenom, username, email,
                                            hashed_password, salt, role, created_by_id])

        # Récupérer le résultat
        for result in cursor.stored_results():
            row = result.fetchone()
            if row:
                print(f"✅ {row[0]} - ID: {row[1]}")

        conn.commit()

    except Error as e:
        print(f"❌ Erreur lors de la création du compte : {e}")
        if e.errno == 1062 or "déjà utilisé" in str(e):
            print("Cet email ou nom d'utilisateur est déjà utilisé. Veuillez en choisir un autre.")
        conn.rollback()


def lecture_compte(conn):
    """
    Affiche tous les comptes existants avec les nouvelles informations.
    """
    try:
        cursor = conn.cursor()
        query = """
                SELECT c.id_compte, \
                       c.nom_compte, \
                       c.prenom_compte, \
                       c.email, \
                       c.nom_utilisateur,
                       c.role_compte, \
                       c.statut_compte, \
                       c.derniere_connexion, \
                       c.created_at,
                       CASE WHEN a.id_admin IS NOT NULL THEN 'Oui' ELSE 'Non' END as est_admin
                FROM Compte c
                         LEFT JOIN Administrateur a ON c.id_compte = a.id_admin
                ORDER BY c.created_at DESC \
                """
        cursor.execute(query)
        accounts = cursor.fetchall()

        if accounts:
            print("\n" + "=" * 120)
            print(
                f"{'ID':<5} {'Nom':<15} {'Prénom':<15} {'Email':<25} {'Username':<15} {'Rôle':<10} {'Statut':<10} {'Admin':<8} {'Dernière Connexion':<20}")
            print("=" * 120)

            for account in accounts:
                last_login = account[7].strftime('%Y-%m-%d %H:%M') if account[7] else 'Jamais'
                print(f"{account[0]:<5} {account[1]:<15} {account[2]:<15} {account[3]:<25} {account[4]:<15} "
                      f"{account[5]:<10} {account[6]:<10} {account[9]:<8} {last_login:<20}")
        else:
            print("\n❌ Aucun compte trouvé dans la base de données.")

    except Error as e:
        print(f"❌ Erreur lors de la lecture des comptes : {e}")


def update_compte(conn, updated_by_id=None):
    """
    Met à jour un compte existant avec la nouvelle structure.
    """
    print("\n--- Mise à jour d'un compte ---")
    account_id = input("Entrez l'ID du compte à mettre à jour : ").strip()

    try:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT nom_compte, prenom_compte, nom_utilisateur, email, role_compte, statut_compte
                       FROM Compte
                       WHERE id_compte = %s
                       """, (account_id,))
        current_data = cursor.fetchone()

        if not current_data:
            print("❌ Aucun compte trouvé avec cet ID.")
            return

        nom_actuel, prenom_actuel, username_actuel, email_actuel, role_actuel, statut_actuel = current_data

        print(f"\nInformations actuelles:")
        print(f"Nom: {nom_actuel}")
        print(f"Prénom: {prenom_actuel}")
        print(f"Username: {username_actuel}")
        print(f"Email: {email_actuel}")
        print(f"Rôle: {role_actuel}")
        print(f"Statut: {statut_actuel}")

    except Error as e:
        print(f"❌ Erreur lors de la récupération des données : {e}")
        return

    # Collecte des nouvelles informations
    nom = input(f"Nouveau nom (Enter pour garder '{nom_actuel}') : ").strip() or nom_actuel
    prenom = input(f"Nouveau prénom (Enter pour garder '{prenom_actuel}') : ").strip() or prenom_actuel

    email = input(f"Nouvel email (Enter pour garder '{email_actuel}') : ").strip()
    if email and not is_valid_email(email):
        print("❌ Email invalide, conservation de l'ancien.")
        email = email_actuel
    elif not email:
        email = email_actuel

    username = input(f"Nouveau username (Enter pour garder '{username_actuel}') : ").strip() or username_actuel

    # Gestion du rôle
    nouveau_role = input(f"Nouveau rôle - admin/user/manager (Enter pour garder '{role_actuel}') : ").strip().lower()
    if nouveau_role and nouveau_role in ['admin', 'user', 'manager']:
        role = nouveau_role
    else:
        role = role_actuel

    # Gestion du statut
    nouveau_statut = input(
        f"Nouveau statut - actif/inactif/suspendu (Enter pour garder '{statut_actuel}') : ").strip().lower()
    if nouveau_statut and nouveau_statut in ['actif', 'inactif', 'suspendu']:
        statut = nouveau_statut
    else:
        statut = statut_actuel

    # Mot de passe
    change_password = input("Changer le mot de passe ? (o/n) : ").strip().lower()
    password_hashed = None
    salt = None
    if change_password == 'o':
        password_hashed, salt = get_valid_password(nom, prenom, username)

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
        if email != email_actuel:
            updates.append("email = %s")
            params.append(email)
        if username != username_actuel:
            updates.append("nom_utilisateur = %s")
            params.append(username)
        if role != role_actuel:
            updates.append("role_compte = %s")
            params.append(role)
        if statut != statut_actuel:
            updates.append("statut_compte = %s")
            params.append(statut)
        if password_hashed and salt:
            updates.append("password = %s, salt = %s")
            params.extend([password_hashed, salt])
        if updated_by_id:
            updates.append("updated_by = %s")
            params.append(updated_by_id)

        if updates:
            query = f"UPDATE Compte SET {', '.join(updates)} WHERE id_compte = %s"
            params.append(account_id)
            cursor.execute(query, tuple(params))

            # Gérer les privilèges admin
            if role == 'admin' and role_actuel != 'admin':
                cursor.execute("INSERT IGNORE INTO Administrateur (id_admin, niveau_acces) VALUES (%s, 'admin')",
                               (account_id,))
            elif role != 'admin' and role_actuel == 'admin':
                cursor.execute("DELETE FROM Administrateur WHERE id_admin = %s", (account_id,))

            conn.commit()
            print("✅ Compte mis à jour avec succès !")
        else:
            print("ℹ️ Aucune modification apportée.")

    except Error as e:
        print(f"❌ Erreur lors de la mise à jour : {e}")
        conn.rollback()


def check_and_create_first_admin(conn):
    """
    Vérifie s'il existe au moins un administrateur. Si aucun, propose d'en créer un.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Compte WHERE role_compte = 'admin' AND statut_compte = 'actif'")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            print("\n🚨 ATTENTION: Aucun administrateur détecté dans le système!")
            print("Pour une utilisation optimale, il est recommandé de créer au moins un compte administrateur.")

            create_admin = input("\nVoulez-vous créer un compte administrateur maintenant ? (o/n) : ").strip().lower()
            if create_admin == 'o':
                print("\n--- Création du premier administrateur ---")

                nom = input("Nom de l'administrateur : ").strip()
                prenom = input("Prénom de l'administrateur : ").strip()

                while True:
                    email = input("Email de l'administrateur : ").strip()
                    if not is_valid_email(email):
                        print("❌ Email invalide.")
                    else:
                        break

                username = input("Nom d'utilisateur de l'administrateur : ").strip()

                print("\n⚠️ Définition du mot de passe administrateur (respectez les règles de sécurité)")
                hashed_password, salt = get_valid_password(nom, prenom, username)

                try:
                    cursor.callproc('sp_creer_compte', [nom, prenom, username, email,
                                                        hashed_password, salt, 'admin', None])

                    for result in cursor.stored_results():
                        row = result.fetchone()
                        if row:
                            print(f"✅ Premier administrateur créé avec succès!")
                            print(f"   ID: {row[1]}")
                            print(f"   Email: {email}")
                            print(f"   Nom d'utilisateur: {username}")

                    conn.commit()
                    return True

                except Error as e:
                    print(f"❌ Erreur lors de la création de l'administrateur : {e}")
                    conn.rollback()
                    return False

        return True

    except Error as e:
        print(f"❌ Erreur lors de la vérification des administrateurs : {e}")
        return False
    """
    Supprime un compte après double confirmation.
    """
    print("\n--- Suppression d'un compte ---")
    account_id = input("Entrez l'ID du compte à supprimer : ").strip()

    try:
        cursor = conn.cursor()
        # Vérifier que le compte existe et obtenir ses infos
        cursor.execute("SELECT nom_compte, prenom_compte, email, role_compte FROM Compte WHERE id_compte = %s",
                       (account_id,))
        compte_info = cursor.fetchone()

        if not compte_info:
            print("❌ Aucun compte trouvé avec cet ID.")
            return

        nom, prenom, email, role = compte_info
        print(f"\n⚠️ Vous êtes sur le point de supprimer le compte :")
        print(f"   Nom: {nom} {prenom}")
        print(f"   Email: {email}")
        print(f"   Rôle: {role}")

        # Double confirmation
        confirm1 = input("\nÊtes-vous sûr ? Tapez 'SUPPRIMER' pour confirmer : ")
        if confirm1 != 'SUPPRIMER':
            print("❌ Suppression annulée.")
            return

        confirm2 = input("Dernière confirmation. Tapez 'OUI' : ")
        if confirm2 != 'OUI':
            print("❌ Suppression annulée.")
            return

        # Vérification admin pour comptes admin
        if role == 'admin':
            admin_password = input("Mot de passe d'un autre administrateur requis : ")

            cursor.execute("""
                           SELECT c.password, c.salt
                           FROM Compte c
                                    JOIN Administrateur a ON c.id_compte = a.id_admin
                           WHERE c.id_compte != %s
                             AND c.statut_compte = 'actif'
                           """, (account_id,))
            admin_accounts = cursor.fetchall()

            is_admin_password_correct = False
            for stored_hash, stored_salt in admin_accounts:
                if verify_password(admin_password, stored_hash, stored_salt):
                    is_admin_password_correct = True
                    break

            if not is_admin_password_correct:
                print("❌ Mot de passe administrateur incorrect. Suppression annulée.")
                return

        # Procéder à la suppression
        cursor.execute("DELETE FROM Compte WHERE id_compte = %s", (account_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print("✅ Compte supprimé avec succès !")
        else:
            print("❌ Erreur lors de la suppression.")

    except Error as e:
        print(f"❌ Erreur lors de la suppression : {e}")
        conn.rollback()


# =====================================================
# NOUVELLES FONCTIONS POUR LES PROSPECTS
# =====================================================

def creation_prospect(conn, created_by_id=None):
    """
    Crée un nouveau prospect avec la structure optimisée.
    """
    print("\n--- Création d'un prospect ---")

    nom = input("Nom du prospect : ").strip()
    prenom = input("Prénom du prospect : ").strip()

    while True:
        email = input("Email du prospect : ").strip()
        if not is_valid_email(email):
            print("❌ Email invalide.")
        else:
            break

    while True:
        telephone = input("Téléphone du prospect : ").strip()
        if not is_valid_phone(telephone):
            print("❌ Numéro de téléphone invalide.")
        else:
            break

    adresse = input("Adresse complète : ").strip()
    code_postal = input("Code postal (optionnel) : ").strip() or None
    ville = input("Ville (optionnel) : ").strip() or None
    pays = input("Pays (défaut: Madagascar) : ").strip() or 'Madagascar'

    print("Sources disponibles : web, telephone, email, referral, publicite, autre")
    source = input("Source du prospect : ").strip().lower()
    if source not in ['web', 'telephone', 'email', 'referral', 'publicite', 'autre']:
        source = None

    print("Priorités disponibles : basse, normale, haute, urgente")
    priorite = input("Priorité (défaut: normale) : ").strip().lower() or 'normale'
    if priorite not in ['basse', 'normale', 'haute', 'urgente']:
        priorite = 'normale'

    valeur_estimee = input("Valeur estimée (optionnel) : ").strip()
    try:
        valeur_estimee = float(valeur_estimee) if valeur_estimee else None
    except ValueError:
        valeur_estimee = None

    resume = input("Résumé/Notes (optionnel) : ").strip() or None

    try:
        cursor = conn.cursor()
        query = """
                INSERT INTO Prospect (nom_prospect, prenom_prospect, email_prospect, telephone_prospect,
                                      adresse_prospect, code_postal, ville, pays, resume_prospect,
                                      source_prospect, priorite, valeur_estimee, id_compte_fk, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                """
        cursor.execute(query, (nom, prenom, email, telephone, adresse, code_postal, ville, pays,
                               resume, source, priorite, valeur_estimee, created_by_id, created_by_id))
        conn.commit()

        prospect_id = cursor.lastrowid
        print(f"✅ Prospect créé avec succès ! ID: {prospect_id}")

    except Error as e:
        print(f"❌ Erreur lors de la création du prospect : {e}")
        conn.rollback()


def lecture_prospects(conn):
    """
    Affiche les prospects avec leurs informations complètes.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM v_prospect_complet ORDER BY date_creation DESC LIMIT 50")
        prospects = cursor.fetchall()

        if prospects:
            print("\n" + "=" * 150)
            print("LISTE DES PROSPECTS (50 plus récents)")
            print("=" * 150)

            for prospect in prospects:
                print(f"ID: {prospect[0]:<5} | {prospect[1]} {prospect[2]:<15} | {prospect[3]:<25}")
                print(f"   📞 {prospect[4]:<15} | Statut: {prospect[5]:<15} | Priorité: {prospect[6]:<10}")
                print(
                    f"   💰 {prospect[7] or 'N/A':<10} | Gestionnaire: {prospect[8] or 'Non assigné'} {prospect[9] or ''}")
                print(f"   📧 {prospect[11]} Communications | 📋 {prospect[12]} Tâches ouvertes")
                print("-" * 150)
        else:
            print("❌ Aucun prospect trouvé.")

    except Error as e:
        print(f"❌ Erreur lors de la lecture des prospects : {e}")


def dashboard_utilisateur(conn, user_id=None):
    """
    Affiche le tableau de bord d'un utilisateur.
    """
    try:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM v_dashboard_utilisateur WHERE id_compte = %s", (user_id,))
        else:
            cursor.execute("SELECT * FROM v_dashboard_utilisateur")

        dashboards = cursor.fetchall()

        if dashboards:
            print("\n" + "=" * 100)
            print("TABLEAU DE BORD UTILISATEURS")
            print("=" * 100)

            for dash in dashboards:
                print(f"👤 {dash[1]} {dash[2]}")
                print(f"   📊 Total prospects: {dash[3]} | En attente: {dash[4]} | Acceptés: {dash[5]}")
                print(f"   📋 Tâches en attente: {dash[6]} | En retard: {dash[7]}")
                print(f"   💰 Valeur totale acceptée: {dash[8] or 0:.2f}")
                print("-" * 100)
        else:
            print("❌ Aucune donnée de tableau de bord disponible.")

    except Error as e:
        print(f"❌ Erreur lors de l'affichage du tableau de bord : {e}")


# =====================================================
# MENU PRINCIPAL OPTIMISÉ
# =====================================================

def main():
    """
    Menu principal avec vérification automatique des administrateurs.
    """
    print("🔌 Connexion à la base de données...")
    conn = connect()
    if not conn:
        print("❌ Impossible de se connecter à la base de données.")
        return

    # Vérifier et proposer la création d'un premier admin si nécessaire
    if not check_and_create_first_admin(conn):
        print("⚠️ Impossible de continuer sans administrateur système.")
        conn.close()
        return

    current_user_id = None  # Dans une vraie application, ceci serait obtenu via l'authentification

    while True:
        print("\n" + "=" * 60)
        print("🏢 PROSPECTIUS - SYSTÈME DE GESTION")
        print("=" * 60)
        print("GESTION DES COMPTES:")
        print("1. 👤 Créer un compte")
        print("2. 📋 Lister les comptes")
        print("3. ✏️  Mettre à jour un compte")
        print("4. 🗑️  Supprimer un compte")
        print("\nGESTION DES PROSPECTS:")
        print("5. 🆕 Créer un prospect")
        print("6. 📊 Lister les prospects")
        print("7. 📈 Tableau de bord")
        print("\nSYSTÈME:")
        print("8. 🧹 Nettoyer les données obsolètes")
        print("9. 🔄 Assignment automatique des prospects")
        print("0. 🚪 Quitter")

        choice = input("\n🔹 Choisissez une option : ").strip()

        try:
            if choice == '1':
                creation_compte(conn, current_user_id)
            elif choice == '2':
                lecture_compte(conn)
            elif choice == '3':
                update_compte(conn, current_user_id)
            elif choice == '4':
                suppression_compte(conn)
            elif choice == '5':
                creation_prospect(conn, current_user_id)
            elif choice == '6':
                lecture_prospects(conn)
            elif choice == '7':
                dashboard_utilisateur(conn, current_user_id)
            elif choice == '8':
                cursor = conn.cursor()
                cursor.callproc('sp_nettoyage_donnees')
                for result in cursor.stored_results():
                    print(f"✅ {result.fetchone()[0]}")
                conn.commit()
            elif choice == '9':
                cursor = conn.cursor()
                cursor.callproc('sp_assigner_prospects_automatiquement')
                for result in cursor.stored_results():
                    print(f"✅ {result.fetchone()[0]}")
                conn.commit()
            elif choice == '0':
                break
            else:
                print("❌ Option invalide. Veuillez réessayer.")
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")

    conn.close()
    print("✅ Déconnexion de la base de données. À bientôt !")


if __name__ == "__main__":
    main()