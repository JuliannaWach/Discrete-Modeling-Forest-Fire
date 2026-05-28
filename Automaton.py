from enum import Enum
import numpy as numpy
import random

# Definicja stanow komorek
class StanKomorki(Enum):
    PUSTY = 0  # Teren (ziemia) -> przejdzie w LAS
    OGIEN = 1  # Plonacy teren -> przejdzie w SPALONY
    WODA = 2  # Woda (rzeka, jezioro) - stan staly
    POWODZ = 3  # Zalany teren -> przejdzie w PUSTY
    LAS = 4  # Mlody las -> przejdzie w LAS_GESTY
    LAS_GESTY = 5  # Gesty las (zarosniety) - stan staly, plonie dluzej
    SPALONY = 6  # Spalony teren -> przejdzie w PUSTY

# Parametry czasowe przejsc miedzy stanami (w krokach symulacji)

# Czas palenia sie terenu
CZAS_SPALANIA_MIN = 1
CZAS_SPALANIA_MAX = 5
MNOZNIK_SPALANIA_GESTEGO_LASU = 6  # Gesty las plonie 6x dluzej

# Czas regeneracji spalonego terenu
CZAS_ZGLISZCZ_MIN = 50
CZAS_ZGLISZCZ_MAX = 75

# Czas wzrostu lasu
CZAS_WZROSTU_MIN = 150
CZAS_WZROSTU_MAX = 175

# Czas zarastania lasu (przeksztalcenie w gesty las)
CZAS_ZARASTANIA_MIN = 500
CZAS_ZARASTANIA_MAX = 700

# Kierunki wiatru - wiatr wplywa na kierunek rozprzestrzeniania sie ognia
class KierunekWiatru(Enum):
    BRAK = 0  # Brak wiatru
    N = 1  # Polnoc
    S = 2  # Poludnie
    W = 3  # Zachod
    E = 4  # Wschod
    NW = 5  # Polnocny-Zachod
    SW = 6  # Poludniowy-Zachod
    NE = 7  # Polnocny-Wschod
    SE = 8  # Poludniowy-Wschod

# Prawdopodobienstwo rozprzestrzeniania sie ognia w zaleznosci od kierunku wiatru
WAGA_KIERUNEK_WIATRU = 0.9  # Kierunek zgodny z wiatrem (najwyzsze prawdopodobienstwo)
WAGA_KIERUNEK_ROWNOLEGLY = 0.7  # Kierunek rownolegly do wiatru
WAGA_KIERUNEK_PRZECIWNY = 0.05  # Kierunek przeciwny do wiatru (najnizsze prawdopodobienstwo)
WAGA_KIERUNEK_NEUTRALNY = 0.1  # Brak wiatru (wszystkie kierunki rowne)

