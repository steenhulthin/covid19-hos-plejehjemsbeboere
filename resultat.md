Lav et Streamlit-dashboard. Overskriften skal være "Covid-19 hos plejehjemsbeboere i Danmark". Tilføj et favicon der passer til sygdom/virus. Layoutet skal være friskt, men stadig professionelt.

Det skal hente data fra <https://steenhulthin.github.io/infectious-diseases-data/>. Data skal hentes med pandas som beskrevet i readme.md her: <https://github.com/steenhulthin/infectious-diseases-data>. Brug data fra <https://steenhulthin.github.io/infectious-diseases-data/17_koen_uge_testede_positive_nye_indlaeggelser.csv> (lande-data), <https://steenhulthin.github.io/infectious-diseases-data/28_plejehjem_ugeoversigt.csv> (plejehjem-data) og <07_antal_doede_pr_dag_pr_region.csv> (dødsfald-lande-data).

Lande-data skal summeres på køn. M og K skal sammenlægges, og tal i kolonner med "pr. 100.000 borgere" skal aggregeres som gennemsnit. Vær opmærksom på at der kan være manglende uger og/eller manglende køn; de skal udfyldes som 0. Vi antager, at der er næsten samme antal kvinder (K) og mænd (M) i befolkningen.

For dødsfald-lande-data skal antal "Døde" summeres for hele landet (alle "Regionkode") og på uge-niveau (data er på dagsligt niveau baseret på "Dato" - ISO-uger skal benyttes (ugen er fra mandag til søndag)). "Kummuleret antal døde" kolonnen må ikke benyttes. Det skal antages at der er 6.000.000 mennesker i hele landet (baseret på <https://www.dst.dk/da/Statistik/udgivelser/NytHtml?cid=55902>). Der skal beregnes en normaliseret "Døde pr. 100.000 borgere" ud fra "Døde" og antagelse om antal mennesker i landet. 

Lande-data og dødsfald-lande-data skal kombineres til et datasæt baseret på ugen. 

Plejehjem-data skal bruge "År" og "Uge" til at danne samme ugeformat som i lande-data, dynamisk, så det kan bruges som x-akse i graferne. Kolonnerne "Antal tests blandt beboere", "Bekræftede tilfælde beboere" og "Dødsfald blandt bekræftede beboere" skal normaliseres til pr. 100.000 beboere. Antag at der er 55.600 beboere på plejehjem over hele perioden: <https://www.kl.dk/analyser/analyser/social-sundhed-og-aeldre/plejehjemsbeboere>.

Der skal være Plotly-grafer på dashboardet. Graferne placeres vertikalt (ikke ved siden af hinanden).

Der skal laves en graf på baggrund af lande-data og plejehjem-data (normaliserede tal) med labelen "Testede pr. 100.000 borgere".

Der skal laves en anden graf med labelen "Positive pr. 100.000 borgere".

Der skal laves en tredje graf med labelen "Døde pr. 100.000 borgere".

På dashboardet skal der være følgende filtre:
- periode (dobbelt slider)

Supplerende kravspecifikation:

- Kolonnenavne fra kildedata skal matches robust, også når danske bogstaver forekommer som `ae/oe/aa`, som rigtige danske tegn, eller som lette encoding-afvigelser.
- Rækker som ikke repræsenterer en rigtig ugeobservation, for eksempel opsummeringsrækker som `I alt`, skal ignoreres i databehandlingen.
- Eventuelle `timestamp_...`-kolonner fra kildedata er metadata og må ikke indgå i visualiseringer eller aggregeringer.

Brugerflade/layout:
- Ved kildeangivelse skal der linkes til "[SSI - Statens Serum Institut](https://ssi.dk) via [steenhulthin's infectious-diseases-data](https://steenhulthin.github.io/infectious-diseases-data/)". Der linkes til kilder for antagelserne om befolknings- og beboer-tal. 
- KPI vises kun for seneste uge, hvor der er data tilgængeligt fra plejehjem-data. 
