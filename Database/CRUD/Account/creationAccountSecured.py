import bcrypt
import re
import datetime
from mysql.connector import Error, connect


# =====================================================
# GESTIONNAIRE DE BASE DE DONNÉES ET CONNEXION
# =====================================================

class DatabaseManager:
    """
    Classe pour gérer la connexion et les opérations de base de données.
    """

    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.conn = None

    def connect(self):
        try:
            self.conn = connect(**self.config)
            print("✅ Connexion à la base de données réussie!")
            return self.conn
        except Error as e:
            print(f"❌ Erreur de connexion à MySQL : {e}")
            return None

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("✅ Connexion à la base de données fermée.")


# =====================================================
# FONCTIONS DE VALIDATION ET SÉCURITÉ
# =====================================================

def password_is_personal_info(nom, prenom, username, password):
    """
    Vérifie si le mot de passe contient le nom, le prénom ou le nom d'utilisateur.
    """
    return nom.lower() in password.lower() or prenom.lower() in password.lower() or username.lower() in password.lower()


def hash_password(password):
    """
    Hache le mot de passe en utilisant Bcrypt.
    """
    # Bcrypt gère le salage automatiquement
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, stored_hash):
    """
    Vérifie si un mot de passe correspond au hash stocké.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:
        return False


def is_password_complex(password):
    """
    Vérifie la complexité du mot de passe.
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
            print("❌ Les mots de passe ne correspondent pas. Veuillez réessayer.")
            continue
        is_complex, message = is_password_complex(password)
        if not is_complex:
            print(f"❌ {message}")
            continue
        if password_is_personal_info(nom, prenom, username, password):
            print("❌ Le mot de passe ne doit pas contenir votre nom, prénom ou nom d'utilisateur. Veuillez réessayer.")
            continue

        return hash_password(password)


def is_valid_email(email):
    """Vérifie le format d'une adresse e-mail."""
    email_regex = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(email_regex, email) is not None


def is_valid_phone(phone):
    """Vérifie le format d'un numéro de téléphone."""
    phone_regex = r'^[0-9+\-\s()]+$'
    return re.match(phone_regex, phone) is not None and len(
        phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) >= 8


# =====================================================
# GESTION DES COMPTES (VERSION OPTIMISÉE)
# =====================================================

