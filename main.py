# Fichier: main.py
# Fichier mis à jour pour corriger les chemins de police
# ainsi que les requêtes SQL selon la nouvelle base de données.

import bcrypt
import re
import mysql.connector
from mysql.connector import Error
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatIconButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.datatables import MDDataTable
from kivy.core.text import LabelBase
from kivymd.toast import toast
from kivy.core.window import Window
import os

# Configuration de la fenêtre
Window.size = (1200, 650)
Window.left = 80
Window.top = 60
Window.minimum_height = 650
Window.minimum_width = 1000


def hash_password(password):
    """
    Hache le mot de passe en utilisant l'algorithme bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


def reverse_date(ex_date):
    """
    Convertit le format de date YYYY-MM-DD en DD-MM-YYYY.
    """
    if isinstance(ex_date, str):
        y, m, d = ex_date.split('-')
    else:
        y, m, d = str(ex_date).split('-')
    date = f'{d}-{m}-{y}'
    return date


def is_valid_email(email):
    """
    Vérifie le format d'une adresse e-mail en utilisant une expression régulière.
    """
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return re.match(email_regex, email) is not None


class Prospect(MDApp):
    copyright = '©Copyright @Dev-Corps 2024'
    name = 'PROSPECTIUS'
    description = 'Logiciel de suivi de prospection'
    CLM = './Assets/CLM.jpg'
    CL = './Assets/CL.jpg'
    idp = 0
    connection = None

    # Définition des chemins des polices ici
    font_dir = os.path.join(os.path.dirname(__file__), 'Poppins')
    poppins_regular = os.path.join(font_dir, 'Poppins-Regular.ttf')
    poppins_bold = os.path.join(font_dir, 'Poppins-Bold.ttf')

    def build(self):
        self.title = 'PROSPECTIUS'
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        self.icon = self.CLM

        # Vérification et enregistrement des polices
        if os.path.exists(self.poppins_regular) and os.path.exists(self.poppins_bold):
            LabelBase.register(name='poppins', fn_regular=self.poppins_regular)
            LabelBase.register(name='poppins-bold', fn_regular=self.poppins_bold)
        else:
            print(
                f"Erreur : Polices introuvables. Vérifiez les chemins : {self.poppins_regular} et {self.poppins_bold}")

        ecran = ScreenManager()
        ecran.add_widget(Builder.load_file('./Screen/Blogin.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Create.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Login.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Home.kv'))
        ecran.add_widget(Builder.load_file('./Screen/New.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Suivi.kv'))

        # Établir la connexion à la base de données
        try:
            self.connection = mysql.connector.connect(
                user='Prospection',
                password='prospect',
                host='localhost',
                database='prospectius'
            )
            print("Connexion à la base de données réussie !")
        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            # Gérer l'erreur de connexion, par exemple en fermant l'application
            self.stop()

        return ecran

    def show_dialog(self, indice, data):
        deconnexion = MDDialog(
            md_bg_color='#56B5FB',
            title='Deconnexion',
            text="[color='black']Voulez-vous vous deconnecter ? [/color]",
            buttons=[
                MDRaisedButton(text='OUI',
                               md_bg_color='#B3F844',
                               theme_text_color='Custom',
                               text_color='black',
                               on_release=self.fermer),
                MDRaisedButton(text="NON",
                               md_bg_color='#FF3333',
                               theme_text_color='Custom',
                               text_color='black',
                               on_release=self.close_dialog)]
        )

        modif = MDDialog(
            md_bg_color='#56B5FB',
            title='Informations sur le prospect',
            type='custom',
            content_cls=MDBoxLayout(
                MDLabel(text=f'Date: {str(data[0])}', pos_hint={'center_x': 1.2, 'center_y': .1}),
                MDLabel(text=f"Nom de l'entreprise: {data[1]}", font_size=20),
                MDLabel(text=f"Identifiant de l'entreprise: {data[2]}", font_size=15),
                MDLabel(text=f'Adresse email: {data[3]}', font_size=15),
                MDLabel(text=f'Numéro: {data[4]}', font_size=15),
                MDLabel(text=f'Adresse: {data[5]}', font_size=15),
                size_hint_y=None,
                spacing='12dp',
                orientation='vertical',
                height='120dp'
            ),

            buttons=[
                MDRaisedButton(text='Modifier',
                               md_bg_color='#B3F844',
                               theme_text_color='Custom',
                               text_color='black',
                               on_press=lambda modif: self.update_info(data)),
                MDRaisedButton(text="Supprimer",
                               md_bg_color='#FF3333',
                               theme_text_color='Custom',
                               text_color='black',
                               on_release=lambda effacer: self.show_dialog('suppression', data)),
                MDRaisedButton(text="Annuler",
                               md_bg_color='#FFEE55',
                               theme_text_color='Custom',
                               text_color='black',
                               on_release=self.close_dialog)
            ]
        )

        if indice == 'deco':
            self.dialog = deconnexion

        if indice == "suppression":
            self.close_dialog()
            self.dialog = MDDialog(
                md_bg_color='#56B5FB',
                title=f'Suppression ',
                type='custom',
                content_cls=MDBoxLayout(
                    MDLabel(text=f'Voulez vous supprimer les informations sur {data[2]}?', font_size=20),
                    size_hint_y=None,
                    spacing='12dp',
                    orientation='vertical',
                    height='120dp'
                ),

                buttons=[
                    MDRaisedButton(text="OUI",
                                   md_bg_color='#B3F844',
                                   theme_text_color='Custom',
                                   text_color='black',
                                   on_release=lambda effacer: self.delete(data)),
                    MDRaisedButton(text="NON",
                                   md_bg_color='#FF3333',
                                   theme_text_color='Custom',
                                   text_color='black',
                                   on_release=self.close_dialog)
                ]
            )

        if indice == 'modification':
            self.dialog = modif

        self.dialog.open()

    def update_info(self, indice):
        check = ['accepté', 'en attente', 'refusé']

        form = self.root.get_screen('New client')
        form.ids.nom.text = indice[1]
        form.ids.date.text = str(reverse_date(indice[0]))
        form.ids.prenom.text = indice[2]
        form.ids.address.text = indice[5]
        form.ids.number.text = indice[4]
        form.ids.email.text = indice[3]
        form.ids.summary.text = indice[6]
        if indice[7] == check[0]:
            form.ids.ok.active = True
        elif indice[7] == check[1]:
            form.ids.wait.active = True
        else:
            form.ids.no.active = True

        self.root.current = 'New client'
        self.root.transition.direction = 'left'
        self.close_dialog()

    def delete(self, indice):
        if not self.connection: return
        query = f"""delete from Prospect where id_prospect = {indice[8]}"""
        self.close_dialog()
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(query)
            self.connection.commit()
        self.add_datatables()
        self.remove_card()
        self.add_card()
        toast('Information supprimé')

    def fermer(self, *args):
        self.root.current = "before login"
        self.dialog.dismiss()
        self.remove_card()

    def close_dialog(self, *args):
        self.dialog.dismiss()

    def show_date_picker(self):
        date_dialog = MDDatePicker(primary_color='#56B5FB')
        date_dialog.open()
        date_dialog.bind(on_save=self.on_save_date)

    def on_save_date(self, instance, date_range, value):
        self.root.get_screen("New client").ids["date"].text = str(reverse_date(date_range))

    def add_datatables(self):
        if not self.connection: return
        with self.connection.cursor(buffered=True) as cursor:
            requete = """
                      select date_creation, nom_prospect, prenom_prospect, statut_prospect \
                      from Prospect
                      order by date_creation DESC"""

            cursor.execute(requete)
            all = cursor.fetchall()
            data = [
                (
                    reverse_date(i[:][0]),
                    i[:][1],
                    i[:][2],
                    i[:][3]
                )
                for i in all
            ]

        self.data_tables = MDDataTable(
            pos_hint={"center_x": .62, "center_y": .5},
            size_hint=(0.7, 0.9),
            rows_num=len(all),
            use_pagination=False,
            background_color_header='#B3F844',
            column_data=[('Date', dp(30)),
                         ("Nom de l'entreprise", dp(40)),
                         ("Identifiant de l'entreprise", dp(40)),
                         ("Status(Conclusion)", dp(70))],
            row_data=data
        )
        self.data_tables.bind(on_row_press=self.row_pressed)
        suivi = self.root.get_screen('Suivi').ids.Datatables
        suivi.add_widget(self.data_tables)

    def row_pressed(self, table, row):
        if not self.connection: return
        row_num = int(row.index / len(table.column_data))
        row_data = table.row_data[row_num]

        with self.connection.cursor(buffered=True) as cursor:
            query = """select id_prospect \
                       from Prospect \
                       where nom_prospect = %s \
                         and prenom_prospect = %s"""
            get = """select date_creation, \
                            nom_prospect, \
                            prenom_prospect, \
                            email_prospect, \
                            telephone_prospect, \
                            adresse_prospect, \
                            resume_prospect, \
                            statut_prospect, \
                            id_prospect \
                     from Prospect
                     where id_prospect = %s"""
            cursor.execute(query, (row_data[1], row_data[2]))
            data = cursor.fetchone()
            self.idp = data[0]
            cursor.execute(get, data)
            self.show_dialog('modification', cursor.fetchone())

    def new_account(self, nom, prenom, email, user, mdp, confirm):
        if not self.connection: return
        if not nom or not prenom or not email or not user or not mdp or not confirm:
            toast('Veuillez completer tous les champs')
        elif mdp != confirm:
            toast('Vérifier votre mot de passe')
        elif not is_valid_email(email):
            toast('Verifier votre adresse Email')
        else:
            hashed_mdp = hash_password(mdp)
            inscription = """
                          INSERT INTO Compte(nom_compte, prenom_compte, email, nom_utilisateur, password, role_compte)
                          VALUES (%s, %s, %s, %s, %s, %s) \
                          """
            with self.connection.cursor(buffered=True) as cursor:
                try:
                    cursor.execute(inscription,
                                   (nom, prenom, email, user, hashed_mdp.decode('utf-8'), 'user'))
                    self.connection.commit()
                    self.root.current = 'Login'
                    self.root.transition.direction = 'left'
                    self.clear('create')
                    toast('Compte créé avec succès')

                except Error as e:
                    print(f"Erreur lors de la création du compte : {e}")
                    if e.errno == 1062:
                        toast("Cet email ou nom/prénom est déjà utilisé.")
                    self.connection.rollback()

    def log_in(self, user, password):
        if not self.connection: return
        if not user or not password:
            toast('Completer tous les champs')
        else:
            login = """
                    SELECT password, role_compte
                    FROM Compte
                    WHERE nom_utilisateur = %s \
                    """
            with self.connection.cursor(buffered=True) as cursor:
                cursor.execute(login, (user,))
                user_data = cursor.fetchone()
                if user_data:
                    hashed_password = user_data[0].encode('utf-8')
                    # Vérifier le mot de passe haché
                    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                        self.root.current = 'Home page'
                        self.root.transition.direction = 'left'
                        toast(f'Bienvenue')
                        self.clear('login')
                        self.add_card()
                    else:
                        toast('Nom d\'utilisateur ou mot de passe incorrect.')
                else:
                    toast('Nom d\'utilisateur ou mot de passe incorrect.')

    def add_card(self):
        if not self.connection: return
        query = """SELECT date_creation, \
                          nom_prospect, \
                          prenom_prospect, \
                          adresse_prospect, \
                          email_prospect, \
                          telephone_prospect, \
                          resume_prospect, \
                          statut_prospect \
                   FROM Prospect \
                   order by date_creation desc"""

        box = MDGridLayout(id='box',
                           cols=1,
                           spacing='15dp',
                           padding='15dp',
                           col_force_default=False,
                           adaptive_height=True,
                           size_hint=(1, None), )
        label = MDLabel(text='Liste des prospections récents :',
                        font_size=25,
                        pos_hint={"center_x": .5, "center_y": .9},
                        font_name='poppins-bold'
                        )
        box.add_widget(label)
        self.root.get_screen('Home page').ids.grille.add_widget(box)

        # Les valeurs de statut correspondent maintenant aux valeurs de l'ENUM
        check = ['accepté', 'en attente', 'refusé']

        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(query)
            for data in cursor.fetchall():
                date, nom, prenom, adresse, email, number, discu, statut = data
                card = MDCard(
                    MDLabel(text=f'Date :{reverse_date(date)} ',
                            pos_hint={"center_x": 1.2, "center_y": .3},
                            font_name='poppins'),
                    MDLabel(text=f'Nom : {nom}',
                            pos_hint={"center_x": .55, "center_y": .85},
                            font_name='poppins'),
                    MDLabel(text=f'Prénom : {prenom}',
                            pos_hint={"center_x": .55, "center_y": .75},
                            font_name='poppins'),
                    MDLabel(text=f'Adresse : {adresse}',
                            pos_hint={"center_x": .55, "center_y": .655},
                            font_name='poppins'),
                    MDLabel(text=f'Email : {email}',
                            pos_hint={"center_x": .55, "center_y": .85},
                            font_name='poppins'),
                    MDLabel(text=f'Numéro : {number}',
                            pos_hint={"center_x": .55, "center_y": .85},
                            font_name='poppins'),
                    MDLabel(text='Résumé de la discussion:',
                            pos_hint={"center_x": .55, "center_y": .85},
                            font_name='poppins'),
                    MDFloatLayout(MDLabel(text=f'"{discu}"',
                                          pos_hint={"center_x": .55, "center_y": .9}),
                                  pos_hint={"center_x": .45, "center_y": .4},
                                  size_hint=(.8, 1)
                                  ),
                    MDRectangleFlatIconButton(icon='check-bold',
                                              icon_color='black',
                                              text='Accepté',
                                              md_bg_color='#B3F844',
                                              pos_hint={'center_x': .8},
                                              text_color='black',
                                              size_hint=(.2, 1),
                                              line_color='#B3F844',
                                              font_size=13) if statut == check[0]
                    else MDRectangleFlatIconButton(icon='account-clock',
                                                   icon_color='black',
                                                   text='Encore en attente',
                                                   md_bg_color='#FFEE55',
                                                   pos_hint={'center_x': .8},
                                                   text_color='black',
                                                   size_hint=(.2, 1),
                                                   line_color='#FFEE55',
                                                   font_size=13) if statut == check[1]
                    else MDRectangleFlatIconButton(icon='cancel',
                                                   icon_color='black',
                                                   text='Réfusé',
                                                   md_bg_color='#FF3333',
                                                   pos_hint={'center_x': .8},
                                                   text_color='black',
                                                   size_hint=(.2, 1),
                                                   line_color='#FF3333',
                                                   font_size=13)
                    ,
                    size_hint=(.1, None),
                    height=dp(300),
                    md_bg_color='#56B5FB',
                    orientation='vertical',
                    padding='10dp',
                    radius=[10]
                )
                box.add_widget(card)

    def remove_card(self):
        scrollview = self.root.get_screen('Home page').ids.grille
        for child in scrollview.children[:]:
            if child.id == 'box':
                scrollview.remove_widget(child)

    def clear(self, indice):
        login = self.root.get_screen("Login")
        create = self.root.get_screen("Create Account")
        nouveau = self.root.get_screen("New client")
        login_input = ["username", "Password"]
        creation_input = ["nom", 'user', 'prenom', 'password', 'email', 'confirm']
        new_input = ["nom", "date", "prenom", "address", "email", "number", "summary"]
        check = ['ok', 'wait', 'no']

        if indice == "login":
            for input in login_input:
                login.ids[input].text = ''

        if indice == "create":
            for input in creation_input:
                create.ids[input].text = ''

        if indice == "new":
            for chk in check:
                nouveau.ids[chk].active = False
            for input in new_input:
                nouveau.ids[input].text = ''

    def add_new_client(self, nom, date, prenom, address, email, number, resume, ok, wait, no):
        if not self.connection: return
        if not nom or not date or not prenom or not address or not email or not resume or not number:
            toast('Veuillez completer tous les champs')
        elif not is_valid_email(email):
            toast("Verifier l'adresse Email")
        else:
            new = """
                  INSERT INTO Prospect(date_creation, nom_prospect, prenom_prospect, email_prospect, telephone_prospect, \
                                       adresse_prospect, resume_prospect, statut_prospect)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

            update = """ UPDATE Prospect \
                         set date_creation=%s, \
                             nom_prospect=%s, \
                             prenom_prospect=%s, \
                             email_prospect=%s, \
                             telephone_prospect=%s, \
                             adresse_prospect=%s, \
                             resume_prospect=%s, \
                             statut_prospect=%s
                         WHERE id_prospect = %s"""

            statut = ''
            if ok:
                statut = 'accepté'
            elif wait:
                statut = 'en attente'
            else:
                statut = 'refusé'

            d, m, y = str(date).split('-')
            datef = f'{y}-{m}-{d}'
            with self.connection.cursor(buffered=True) as cursor:
                if self.idp == 0:
                    try:
                        cursor.execute(new, (datef, nom, prenom, email, number, address, resume, statut))
                        self.connection.commit()
                        toast('Informations enregistrées')
                    except Error as e:
                        print(f"Erreur lors de l'ajout du prospect : {e}")
                        toast("Erreur lors de l'enregistrement, vérifiez les données.")
                        self.connection.rollback()
                else:
                    cursor.execute(update, (datef, nom, prenom, email, number, address, resume, statut, self.idp))
                    self.connection.commit()
                    toast('Informations mises à jour')

                self.clear('new')
                self.add_datatables()
                self.remove_card()
                self.add_card()
                self.idp = 0

    def on_stop(self):
        """Ferme la connexion à la base de données lorsque l'application s'arrête."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Connexion à la base de données fermée.")


if __name__ == "__main__":
    Prospect().run()
