from Automaton import AutomatKomorkowy, StanKomorki, KierunekWiatru
import numpy
import pygame

class Wizualizacja:

    def __init__(self, automat: AutomatKomorkowy, rozmiar_komorki: int):
        self.automat = automat

        # Ustawienia okna (rozmiar komorki, panelu UI, szerokosc i wysokosc okna)
        self.rozmiar_komorki = rozmiar_komorki
        self.rozmiar_panelu_UI = 280
        self.szerokosc_okna = automat.kolumny * rozmiar_komorki + self.rozmiar_panelu_UI
        self.wysokosc_okna = automat.wiersze * rozmiar_komorki

        # Predkosc aktualizacji
        self.MAKS_PREDKOSC = 30
        self.MIN_PREDKOSC = 1
        self.ZMIANA_WOLNA = 1
        self.ZMIANA_NORMALNA = 5
        self.ZMIANA_SZYBKA = 10
        self._ustaw_predkosc_aktualizacji(5)
        self.czas_od_ostatniej_aktualizacji = 0

        self.delta_czasu = 0

        # Flagi
        self.dziala = True
        self.pauza = True
        self.wybrane_narzedzie = StanKomorki.OGIEN

        pygame.init()
        self.ekran = pygame.display.set_mode((self.szerokosc_okna, self.wysokosc_okna))
        pygame.display.set_caption("Symulacja Pozaru Lasu")
        self.zegar = pygame.time.Clock()

        # Pozycje przyciskow
        SZEROKOSC = self.rozmiar_panelu_UI * 4 / 5
        WYSOKOSC = 35

        x_start = self.automat.kolumny * self.rozmiar_komorki + 20

        self.przyciski = {
            "pauza": {"rect": pygame.Rect(x_start, 20, SZEROKOSC, WYSOKOSC), "text": "Start"},
            "reset": {"rect": pygame.Rect(x_start, 60, SZEROKOSC, WYSOKOSC), "text": "Reset"},
            "wolniej": {"rect": pygame.Rect(x_start, 100, SZEROKOSC / 2 - 5, WYSOKOSC), "text": "<<"},
            "szybciej": {"rect": pygame.Rect(x_start + SZEROKOSC / 2 + 5, 100, SZEROKOSC / 2 - 5, WYSOKOSC), "text": ">>"},
            "wiatr": {"rect": pygame.Rect(x_start, 180, SZEROKOSC, WYSOKOSC),
                      "text": f"Wiatr: {self._tlumacz_kierunek(self.automat.kierunek_wiatru)}"},
            "predkosc_wiatru_minus": {"rect": pygame.Rect(x_start, 220, SZEROKOSC / 2 - 5, WYSOKOSC), "text": "-"},
            "predkosc_wiatru_plus": {"rect": pygame.Rect(x_start + SZEROKOSC / 2 + 5, 220, SZEROKOSC / 2 - 5, WYSOKOSC), "text": "+"},
            "wilgotnosc_minus": {"rect": pygame.Rect(x_start, 280, SZEROKOSC / 2 - 5, WYSOKOSC), "text": "-"},
            "wilgotnosc_plus": {"rect": pygame.Rect(x_start + SZEROKOSC / 2 + 5, 280, SZEROKOSC / 2 - 5, WYSOKOSC), "text": "+"},
            "pusty": {"rect": pygame.Rect(x_start, 350, SZEROKOSC, WYSOKOSC), "text": "Ziemia"},
            "las": {"rect": pygame.Rect(x_start, 390, SZEROKOSC, WYSOKOSC), "text": "Las"},
            "las_gesty": {"rect": pygame.Rect(x_start, 430, SZEROKOSC, WYSOKOSC), "text": "Gesty Las"},
            "ogien": {"rect": pygame.Rect(x_start, 470, SZEROKOSC, WYSOKOSC), "text": "Ogien"},
            "woda": {"rect": pygame.Rect(x_start, 510, SZEROKOSC, WYSOKOSC), "text": "Woda"},
            "powodz": {"rect": pygame.Rect(x_start, 550, SZEROKOSC, WYSOKOSC), "text": "Powodz"},
            "spalony": {"rect": pygame.Rect(x_start, 590, SZEROKOSC, WYSOKOSC), "text": "Zgliszcza"}
        }

    def _tlumacz_kierunek(self, kierunek: KierunekWiatru) -> str:
        tlumaczenia = {
            KierunekWiatru.BRAK: "Brak",
            KierunekWiatru.N: "Polnoc",
            KierunekWiatru.S: "Poludnie",
            KierunekWiatru.W: "Zachod",
            KierunekWiatru.E: "Wschod",
            KierunekWiatru.NW: "Pln-Zach",
            KierunekWiatru.SW: "Pld-Zach",
            KierunekWiatru.NE: "Pln-Wsch",
            KierunekWiatru.SE: "Pld-Wsch"
        }
        return tlumaczenia.get(kierunek, "Brak")

    def _aktualizuj(self):
        self._obsluz_zdarzenia()
        if not self.pauza:
            self.czas_od_ostatniej_aktualizacji += self.delta_czasu
            if self.czas_od_ostatniej_aktualizacji >= self.czas_miedzy_aktualizacjami:
                self.automat.aktualizuj()
                self.czas_od_ostatniej_aktualizacji = 0

    def _obsluz_zdarzenia(self):
        for zdarzenie in pygame.event.get():
            if zdarzenie.type == pygame.QUIT:
                self.dziala = False
            elif zdarzenie.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # Sprawdz klikniecie na siatce
                if x < self.automat.kolumny * self.rozmiar_komorki:
                    kol, wiersz = x // self.rozmiar_komorki, y // self.rozmiar_komorki
                    if 0 <= wiersz < self.automat.wiersze and 0 <= kol < self.automat.kolumny:
                        # UMIESZCZENIE KOMORKI - zmiana przestrzeni automatu
                        self.automat.umiesc_komorke(wiersz, kol, self.wybrane_narzedzie)
                # Sprawdz klikniecie na przyciskach
                for klucz, przycisk in self.przyciski.items():
                    if przycisk["rect"].collidepoint(x, y):
                        if klucz == "pauza":
                            self.pauza = not self.pauza
                            self.przyciski["pauza"]["text"] = "Wznow" if self.pauza else "Pauza"
                        elif klucz == "reset":
                            self.przyciski["pauza"]["text"] = "Start"
                            self.pauza = True
                            self.automat.resetuj()
                        elif klucz == "wolniej":
                            krok = self._dostosuj_zmiane_predkosci()
                            self._ustaw_predkosc_aktualizacji(self.aktualizacje_na_sek - krok)
                        elif klucz == "szybciej":
                            krok = self._dostosuj_zmiane_predkosci()
                            self._ustaw_predkosc_aktualizacji(self.aktualizacje_na_sek + krok)
                        elif klucz == "wiatr":
                            kierunki = list(KierunekWiatru)
                            aktualny_indeks = kierunki.index(self.automat.kierunek_wiatru)
                            nowy_kierunek = kierunki[(aktualny_indeks + 1) % len(kierunki)]
                            self.automat.ustaw_wiatr(nowy_kierunek)
                            self.przyciski["wiatr"]["text"] = f"Wiatr: {self._tlumacz_kierunek(nowy_kierunek)}"
                        elif klucz == "predkosc_wiatru_minus":
                            self.automat.ustaw_predkosc_wiatru(self.automat.predkosc_wiatru - 0.1)
                        elif klucz == "predkosc_wiatru_plus":
                            self.automat.ustaw_predkosc_wiatru(self.automat.predkosc_wiatru + 0.1)
                        elif klucz == "wilgotnosc_minus":
                            self.automat.ustaw_wilgotnosc(self.automat.wilgotnosc - 0.1)
                        elif klucz == "wilgotnosc_plus":
                            self.automat.ustaw_wilgotnosc(self.automat.wilgotnosc + 0.1)
                        elif klucz == "pusty":
                            self.wybrane_narzedzie = StanKomorki.PUSTY
                        elif klucz == "las":
                            self.wybrane_narzedzie = StanKomorki.LAS
                        elif klucz == "las_gesty":
                            self.wybrane_narzedzie = StanKomorki.LAS_GESTY
                        elif klucz == "ogien":
                            self.wybrane_narzedzie = StanKomorki.OGIEN
                        elif klucz == "woda":
                            self.wybrane_narzedzie = StanKomorki.WODA
                        elif klucz == "powodz":
                            self.wybrane_narzedzie = StanKomorki.POWODZ
                        elif klucz == "spalony":
                            self.wybrane_narzedzie = StanKomorki.SPALONY

            elif zdarzenie.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # Lewy przycisk wcisniety
                    x, y = pygame.mouse.get_pos()
                    if x < self.automat.kolumny * self.rozmiar_komorki:
                        kol, wiersz = x // self.rozmiar_komorki, y // self.rozmiar_komorki
                        if 0 <= wiersz < self.automat.wiersze and 0 <= kol < self.automat.kolumny:
                            self.automat.umiesc_komorke(wiersz, kol, self.wybrane_narzedzie)

            elif zdarzenie.type == pygame.KEYDOWN:
                if zdarzenie.key == pygame.K_SPACE:
                    self.pauza = not self.pauza

    def _ustaw_predkosc_aktualizacji(self, nowa_predkosc: float):
        self.aktualizacje_na_sek = self._ogranicz(nowa_predkosc, self.MIN_PREDKOSC, self.MAKS_PREDKOSC)
        self.czas_miedzy_aktualizacjami = (1 / self.aktualizacje_na_sek) * 1000.0  # Milisekundy

    def _ogranicz(self, wartosc: float, minimum: float, maksimum: float) -> float:
        if wartosc > maksimum: return maksimum
        if wartosc < minimum: return minimum
        return wartosc

    def _renderuj(self):
        self.ekran.fill((220, 220, 220))
        self._rysuj_siatke()
        self._rysuj_przyciski()
        self._rysuj_tekst()
        pygame.display.flip()
        self.delta_czasu = self.zegar.tick(60)

    def _rysuj_siatke(self):
        for wiersz in range(self.automat.wiersze):
            for kol in range(self.automat.kolumny):
                stan = self.automat.siatka[wiersz, kol]
                kolor = self._pobierz_kolor(StanKomorki(stan))
                pygame.draw.rect(self.ekran, kolor,
                                 (kol * self.rozmiar_komorki, wiersz * self.rozmiar_komorki,
                                  self.rozmiar_komorki, self.rozmiar_komorki))
                # Linie siatki
                pygame.draw.rect(self.ekran, (200, 200, 200),
                                 (kol * self.rozmiar_komorki, wiersz * self.rozmiar_komorki,
                                  self.rozmiar_komorki, self.rozmiar_komorki), 1)

    def _rysuj_przyciski(self):
        czcionka = pygame.font.Font(None, 28)
        for klucz, przycisk in self.przyciski.items():
            # Podswietlenie wybranego narzedzia
            if klucz in ["pusty", "las", "las_gesty", "ogien", "woda", "powodz", "spalony"]:
                stan_mapy = {
                    "pusty": StanKomorki.PUSTY,
                    "las": StanKomorki.LAS,
                    "las_gesty": StanKomorki.LAS_GESTY,
                    "ogien": StanKomorki.OGIEN,
                    "woda": StanKomorki.WODA,
                    "powodz": StanKomorki.POWODZ,
                    "spalony": StanKomorki.SPALONY
                }
                if stan_mapy[klucz] == self.wybrane_narzedzie:
                    pygame.draw.rect(self.ekran, (200, 255, 200), przycisk["rect"])  # Zielone tlo dla wybranego
                else:
                    pygame.draw.rect(self.ekran, (255, 255, 255), przycisk["rect"])  # Biale tlo
            else:
                pygame.draw.rect(self.ekran, (255, 255, 255), przycisk["rect"])  # Biale tlo

            pygame.draw.rect(self.ekran, (0, 0, 0), przycisk["rect"], 2)
            tekst = czcionka.render(przycisk["text"], True, (0, 0, 0))
            tekst_rect = tekst.get_rect(center=przycisk["rect"].center)
            self.ekran.blit(tekst, tekst_rect)

    def _rysuj_tekst(self):
        x_start = self.automat.kolumny * self.rozmiar_komorki + 20

        # Predkosc aktualizacji
        czcionka_predkosc = pygame.font.Font(None, 28)
        tekst_predkosc = f"Predkosc: {self.aktualizacje_na_sek} m/s"
        powierzchnia_predkosc = czcionka_predkosc.render(tekst_predkosc, True, (0, 0, 0))
        rect_predkosc = powierzchnia_predkosc.get_rect(center=(x_start + 110, 150))
        self.ekran.blit(powierzchnia_predkosc, rect_predkosc)

        # Predkosc wiatru
        czcionka_param = pygame.font.Font(None, 24)
        tekst_pw = f"Predkosc wiatru: {self.automat.predkosc_wiatru:.1f} m/s"
        powierzchnia_pw = czcionka_param.render(tekst_pw, True, (0, 0, 0))
        rect_pw = powierzchnia_pw.get_rect(center=(x_start + 110, 270))
        self.ekran.blit(powierzchnia_pw, rect_pw)

        # Wilgotnosc
        tekst_w = f"Wilgotnosc: {self.automat.wilgotnosc:.1f}"
        powierzchnia_w = czcionka_param.render(tekst_w, True, (0, 0, 0))
        rect_w = powierzchnia_w.get_rect(center=(x_start + 110, 330))
        self.ekran.blit(powierzchnia_w, rect_w)

    def _pobierz_kolor(self, stan: StanKomorki):
        mapa_kolorow = {
            StanKomorki.PUSTY: (153, 76, 0),  # Brazowy (ziemia)
            StanKomorki.OGIEN: (255, 0, 0),  # Czerwony (ogien)
            StanKomorki.WODA: (51, 153, 255),  # Niebieski (woda)
            StanKomorki.POWODZ: (102, 178, 255),  # Jasnoniebieski (powodz)
            StanKomorki.LAS: (0, 255, 0),  # Zielony (las)
            StanKomorki.LAS_GESTY: (0, 190, 0),  # Ciemnozielony (gesty las)
            StanKomorki.SPALONY: (160, 160, 160),  # Szary (zgliszcza)
        }
        return mapa_kolorow[stan]

    def uruchom(self):
        while self.dziala:
            self._aktualizuj()
            self._renderuj()

        pygame.quit()