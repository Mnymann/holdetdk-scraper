# holdetdk
Hent data fra Holdet.dk's managerspil.

## Eksempel
Lav en ny instans af HoldetScraper-klassen med HoldetScraper()

```
from HoldetScraper import HoldetScraper
scraper = HoldetScraper()
```

Herefter kan du få en liste over aktive spil på Holdet.dk således:
```
scraper.active_games
```

Quick start:

```
table, teams = scraper.get_table_and_teams(scraper.active_games[0], top=10)
```

### Disclaimer
Scraperen er primært bygget til Holdet.dk's fodboldmanagerspil og terminologien i outputtet stammer herfra.
Den kan dog også scrape data fra andre spil, fx Håndbold Manager, Golf Manager, Tour de France Manager etc.


Bemærk at de hold, som scraperen returnerer, altid vil være holdene fra den seneste runde.

Umiddelbart kræver det login + guldhold samt brug af selenium-pakken, hvis man vil scrape et specifikt hold fra en specifik runde. Det er indtil videre ude af scope for dette projekt.

