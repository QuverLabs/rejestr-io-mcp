# rejestr-io-mcp

Serwer MCP (Model Context Protocol) udostępniający pełne API [rejestr.io](https://rejestr.io/api) — Krajowy Rejestr Sądowy (KRS), Centralny Rejestr Beneficjentów Rzeczywistych (CRBR) oraz sprawozdania finansowe — jako zestaw narzędzi (tools) wywoływalnych przez klientów MCP (np. Claude Desktop, Claude Code).

## Szybka instalacja (bez Pythona/uv)

Jeśli nie chcesz instalować Pythona ani `uv`, pobierz gotową paczkę dla swojego
systemu z zakładki [Releases](../../releases) tego repozytorium:

1. Pobierz `rejestr-io-mcp-windows.zip` (Windows) lub `rejestr-io-mcp-macos.zip`
   (macOS, procesory Apple Silicon/M1-M4).
2. Rozpakuj całe archiwum ZIP do jednego folderu.
3. Uruchom instalator: `Zainstaluj.bat` (Windows) lub `Zainstaluj.command`
   (macOS) — dwuklik.
4. Podaj swój klucz API rejestr.io, gdy zostaniesz o niego poproszony/a.
5. Uruchom ponownie Claude Desktop i/lub aplikację ChatGPT.

Instalator konfiguruje automatycznie zarówno Claude Desktop, jak i aplikację
ChatGPT (desktop) — nie trzeba ręcznie edytować żadnych plików konfiguracyjnych.
Szczegółowe instrukcje, w tym jak obejść ostrzeżenie systemu o niepodpisanym
programie, znajdują się w pliku `INSTRUKCJA.txt` dołączonym do paczki.

Ta ścieżka instalacji obsługuje obecnie Windows oraz macOS na Apple Silicon.
Na Linuksie lub starszych (Intel) Makach użyj instalacji przez `uv` opisanej
poniżej.

## Wymagania

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/)
- Klucz API rejestr.io — patrz [docs/api-reference.md](docs/api-reference.md#jak-zacząć)

## Instalacja

```bash
uv sync --extra dev
cp .env.example .env
# uzupełnij REJESTR_IO_API_KEY w .env
```

## Uruchomienie

Transport stdio (domyślny, do integracji z Claude Desktop/Claude Code):

```bash
uv run rejestr-io-mcp
```

Transport HTTP (domyślnie nasłuch tylko na `127.0.0.1`):

```bash
uv run rejestr-io-mcp --transport http --port 8000
```

Aby udostępnić serwer w swojej sieci lokalnej, podaj adres nasłuchu i ustaw token uwierzytelniający — patrz [Zmienne środowiskowe](#zmienne-środowiskowe):

```bash
MCP_HTTP_AUTH_TOKEN="$(openssl rand -hex 32)" uv run rejestr-io-mcp --transport http --host 0.0.0.0 --port 8000
```

## Konfiguracja klienta MCP

Przykładowy wpis w `mcp.json`:

```json
{
  "mcpServers": {
    "rejestr-io": {
      "command": "uv",
      "args": ["run", "--directory", "/ścieżka/do/rejestr-io-mcp", "rejestr-io-mcp"],
      "env": {
        "REJESTR_IO_API_KEY": "twój-klucz-api"
      }
    }
  }
}
```

## Zmienne środowiskowe

| Zmienna | Wymagana | Domyślnie | Opis |
|---|---|---|---|
| `REJESTR_IO_API_KEY` | tak | — | Klucz API rejestr.io |
| `REJESTR_IO_BASE_URL` | nie | `https://rejestr.io/api/v2/` | Bazowy adres API |
| `REJESTR_IO_CACHE_TTL_SECONDS` | nie | `300` | TTL cache w pamięci (sekundy) |
| `REJESTR_IO_CACHE_MAX_SIZE` | nie | `512` | Maks. liczba wpisów w cache |
| `REJESTR_IO_DOWNLOAD_DIR` | nie | `./downloads` | Katalog zapisu plików PDF |
| `MCP_TRANSPORT` | nie | `stdio` | `stdio` lub `http` |
| `MCP_HTTP_PORT` | nie | `8000` | Port nasłuchu dla `MCP_TRANSPORT=http` |
| `MCP_HTTP_HOST` | nie | `127.0.0.1` | Adres nasłuchu dla `MCP_TRANSPORT=http`. Domyślnie tylko pętla zwrotna (localhost); ustaw np. `0.0.0.0`, aby udostępnić serwer w swojej sieci |
| `MCP_HTTP_AUTH_TOKEN` | nie | — (brak) | Opcjonalny token uwierzytelniający (bearer) dla transportu HTTP |

Uwagi bezpieczeństwa:

- **Jeśli `MCP_HTTP_AUTH_TOKEN` nie jest ustawiony, transport HTTP NIE ma żadnego uwierzytelniania** — każdy, kto ma dostęp sieciowy do portu, może wywoływać narzędzia na Twoim (płatnym) kluczu API rejestr.io. Przy `MCP_HTTP_HOST` innym niż `127.0.0.1` ustaw token.
- Gdy token jest ustawiony, klient MCP musi wysyłać nagłówek `Authorization: Bearer <token>`.
- **Używaj tokenu złożonego wyłącznie ze znaków ASCII** (np. `openssl rand -hex 32`). Nagłówki HTTP nie mają jednoznacznego kodowania — znaki spoza ASCII (np. `ó`) różne klienty MCP zakodują różnie, więc token z polskimi znakami może nie zostać uznany za poprawny. Serwer w takiej sytuacji bezpiecznie odrzuca żądanie (401), ale token po prostu nie zadziała.
- Obie zmienne dotyczą wyłącznie transportu HTTP — domyślny transport `stdio` ignoruje je (proces komunikuje się przez standardowe wejście/wyjście, bez gniazda sieciowego).

Adres i port można też podać z linii poleceń (`--host`, `--port`) — flagi mają pierwszeństwo przed zmiennymi środowiskowymi.

## Narzędzia MCP

Serwer udostępnia 12 narzędzi. Nazwy narzędzi i ich parametry są angielskie — serwer tłumaczy je na polskie nazwy parametrów wymagane przez API rejestr.io.

| Narzędzie | Opis | Wymagany plan |
|---|---|---|
| `search_organizations` | Wyszukiwanie organizacji w KRS wg nazwy, NIP/REGON, formy prawnej, kodów PKD, statusów, adresu, z paginacją | — |
| `get_organization` | Podstawowe dane organizacji wg numeru KRS lub NIP (np. `12345` albo `nip1234567890`) | — |
| `get_organization_krs_chapter` | Jeden rozdział KRS organizacji: `general`, `branches`, `shares`, `mentions`, `liabilities`, `transformations` | `branches`, `liabilities`, `transformations` — Premium+ |
| `get_organization_beneficial_owners` | Beneficjenci rzeczywiści (CRBR) organizacji | Premium+ |
| `get_organization_relations` | Aktualne lub historyczne powiązania organizacji z innymi organizacjami i osobami w KRS | — |
| `get_organization_krs_extract` | Pobranie odpisu z KRS (PDF): `current` (aktualny) lub `full` (pełny) | `current` — Premium+, `full` — Biznes |
| `list_organization_krs_entries` | Lista wszystkich wpisów do KRS zarejestrowanych dla organizacji | — |
| `get_person` | Aktualne dane osoby występującej w KRS wg jej identyfikatora | — |
| `get_person_relations` | Aktualne lub historyczne powiązania osoby z organizacjami w KRS | — |
| `list_organization_financial_documents` | Lista grup dokumentów finansowych (wg okresu sprawozdawczego) dostępnych w KRS dla organizacji | Premium+ |
| `get_organization_financial_document` | Jeden dokument finansowy organizacji: `format='pdf'` (plik) albo `format='json'` (treść sparsowana) | `pdf` — Premium+, `json` — Biznes |
| `get_account_balance` | Aktualny stan konta API rejestr.io w PLN | brak (darmowe) |

`—` w kolumnie „Wymagany plan" oznacza brak dodatkowych wymagań ponad standardowy klucz API. Pełne zestawienie wymagań planów: [docs/api-reference.md](docs/api-reference.md#plany-abonamentowe--wymagania-wg-endpointu).

### Pobieranie plików PDF

Narzędzia `get_organization_krs_extract` i `get_organization_financial_document` (dla `format='pdf'`) zapisują plik w katalogu z `REJESTR_IO_DOWNLOAD_DIR` (domyślnie `./downloads`, względem katalogu roboczego procesu serwera) i zwracają bezwzględną ścieżkę do zapisanego pliku. Katalog jest tworzony automatycznie; ustaw `REJESTR_IO_DOWNLOAD_DIR` na zapisywalną ścieżkę bezwzględną, jeśli klient MCP uruchamia serwer w katalogu bez prawa zapisu.

Oba narzędzia przyjmują wspólny parametr `return_base64` (domyślnie `false`). Przy `return_base64=true` oprócz ścieżki zwracana jest także zawartość pliku w odpowiedzi (blok treści z plikiem zakodowanym base64) — przydatne, gdy klient MCP nie ma dostępu do systemu plików serwera.

Szczegóły samego API rejestr.io (polskie nazwy parametrów, struktury odpowiedzi, wymagania planów) — zobacz [docs/api-reference.md](docs/api-reference.md). Uwaga: ten dokument opisuje surowe API rejestr.io, a nie nazwy narzędzi tego serwera MCP.

## Testy

```bash
uv run pytest -v
```

Wszystkie wywołania HTTP do rejestr.io są mockowane (`respx`) — testy nie wymagają dostępu do sieci ani prawdziwego klucza API.

## Zastrzeżenie prawne

Nazwa „Rejestr.io" oraz usługa (API) rejestr.io są własnością **Fundacji Moje Państwo** (dawniej: Fundacja ePaństwo), KRS 0000359730, NIP 1231216692, REGON 142445947, ul. Nowogrodzka 25/37, 00-511 Warszawa.

Ten projekt (`rejestr-io-mcp`) **nie jest oficjalnym produktem Fundacji Moje Państwo, nie jest z nią afiliowany, sponsorowany, popierany ani certyfikowany**. Jest to niezależne, otwartoźródłowe narzędzie integracyjne (klient MCP), które wyłącznie przekazuje żądania do publicznego API rejestr.io przy użyciu własnego klucza API użytkownika, wykupionego bezpośrednio w serwisie rejestr.io. Nazwa i znak „rejestr.io" są tu przywoływane wyłącznie w celach informacyjnych/opisowych — aby wskazać, z jakim serwisem ten projekt współpracuje (tzw. użycie nominatywne) — a nie w celu przypisania sobie jakichkolwiek praw do tej nazwy, znaku towarowego czy danych udostępnianych przez rejestr.io.

Korzystanie z samego API i danych zwracanych za jego pośrednictwem podlega [Regulaminowi usługi Rejestr.io API](https://rejestr.io/regulamin/api) oraz ogólnemu [Regulaminowi](https://rejestr.io/regulamin) serwisu rejestr.io — tam też znajdziesz aktualny cennik, zasady planów abonamentowych oraz [informacje o przetwarzaniu danych osobowych](https://rejestr.io/dane-osobowe). Ten projekt nie rości sobie żadnych praw do treści pochodzących z Krajowego Rejestru Sądowego, CRBR ani innych rejestrów publicznych udostępnianych przez rejestr.io.
