#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFrame,
                             QGridLayout, QMessageBox, QInputDialog, QDialog,
                             QTabWidget)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QTimer

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def get_numeric_value(self):
        if self.value in ['J', 'Q', 'K']:
            return 10
        elif self.value == 'A':
            return 11  # Ez később 1-re változhat a játékmenet során
        else:
            return int(self.value)

    def get_image_file(self):
        # Speciális kezelés a figurás lapokhoz
        if self.value == 'J':
            file_value = 'jack'
        elif self.value == 'Q':
            file_value = 'queen'
        elif self.value == 'K':
            file_value = 'king'
        elif self.value == 'A':
            file_value = 'ace'
        else:
            file_value = self.value

        # Kisbetűsre alakítjuk a suit-ot is, és alulvonással kapcsoljuk össze
        return f"cards/{file_value}_of_{self.suit.lower()}.png"

    def __str__(self):
        return f"{self.value} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        self.create_deck()

    def create_deck(self):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

        for suit in suits:
            for value in values:
                self.cards.append(Card(suit, value))

        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            self.create_deck()
        return self.cards.pop()

class Hand:
    def __init__(self):
        self.cards = []
        self.is_active = True
        self.doubled = False
        self.bet = 0

    def add_card(self, card):
        self.cards.append(card)

    def calculate_value(self):
        value = 0
        aces = 0

        for card in self.cards:
            value += card.get_numeric_value()
            if card.value == 'A':
                aces += 1

        # Kezelni az Ászokat, hogy ne legyen nagyobb az érték 21-nél
        while value > 21 and aces > 0:
            value -= 10  # Változtatjuk az Ász értékét 11-ről 1-re
            aces -= 1

        return value

    def is_blackjack(self):
        return len(self.cards) == 2 and self.calculate_value() == 21

    def can_split(self):
        if len(self.cards) != 2:
            return False

        # Két azonos értékű lap esetén lehet osztani
        return self.cards[0].value == self.cards[1].value or (
            self.cards[0].value in ['10', 'J', 'Q', 'K'] and
            self.cards[1].value in ['10', 'J', 'Q', 'K']
        )

    def can_double(self):
        # Csak akkor lehet duplázni, ha 2 lap van és az érték 9, 10 vagy 11
        value = self.calculate_value()
        return len(self.cards) == 2 and 9 <= value <= 11

class CardLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(80, 120)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: transparent;")

