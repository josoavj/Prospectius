import mysql.connector
from mysql.connector import Error

def connect():
    """
    Établit une connexion à la base de données MySQL.
    Demande les informations de connexion à l'utilisateur et gère les erreurs.
    """
    while True:
        try:
            user = input("Nom d'utilisateur MySQL : ")
            password = input("Mot de passe MySQL : ")
            host = input("Hôte MySQL (laissez vide pour localhost) : ") or "localhost"
            database = input("Nom de la base de données : ")

            config = {
                'user': user,
                'password': password,
                'host': host,
                'database': database,
                'raise_on_warnings': True
            }

            conn = mysql.connector.connect(**config)
            print("Connexion à la base de données réussie !")
            return conn

        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            retry = input("Voulez-vous réessayer ? (oui/non) : ").lower()
            if retry != 'oui':
                return None
