# Rejestr zmian

Wszystkie istotne zmiany w aplikacji **Strzelnica „Mnożenie” (mkTabliczka)** są opisywane w tym pliku.

---

## [1.5.0.0] – 2026-11-02

Pierwsze wydanie opublikowane na GitHubie.

### Dodano

- Błędne odpowiedzi na kulkach przypominają typowe pomyłki uczniów (sąsiednie iloczyny, wyniki różniące się o 1 lub 10) zamiast przypadkowych liczb.
- Zatwierdzanie imienia w tabeli rekordów klawiszem Enter z klawiatury numerycznej.
- Krótka blokada kliknięć na ekranie końca gry, chroniąca przed przypadkowym przeklikaniem.
- Instalator instaluje grę w 64-bitowym folderze Program Files i wyświetla jej ikonę w „Aplikacje i funkcje”.

### Zmieniono

- Imię w tabeli rekordów może mieć do 10 znaków (wcześniej 4).
- Komunikat o awansie podaje numer nowego poziomu.
- Gra jest dystrybuowana jako folder z programem zamiast pojedynczego pliku `.exe`, dzięki czemu uruchamia się szybciej.
- Instalator przy aktualizacji zamyka uruchomioną grę i usuwa nieaktualne pliki poprzedniej wersji.
- Poprawiona wydajność rysowania na słabszych komputerach.

### Naprawiono

- Pociski wystrzelone poziomo mogły krążyć po ekranie bez końca i niespodziewanie trafiać spadające kulki, odbierając życie. Pociski odbijają się teraz maksymalnie 5 razy, a strzały poziome i w dół są blokowane.
- Brak dźwięków po spakowaniu gry do `.exe` lub uruchomieniu jej z innego folderu.
- Licznik poziomu zatrzymywał się na 3, mimo że gra przechodziła na poziom 4.
- Wyjście z gry (ESC) podczas wpisywania imienia powodowało utratę rekordu.
- Kółko myszy na ekranie startowym przypadkowo rozpoczynało grę.