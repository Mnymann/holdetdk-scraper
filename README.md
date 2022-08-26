<h1 align="center">
:soccer: :football: :golf: :biking_man: :racing_car: &nbsp; holdetdk-scraper &nbsp; :computer: :robot: :1234: :nerd_face: :trophy:
</h1>

## Intro
Med denne scraper kan du hente data fra [Holdet.dk](http://www.holdet.dk)'s managerspil. <br/>
Udvikleren bag scraperen er på ingen måde associeret med Holdet.dk og scraperen er udviklet som et hyggeprojekt.

## Formål
På Holdet.dk findes der allerede en statistikside, hvor man bl.a. kan se spillervækst, trend og popularitetsprocent runde for runde. Disse tal er beregnet på baggrund af alle hold, der deltager i spillet. For de mere seriøse managerspillere er det imidlertid langt mere interessant at se på statistikker der er beregnet udelukkende på baggrund af hold fra præmiepuljen (eller dele heraf).

Det primære formål med denne scraper er derfor at beregne spillernes popularitetsprocent og anførerpopularitet udelukkende på baggrund af hold fra præmiepuljen (eller dele heraf).

## Terminologi
Scraperen er primært bygget til Holdet.dk's fodboldspil og terminologien i outputtet fra scraperen stammer herfra. Den kan dog også hente data fra andre spil, fx Håndbold Manager, Golf Manager, Tour Manager, Motor Manager etc.

## Begrænsninger
Uden et login på Holdet.dk kan man udelukkende se på andre manageres hold fra den aktive runde i et spil. Scraperen er derfor primært bygget med henblik på at scrape hold fra den aktive runde. <br/>
Ønsker man at scrape hold fra en tidligere runde vil man undervejs blive bedt om at logge ind på Holdet.dk med en bruger som har et guldhold i det pågældende spil. Scraper man hold fra en tidligere runde vil man desuden i outputtet opleve dummy-værdier for 'SpillerHold' og 'SpillerVærdi' da disse oplysninger ikke er tilgængelige for hold fra tidligere runder. <br/>
Scraping af hold fra tidligere runder kræver desuden brug af en ```Selenium``` webdriver og du vil derfor blive bedt om at downloade en ```chromedriver``` ([link](https://sites.google.com/chromium.org/driver/)) og gemme den under ```.../Drivers```

## Performance
Scraper man hold fra den aktive runde kan man forvente en performance på ~10 min pr. 1.000 hold. <br/>
Scraper man hold fra en tidligere runde falder performance imidlertid til ~60 min pr. 1.000 hold, da dette kræver brug af en ```Selenium``` webdriver. 

## Eksempel på brug
Importér pakker
```
import pandas as pd
import os
from holdetdk_scraper import HoldetScraper
```

Lav en scraper instans
```
scraper = HoldetScraper()
```

Få en liste over aktive spil
```
scraper.active_games
```

Vælg hvad du vil scrape ved at indstille parametrene ```game```, ```round``` og ```top```. <br/>
Du kan f.eks. hente data Top 100 hold i præmiepuljen for runde 1 i Premier Manager Efterår 2022 således:
```
table, teams = scraper.get_table_and_teams(game='Premier Manager Efterår 2022', round=1, top=100)
```

Du kan også tilfældigt udvalgte hold fra den aktive runde ved at sætte ```random_sample=True``` og ```round=0```:
```
table, teams = scraper.get_table_and_teams(game='Premier Manager Efterår 2022', round=0, top=100) 
```

Når du (som ovenfor) har gemt en tabel med hold i variablen ```teams``` kan du udregne popularitetsprocenter og anførerpopulariteter for de valgte ```splits``` således:
```
popularity = scraper.calc_popularity_table(teams_table=teams, splits = [100, 1000])
```

Du kan gemme outputtet i en Excel-fil således:
```
output_folder = os.path.abspath('') + '/Output'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

output_path = f'{output_folder}/{game}, Runde {str(table.at[0, "Runde"])}, Top {len(table)}.xlsx'
with pd.ExcelWriter(output_path) as writer:  
    table.to_excel(writer, sheet_name='Tabel', index=False)
    teams.to_excel(writer, sheet_name='Hold', index=False)
    popularity.to_excel(writer, sheet_name='Popularitet', index=False)
```