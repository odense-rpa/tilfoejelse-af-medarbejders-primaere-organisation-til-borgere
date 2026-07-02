# Tilføjelse af medarbejders primære organisation til borgere

Robotten finder borgere, der for nylig har fået tilknyttet en fagperson fra en bestemt organisation i KMD Nexus, og tilføjer automatisk den pågældende organisation til borgerens profil.

## Hvad gør robotten?

1. Indlæser organisations-mapping fra Excel-filen `Regelsæt.xlsx` (kolonnen *Organisationer*).
2. For hver organisation hentes borgere fra KMD Nexus-databasen, der inden for de seneste 2 dage har fået tilknyttet en fagperson fra den pågældende organisation.
3. Hvert borger/organisation-par tilføjes som et arbejdselement i arbejdskøen.
4. For hvert arbejdselement hentes borgeren fra KMD Nexus.
5. Kontrollerer om borgeren allerede er tilknyttet organisationen — springer over hvis ja.
6. Henter organisationsobjektet fra KMD Nexus og tilføjer borgeren til organisationen.
7. Registrerer den udførte opgave i tracking-systemet via Odense SQL Server.

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø og credentials)
- Adgang til **KMD Nexus** (produktion og database)
- Adgang til **Odense SQL Server** (tracking)
- Excel-filen `Regelsæt.xlsx` med en kolonne kaldet `Organisationer`

## Installation

```sh
uv sync
```

## Konfiguration

Credentials registreres i Automation Server:

- `KMD Nexus - produktion`
- `KMD Nexus - database`
- `Odense SQL Server`

| Miljøvariabel | Beskrivelse |
|---|---|
| `ATS_URL` | URL til Automation Server (standard: `http://localhost:8000`) |
| `ATS_TOKEN` | Bearer token til Automation Server API |
| `ATS_WORKQUEUE_OVERRIDE` | Tilsidesæt workqueue-ID (valgfri) |

## Kørsel

```sh
uv run python main.py --queue   # Fyld arbejdskøen
uv run python main.py           # Behandl arbejdskøen
```

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Klient til Automation Server — workqueue, credentials og arbejdselementer |
| `kmd-nexus-client` | Klient til KMD Nexus API — hent og opdater borger- og organisationsdata |
| `nexus-database-client` | Databaseklient til KMD Nexus — forespørgsler på borgere med nyligt tilknyttede fagpersoner |
| `odk-tools` | Tracking-funktionalitet til registrering af udførte opgaver |
| `openpyxl` | Læsning af Excel-filen `Regelsæt.xlsx` med organisations-mapping |

## GDPR og sikkerhed

Robotten behandler CPR-numre på borgere. CPR-numrene overføres som arbejdselementer i Automation Servers arbejdskø og anvendes udelukkende til opslag og opdatering i KMD Nexus. Der gemmes ingen personoplysninger lokalt. Adgang til Automation Server og KMD Nexus bør begrænses til relevante medarbejdere og systemkonti.
