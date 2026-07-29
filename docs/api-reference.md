# Rejestr.io API — dokumentacja referencyjna

> Źródło: [rejestr.io/api](https://rejestr.io/api) i podstrony `rejestr.io/api/info/*` (stan na 2026-07-28).

Rejestr.io API to REST API dające programistyczny dostęp do danych z Krajowego Rejestru Sądowego (KRS), Centralnego Rejestru Beneficjentów Rzeczywistych (CRBR) oraz sprawozdań finansowych podmiotów. Umożliwia m.in.:

- wyszukiwanie organizacji wg zadanych kryteriów,
- pobieranie szczegółowych, ustrukturyzowanych danych o organizacjach i osobach,
- nawigację po sieci powiązań między organizacjami i osobami w KRS,
- pobieranie sprawozdań finansowych w formacie JSON lub PDF,
- pobieranie odpisów KRS (PDF).

## Spis treści

- [Podstawy](#podstawy)
- [Autoryzacja](#autoryzacja)
- [Limity zapytań](#limity-zapytań)
- [Cennik](#cennik)
- [Jak zacząć](#jak-zacząć)
- [Konwencje](#konwencje)
- [Endpointy](#endpointy)
  1. [Wyszukiwanie organizacji](#1-wyszukiwanie-organizacji)
  2. [Podstawowe dane organizacji](#2-podstawowe-dane-organizacji)
  3. [Zaawansowane dane organizacji (rozdziały KRS)](#3-zaawansowane-dane-organizacji-rozdziały-krs)
  4. [Dane osoby](#4-dane-osoby)
  5. [Beneficjenci rzeczywiści](#5-beneficjenci-rzeczywiści)
  6. [Powiązania organizacji](#6-powiązania-organizacji)
  7. [Powiązania osoby](#7-powiązania-osoby)
  8. [Odpis z KRS organizacji](#8-odpis-z-krs-organizacji)
  9. [Lista wpisów do KRS dla organizacji](#9-lista-wpisów-do-krs-dla-organizacji)
  10. [Lista dokumentów finansowych organizacji](#10-lista-dokumentów-finansowych-organizacji)
  11. [Dokument finansowy organizacji](#11-dokument-finansowy-organizacji)
  12. [Stan konta API](#12-stan-konta-api)
- [Wspólne struktury danych](#wspólne-struktury-danych)
- [Plany abonamentowe — wymagania wg endpointu](#plany-abonamentowe--wymagania-wg-endpointu)

---

## Podstawy

- **Adres bazowy:** `https://rejestr.io/api/v2/`
- **Protokół:** REST API po HTTP(S), format odpowiedzi JSON (poza endpointami zwracającymi pliki PDF).
- Żądania i odpowiedzi można wysyłać dowolnym oprogramowaniem obsługującym HTTP, np. [curl](https://curl.se).

## Autoryzacja

Wszystkie żądania muszą być podpisane ważnym kluczem API przekazanym w nagłówku HTTP `Authorization`.

```bash
curl -H "Authorization: <TWÓJ_KLUCZ_API>" \
  "https://rejestr.io/api/v2/org/12345"
```

## Limity zapytań

API pozwala na wykonywanie **1000 zapytań na minutę**.

## Cennik

| Pakiet | Liczba żądań | Koszt |
|---|---|---|
| Standard | 10 000 | 500 zł |

- Wyjątek: żądanie **Dokument finansowy organizacji** ma cenę jednostkową **0,5 zł** za żądanie (zamiast korzystania z puli pakietu) — patrz też uwaga o wyższym koszcie formatu JSON w opisie tego endpointu.
- Opłaty są dokonywane z góry (przedpłata). Wystawiane są faktury VAT.
- Obsługiwane formy płatności: karty VISA, Mastercard.

## Jak zacząć

1. Załóż konto na [rejestr.io](https://rejestr.io/register) (lub [zaloguj się](https://rejestr.io/login), jeśli już je masz).
2. Przejdź do [strony zarządzania kontem](https://rejestr.io/konto).
3. W sekcji **API** kliknij **Włącz API** i zaakceptuj [regulamin usługi](https://rejestr.io/regulamin/api).
4. W sekcji **Kredyty** kliknij **Dodaj środki** i wybierz kwotę doładowania.
5. Przejdź do [strony zarządzania kluczami API](https://rejestr.io/konto/api) i kliknij **Wygeneruj nowy klucz**.

## Konwencje

**Identyfikator organizacji (`id`)** — w większości endpointów parametr `id` przyjmuje jedną z dwóch postaci (wzorzec: `^([0-9]{1,10})|(nip[0-9]{10})$`):
- numer KRS, np. `12345` lub `0000012345`,
- numer NIP poprzedzony słowem `nip`, np. `nip1234567890`.

Jeśli znasz numer KRS organizacji, nie musisz jej wyszukiwać — możesz od razu pobrać jej podstawowe dane.

**Identyfikator osoby (`id`)** — liczba całkowita (`integer int64`).

**Daty** — w formacie `RRRR-MM-DD`.

**Struktura pól "prosta" i "grupowa"** (dotyczy odpowiedzi endpointu *Zaawansowane dane organizacji*) — pola zwracane w rozdziałach KRS mogą mieć jedną z dwóch postaci:

*Pole w formie prostej* — zawiera aktualną wartość oraz informację od kiedy obowiązuje:

```json
"nazwa_krotka": {
    "_wartosc": "EXAMPLEX POLSKA",
    "_zakres": {
        "wpis_wprowadzajacy_numer": 7,
        "wpis_wprowadzajacy_data": "2010-02-03"
    }
}
```

*Pole w formie grupowej* — zawiera podobiekty (`_podobiekty`), z których każdy ma numer porządkowy i może być prosty lub grupowy; `_wartosc` wskazuje, które podobiekty są aktualne:

```json
"przedmiot_pozostalej_dzialalnosci_przedsiebiorcy": {
    "_podobiekty": {
        "3": { "_wartosc": { "symbol": ["46", null, null], "opis": "Handel hurtowy..." },
               "_zakres": { "wpis_wprowadzajacy_numer": 1, "wpis_wprowadzajacy_data": "2011-03-04" } },
        "6": { "_wartosc": { "symbol": ["46", "90", "Z"], "opis": "Sprzedaż hurtowa niewyspecjalizowana" },
               "_zakres": { "wpis_wprowadzajacy_numer": 5, "wpis_wprowadzajacy_data": "2012-04-05" } }
    },
    "_wartosc": {
        "podobiekty": [3, 6, 7],
        "podobiekty_liczba_aktualnych": 3,
        "podobiekty_liczba_wszystkich": 7
    },
    "_zakres": { "wpis_wprowadzajacy_numer": 5, "wpis_wprowadzajacy_data": "2012-04-05" }
}
```

---

## Endpointy

### 1. Wyszukiwanie organizacji

Zwraca listę organizacji na podstawie zadanych kryteriów.

```
GET https://rejestr.io/api/v2/org
```

> Jeśli znasz numer KRS organizacji, nie musisz jej wyszukiwać — użyj od razu [Podstawowych danych organizacji](#2-podstawowe-dane-organizacji).

**Parametry GET (kryteria wyszukiwania):**

| Parametr | Typ | Opis |
|---|---|---|
| `nazwa` | string | Fragment nazwy organizacji |
| `nip` | string | Pełen numer NIP, bez myślników |
| `regon` | string | Pełen numer REGON |
| `forma_prawna` | string | Pełna forma prawna, pisana wielkimi literami |
| `wpis_pierwszy_data` | string | Data pierwszego wpisu do KRS |
| `wpis_najnowszy_data` | string | Data najnowszego wpisu do KRS |
| `przewazajacy_pkd` | string | Kod PKD przeważającej działalności |
| `pozostaly_pkd` | string | Kod PKD pozostałej działalności |
| `dowolny_pkd` | string | Kod PKD przeważającej lub pozostałej działalności |
| `czy_pozytku_publicznego` | boolean | Czy organizacja ma status OPP |
| `czy_wykreslona` | boolean | Czy organizacja jest wykreślona z KRS |
| `czy_w_likwidacji` | boolean | Czy organizacja jest w likwidacji |
| `czy_w_upadlosci` | boolean | Czy organizacja jest w upadłości |
| `czy_w_zawieszeniu` | boolean | Czy organizacja jest w zawieszeniu |
| `kapital` | string | Wysokość kapitału zakładowego |
| `wielkosc` | string | `duza_srednia`, `mala`, `mikro`, `ngo` — wg klasyfikacji z ustawy o rachunkowości |
| `typ_adresu` | string | `dowolny` (domyślnie), `organizacja`, `oddzial` — czy ograniczyć kryteria adresowe tylko do adresu organizacji lub oddziału |
| `panstwo` | string | Państwo w adresie organizacji/oddziału |
| `miejscowosc` | string | Miejscowość w adresie organizacji/oddziału |
| `kod_pocztowy` | string | Kod pocztowy w adresie organizacji/oddziału |
| `ulica` | string | Ulica w adresie organizacji/oddziału |
| `nr_domu` | string | Numer domu w adresie organizacji/oddziału |
| `terc_wojewodztwo` | string | Dwucyfrowy kod TERC województwa |
| `terc_powiat` | string | Czterocyfrowy kod TERC powiatu |
| `terc_gmina` | string | Sześciocyfrowy kod TERC gminy |

**Sortowanie:**

| Parametr | Typ | Opis |
|---|---|---|
| `sortowanie` | string | Określa porządek sortowania wyników |

Reguła sortowania (gdy `sortowanie` nie jest podane): jeśli używany jest parametr `nazwa` — wg dopasowania tekstu do nazwy, modyfikowane kapitałem zakładowym (większy kapitał = wyższy wynik); w przeciwnym razie — po numerze KRS malejąco.

**Stronicowanie:**

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `strona` | integer (int64) | `1` | Numer strony wyników |
| `ile_na_strone` | integer (int64) | `10` | Liczba wyników na stronę |

**Odpowiedź:**

| Pole | Typ | Opis |
|---|---|---|
| `liczba_wszystkich_wynikow` | integer | Łączna liczba znalezionych organizacji |
| `wyniki` | array\<[obiekt organizacji](#obiekt-organizacji)\> | Lista organizacji na bieżącej stronie |

---

### 2. Podstawowe dane organizacji

Zwraca podstawowe dane organizacji dla podanego `id` (numer KRS lub NIP).

```
GET https://rejestr.io/api/v2/org/{id}
```

**Parametry GET:**

| Parametr | Typ | Opis |
|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | KRS (np. `12345`, `0000012345`) lub NIP poprzedzony `nip` (np. `nip1234567890`) |

**Odpowiedź:** [obiekt organizacji](#obiekt-organizacji).

---

### 3. Zaawansowane dane organizacji (rozdziały KRS)

Zwraca dane z podanego rozdziału KRS dla organizacji o podanym `id`.

```
GET https://rejestr.io/api/v2/org/{id}/krs-rozdzialy/{rozdzial}
```

> Rozdziały `oddzialy`, `zobowiazania` i `przeksztalcenia` wymagają planu **Rejestr.io Premium** lub wyższego.

**Parametry GET:**

| Parametr | Typ | Opis |
|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | KRS lub NIP organizacji |
| `rozdzial` | string `^(ogolny\|oddzialy\|akcje\|wzmianki\|zobowiazania\|przeksztalcenia)$` | Jeden z sześciu rozdziałów KRS |
| `nr_wpisu` | integer (int64) | Numer wpisu do KRS, wg którego zwracane są dane rozdziału (stan historyczny) |

**Rozdziały:**

| Rozdział | Zawartość (skrót) |
|---|---|
| `ogolny` | Dane ogólne: nazwa, adres, siedziba, NIP/REGON, forma prawna, kapitał, organ reprezentacji, prokurenci, pełnomocnicy, wspólnicy/akcjonariusze, przedmiot działalności (PKD), status OPP, dane likwidacji/upadłości i in. — bardzo obszerny zestaw pól |
| `oddzialy` | Oddziały organizacji *(Premium+)* |
| `akcje` | Dane o akcjach/udziałach |
| `wzmianki` | Wzmianki w KRS |
| `zobowiazania` | Zobowiązania *(Premium+)* |
| `przeksztalcenia` | Przekształcenia, połączenia, podziały *(Premium+)* |

Ze względu na dużą liczbę pól technicznych (setki kluczy zagnieżdżonych, np. `dane_wspolnikow.*`, `organ_reprezentacji.*`, `pelnomocnicy.*`), pełny słownik pól dla każdego rozdziału najlepiej sprawdzić bezpośrednio na stronie [rejestr.io/api/info/zaawansowane-dane-organizacji](https://rejestr.io/api/info/zaawansowane-dane-organizacji). Każde pole zwracane jest w [formie prostej lub grupowej](#konwencje) opisanej wyżej.

**Odpowiedź:** obiekt, którego klucze odpowiadają polom dostępnym dla wybranego rozdziału (patrz [Konwencje](#konwencje) — struktura pól prosta/grupowa).

---

### 4. Dane osoby

Zwraca aktualne dane o osobie występującej w KRS.

```
GET https://rejestr.io/api/v2/osoby/{id}
```

**Parametry GET:**

| Parametr | Typ | Opis |
|---|---|---|
| `id` | integer (int64) | Id osoby |

**Odpowiedź:** [obiekt osoby](#obiekt-osoby).

---

### 5. Beneficjenci rzeczywiści

Zwraca listę osób będących beneficjentami rzeczywistymi dla organizacji. Dane pochodzą z Centralnego Rejestru Beneficjentów Rzeczywistych (CRBR), nie z KRS.

```
GET https://rejestr.io/api/v2/org/{id}/crbr
```

> Wymaga planu **Rejestr.io Premium** lub wyższego.

**Parametry GET:**

| Parametr | Typ | Opis |
|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | KRS lub NIP organizacji |

**Odpowiedź:** lista obiektów:

| Pole | Typ | Opis |
|---|---|---|
| `id` | integer | Id osoby w systemie Rejestr.io (brak dla osób bez nr PESEL) |
| `kod_kraju_rezydencji` | string | Kod ISO 3166 kraju rezydencji |
| `kody_krajow_obywatelstwa` | array | Lista kodów ISO 3166 krajów obywatelstwa |
| `tozsamosc` | object | Dane o osobie |
| `typ` | string | `osoba` lub `osoba-bez-pesel` |

---

### 6. Powiązania organizacji

Zwraca aktualne i/lub historyczne powiązania organizacji z innymi organizacjami lub osobami w KRS.

```
GET https://rejestr.io/api/v2/org/{id}/krs-powiazania
```

**Parametry GET:**

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | — | KRS lub NIP organizacji |
| `aktualnosc` | string: `aktualne`, `historyczne` | `aktualne` | Rodzaj zwracanych powiązań |

**Odpowiedź:** lista elementów, każdy jako [obiekt organizacji](#obiekt-organizacji), [obiekt osoby](#obiekt-osoby) lub obiekt "osoba nieposiadająca profilu" (`typ: osoba-bez-pesel`), z dodatkowym polem:

| Pole | Typ | Opis |
|---|---|---|
| `krs_powiazania_kwerendowane` | array | Lista powiązań do organizacji/osoby kwerendowanej — patrz niżej |

Każdy element `krs_powiazania_kwerendowane` zawiera:

| Pole | Typ | Opis |
|---|---|---|
| `data_start` | string | Data początku powiązania (`RRRR-MM-DD`) |
| `data_koniec` | string \| null | Data końca powiązania, `null` jeśli powiązanie trwa nadal |
| `kierunek` | string: `AKTYWNY`, `PASYWNY` | Patrz wyjaśnienie niżej |
| `opis` | string | Szczegółowy opis typu powiązania |
| `typ` | string | Typ powiązania, np. `KRS_SHAREHOLDER`, `KRS_BOARD` |

**Znaczenie `kierunek`:** jeśli odpytujemy o powiązania organizacji A i w wyniku otrzymujemy organizację B z typem powiązania "jedyny udziałowiec":
- `AKTYWNY` — obiekt B pełni rolę wskazaną w `typ` wobec obiektu kwerendowanego (B jest jedynym udziałowcem A, czyli B posiada A);
- `PASYWNY` — obiekt kwerendowany pełni tę rolę wobec obiektu B (B jest posiadane przez A).

Kierunek jest zawsze określony z punktu widzenia obiektu na liście wyników, a nie obiektu kwerendowanego.

---

### 7. Powiązania osoby

Zwraca aktualne i/lub historyczne powiązania osoby z organizacjami wpisanymi do KRS.

```
GET https://rejestr.io/api/v2/osoby/{id}/krs-powiazania
```

**Parametry GET:**

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `id` | integer (int64) | — | Id osoby |
| `aktualnosc` | string: `aktualne`, `historyczne` | `aktualne` | Rodzaj zwracanych powiązań |

**Odpowiedź:** lista [obiektów organizacji](#obiekt-organizacji), każdy z dodatkowym polem `krs_powiazania_kwerendowane` — struktura identyczna jak w [Powiązaniach organizacji](#6-powiązania-organizacji).

---

### 8. Odpis z KRS organizacji

Zwraca plik PDF z aktualnym lub pełnym odpisem KRS organizacji o danym `id`.

```
GET https://rejestr.io/api/v2/org/{id}/krs-odpisy
```

**Uwagi:**
- Odpis **aktualny** wymaga planu **Rejestr.io Premium** lub wyższego; odpis **pełny** wymaga planu **Rejestr.io Biznes**.
- Plik odpisu pochodzi z jednego z ostatnich 30 dni kalendarzowych — bardzo świeże zmiany w KRS mogą jeszcze nie być uwzględnione.
- Odpowiedź może być w formacie **PDF** (plik odpisu) lub **JSON** (w przypadku błędu).
- Organizacje wykreślone nie mają odpisu aktualnego — zapytanie o niego zwróci **404 Not Found**; odpis pełny jest dla nich nadal dostępny.

**Parametry GET:**

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | — | KRS lub NIP organizacji |
| `typ` | string: `aktualny`, `pelny` | `aktualny` | Typ pobieranego odpisu |

**Odpowiedź:** plik PDF z odpisem KRS.

---

### 9. Lista wpisów do KRS dla organizacji

Zwraca listę informacji o wpisach do KRS dla danej organizacji.

```
GET https://rejestr.io/api/v2/org/{id}/krs-wpisy
```

**Parametry GET:**

| Parametr | Typ | Opis |
|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | KRS lub NIP organizacji |

**Odpowiedź:** tablica obiektów:

| Pole | Typ | Opis |
|---|---|---|
| `numer` | integer | Numer porządkowy wpisu (sekwencja 1, 2, 3, ...) |
| `sygnatura` | string | Sygnatura wpisu |
| `data` | string | Data dokonania wpisu (`RRRR-MM-DD`) |
| `data_obowiazywania_ostatnia` | string \| null | Ostatnia data obowiązywania stanu z wpisu (zwykle dzień przed kolejnym wpisem); `null` jeśli wpis wciąż aktualny |
| `sad` | string | Sąd, w którym dokonano wpisu |

---

### 10. Lista dokumentów finansowych organizacji

Pobiera listę dokumentów finansowych w KRS dla organizacji.

```
GET https://rejestr.io/api/v2/org/{id}/krs-dokumenty
```

> Wymaga planu **Rejestr.io Premium** lub wyższego.

**Parametry GET:**

| Parametr | Typ | Opis |
|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | KRS lub NIP organizacji |

**Odpowiedź:** tablica obiektów (grupy dokumentów wg okresu rozliczeniowego):

| Pole | Typ | Opis |
|---|---|---|
| `data_start` | string | Data początkowa okresu rozliczeniowego |
| `data_koniec` | string | Data końcowa okresu rozliczeniowego (włącznie) |
| `dokumenty` | array | Lista dokumentów w danym zbiorze |

Każdy element `dokumenty` zawiera:

| Pole | Typ | Opis |
|---|---|---|
| `id` | integer | Id dokumentu, do użycia w zapytaniu [Dokument finansowy organizacji](#11-dokument-finansowy-organizacji) |
| `nazwa` | string | Nazwa dokumentu, np. "bilans", "rachunek zysków i strat" |
| `czy_ma_json` | boolean | Czy dokument dostępny jest też w formacie JSON (PDF jest zawsze dostępny) |

---

### 11. Dokument finansowy organizacji

Pobiera dokument finansowy w KRS dla organizacji.

```
GET https://rejestr.io/api/v2/org/{id}/krs-dokumenty/{doc_id}
```

**Uwagi:**
- Dokumenty **PDF** wymagają planu **Rejestr.io Premium** lub wyższego; dokumenty **JSON** wymagają planu **Rejestr.io Biznes**.
- Pobieranie w formacie JSON ma wyższy koszt niż podstawowa cena żądania API (patrz [Cennik](#cennik)).

**Parametry GET:**

| Parametr | Typ | Domyślnie | Opis |
|---|---|---|---|
| `id` | string `^([0-9]{1,10})\|(nip[0-9]{10})$` | — | KRS lub NIP organizacji |
| `doc_id` | integer (int64) | — | Id dokumentu (z listy dokumentów finansowych) |
| `format` | string: `json`, `pdf` | `pdf` | Format zwracanego dokumentu |

**Odpowiedź (`format=pdf`):** plik PDF z dokumentem finansowym.

**Odpowiedź (`format=json`):**

| Pole | Typ | Opis |
|---|---|---|
| `id_organizacji` | integer | Id organizacji (KRS bez zer wiodących) |
| `id_dokumentu` | integer | Id dokumentu |
| `nazwa` | string | Nazwa dokumentu |
| `okres_data_start` | string | Data początkowa okresu rozliczeniowego |
| `okres_data_koniec` | string | Data końcowa okresu rozliczeniowego (włącznie) |
| `zawartosc` | object | Drzewiasta struktura JSON dokumentu (przetworzona ze źródłowego XML wg schemy Ministerstwa Finansów) |

Każdy węzeł w `zawartosc` (rekurencyjnie, przez `podobiekty`) zawiera:

| Pole | Typ | Opis |
|---|---|---|
| `nazwa_wezla` | string | Techniczna nazwa węzła w źródłowym XML (węzeł najwyższego poziomu wskazuje typ schemy — patrz [struktury e-sprawozdań MF](https://www.gov.pl/web/kas/struktury-e-sprawozdan)) |
| `etykieta` | string | Opis węzła wg schemy XML Ministerstwa Finansów |
| `podetykieta` | string | Opis węzła wg opisu podanego przez składającą organizację (zwykle dot. pól "uszczegóławiających") |
| `pln_rok_obrotowy_biezacy` | number | Wartość pozycji w PLN za okres opisywany dokumentem |
| `pln_rok_obrotowy_poprzedni` | number | Wartość pozycji w PLN za okres poprzedni |
| `podobiekty` | array | Lista podwęzłów o identycznej strukturze |

---

### 12. Stan konta API

Zwraca aktualny stan konta API w PLN, z dokładnością czasową do paru minut.

```
GET https://rejestr.io/api/v2/konto/stan
```

> Operacja darmowa — nie zmniejsza stanu konta.

**Odpowiedź:** liczba wyrażająca stan konta API w PLN.

---

## Wspólne struktury danych

### Obiekt organizacji

Zwracany m.in. przez wyszukiwanie, podstawowe dane organizacji oraz powiązania.

| Pole | Typ | Opis |
|---|---|---|
| `id` | integer | Id organizacji — nr KRS bez początkowych zer |
| `nazwy` | object | Warianty nazwy organizacji |
| `numery` | object | Numery rejestrowe organizacji (KRS, NIP, REGON) |
| `stan` | object | Kluczowe dane o stanie organizacji |
| `glowna_osoba` | object | Osoba stojąca na czele organizacji (prezes zarządu, przewodniczący itp.) |
| `adres` | object | Główny adres organizacji wg KRS |
| `kontakt` | object | Dane kontaktowe (z KRS i spoza KRS) — **wymaga planu Rejestr.io Biznes** |
| `ostatnie_sprawozdanie` | object | Dane z ostatniego sprawozdania finansowego (przychody, koszty, zysk, aktywa/pasywa) — **wymaga planu Rejestr.io Biznes** |
| `krs_rejestry` | object | Wpisanie/wykreślenie z rejestrów przedsiębiorców i stowarzyszeń |
| `krs_wpisy` | object | Informacje o kluczowych wpisach do KRS |
| `krs_powiazania_liczby` | object | Liczby powiązań organizacji z innymi organizacjami/osobami w KRS |
| `metadane` | object | Dane o wewnętrznym stanie organizacji w systemie Rejestr.io |
| `typ` | string | Zawsze `organizacja` |

### Obiekt osoby

Zwracany m.in. przez dane osoby oraz powiązania osoby (jako uczestnik powiązań organizacji).

| Pole | Typ | Opis |
|---|---|---|
| `id` | integer | Id osoby |
| `tozsamosc` | object | Dane o osobie |
| `krs_powiazania_liczby` | object | Liczby powiązań osoby z organizacjami w KRS |
| `typ` | string | `osoba` (lub `osoba-bez-pesel` w kontekście beneficjentów/powiązań, dla osób bez profilu) |

---

## Plany abonamentowe — wymagania wg endpointu

| Funkcja / pole | Wymagany plan |
|---|---|
| Pole `kontakt` i `ostatnie_sprawozdanie` w obiekcie organizacji | Rejestr.io Biznes |
| Rozdziały KRS: `oddzialy`, `zobowiazania`, `przeksztalcenia` | Rejestr.io Premium+ |
| Beneficjenci rzeczywiści (CRBR) | Rejestr.io Premium+ |
| Odpis z KRS — typ `aktualny` | Rejestr.io Premium+ |
| Odpis z KRS — typ `pelny` | Rejestr.io Biznes |
| Lista dokumentów finansowych organizacji | Rejestr.io Premium+ |
| Dokument finansowy — format `pdf` | Rejestr.io Premium+ |
| Dokument finansowy — format `json` | Rejestr.io Biznes |
| Stan konta API | brak wymagań (darmowe) |

---

## Dodatkowe zasoby

- [Regulamin Rejestr.io API](https://rejestr.io/regulamin/api)
- [Cennik](https://rejestr.io/cennik)
- [Strona zarządzania kontem](https://rejestr.io/konto)
- [Strona zarządzania kluczami API](https://rejestr.io/konto/api)
- [Struktury e-sprawozdań finansowych (Ministerstwo Finansów)](https://www.gov.pl/web/kas/struktury-e-sprawozdan)
