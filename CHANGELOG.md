# Rejestr zmian

Wszystkie istotne zmiany w aplikacji **mkTabliczka** są opisywane w tym pliku.

Format oparty jest na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/).
Nowe wersje dopisuj na górze, pod sekcją „Nieopublikowane”.

---

## [Nieopublikowane]

### Dodano

### Zmieniono

### Naprawiono

---

## [1.7.0.0] – 2026-11-23

### Zmieniono

- Kulki spadają wolniej na wszystkich poziomach, a przyspieszanie na poziomie 4 jest łagodniejsze i ma górną granicę.
- Na poziomie 4 laser celowniczy nie jest wyświetlany — trzeba celować samodzielnie. Ekran awansu na poziom 4 informuje o tym gracza.
- Program nazywa się teraz „mkTabliczka” (wcześniej Strzelnica „Mnożenie”) — na ekranie gry i we właściwościach pliku.

---

## [1.6.0.0] – 2026-11-03

### Dodano

- Armatka na dole ekranu: obrotowa lufa podąża za myszką, a strzał wywołuje odrzut i błysk z wylotu.
- Celownik w miejscu kursora myszy. Gdy kursor jest poniżej zasięgu lufy, celownik staje się szary.

### Zmieniono

- Podczas gry kursor myszy jest ukryty; wraca w menu, przy wpisywaniu imienia i na ekranie końca gry.
- Działanie do rozwiązania jest wyświetlane na tablicy w podstawie armatki.
- Kliknięcie poniżej zasięgu lufy oddaje strzał pod najmniejszym możliwym kątem zamiast go blokować.

---

## [1.5.0.1] – 2026-11-02

### Zmieniono

- Tabela 10 najlepszych wyników jest wspólna dla wszystkich użytkowników komputera (`C:\ProgramData\mkTabliczka`) zamiast osobnej dla każdego konta Windows.
- Rekordy zapisane w poprzedniej wersji są automatycznie dołączane do wspólnej tabeli przy pierwszym uruchomieniu gry na danym koncie.
- Odinstalowanie gry usuwa wspólną tabelę rekordów.

### Naprawiono

- Przerwany zapis (np. wyłączenie komputera) nie może już uszkodzić pliku rekordów.
- Rekord zapisany przez innego użytkownika nie jest nadpisywany przy zapisie nowego wyniku.
- Brak uprawnień do zapisu rekordów nie przerywa gry.

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

---

[Nieopublikowane]: #
[1.7.0.0]: #
[1.6.0.0]: #
[1.5.0.1]: #
[1.5.0.0]: #
