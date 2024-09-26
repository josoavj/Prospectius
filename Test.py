from kivy.lang import Builder
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.app import MDApp

KV = '''

<Card>
    size_hint: .1, None
    height: dp(300)
    md_bg_color: '#56B5FB'
    orientation: 'vertical'
    radius: [10]
    MDLabel:
        text: 'Nom: Andriamasinoro'
        pos_hint:{"center_x":.55,"center_y":.85}
    MDLabel:
        text: 'Prénom: Aina Maminirina'
        pos_hint:{"center_x":.55,"center_y":.75}
    MDLabel:
        text: 'Adresse: Ankadindramamy'
        pos_hint:{"center_x":.55,"center_y":.65}
    MDLabel:
        text: 'Email: maminirina@gmaail.com'
        pos_hint:{"center_x":.55,"center_y":.55}
    MDLabel:
        text: 'Date: 29 - 12 - 2024'
        pos_hint:{"center_x":1.2,"center_y":.85}
    MDLabel:
        text: 'Résumé de la discussion: '
        pos_hint:{"center_x":.55,"center_y":.45}
    MDFloatLayout:
        pos_hint:{"center_x":.45,"center_y":.4}
        size_hint:.8, 1
        MDLabel:
            text: '"Lorem ezufhvzeuif izhefu uy ziero oz uizeurz uoi u iuiu iozeriuoi uiou iu uu iu o oiu i uiu e  e e   zer  ze fe f ze fz ef zef dv d gze t zt zegze gze zt eg zv z ef zefzaz ertyui oopqs fghhj kklmwx cvbnnaz erty uiopq sdfgh jklm wxc vvbn"'
            pos_hint:{"center_x":.55,"center_y":.4}
    MDRaisedButton:
        text:'Clique moi'
        pos_hint:{"center_x":.8,"center_y":.1}



MDBoxLayout:
    orientation: "vertical"
    size_hint: 1, 1

    ScrollView:
        do_scroll_x: False
        size_hint: 1, 1

        MDGridLayout:
            cols: 1
            col_force_default: False
            spacing: dp(6)
            size_hint: 1, None
            adaptive_height: True
            padding: dp(6)
            MDCard:
                size_hint: .1, None
                height: dp(300)
                md_bg_color: '#56B5FB'
                orientation: 'vertical'
                radius: [10]
                MDLabel:
                    text: 'Date: 29 - 12 - 2024'
                    pos_hint:{"center_x":1.2,"center_y":.3}
                MDLabel:
                    text: 'Nom: Andriamasinoro'
                    pos_hint:{"center_x":.55,"center_y":.85}
                MDLabel:
                    text: 'Prénom: Aina Maminirina'
                    pos_hint:{"center_x":.55,"center_y":.75}
                MDLabel:
                    text: 'Adresse: Ankadindramamy'
                    pos_hint:{"center_x":.55,"center_y":.65}
                MDLabel:
                    text: 'Email: maminirina@gmaail.com'
                    pos_hint:{"center_x":.55,"center_y":.55}
                MDLabel:
                    text: 'Résumé de la discussion: '
                    pos_hint:{"center_x":.55,"center_y":.45}
                MDFloatLayout:
                    pos_hint:{"center_x":.45,"center_y":.4}
                    size_hint:.8, 1
                    MDLabel:
                        text: '"Lorem ezufhvzeuif azerrt zrt   e ere zefzef zefzzeer zer zerizhefu uy ziero oz uizeurz uoi u iuiu iozeriuoi uiou iu uu iu o oiu i uiu e  e e   zer  ze fe f ze fz ef zef dv d gze t zt zegze gze zt eg zv z ef zefzaz ertyui oopqs fghhj kklmwx cvbnnaz erty uiopq sdfgh jklm wxc vvbn"'
                        pos_hint:{"center_x":.55,"center_y":.4}
                MDRaisedButton:
                    text:'Clique moi'
                    pos_hint:{"center_x":.8,"center_y":.2}

            Card:
            Card:
            Card:
            Card:
'''


class Card(RoundedRectangularElevationBehavior, MDFloatLayout):
    pass


class Example(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)


Example().run()