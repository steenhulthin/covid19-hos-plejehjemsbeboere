lav et streamlit dashboard. Overskriften skal "Covid-19 hos plejehjemsbeboere i Danmark". Tilføj favicon der passer til sygdom/virus. Layout skal være friskt, men stadig professionelt.

Det skal hente data fra <https://steenhulthin.github.io/infectious-diseases-data/> . Data skal hentes med pandas som beskrevet i readme.md her: <https://github.com/steenhulthin/infectious-diseases-data>. Brug data fra <https://steenhulthin.github.io/infectious-diseases-data/17_koen_uge_testede_positive_nye_indlaeggelser.csv> (lad os kalde datasættet for "lande-data") og <https://steenhulthin.github.io/infectious-diseases-data/28_plejehjem_ugeoversigt.csv> (lad os kalde datasættet for "plejehjem-data")

Lande-data skal summeres på køn - M og K skal sammenlægges og tal og kolonner med "pr. 100.000 borgere" skal der tages et gennemsnit af (vær opmærksom på at der er manglende uger og/eller køn - de skal udfyldes som 0) Bemærk: vi antager, at der er næsten samme antal kvinder (K) og mænd (M) i befolkningen. 

plejehjem-data skal "År" og "Uge" skal gøre sammenlignelig med til "Uge" i lande-data (dynamisk), da det skal være vores x-akse i vores graf. Kolonnerne "Antal tests blandt beboere", "Bekræftede tilfælde beboere", "Dødsfald blandt bekræftede beboere" skal normaliseres til pr. 100.000 beboere. Antag at der er 55.600 beboere på plejehjem over hele perioden [kile](https://www.kl.dk/analyser/analyser/social-sundhed-og-aeldre/plejehjemsbeboere) 

Der skal være grafer på dashboardet. Grafer skal være plotly grafer.

Der skal laves graf på baggrund af data: Lande-data og plejehjem-data (normaliserede tal) med labelen "Testede pr. 100.000 borgere" 

Anden graf skal være "Positive pr. 100.000 borgere". 


På dashboardet skal der være følgende filtre:
- periode (dobbelt slider)
