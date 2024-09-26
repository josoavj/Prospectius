from kivymd.app import MDApp

from kivy.lang import Builder
from kivy.metrics import dp

from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.datatables import MDDataTable

from kivy.core.text import LabelBase
from kivymd.toast import toast
from kivy.core.window import Window

import mysql.connector

Window.size = (1200, 650)
Window.left = 80
Window.top = 60

Window.minimum_height = 650
Window.minimum_width = 1000

connection = mysql.connector.connect(
    user='root',
    password='Asecna2024',
    host='localhost',
    database='prospectius'
)


class Prospect(MDApp):
    name = 'PROSPECTIUS'
    description = 'Logiciel de suivi de prospection'
    CLM = './Assets/CLM.jpg'
    CL = './Assets/CL.jpg'

    def build(self):
        self.title = 'Suivie de prospection'
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        ecran = ScreenManager()
        ecran.add_widget(Builder.load_file('./Screen/Home.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Blogin.kv'))
        ecran.add_widget(Builder.load_file('./Screen/New.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Create.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Login.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Suivi.kv'))
        return ecran

    def show_dialog(self):
        self.dialog = MDDialog(
            md_bg_color='#56B5FB',
            title='Deconnexion',
            text="[color='black']Voulez-vous vous deconnecter ? [/color]",
            buttons=[
                MDRaisedButton(text='OUI',
                               md_bg_color='#FFEE55',
                               theme_text_color='Custom',
                               text_color='black',
                               on_release=self.fermer),
                MDRaisedButton(text="NON",
                               md_bg_color='#FF3333',
                               theme_text_color='Custom',
                               text_color='black',
                               on_release=self.close_dialog)]
        )
        self.dialog.open()

    def fermer(self, *args):
        self.root.current = "before login"
        self.dialog.dismiss()

    def close_dialog(self,*args):
        self.dialog.dismiss()

    def show_date_picker(self):
        date_dialog = MDDatePicker(primary_color='#56B5FB')
        date_dialog.open()
        date_dialog.bind(on_save=self.on_save_date)

    def on_save_date(self, instance, date_range, value):
        self.root.get_screen("New client").ids["date"].text = str(date_range)
        print(instance, value, date_range)

    def add_datatables(self):
        with connection.cursor() as cursor:
            requete = """
            select datee, nom, prenom, summary from new_client 
            order by datee DESC"""

            cursor.execute(requete)
            all = cursor.fetchall()
            data = [
                (
                    i[:][0],
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
            check=True,
            background_color_header='#B3F844',
            column_data=[('Date', dp(30)),
                         ("Nom", dp(40)),
                         ("Prénom", dp(40)),
                         ("Status(Conclusion)", dp(70))],
            row_data=data
        )
        suivi = self.root.get_screen('Suivi').ids.Datatables
        suivi.add_widget(self.data_tables)

    def remove_datatables(self):
        container = self.root.get_screen('Suivi').ids.Datatables
        container.remove_widget(self.data_tables)
        self.add_datatables()

    def new_account(self, nom, prenom, email, user, mdp, confirm):
        if not nom or not prenom or not email or not user or not mdp or not confirm:
            toast('Veuillez completer tous les champs')
        if mdp != confirm:
            toast('Vérifier votre mot de passe')

        inscription = """
            INSERT INTO login(nom, prenom, email, username, passwrd)
            VALUES (%(nom)s, %(prenom)s, %(email)s, %(user)s, %(mdp)s)
        """
        with connection.cursor() as cursor:
            try:
                cursor.execute(inscription,
                               {'nom': nom,
                                'prenom': prenom,
                                'email': email,
                                'user': user,
                                'mdp': mdp})
                connection.commit()
                self.root.current = 'Login'
                self.root.transition.direction = 'left'
                self.clear('create')

            except Exception as e:
                toast("Erreur", f"Une erreur est survenue : {str(e)}")

    def log_in(self, user, password):
        if not user or not password:
            toast('Completer tous les champs')
        else:
            login = """
                SELECT prenom
                FROM login 
                WHERE username = %s AND passwrd = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(login, (user, password))
                user_data = cursor.fetchone()
                if user_data:
                    self.root.current = 'Home page'
                    self.root.transition.direction = 'left'
                    toast('Bienvenue')
                    self.clear('login')
                else:
                    toast('Verifier tous les champs')

    def clear(self, indice):
        login = self.root.get_screen("Login")
        create = self.root.get_screen("Create Account")
        nouveau = self.root.get_screen("New client")
        login_input = ["username", "Password"]
        creation_input = ["nom", 'user', 'prenom', 'password', 'email', 'confirm']
        new_input = ["nom", "date", "prenom", "address", "email", "summary"]

        if indice == "login":
            for input in login_input:
                login.ids[input].text = ''

        if indice == "create":
            for input in creation_input:
                create.ids[input].text = ''

        if indice == "new":
            for input in new_input:
                nouveau.ids[input].text = ''

    def add_new_client(self, nom, date, prenom, address, email, resume ):
        if not nom or not date or not prenom or not address or not email or not resume:
            toast('Veuillez completer tous les champs')
        else:
            new = """
            INSERT INTO new_client VALUES (%(datee)s, %(nom)s,%(prenom)s, %(adresse)s, %(email)s, %(resume)s)"""
            with connection.cursor() as cursor:
                cursor.execute(new, {'datee': date,
                                     'nom': nom,
                                     'prenom': prenom,
                                     'adresse': address,
                                     'email': email,
                                     'resume': resume})
                connection.commit()
                self.clear('new')
                toast('Informations enregistrer')
                self.remove_datatables()


if __name__ == "__main__":

    LabelBase.register(name='poppins',
                       fn_regular='Poppins/Poppins-Regular.ttf')
    LabelBase.register(name='poppins-bold',
                       fn_regular='Poppins/Poppins-bold.ttf')
    Prospect().run()