class AutomatKomorkowy:

    def __init__(self, wiersze: int, kolumny: int):
        self.wiersze = wiersze
        self.kolumny = kolumny
        self.siatka = numpy.zeros((wiersze, kolumny), dtype=int)  # Inicjalizacja pustej siatki
        self._siatka_poczatkowa = self.siatka.copy()

        # Parametry z mozliwoscia modyfikacji przez uzytkownika
        self.kierunek_wiatru = KierunekWiatru.BRAK  # Domyslnie: brak wiatru
        self.predkosc_wiatru = 0.5  # Predkosc wiatru (0.0 - 1.0)
        self.wilgotnosc = 0.5  # Wilgotnosc terenu (0.0 - 1.0)

        # Szansa na rozprzestrzenienie ognia (modyfikowana przez parametry)
        self._bazowa_szansa_ognia = 0.5

        # Zegary dla kazdej komorki (okreslaja czas do nastepnego przejscia)
        self._zegary = numpy.full((wiersze, kolumny), -1, dtype=int)  # -1 = brak przejscia czasowego

        # Wysokosc terenu (wplywa na rozprzestrzenianie ognia - ogien wedruje w gore szybciej)
        self._wysokosc_terenu = numpy.zeros((wiersze, kolumny), dtype=float)

    def inicjalizuj_z_mapy(self, tablica_mapy: numpy.ndarray):
        self.siatka = numpy.array(tablica_mapy)

        # Inicjalizacja wszystkich komorek
        for wiersz in range(self.wiersze):
            for kolumna in range(self.kolumny):
                stan = self.siatka[wiersz, kolumna]
                self._inicjalizuj_komorke(wiersz, kolumna, stan)

        # Kopia do resetowania
        self._siatka_poczatkowa = self.siatka.copy()

    def ustaw_wysokosc_terenu(self, wysokosc: numpy.ndarray):
        self._wysokosc_terenu = wysokosc

    def aktualizuj(self):
        # Pracujemy na kopii siatki
        nowa_siatka = self.siatka.copy()

        # Iteracja po wszystkich komorkach
        for wiersz in range(self.wiersze):
            for kolumna in range(self.kolumny):
                stan = self.siatka[wiersz, kolumna]

                # Zmniejszanie zegara komorki
                if self._zegary[wiersz, kolumna] > 0:
                    self._zegary[wiersz, kolumna] -= 1
                elif self._zegary[wiersz, kolumna] == 0:
                    # Przejscie do nastepnego stanu gdy zegar osiagnie 0
                    self._przejscie_komorki(wiersz, kolumna, stan, nowa_siatka)

                # Rozprzestrzenianie ognia
                if stan == StanKomorki.OGIEN.value:
                    sasiedzi_z_wagami = self._pobierz_sasiadow_z_wiatrem_i_wagami(wiersz, kolumna)
                    for (sw, sk), waga in sasiedzi_z_wagami:
                        stan_sasiada = self.siatka[sw, sk]
                        if stan_sasiada == StanKomorki.LAS.value or stan_sasiada == StanKomorki.LAS_GESTY.value:
                            # Obliczenie prawdopodobienstwa zapalenia z uwzglednieniem parametrow
                            szansa = self._oblicz_szanse_zapalenia(wiersz, kolumna, sw, sk, waga)
                            if random.random() < szansa:
                                nowa_siatka[sw, sk] = StanKomorki.OGIEN.value
                                self._inicjalizuj_komorke(sw, sk, StanKomorki.OGIEN.value)

                # Rozprzestrzenianie wody
                elif stan == StanKomorki.WODA.value or stan == StanKomorki.POWODZ.value:
                    sasiedzi = self._pobierz_sasiadow(wiersz, kolumna)
                    for sw, sk in sasiedzi:
                        stan_sasiada = self.siatka[sw, sk]
                        if stan_sasiada in [StanKomorki.OGIEN.value, StanKomorki.SPALONY.value]:
                            nowa_siatka[sw, sk] = StanKomorki.POWODZ.value
                            self._inicjalizuj_komorke(sw, sk, StanKomorki.POWODZ.value)

        self.siatka = nowa_siatka

    def _oblicz_szanse_zapalenia(self, wiersz_zrodla, kol_zrodla, wiersz_celu, kol_celu, waga_wiatru):
        szansa = self._bazowa_szansa_ognia * waga_wiatru

        # Modyfikacja przez predkosc wiatru
        szansa *= (0.5 + self.predkosc_wiatru * 0.5)

        # Modyfikacja przez wilgotnosc (wysoka wilgotnosc zmniejsza szanse na zapalenie)
        szansa *= (1.5 - self.wilgotnosc)

        # Modyfikacja przez roznice wysokosci
        roznica_wysokosci = self._wysokosc_terenu[wiersz_celu, kol_celu] - self._wysokosc_terenu[
            wiersz_zrodla, kol_zrodla]
        if roznica_wysokosci > 0:  # Ogien wedruje w gore - zwiekszona szansa
            szansa *= (1.0 + roznica_wysokosci * 0.5)
        else:  # Ogien wedruje w dol - zmniejszona szansa
            szansa *= (1.0 + roznica_wysokosci * 0.3)

        return min(szansa, 1.0)  # Maksymalnie 100%

    def resetuj(self):
        self.siatka = self._siatka_poczatkowa.copy()
        self._zegary = numpy.full((self.wiersze, self.kolumny), -1, dtype=int)

        # Ponowna inicjalizacja wszystkich komorek
        for wiersz in range(self.wiersze):
            for kolumna in range(self.kolumny):
                stan = self.siatka[wiersz, kolumna]
                self._inicjalizuj_komorke(wiersz, kolumna, stan)

    def umiesc_komorke(self, wiersz: int, kolumna: int, stan: StanKomorki):
        self.siatka[wiersz, kolumna] = stan.value
        self._inicjalizuj_komorke(wiersz, kolumna, stan.value)

    def ustaw_wiatr(self, kierunek: KierunekWiatru):
        self.kierunek_wiatru = kierunek

    def ustaw_predkosc_wiatru(self, predkosc: float):
        self.predkosc_wiatru = max(0.0, min(1.0, predkosc))

    def ustaw_wilgotnosc(self, wilgotnosc: float):
        self.wilgotnosc = max(0.0, min(1.0, wilgotnosc))

    def _inicjalizuj_komorke(self, wiersz: int, kolumna: int, stan: int):
        if stan == StanKomorki.PUSTY.value:
            self._zegary[wiersz, kolumna] = random.randint(CZAS_WZROSTU_MIN, CZAS_WZROSTU_MAX)
        elif stan == StanKomorki.OGIEN.value:
            # Gesty las plonie dluzej
            if self.siatka[wiersz, kolumna] == StanKomorki.LAS_GESTY.value:
                self._zegary[wiersz, kolumna] = random.randint(
                    CZAS_SPALANIA_MIN * MNOZNIK_SPALANIA_GESTEGO_LASU,
                    CZAS_SPALANIA_MAX * MNOZNIK_SPALANIA_GESTEGO_LASU
                )
            else:
                self._zegary[wiersz, kolumna] = random.randint(CZAS_SPALANIA_MIN, CZAS_SPALANIA_MAX)
        elif stan == StanKomorki.WODA.value:
            self._zegary[wiersz, kolumna] = -1  # Stan staly
        elif stan == StanKomorki.POWODZ.value:
            self._zegary[wiersz, kolumna] = random.randint(CZAS_ZGLISZCZ_MIN, CZAS_ZGLISZCZ_MAX)
        elif stan == StanKomorki.LAS.value:
            self._zegary[wiersz, kolumna] = random.randint(CZAS_ZARASTANIA_MIN, CZAS_ZARASTANIA_MAX)
        elif stan == StanKomorki.LAS_GESTY.value:
            self._zegary[wiersz, kolumna] = -1  # Stan staly
        elif stan == StanKomorki.SPALONY.value:
            self._zegary[wiersz, kolumna] = random.randint(CZAS_ZGLISZCZ_MIN, CZAS_ZGLISZCZ_MAX)

    def _przejscie_komorki(self, wiersz: int, kolumna: int, stan: int, siatka: numpy.ndarray):
        nowy_stan = stan
        if stan == StanKomorki.PUSTY.value:
            nowy_stan = StanKomorki.LAS.value
        elif stan == StanKomorki.OGIEN.value:
            nowy_stan = StanKomorki.SPALONY.value
        elif stan == StanKomorki.POWODZ.value:
            nowy_stan = StanKomorki.PUSTY.value
        elif stan == StanKomorki.LAS.value:
            nowy_stan = StanKomorki.LAS_GESTY.value
        elif stan == StanKomorki.SPALONY.value:
            nowy_stan = StanKomorki.PUSTY.value
        else:  # Nieobslugiwany stan (WODA, LAS_GESTY)
            return

        siatka[wiersz, kolumna] = nowy_stan
        self._inicjalizuj_komorke(wiersz, kolumna, nowy_stan)

    def _pobierz_sasiadow(self, wiersz: int, kolumna: int) -> list:
        sasiedzi = []
        for dw, dk in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            sw, sk = wiersz + dw, kolumna + dk
            if 0 <= sw < self.wiersze and 0 <= sk < self.kolumny:
                sasiedzi.append((sw, sk))
        return sasiedzi

    def _pobierz_sasiadow_z_wiatrem_i_wagami(self, wiersz, kolumna) -> list:
        # Wagi w zaleznosci od orientacji wzgledem wiatru
        wkw = WAGA_KIERUNEK_WIATRU
        wkr = WAGA_KIERUNEK_ROWNOLEGLY
        wkp = WAGA_KIERUNEK_PRZECIWNY
        wkn = WAGA_KIERUNEK_NEUTRALNY

        # Mapowanie kierunkow wiatru na wagi sasiadow
        wagi_kierunkow = {
            KierunekWiatru.N: [((-1, 0), wkw), ((-1, -1), wkr), ((-1, 1), wkr),
                               ((0, -1), wkn), ((0, 1), wkn), ((1, 0), wkp), ((1, -1), wkp), ((1, 1), wkp)],
            KierunekWiatru.S: [((1, 0), wkw), ((1, -1), wkr), ((1, 1), wkr),
                               ((0, -1), wkn), ((0, 1), wkn), ((-1, 0), wkp), ((-1, -1), wkp), ((-1, 1), wkp)],
            KierunekWiatru.W: [((0, -1), wkw), ((-1, -1), wkr), ((1, -1), wkr),
                               ((-1, 0), wkn), ((1, 0), wkn), ((0, 1), wkp), ((-1, 1), wkp), ((1, 1), wkp)],
            KierunekWiatru.E: [((0, 1), wkw), ((-1, 1), wkr), ((1, 1), wkr),
                               ((-1, 0), wkn), ((1, 0), wkn), ((0, -1), wkp), ((-1, -1), wkp), ((1, -1), wkp)],
            KierunekWiatru.NW: [((-1, -1), wkw), ((-1, 0), wkr), ((0, -1), wkr),
                                ((1, 1), wkp), ((1, 0), wkn), ((0, 1), wkn), ((-1, 1), wkn), ((1, -1), wkn)],
            KierunekWiatru.NE: [((-1, 1), wkw), ((-1, 0), wkr), ((0, 1), wkr),
                                ((1, -1), wkp), ((1, 0), wkn), ((0, -1), wkn), ((-1, -1), wkn), ((1, 1), wkn)],
            KierunekWiatru.SW: [((1, -1), wkw), ((1, 0), wkr), ((0, -1), wkr),
                                ((-1, 1), wkp), ((-1, 0), wkn), ((0, 1), wkn), ((-1, -1), wkn), ((1, 1), wkn)],
            KierunekWiatru.SE: [((1, 1), wkw), ((1, 0), wkr), ((0, 1), wkr),
                                ((-1, -1), wkp), ((-1, 0), wkn), ((0, -1), wkn), ((-1, 1), wkn), ((1, -1), wkn)],
            KierunekWiatru.BRAK: [((-1, 0), wkn), ((1, 0), wkn), ((0, -1), wkn), ((0, 1), wkn),
                                  ((-1, -1), wkn), ((-1, 1), wkn), ((1, -1), wkn), ((1, 1), wkn)],
        }

        # Pobranie sasiadow dla aktualnego kierunku wiatru
        sasiedzi_wiatru = wagi_kierunkow.get(self.kierunek_wiatru, [])
        sasiedzi_z_wagami = []

        for (dw, dk), waga in sasiedzi_wiatru:
            sw, sk = wiersz + dw, kolumna + dk
            if 0 <= sw < self.wiersze and 0 <= sk < self.kolumny:
                sasiedzi_z_wagami.append(((sw, sk), waga))

        return sasiedzi_z_wagami