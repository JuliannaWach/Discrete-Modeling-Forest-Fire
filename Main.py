from Automaton import AutomatKomorkowy, StanKomorki
from Visualization import Wizualizacja
from PIL import Image
import numpy
import pygame

SCIEZKA_WEJSCIOWA = "Obrazy/"

def wczytaj_mape_z_obrazu(sciezka_obrazu: str, wiersze: int, kolumny: int) -> numpy.ndarray:
    # Wczytanie i skalowanie obrazu
    obraz = Image.open(sciezka_obrazu).convert("RGB")
    obraz = obraz.resize((kolumny, wiersze))
    siatka = numpy.zeros((wiersze, kolumny), dtype=int)

    # Mapowanie pikseli na stany
    for y in range(wiersze):
        for x in range(kolumny):
            piksel = obraz.getpixel((x, y))
            siatka[y, x] = mapuj_piksel_na_stan(piksel)

    return siatka

def mapuj_piksel_na_stan(piksel: tuple) -> int:
    r, g, b = piksel

    # Woda: dominacja niebieskiego
    if b > g and b > r and b - max(r, g) > 20:
        return StanKomorki.WODA.value

    # Las: dominacja zielonego
    if g > r and g > b:
        if g > 100:  # Jasniejszy zielony -> mlody las
            return StanKomorki.LAS.value
        else:  # Ciemniejszy zielony -> gesty las
            return StanKomorki.LAS_GESTY.value

    # Pozostale -> ziemia
    return StanKomorki.PUSTY.value

def wybierz_mape():
    pygame.init()
    ekran = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Wybor Mapy - Symulacja Pozaru Lasu")
    czcionka_tytul = pygame.font.Font(None, 48)
    czcionka_przycisk = pygame.font.Font(None, 32)

    # Dostepne mapy
    mapy = ["forest1.png", "forest2.png", "forest3.png", "forest4.png", "losowa"]

    # Przyciski
    przyciski = []
    for i, mapa in enumerate(mapy):
        y_pozycja = 80 + i * 60
        nazwa_wyswietlana = f"Mapa {i + 1}" if mapa != "losowa" else "Losowa Mapa"
        przyciski.append({
            "rect": pygame.Rect(150, y_pozycja, 300, 50),
            "text": nazwa_wyswietlana,
            "value": mapa
        })

    wybrana_mapa = None
    dziala = True

    while dziala:
        for zdarzenie in pygame.event.get():
            if zdarzenie.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif zdarzenie.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                for przycisk in przyciski:
                    if przycisk["rect"].collidepoint(x, y):
                        wybrana_mapa = przycisk["value"]
                        dziala = False

        # Renderowanie
        ekran.fill((220, 220, 220))

        # Tytul
        tytul = czcionka_tytul.render("Wybierz Mape", True, (0, 0, 0))
        tytul_rect = tytul.get_rect(center=(300, 40))
        ekran.blit(tytul, tytul_rect)

        # Przyciski
        for przycisk in przyciski:
            pygame.draw.rect(ekran, (255, 255, 255), przycisk["rect"])
            pygame.draw.rect(ekran, (0, 0, 0), przycisk["rect"], 2)
            tekst = czcionka_przycisk.render(przycisk["text"], True, (0, 0, 0))
            tekst_rect = tekst.get_rect(center=przycisk["rect"].center)
            ekran.blit(tekst, tekst_rect)

        pygame.display.flip()

    return wybrana_mapa

def generuj_losowa_wysokosc(wiersze: int, kolumny: int) -> numpy.ndarray:
    # Prosta losowa wysokosc z wygladzeniem
    wysokosc = numpy.random.rand(wiersze, kolumny)

    # Wygladzenie (usrednienie z sasiadami)
    for _ in range(3):
        nowa_wysokosc = wysokosc.copy()
        for w in range(1, wiersze - 1):
            for k in range(1, kolumny - 1):
                nowa_wysokosc[w, k] = (
                    wysokosc[w - 1:w + 2, k - 1:k + 2].mean()
                )
        wysokosc = nowa_wysokosc

    return wysokosc

def main():
    # Ustawienia
    wiersze = 70
    kolumny = 120
    rozmiar_komorki = 10

    # Wybor mapy z dostepnych w menu
    wybrana_mapa = wybierz_mape()

    # Utworzenie automatu komorkowego
    automat = AutomatKomorkowy(wiersze, kolumny)

    if wybrana_mapa == "losowa":
        # Generowanie losowej mapy
        pula_stanow = [StanKomorki.LAS.value, StanKomorki.LAS_GESTY.value]
        automat.inicjalizuj_z_mapy(numpy.random.choice(pula_stanow, size=(wiersze, kolumny)))
    else:
        # Wczytanie mapy z obrazu
        sciezka_mapy = SCIEZKA_WEJSCIOWA + wybrana_mapa
        try:
            siatka = wczytaj_mape_z_obrazu(sciezka_mapy, wiersze, kolumny)
            automat.inicjalizuj_z_mapy(siatka)
        except FileNotFoundError:
            print(f"Nie znaleziono pliku: {sciezka_mapy}")
            print("Uzywam losowej mapy")
            pula_stanow = [StanKomorki.LAS.value, StanKomorki.LAS_GESTY.value]
            automat.inicjalizuj_z_mapy(numpy.random.choice(pula_stanow, size=(wiersze, kolumny)))

    # Generowanie wysokosci terenu (wplywa na rozprzestrzenianie ognia)
    wysokosc_terenu = generuj_losowa_wysokosc(wiersze, kolumny)
    automat.ustaw_wysokosc_terenu(wysokosc_terenu)

    # Utworzenie wizualizacji
    wizualizacja = Wizualizacja(automat, rozmiar_komorki)

    wizualizacja.uruchom()

if __name__ == "__main__":
    main()