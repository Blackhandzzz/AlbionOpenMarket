import os
import sys
import requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import io

from items import mapa_przedmiotow
from factions import mapa_frakcji

# --- Funkcja zamieniająca dużą liczbę na krótką formę ---
def skroc_cene(liczba):
    if liczba >= 1_000_000:
        return f"{liczba/1_000_000:.1f}M"
    elif liczba >= 1_000:
        return f"{liczba/1_000:.0f}k"
    else:
        return str(liczba)

# --- Funkcja zamieniająca nazwę i tier/enchant na ID ---
def przetworz_nazwe(tekst):
    try:
        parts = tekst.strip().lower().split()
        if len(parts) < 2:
            return None

        enchant_info = parts[-1]
        nazwa_przedmiotu = " ".join(parts[:-1])

        if nazwa_przedmiotu not in mapa_przedmiotow:
            return None

        id_przedmiotu = mapa_przedmiotow[nazwa_przedmiotu]

        tier, enchant = enchant_info.split(".")
        tier = int(tier)
        enchant = int(enchant)

        item_id = f"T{tier}_{id_przedmiotu}"
        if enchant > 0:
            item_id += f"@{enchant}"

        return item_id
    except Exception as e:
        print(e)
        return None

# --- Funkcja zwracająca poprawną ścieżkę do zasobów ---
def resource_path(relative_path):
    """ Funkcja zapewnia poprawne ścieżki zarówno w .py jak i .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- Cache obrazków frakcji ---
cache_frakcji = {}

# --- Funkcja sprawdzająca cenę i pobierająca obrazek ---
def sprawdz_cene():
    tekst = entry.get()

    item_id = przetworz_nazwe(tekst)
    if not item_id:
        messagebox.showwarning("Uwaga", "Niepoprawna nazwa lub format! Spróbuj np. dawonsong 4.0")
        return

    url = f"https://europe.albion-online-data.com/api/v2/stats/prices/{item_id}.json"
    ikona_url = f"https://render.albiononline.com/v1/item/{item_id}.png"

    try:
        # Pobieranie danych o cenie
        response = requests.get(url)
        data = response.json()

        # Pobieranie obrazka przedmiotu
        img_response = requests.get(ikona_url)
        img_data = img_response.content
        img = Image.open(io.BytesIO(img_data))
        img = img.resize((100, 100))
        img_tk = ImageTk.PhotoImage(img)

        obrazek_label.configure(image=img_tk)
        obrazek_label.image = img_tk  # musimy zapisać referencję

        # Czyścimy stare wyniki
        for widget in frame_wynik.winfo_children():
            widget.destroy()

        if data:
            miasta = {}

            for entry_data in data:
                city = entry_data['city']
                sell_price = entry_data.get('sell_price_min', 0)
                buy_price = entry_data.get('buy_price_max', 0)

                if city not in miasta:
                    miasta[city] = {"sell": sell_price, "buy": buy_price}
                else:
                    if sell_price > 0:
                        if miasta[city]["sell"] == 0 or sell_price < miasta[city]["sell"]:
                            miasta[city]["sell"] = sell_price
                    if buy_price > 0:
                        if miasta[city]["buy"] == 0 or buy_price > miasta[city]["buy"]:
                            miasta[city]["buy"] = buy_price

            if miasta:
                miasta_posortowane = sorted(miasta.items(), key=lambda x: (x[1]['sell'] if x[1]['sell'] > 0 else float('inf')))

                for city, prices in miasta_posortowane:
                    sell = prices["sell"]
                    buy = prices["buy"]
                    sell_price_s = skroc_cene(sell) if sell else "Brak"
                    buy_price_s = skroc_cene(buy) if buy else "Brak"

                    frame_miasto = tk.Frame(frame_wynik, bg="#393e46")
                    frame_miasto.pack(pady=5, fill="x", padx=10)

                    # Ikona frakcji
                    if city in mapa_frakcji:
                        if city not in cache_frakcji:
                            try:
                                sciezka_wzgledna = mapa_frakcji[city]
                                sciezka_bezpieczna = resource_path(sciezka_wzgledna)
                                frakcja_img = Image.open(sciezka_bezpieczna)
                                frakcja_img = frakcja_img.resize((30, 30))
                                frakcja_img_tk = ImageTk.PhotoImage(frakcja_img)
                                cache_frakcji[city] = frakcja_img_tk
                            except Exception as e:
                                print(f"Błąd ładowania frakcji dla {city}: {e}")
                                cache_frakcji[city] = None

                        if cache_frakcji[city]:
                            ikona = tk.Label(frame_miasto, image=cache_frakcji[city], bg="#393e46")
                            ikona.pack(side="left", padx=(0, 5))

                    # Tekst miasta + ceny
                    tekst_label = tk.Label(frame_miasto,
                        text=f"{city}:\n  Cena sprzedaży: {sell_price_s}\n  Cena kupna: {buy_price_s}",
                        bg="#393e46", fg="#eeeeee", font=("Helvetica", 11), justify="left", anchor="w")
                    tekst_label.pack(side="left", fill="both")
            else:
                wynik.set("Brak aktywnych ofert na rynku dla tego przedmiotu.")
        else:
            wynik.set("Brak danych dla tego przedmiotu.")

    except Exception as e:
        messagebox.showerror("Błąd", f"Coś poszło nie tak:\n{e}")

# --- GUI ---
okno = tk.Tk()
okno.title("Albion Online - Sprawdzanie cen")
okno.geometry("500x850")
okno.configure(bg="#222831")

label = tk.Label(okno, text="Wpisz: nazwa tier.enchant (np. dawnsong 6.3)", bg="#222831", fg="#eeeeee", font=("Helvetica", 12))
label.pack(pady=10)

entry = tk.Entry(okno, font=("Helvetica", 12))
entry.pack(pady=5)

button = tk.Button(okno, text="Sprawdź cenę", command=sprawdz_cene, bg="#00adb5", fg="white", font=("Helvetica", 12))
button.pack(pady=10)

# --- Obrazek przedmiotu ---
obrazek_label = tk.Label(okno, bg="#222831")
obrazek_label.pack(pady=(20, 20))

# --- Frame na wyniki cen ---
frame_wynik = tk.Frame(okno, bg="#222831")
frame_wynik.pack(pady=(10, 20), fill="both", expand=True)

# --- Zmienna na wyniki fallback ---
wynik = tk.StringVar()

okno.mainloop()