class HandWidget(QWidget):
    def __init__(self, parent=None, is_dealer=False):
        super().__init__(parent)
        self.is_dealer = is_dealer
        self.hand = Hand()

        # Layout létrehozása
        self.layout = QVBoxLayout(self)

        # Kéz címe
        if self.is_dealer:
            self.title_label = QLabel("Osztó kártyái:")
        else:
            self.title_label = QLabel("Játékos kártyái:")
        self.title_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.layout.addWidget(self.title_label)

        # Érték címke
        self.value_label = QLabel("Érték: 0")
        self.value_label.setFont(QFont('Arial', 10))
        self.layout.addWidget(self.value_label)

        # Tét címke (csak játékosnál)
        if not self.is_dealer:
            self.bet_label = QLabel("Tét: 0 Ft")
            self.bet_label.setFont(QFont('Arial', 10))
            self.layout.addWidget(self.bet_label)

        # Kártyák elrendezése
        self.cards_layout = QHBoxLayout()
        self.layout.addLayout(self.cards_layout)

        # Játékos gombok (csak játékosnál)
        if not self.is_dealer:
            self.buttons_layout = QHBoxLayout()

            self.hit_button = QPushButton("Kérek lapot")
            self.hit_button.setFont(QFont('Arial', 10))
            self.hit_button.setEnabled(False)

            self.stand_button = QPushButton("Megállok")
            self.stand_button.setFont(QFont('Arial', 10))
            self.stand_button.setEnabled(False)

            self.double_button = QPushButton("Duplázás")
            self.double_button.setFont(QFont('Arial', 10))
            self.double_button.setEnabled(False)

            self.split_button = QPushButton("Split")
            self.split_button.setFont(QFont('Arial', 10))
            self.split_button.setEnabled(False)

            self.buttons_layout.addWidget(self.hit_button)
            self.buttons_layout.addWidget(self.stand_button)
            self.buttons_layout.addWidget(self.double_button)
            self.buttons_layout.addWidget(self.split_button)

            self.layout.addLayout(self.buttons_layout)

    def clear(self):
        # Kártyák törlése
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Kéz újraindítása
        self.hand = Hand()

        # Címkék frissítése
        self.value_label.setText("Érték: 0")
        if not self.is_dealer:
            self.bet_label.setText("Tét: 0 Ft")

            # Gombok letiltása
            self.hit_button.setEnabled(False)
            self.stand_button.setEnabled(False)
            self.double_button.setEnabled(False)
            self.split_button.setEnabled(False)

    def update_display(self, reveal_dealer=False):
        # Kártyák törlése
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Kártyák megjelenítése
        for i, card in enumerate(self.hand.cards):
            # Az osztónál a második kártyát csak akkor mutatjuk, ha reveal_dealer=True
            if not self.is_dealer or i == 0 or reveal_dealer:
                card_label = self.create_card_label(card)
            else:
                card_label = self.create_card_back_label()
            self.cards_layout.addWidget(card_label)

        # Érték frissítése
        if self.is_dealer and not reveal_dealer and len(self.hand.cards) > 1:
            # Csak az első lap értékét mutatjuk az osztónál
            first_card_value = self.hand.cards[0].get_numeric_value()
            self.value_label.setText(f"Érték: {first_card_value}+?")
        else:
            value = self.hand.calculate_value()
            self.value_label.setText(f"Érték: {value}")

        # Tét frissítése (csak játékosnál)
        if not self.is_dealer:
            self.bet_label.setText(f"Tét: {self.hand.bet} Ft")

            # Split és Double gombok frissítése
            self.update_buttons()

    def update_buttons(self):
        if not self.is_dealer and self.hand.is_active:
            self.hit_button.setEnabled(True)
            self.stand_button.setEnabled(True)

            # Double gomb csak akkor aktív, ha lehet duplázni
            self.double_button.setEnabled(self.hand.can_double())

            # Split gomb csak akkor aktív, ha lehet splittelni
            self.split_button.setEnabled(self.hand.can_split())
        else:
            self.hit_button.setEnabled(False)
            self.stand_button.setEnabled(False)
            self.double_button.setEnabled(False)
            self.split_button.setEnabled(False)

    def create_card_label(self, card):
        card_label = CardLabel()
        card_image_path = card.get_image_file()

        # Ellenőrizzük, hogy a kártyakép létezik-e
        if os.path.exists(card_image_path):
            pixmap = QPixmap(card_image_path)
            pixmap = pixmap.scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            card_label.setPixmap(pixmap)
        else:
            # Ha nincs kép, akkor szöveggel jelenítjük meg
            card_label.setText(str(card))
            card_label.setStyleSheet("background-color: white; color: black; border: 1px solid black;")

        return card_label

    def create_card_back_label(self):
        card_label = CardLabel()
        card_back_path = "cards/black_joker.png"  # Joker használata kártya hátlapként

        # Ellenőrizzük, hogy a kártyahát kép létezik-e
        if os.path.exists(card_back_path):
            pixmap = QPixmap(card_back_path)
            pixmap = pixmap.scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            card_label.setPixmap(pixmap)
        else:
            # Ha nincs kép, akkor egyszerű szöveggel jelenítjük meg
            card_label.setText("🂠")
            card_label.setFont(QFont('Arial', 30))
            card_label.setStyleSheet("background-color: #0033cc; color: white; border: 1px solid black;")

        return card_label