def get_role_id(conn, role_name):
    """Récupère l'ID d'un rôle par son nom."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_role FROM Role WHERE nom_role = %s", (role_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"❌ Erreur lors de la récupération de l'ID de rôle : {e}")
        return None


def creation_compte(conn, created_by_id=None):
    """Crée un nouveau compte avec la nouvelle structure."""
    print("\n--- Création d'un compte ---")
    nom = input("Entrez le nom : ").strip()
    prenom = input("Entrez le prénom : ").strip()
    while True:
        email = input("Entrez l'email : ").strip()
        if not is_valid_email(email):
            print("❌ L'adresse e-mail n'est pas valide. Veuillez réessayer.")
        else:
            break
    username = input("Entrez votre nom d'utilisateur : ").strip()

    while True:
        print("Rôles disponibles : admin, user, manager")
        role = input("Entrez le rôle : ").lower()
        if role in ['admin', 'user', 'manager']:
            break
        else:
            print("❌ Rôle invalide. Veuillez choisir entre 'admin', 'user' ou 'manager'.")

    hashed_password = get_valid_password(nom, prenom, username)
    role_id = get_role_id(conn, role)

    if not role_id:
        print("❌ Impossible de trouver l'ID du rôle. Création de compte annulée.")
        return

    try:
        cursor = conn.cursor()
        cursor.callproc('sp_creer_compte', [nom, prenom, username, email, hashed_password, role_id, created_by_id])
        for result in cursor.stored_results():
            row = result.fetchone()
            if row:
                print(f"✅ {row[0]} - ID: {row[1]}")
        conn.commit()
    except Error as e:
        print(f"❌ Erreur lors de la création du compte : {e}")
        if "déjà utilisé" in str(e):
            print("Cet email ou nom d'utilisateur est déjà utilisé. Veuillez en choisir un autre.")
        conn.rollback()


def lecture_compte(conn):
    """
    Affiche tous les comptes avec leurs rôles.
    """
    try:
        cursor = conn.cursor()
        query = """
                SELECT c.id_compte, \
                       c.nom_compte, \
                       c.prenom_compte, \
                       c.email, \
                       c.nom_utilisateur,
                       GROUP_CONCAT(r.nom_role SEPARATOR ', ') as roles,
                       c.statut_compte, \
                       c.derniere_connexion
                FROM Compte c
                         LEFT JOIN Compte_Role cr ON c.id_compte = cr.id_compte_fk
                         LEFT JOIN Role r ON cr.id_role_fk = r.id_role
                GROUP BY c.id_compte
                ORDER BY c.created_at DESC
                """
        cursor.execute(query)
        accounts = cursor.fetchall()
        if accounts:
            print("\n" + "=" * 120)
            print(
                f"{'ID':<5} {'Nom':<15} {'Prénom':<15} {'Email':<25} {'Username':<15} {'Rôles':<15} {'Statut':<10} {'Dernière Connexion':<20}")
            print("=" * 120)
            for account in accounts:
                last_login = account[7].strftime('%Y-%m-%d %H:%M') if account[7] else 'Jamais'
                print(f"{account[0]:<5} {account[1]:<15} {account[2]:<15} {account[3]:<25} {account[4]:<15} "
                      f"{account[5]:<15} {account[6]:<10} {last_login:<20}")
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
        cursor.execute("SELECT nom_compte, prenom_compte, nom_utilisateur, email FROM Compte WHERE id_compte = %s",
                       (account_id,))
        current_data = cursor.fetchone()
        if not current_data:
            print("❌ Aucun compte trouvé avec cet ID.")
            return
        nom_actuel, prenom_actuel, username_actuel, email_actuel = current_data

        print(f"\nInformations actuelles:")
        print(f"Nom: {nom_actuel}, Prénom: {prenom_actuel}, Username: {username_actuel}, Email: {email_actuel}")

        nom = input(f"Nouveau nom (Enter pour garder '{nom_actuel}') : ").strip() or nom_actuel
        prenom = input(f"Nouveau prénom (Enter pour garder '{prenom_actuel}') : ").strip() or prenom_actuel
        email = input(f"Nouvel email (Enter pour garder '{email_actuel}') : ").strip() or email_actuel
        username = input(f"Nouveau username (Enter pour garder '{username_actuel}') : ").strip() or username_actuel

        updates = {}
        if nom != nom_actuel: updates['nom_compte'] = nom
        if prenom != prenom_actuel: updates['prenom_compte'] = prenom
        if email != email_actuel: updates['email'] = email
        if username != username_actuel: updates['nom_utilisateur'] = username

        change_password = input("Changer le mot de passe ? (o/n) : ").strip().lower()
        if change_password == 'o':
            new_password_hash = get_valid_password(nom, prenom, username)
            updates['password_hash'] = new_password_hash

        if updates:
            updates['updated_by'] = updated_by_id
            updates['updated_at'] = datetime.datetime.now()

            query = f"UPDATE Compte SET {', '.join([f'{k} = %s' for k in updates.keys()])} WHERE id_compte = %s"
            params = list(updates.values())
            params.append(account_id)

            cursor.execute(query, tuple(params))
            conn.commit()
            print("✅ Compte mis à jour avec succès!")
        else:
            print("ℹ️ Aucune modification apportée.")

    except Error as e:
        print(f"❌ Erreur lors de la mise à jour : {e}")
        conn.rollback()


def suppression_compte(conn):
    """
    Supprime un compte après double confirmation.
    """
    print("\n--- Suppression d'un compte ---")
    account_id = input("Entrez l'ID du compte à supprimer : ").strip()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nom_compte, prenom_compte, email FROM Compte WHERE id_compte = %s", (account_id,))
        compte_info = cursor.fetchone()

        if not compte_info:
            print("❌ Aucun compte trouvé avec cet ID.")
            return

        nom, prenom, email = compte_info
        print(f"\n⚠️ Vous êtes sur le point de supprimer le compte :")
        print(f"   Nom: {nom} {prenom}")
        print(f"   Email: {email}")

        confirm1 = input("\nÊtes-vous sûr ? Tapez 'SUPPRIMER' pour confirmer : ")
        if confirm1 != 'SUPPRIMER':
            print("❌ Suppression annulée.")
            return

        confirm2 = input("Dernière confirmation. Tapez 'OUI' : ")
        if confirm2 != 'OUI':
            print("❌ Suppression annulée.")
            return

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
    Crée un nouveau prospect avec la structure optimisée, incluant l'adresse.
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

    # Création de l'adresse
    print("\n--- Informations d'adresse ---")
    ligne1 = input("Ligne 1 de l'adresse : ").strip()
    ligne2 = input("Ligne 2 de l'adresse (optionnel) : ").strip() or None
    code_postal = input("Code postal (optionnel) : ").strip() or None
    ville = input("Ville (optionnel) : ").strip() or None
    pays = input("Pays (défaut: Madagascar) : ").strip() or 'Madagascar'

    try:
        cursor = conn.cursor()
        # Insertion dans la table Adresse
        cursor.execute("INSERT INTO Adresse (ligne1, ligne2, code_postal, ville, pays) VALUES (%s, %s, %s, %s, %s)",
                       (ligne1, ligne2, code_postal, ville, pays))
        id_adresse = cursor.lastrowid

        # Insertion dans la table Prospect
        query = """
                INSERT INTO Prospect (nom_prospect, prenom_prospect, email_prospect, telephone_prospect,
                                      id_adresse_fk, source_prospect, priorite, valeur_estimee,
                                      resume_prospect, id_compte_fk, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
        print("Sources disponibles : web, telephone, email, referral, publicite, autre")
        source = input("Source du prospect : ").strip().lower()
        source = source if source in ['web', 'telephone', 'email', 'referral', 'publicite', 'autre'] else None

        print("Priorités disponibles : basse, normale, haute, urgente")
        priorite = input("Priorité (défaut: normale) : ").strip().lower() or 'normale'
        priorite = priorite if priorite in ['basse', 'normale', 'haute', 'urgente'] else 'normale'

        valeur_estimee_str = input("Valeur estimée (optionnel) : ").strip()
        valeur_estimee = float(valeur_estimee_str) if valeur_estimee_str and valeur_estimee_str.replace('.', '',
                                                                                                        1).isdigit() else None

        resume = input("Résumé/Notes (optionnel) : ").strip() or None

        cursor.execute(query, (nom, prenom, email, telephone, id_adresse, source, priorite, valeur_estimee,
                               resume, created_by_id, created_by_id))
        conn.commit()

        prospect_id = cursor.lastrowid
        print(f"✅ Prospect créé avec succès ! ID: {prospect_id}")
    except Error as e:
        print(f"❌ Erreur lors de la création du prospect : {e}")
        conn.rollback()


def lecture_prospects(conn):
    """
    Affiche les prospects avec leurs informations complètes à partir de la vue.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM v_prospect_complet ORDER BY date_creation DESC LIMIT 50")
        prospects = cursor.fetchall()

        if prospects:
            print("\n" + "=" * 150)
            print("LISTE DES PROSPECTS (50 plus récents)")
            print("=" * 150)

            for p in prospects:
                print(f"ID: {p[0]:<5} | Nom: {p[1]:<15} Prénom: {p[2]:<15} | Email: {p[3]:<25}")
                print(f"   📞 Téléphone: {p[4]:<15} | Adresse: {p[5] or 'N/A'}")
                print(f"   📍 Ville: {p[7] or 'N/A'}, {p[8] or 'N/A'}")
                print(f"   📊 Statut: {p[9]:<15} | Priorité: {p[10]:<10}")
                print(f"   💰 Valeur: {p[11] or 'N/A':<10} | Créé le: {p[12]}")
                print(f"   👤 Gestionnaire: {p[14] or 'Non assigné'}")
                print(f"   📧 Communications: {p[16]} | 📋 Tâches ouvertes: {p[17]}")
                print("-" * 150)
        else:
            print("❌ Aucun prospect trouvé.")
    except Error as e:
        print(f"❌ Erreur lors de la lecture des prospects : {e}")


def dashboard_utilisateur(conn, user_id=None):
    """
    Affiche le tableau de bord d'un utilisateur ou de tous les utilisateurs.
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

    conn = connect()
    if not conn:
        print("Le programme ne peut pas continuer sans connexion à la base de données.")
        return

    current_user_id = None

    # Vérification et proposition de création d'un premier admin
    try:
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT COUNT(*)
                       FROM Compte c
                                JOIN Compte_Role cr ON c.id_compte = cr.id_compte_fk
                                JOIN Role r ON cr.id_role_fk = r.id_role
                       WHERE r.nom_role = 'admin'
                         AND c.statut_compte = 'actif'
                       """)
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            print("\n🚨 ATTENTION: Aucun administrateur détecté dans le système!")
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
                hashed_password = get_valid_password(nom, prenom, username)
                role_id = get_role_id(conn, 'admin')

                cursor.callproc('sp_creer_compte', [nom, prenom, username, email, hashed_password, role_id, None])
                for result in cursor.stored_results():
                    row = result.fetchone()
                    if row:
                        print(f"✅ Premier administrateur créé avec succès!")
                conn.commit()

    except Error as e:
        print(f"❌ Erreur lors de la vérification des administrateurs : {e}")
        db_manager.close()
        return

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
        except Error as e:
            print(f"❌ Erreur de base de données : {e}")
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")



if __name__ == "__main__":
    main()