<h1 align="left">
:soccer: :football: :golf: :bike: :racing_car:
</h1> <h1 align="center">
holdetdk-scraper
</h1> <h1 align="right">
:computer: :robot: :1234:
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
Ønsker man at scrape hold fra en tidligere runde vil man undervejs blive bedt om at logge ind på Holdet.dk med en bruger som har et guldhold i det pågældende spil. Scraper man hold fra en tidligere runde vil man desuden i outputtet opleve dummy-værdier for 'SpillerHold' og 'SpillerVærdi' da disse oplysninger ikke er tilgængelige for hold fra tidligere runder.

## Performance
Scraper man hold fra den aktive runde kan man forvente en performance på ~10 min pr. 1.000 hold. <br/>
Scraper man hold fra en tidligere runde falder performance imidlertid til ~60 min pr. 1.000 hold, da dette kræver brug af en ```Selenium``` webdriver. 

## Eksempel på brug