class BlackjackGame(QMainWindow):
    def __init__(self):
        super().__init__()

        # Játék logikai változók
        self.deck = Deck()
        self.dealer_hand = Hand()
        self.player_hands = []  # Több kéz a split miatt
        self.active_hand_index = 0
        self.game_over = False
        self.player_money = 1000000
        self.current_bet = 0

        # Ellenőrizzük, hogy a kártyák képei elérhetők-e
        self.check_card_images()

        # UI beállítása
        self.init_ui()

    def check_card_images(self):
        cards_dir = "cards"
        if not os.path.exists(cards_dir):
            os.makedirs(cards_dir)
            QMessageBox.warning(self, "Figyelmeztetés",
                               "A kártyaképek mappája hiányzik. Kérlek, töltsd le és helyezd a 'cards' mappába a megfelelő képeket!")

    def create_new_hand(self):
        # Új kéztartó widget létrehozása
        hand_widget = HandWidget()

        # Aktuális fogadás beállítása
        hand_widget.hand.bet = self.current_bet

        # Kezek listájához adás (FONTOS: ez legyen előbb!)
        self.player_hands.append(hand_widget)

        # Az aktuális kéz indexének meghatározása
        hand_index = len(self.player_hands) - 1

        # Gomb események beállítása
        hand_widget.hit_button.clicked.connect(lambda checked=False, idx=hand_index: self.hit(idx))
        hand_widget.stand_button.clicked.connect(lambda checked=False, idx=hand_index: self.stand(idx))
        hand_widget.double_button.clicked.connect(lambda checked=False, idx=hand_index: self.double_down(idx))
        hand_widget.split_button.clicked.connect(lambda checked=False, idx=hand_index: self.split(idx))

        # Tab hozzáadása
        self.hands_tab.addTab(hand_widget, f"Kéz {hand_index + 1}")

        return hand_widget

    def init_ui(self):
        # Ablak beállítása
        self.setWindowTitle("Blackjack")
        self.setMinimumSize(1000, 700)  # Megnövelt méret

        # Színsémák beállítása
        self.set_color_scheme()

        # Központi widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Fő elrendezés
        main_layout = QVBoxLayout(central_widget)

        # Felső információs panel
        info_panel = QFrame()
        info_panel.setFrameShape(QFrame.StyledPanel)
        info_layout = QHBoxLayout(info_panel)

        # Pénz és tét megjelenítése
        self.money_label = QLabel(f"Pénz: {self.player_money} Ft")
        self.money_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.bet_label = QLabel(f"Tét: {self.current_bet} Ft")
        self.bet_label.setFont(QFont('Arial', 12, QFont.Bold))

        info_layout.addWidget(self.money_label)
        info_layout.addWidget(self.bet_label)

        main_layout.addWidget(info_panel)

        # Dealer kártyái
        dealer_frame = QFrame()
        dealer_frame.setFrameShape(QFrame.StyledPanel)
        dealer_layout = QVBoxLayout(dealer_frame)

        self.dealer_widget = HandWidget(is_dealer=True)
        dealer_layout.addWidget(self.dealer_widget)

        main_layout.addWidget(dealer_frame)

        # Játékos kártyái - TabWidget a split kezekhez
        self.hands_tab = QTabWidget()
        self.hands_tab.setTabPosition(QTabWidget.South)

        # Fő kéz létrehozása
        self.create_new_hand()

        main_layout.addWidget(self.hands_tab)

        # Gombok panel
        buttons_panel = QFrame()
        buttons_layout = QHBoxLayout(buttons_panel)

        # Stílusok az olvashatóbb szövegekért
        button_style = """
        QPushButton {
            background-color: #0066cc;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #0055aa;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        """

        self.bet_button = QPushButton("Tét")
        self.bet_button.setFont(QFont('Arial', 12))
        self.bet_button.clicked.connect(self.place_bet)

        self.deal_button = QPushButton("Osztás")
        self.deal_button.setFont(QFont('Arial', 12))
        self.deal_button.clicked.connect(self.deal_cards)
        self.deal_button.setEnabled(False)

        self.new_game_button = QPushButton("Új játék")
        self.new_game_button.setFont(QFont('Arial', 12))
        self.new_game_button.clicked.connect(self.new_game)

        self.bet_button.setStyleSheet(button_style)
        self.deal_button.setStyleSheet(button_style)
        self.new_game_button.setStyleSheet(button_style)

        buttons_layout.addWidget(self.bet_button)
        buttons_layout.addWidget(self.deal_button)
        buttons_layout.addWidget(self.new_game_button)

        main_layout.addWidget(buttons_panel)

        # Eredmény címke
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(QFont('Arial', 14, QFont.Bold))
        main_layout.addWidget(self.result_label)

        # Státusz sáv
        self.statusBar().showMessage("Helyezz tétet a játék indításához!")

    def set_color_scheme(self):
        # Zöld alapú téma, kaszinó stílusban
        palette = QPalette()

        # Zöld háttér a kaszinó asztalhoz
        palette.setColor(QPalette.Window, QColor(53, 101, 77))
        palette.setColor(QPalette.WindowText, Qt.white)

        # Világosabb szöveg a jobb olvashatóságért
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.ButtonText, Qt.white)

        # Panel háttérszínek
        palette.setColor(QPalette.Base, QColor(27, 67, 50))

        self.setPalette(palette)

        # Stílus lap az egész alkalmazáshoz
        self.setStyleSheet("""
            QFrame {
                background-color: #1B4332;
                border-radius: 8px;
                border: 1px solid #2D6A4F;
            }

            QLabel {
                color: white;
            }

            QMainWindow {
                background-color: #355E4D;
            }

            QTabWidget::pane {
                border: 1px solid #2D6A4F;
                background-color: #1B4332;
                border-radius: 8px;
            }

            QTabBar::tab {
                background-color: #2D6A4F;
                color: white;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: #3B8C6E;
                font-weight: bold;
            }
        """)

    def place_bet(self):
        if self.player_money <= 0:
            QMessageBox.warning(self, "Figyelmeztetés", "Elfogyott a pénzed! Új játékot kell kezdened.")
            return

        # Zseton dialógus megnyitása
        self.open_chip_dialog()

    def open_chip_dialog(self):
        # Zseton dialógus létrehozása
        dialog = QDialog(self)
        dialog.setWindowTitle("Válassz zsetonokat")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Jelenlegi tét és egyenleg mutatása
        info_label = QLabel(f"Egyenleg: {self.player_money} Ft\nJelenlegi tét: {self.current_bet} Ft")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont('Arial', 12))
        layout.addWidget(info_label)

        # Zsetonok
        chips_layout = QHBoxLayout()

        # Különböző értékű zsetonok
        chip_values = [1000, 5000, 10000, 50000, 100000]
        chip_colors = ["#1E88E5", "#43A047", "#F9A825", "#D81B60", "#6D4C41"]

        # Zseton gombok
        for i, (value, color) in enumerate(zip(chip_values, chip_colors)):
            chip_button = QPushButton(f"{value}")
            chip_button.setFixedSize(80, 80)
            chip_button.setFont(QFont('Arial', 10, QFont.Bold))
            chip_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 40px;
                    border: 3px solid white;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    border: 3px solid #FFEB3B;
                }}
                QPushButton:pressed {{
                    background-color: {color};
                    border: 3px solid #FFC107;
                }}
            """)
            chip_button.clicked.connect(lambda checked, v=value: self.add_chip(v, info_label))
            chips_layout.addWidget(chip_button)

        layout.addLayout(chips_layout)

        # Törlés gomb
        clear_button = QPushButton("Törlés")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        clear_button.clicked.connect(lambda: self.clear_chips(info_label))
        layout.addWidget(clear_button)

        # OK és Mégse gombok
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        ok_button.clicked.connect(dialog.accept)

        cancel_button = QPushButton("Mégse")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        # Zseton ideiglenes értéke a dialógusban
        self.temp_bet = self.current_bet

        # Dialógus megjelenítése
        result = dialog.exec_()

        # Ha az OK-ra kattintottak
        if result == QDialog.Accepted and self.temp_bet > 0:
            self.current_bet = self.temp_bet
            self.player_money -= self.current_bet
            self.update_money_labels()
            self.bet_button.setEnabled(False)
            self.deal_button.setEnabled(True)
            self.statusBar().showMessage("Kattints az 'Osztás' gombra a játék kezdéséhez!")

    def add_chip(self, value, info_label):
        if value <= self.player_money:
            self.temp_bet += value
            info_label.setText(f"Egyenleg: {self.player_money} Ft\nJelenlegi tét: {self.temp_bet} Ft")

    def clear_chips(self, info_label):
        self.temp_bet = 0
        info_label.setText(f"Egyenleg: {self.player_money} Ft\nJelenlegi tét: {self.temp_bet} Ft")

    def update_money_labels(self):
        self.money_label.setText(f"Pénz: {self.player_money} Ft")
        self.bet_label.setText(f"Tét: {self.current_bet} Ft")

    def deal_cards(self):
        # Új játék kezdése
        self.dealer_widget.clear()
        self.dealer_hand = self.dealer_widget.hand

        # Játékos kézhez tét hozzáadása
        current_hand = self.player_hands[0]
        current_hand.hand.bet = self.current_bet
        current_hand.bet_label.setText(f"Tét: {self.current_bet} Ft")

        # Kezdő lapok osztása
        current_hand.hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        current_hand.hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())

        # UI frissítése
        current_hand.update_display()
        self.dealer_widget.update_display()

        # Gomb állapotok beállítása
        self.deal_button.setEnabled(False)
        current_hand.hit_button.setEnabled(True)
        current_hand.stand_button.setEnabled(True)

        # Frissítjük a dupla és split gombokat
        current_hand.update_buttons()

        # Ellenőrizzük, van-e blackjack
        if current_hand.hand.is_blackjack():
            self.stand(0)  # Automatikusan megállunk blackjack esetén

        # Aktív kéz beállítása
        self.active_hand_index = 0
        self.hands_tab.setCurrentIndex(0)

        self.statusBar().showMessage("Kérsz még lapot, vagy megállsz?")

    def hit(self, hand_index):
        # Ellenőrizzük, hogy a megfelelő kéz aktív-e
        if hand_index != self.active_hand_index or not self.player_hands[hand_index].hand.is_active:
            return

        # Játékos lapot kér
        current_hand = self.player_hands[hand_index]
        current_hand.hand.add_card(self.deck.deal())
        current_hand.update_display()

        # Dupla esetén automatikusan megáll
        if current_hand.hand.doubled:
            self.stand(hand_index)
            return

        # Ellenőrizzük, hogy túlléptük-e a 21-et
        if current_hand.hand.calculate_value() > 21:
            current_hand.hand.is_active = False
            current_hand.update_buttons()

            # Következő kézre lépés vagy játék vége
            self.move_to_next_hand()

    def stand(self, hand_index):
        # Ellenőrizzük, hogy a megfelelő kéz aktív-e
        if hand_index != self.active_hand_index or not self.player_hands[hand_index].hand.is_active:
            return

        # A játékos megáll
        current_hand = self.player_hands[hand_index]
        current_hand.hand.is_active = False
        current_hand.update_buttons()

        # Következő kézre lépés vagy játék vége
        self.move_to_next_hand()

    def double_down(self, hand_index):
        # Ellenőrizzük, hogy a megfelelő kéz aktív-e
        if hand_index != self.active_hand_index or not self.player_hands[hand_index].hand.is_active:
            return

        current_hand = self.player_hands[hand_index]

        # Csak akkor duplázhatunk, ha van elég pénz
        if self.player_money < current_hand.hand.bet:
            QMessageBox.warning(self, "Figyelmeztetés", "Nincs elég pénzed a duplázáshoz!")
            return

        # Tét duplázása
        self.player_money -= current_hand.hand.bet
        current_hand.hand.bet *= 2
        current_hand.bet_label.setText(f"Tét: {current_hand.hand.bet} Ft")
        self.update_money_labels()

        # Duplázás jelzése
        current_hand.hand.doubled = True

        # Egy lap húzása és automatikus megállás
        self.hit(hand_index)

    def split(self, hand_index):
        # Ellenőrizzük, hogy a megfelelő kéz aktív-e
        if hand_index != self.active_hand_index or not self.player_hands[hand_index].hand.is_active:
            return

        current_hand = self.player_hands[hand_index]

        # Ellenőrizzük, hogy lehet-e splittelni
        if not current_hand.hand.can_split():
            return

        # Ellenőrizzük, hogy van-e elég pénz
        if self.player_money < current_hand.hand.bet:
            QMessageBox.warning(self, "Figyelmeztetés", "Nincs elég pénzed a split-hez!")
            return

        # A második lap kivétele
        second_card = current_hand.hand.cards.pop()

        # Új kéz létrehozása
        new_hand = self.create_new_hand()

        # Tét levonása a játékos pénzéből
        self.player_money -= current_hand.hand.bet
        new_hand.hand.bet = current_hand.hand.bet
        new_hand.bet_label.setText(f"Tét: {new_hand.hand.bet} Ft")
        self.update_money_labels()

        # Kártya hozzáadása az új kézhez
        new_hand.hand.add_card(second_card)

        # Kártyák kiosztása mindkét kézhez
        current_hand.hand.add_card(self.deck.deal())
        new_hand.hand.add_card(self.deck.deal())

        # UI frissítése
        current_hand.update_display()
        new_hand.update_display()

        # Ellenőrizzük a split utáni kártyák értékét
        # Ha ászokat splitteltünk, automatikusan megállunk
        if current_hand.hand.cards[0].value == 'A':
            current_hand.hand.is_active = False
            new_hand.hand.is_active = False
            self.move_to_next_hand()
        else:
            # Gombok frissítése
            current_hand.update_buttons()
            new_hand.update_buttons()

    def move_to_next_hand(self):
        # Ellenőrizzük, hogy van-e még aktív kéz
        next_hand_index = self.active_hand_index + 1

        if next_hand_index < len(self.player_hands):
            # Következő kézre lépés
            self.active_hand_index = next_hand_index
            self.hands_tab.setCurrentIndex(next_hand_index)

            # Gombok frissítése
            self.player_hands[next_hand_index].update_buttons()
        else:
            # Nincs több kéz, az osztó következik
            self.play_dealer_hand()

    def play_dealer_hand(self):
        # Felfedni az osztó második lapját
        self.dealer_widget.update_display(reveal_dealer=True)

        # Ellenőrizzük, hogy minden játékos kéz besült-e
        all_busted = True
        for hand_widget in self.player_hands:
            if hand_widget.hand.calculate_value() <= 21:
                all_busted = False
                break

        # Ha minden kéz besült, az osztó nem húz
        if all_busted:
            self.check_winners()
            return

        # Az osztó húz lapokat, amíg a keze értéke kevesebb mint 17
        dealer_value = self.dealer_hand.calculate_value()

        def dealer_draw():
            nonlocal dealer_value
            if dealer_value < 17:
                self.dealer_hand.add_card(self.deck.deal())
                dealer_value = self.dealer_hand.calculate_value()
                self.dealer_widget.update_display(reveal_dealer=True)

                if dealer_value < 17:
                    QTimer.singleShot(1000, dealer_draw)  # Késleltetett húzás animációhoz
                else:
                    self.check_winners()
            else:
                self.check_winners()

        if dealer_value < 17:
            QTimer.singleShot(1000, dealer_draw)
        else:
            self.check_winners()

    def check_winners(self):
        dealer_value = self.dealer_hand.calculate_value()
        dealer_blackjack = self.dealer_hand.is_blackjack()
        dealer_busted = dealer_value > 21

        results = []
        total_win = 0

        # Ellenőrizzük minden kéz eredményét
        for i, hand_widget in enumerate(self.player_hands):
            hand = hand_widget.hand
            hand_value = hand.calculate_value()
            hand_busted = hand_value > 21
            hand_blackjack = hand.is_blackjack()

            # Nyeremény kiszámítása
            result = ""
            win_amount = 0

            if hand_busted:
                result = f"Kéz {i+1}: Vesztettél! Túllépted a 21-et."
            elif dealer_busted:
                result = f"Kéz {i+1}: Nyertél! Az osztó túllépte a 21-et."
                win_amount = hand.bet * 2
            elif hand_blackjack and not dealer_blackjack:
                result = f"Kéz {i+1}: Nyertél! Blackjack!"
                win_amount = int(hand.bet * 2.5)  # 3:2 kifizetés blackjack-re
            elif dealer_blackjack and not hand_blackjack:
                result = f"Kéz {i+1}: Vesztettél! Az osztónak Blackjack-je van."
            elif hand_blackjack and dealer_blackjack:
                result = f"Kéz {i+1}: Döntetlen! Mindkét félnek Blackjack-je van."
                win_amount = hand.bet  # Visszakapja a tétet
            elif hand_value > dealer_value:
                result = f"Kéz {i+1}: Nyertél! A lapjaid értéke magasabb."
                win_amount = hand.bet * 2
            elif dealer_value > hand_value:
                result = f"Kéz {i+1}: Vesztettél! Az osztó lapjainak értéke magasabb."
            else:
                result = f"Kéz {i+1}: Döntetlen! Ugyanaz az érték."
                win_amount = hand.bet  # Visszakapja a tétet

            # Nyeremény hozzáadása
            total_win += win_amount
            results.append(result)

        # Eredmények megjelenítése
        results_text = "<br>".join(results)
        self.result_label.setText(f"<html>{results_text}</html>")

        # Összes nyeremény hozzáadása
        self.player_money += total_win
        self.update_money_labels()

        # Gombok frissítése
        self.bet_button.setEnabled(True)
        self.deal_button.setEnabled(False)

        # Státusz frissítése
        self.statusBar().showMessage("Játék vége. Helyezz új tétet vagy kezdj új játékot!")

        # Ha elfogyott a pénz
        if self.player_money <= 0:
            QMessageBox.information(self, "Játék vége",
                                   "Elfogyott a pénzed! Új játékot kell kezdened.")
            self.bet_button.setEnabled(False)

    def new_game(self):
        reply = QMessageBox.question(self, "Új játék",
                                    "Biztosan új játékot szeretnél kezdeni?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Kezek törlése
            while self.hands_tab.count() > 0:
                self.hands_tab.removeTab(0)

            # Változók alaphelyzetbe állítása
            self.player_hands = []
            self.deck = Deck()
            self.dealer_widget.clear()
            self.game_over = False
            self.current_bet = 0
            self.temp_bet = 0
            self.active_hand_index = 0

            # Első kéz létrehozása
            self.create_new_hand()

            # UI frissítése
            self.update_money_labels()
            self.result_label.setText("")

            # Gombok visszaállítása
            self.bet_button.setEnabled(True)
            self.deal_button.setEnabled(False)

            self.statusBar().showMessage("Új játék kezdődött! Helyezz tétet a kezdéshez.")

if __name__ == "__main__":
    try:
        print("Program indítása...")
        app = QApplication(sys.argv)
        print("QApplication létrehozva")
        window = BlackjackGame()
        print("BlackjackGame létrehozva")
        window.show()
        print("Ablak megjelenítve")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Hiba történt: {e}")
        import traceback
        traceback.print_exc()

