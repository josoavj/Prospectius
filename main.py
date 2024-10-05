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

import mysql.connector

Window.size = (1200, 650)
Window.left = 80
Window.top = 60

Window.minimum_height = 650
Window.minimum_width = 1000

connection = mysql.connector.connect(
    user='Prospection',
    password='prospect',
    host='localhost',
    database='prospectius'
)


def reverse_date(ex_date):
    Y, M, D = str(ex_date).split('-')
    date = f'{D}-{M}-{Y}'
    return date


class Prospect(MDApp):
    name = 'PROSPECTIUS'
    description = 'Logiciel de suivi de prospection'
    CLM = './Assets/CLM.jpg'
    CL = './Assets/CL.jpg'
    idp = 0

    def build(self):
        self.title = 'PROSPECTIUS'
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        self.icon = self.CLM
        ecran = ScreenManager()
        ecran.add_widget(Builder.load_file('./Screen/Blogin.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Login.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Create.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Home.kv'))
        ecran.add_widget(Builder.load_file('./Screen/New.kv'))
        ecran.add_widget(Builder.load_file('./Screen/Suivi.kv'))
        return ecran

    def show_dialog(self, indice):
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

        if indice == 'deco':
            self.dialog = deconnexion
            self.dialog.open()

        if indice != 'deco':
            self.dialog = modif = MDDialog(
                    md_bg_color='#56B5FB',
                    title='Informations sur le prospect',
                    type='custom',
                    content_cls=MDBoxLayout(
                        MDLabel(text=f'Date: {str(indice[0])}', pos_hint={'center_x':1.2,'center_y':.1}),
                        MDLabel(text=f'Nom: {indice[1]}', font_size=20),
                        MDLabel(text=f'Prenom: {indice[2]}', font_size=15),
                        MDLabel(text=f'Adresse email: {indice[3]}', font_size=15),
                        MDLabel(text=f'Numéro: {indice[4]}', font_size=15),
                        MDLabel(text=f'Adresse: {indice[5]}', font_size=15),
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
                                       on_press=lambda modif:self.update_info(indice)),
                        MDRaisedButton(text="Supprimer",
                                       md_bg_color='#FF3333',
                                       theme_text_color='Custom',
                                       text_color='black',
                                       on_release=lambda effacer: self.delete(indice)),
                        MDRaisedButton(text="Annuler",
                                       md_bg_color='#FFEE55',
                                       theme_text_color='Custom',
                                       text_color='black',
                                       on_release=self.close_dialog)
                    ]
                )
            self.dialog.open()

    def update_info(self, indice):
        check = ['Le client à accepté', 'Sa réponse est encore en attente', 'Le client à refusé']

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
        query = f"""delete from prospect where idProspect = {indice[8]}"""
        self.close_dialog()
        with connection.cursor(buffered=True) as cursor:
            cursor.execute(query)
            connection.commit()
            cursor.close()
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
        with connection.cursor(buffered=True) as cursor:
            requete = """
            select dateP, nomP, prenomP, conclusionP from prospect 
            order by dateP DESC"""

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
            cursor.close()

        self.data_tables = MDDataTable(
            pos_hint={"center_x": .62, "center_y": .5},
            size_hint=(0.7, 0.9),
            rows_num=len(all),
            use_pagination=False,
            background_color_header='#B3F844',
            column_data=[('Date', dp(30)),
                         ("Nom", dp(40)),
                         ("Prénom", dp(40)),
                         ("Status(Conclusion)", dp(70))],
            row_data=data
        )
        self.data_tables.bind(on_row_press=self.row_pressed)
        suivi = self.root.get_screen('Suivi').ids.Datatables
        suivi.add_widget(self.data_tables)

    def row_pressed(self, table, row):
        row_num = int(row.index / len(table.column_data))
        row_data = table.row_data[row_num]

        with connection.cursor(buffered=True) as cursor:
            query = """select idProspect from Prospect where nomP = %s and prenomP=%s"""
            get = """select dateP, nomP, prenomP, mailP,numberP, adresseP, resumeP, conclusionP,idProspect from Prospect 
                    where idProspect=%s"""
            cursor.execute(query, (row_data[1], row_data[2]))
            data = cursor.fetchone()
            self.idp = data[0]
            cursor.execute(get, data)
            self.show_dialog(cursor.fetchone())

    def new_account(self, nom, prenom, email, user, mdp, confirm):
        if not nom or not prenom or not email or not user or not mdp or not confirm:
            toast('Veuillez completer tous les champs')
        elif mdp != confirm:
            toast('Vérifier votre mot de passe')
        elif not '@' in email or not '.' in email:
            toast('Verifier vote adresse Email')
        else:
            inscription = """
                INSERT INTO Compte(nomCompte, prenomCompte, mail, n_utilisateur, mdp)
                VALUES (%(nom)s, %(prenom)s, %(email)s, %(user)s, %(mdp)s)
            """
            with connection.cursor(buffered=True) as cursor:
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
                    toast(f"Une erreur est survenue : {str(e)}")
                cursor.close()

    def log_in(self, user, password):
        if not user or not password:
            toast('Completer tous les champs')
        else:
            login = """
                SELECT prenomCompte
                FROM Compte 
                WHERE n_utilisateur = %s AND mdp = %s
            """
            with connection.cursor(buffered=True) as cursor:
                cursor.execute(login, (user, password))
                user_data = cursor.fetchone()
                if user_data:
                    self.root.current = 'Home page'
                    self.root.transition.direction = 'left'
                    toast('Bienvenue')
                    self.clear('login')
                    self.add_card()
                else:
                    toast('Verifier tous les champs')
                cursor.close()

    def add_card(self):
        query = """SELECT dateP, nomP, prenomP, adresseP, mailP,numberP, resumeP, conclusionP FROM prospect order by dateP desc"""

        box = MDGridLayout(id='box',
                           cols=1,
                           spacing='15dp',
                           padding='15dp',
                           col_force_default=False,
                           adaptive_height=True,
                           size_hint=(1, None),)
        label = MDLabel(text='Liste des prospections récents',
                        font_size=20,
                        pos_hint={"center_x": .5, "center_y": .9},
                        font_name='poppins-bold'
                        )
        box.add_widget(label)
        self.root.get_screen('Home page').ids.grille.add_widget(box)

        check = ['Le client à accepté', 'Sa réponse est encore en attente', 'Le client à refusé']

        with connection.cursor(buffered=True) as cursor:
            cursor.execute(query)
            for data in cursor.fetchall():
                date, nom, prenom, adresse, email,number, discu, conclusion = data
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
                                              size_hint=(.2,1),
                                              line_color='#B3F844',
                                              font_size=13) if conclusion == check[0]
            else MDRectangleFlatIconButton(icon='account-clock',
                                           icon_color='black',
                                           text='Encore en attente',
                                           md_bg_color='#FFEE55',
                                           pos_hint={'center_x': .8},
                                           text_color='black',
                                           size_hint=(.2,1),
                                           line_color='#FFEE55',
                                           font_size=13) if conclusion == check[1]
            else MDRectangleFlatIconButton(icon='cancel',
                                           icon_color='black',
                                           text='Réfusé',
                                           md_bg_color='#FF3333',
                                           pos_hint={'center_x': .8},
                                           text_color='black',
                                           size_hint=(.2,1),
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
        cursor.close()

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
        new_input = ["nom", "date", "prenom", "address", "email","number", "summary"]
        check = ['ok', 'wait', 'no']

        if indice == "login":
            for input in login_input:
                login.ids[input].text = ''

        if indice == "create":
            for input in creation_input:
                create.ids[input].text = ''

        if indice == "new":
            for chk in check:
                nouveau.ids[chk].active= False
            for input in new_input:
                nouveau.ids[input].text = ''

    def add_new_client(self, nom, date, prenom, address, email, number, resume, ok, wait, no):
        if not nom or not date or not prenom or not address or not email or not resume or not number:
            toast('Veuillez completer tous les champs')
        elif not '@' in email or not '.' in email:
            toast("Verifier  l'adresse Email")
        else:
            new = """
            INSERT INTO prospect(dateP, nomP, prenomP, mailP,numberP, adresseP, resumeP, conclusionP) 
            VALUES (%(date)s, %(nom)s,%(prenom)s, %(email)s, %(number)s,%(adresse)s, %(resume)s, %(conclusion)s)"""

            update = """ UPDATE prospect set dateP=%s, nomP=%s,prenomP=%s,mailP=%s,numberP=%s,adresseP=%s,resumeP=%s,conclusionP=%s
                         WHERE idProspect = %s"""

            conclusion =''
            if ok:
                conclusion = 'Le client à accepté'
            if wait:
                conclusion = 'Sa réponse est encore en attente'
            if no:
                conclusion = 'Le client à refusé'

            D,M,Y = str(date).split('-')
            datef = f'{Y}-{M}-{D}'
            with connection.cursor(buffered=True) as cursor:
                if self.idp == 0:
                    cursor.execute(new, {'date': datef,
                                         'nom': nom,
                                         'prenom': prenom,
                                         'adresse': address,
                                         'number': number,
                                         'email': email,
                                         'resume': resume,
                                         'conclusion': conclusion})
                    connection.commit()
                else:
                    cursor.execute(update, (datef, nom, prenom, email, number, address, resume, conclusion,self.idp))
                    connection.commit()
                self.clear('new')
                toast('Informations enregistrer')
                self.add_datatables()
                self.remove_card()
                self.add_card()
                self.idp = 0
            cursor.close()


if __name__ == "__main__":

    LabelBase.register(name='poppins',
                       fn_regular='Poppins/Poppins-Regular.ttf')
    LabelBase.register(name='poppins-bold',
                       fn_regular='Poppins/Poppins-bold.ttf')
    Prospect().run()
