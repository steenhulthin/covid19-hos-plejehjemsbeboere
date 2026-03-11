Lav et Streamlit-dashboard. Overskriften skal vaere "Covid-19 hos plejehjemsbeboere i Danmark". Tilfoej et favicon der passer til sygdom/virus. Layoutet skal vaere friskt, men stadig professionelt.

Det skal hente data fra <https://steenhulthin.github.io/infectious-diseases-data/>. Data skal hentes med pandas som beskrevet i readme.md her: <https://github.com/steenhulthin/infectious-diseases-data>. Brug data fra <https://steenhulthin.github.io/infectious-diseases-data/17_koen_uge_testede_positive_nye_indlaeggelser.csv> (lande-data) og <https://steenhulthin.github.io/infectious-diseases-data/28_plejehjem_ugeoversigt.csv> (plejehjem-data).

Lande-data skal summeres paa koen. M og K skal sammenlaegges, og tal i kolonner med "pr. 100.000 borgere" skal aggregeres som gennemsnit. Vaer opmaerksom paa at der kan vaere manglende uger og/eller manglende koen; de skal udfyldes som 0. Vi antager, at der er naesten samme antal kvinder (K) og maend (M) i befolkningen.

Plejehjem-data skal bruge "Aar" og "Uge" til at danne samme ugeformat som i lande-data, dynamisk, saa det kan bruges som x-akse i graferne. Kolonnerne "Antal tests blandt beboere", "Bekraeftede tilfaelde beboere" og "Doedsfald blandt bekraeftede beboere" skal normaliseres til pr. 100.000 beboere. Antag at der er 55.600 beboere paa plejehjem over hele perioden: <https://www.kl.dk/analyser/analyser/social-sundhed-og-aeldre/plejehjemsbeboere>.

Der skal vaere Plotly-grafer paa dashboardet.

Der skal laves en graf paa baggrund af lande-data og plejehjem-data (normaliserede tal) med labelen "Testede pr. 100.000 borgere".

Der skal laves en anden graf med labelen "Positive pr. 100.000 borgere".

Paa dashboardet skal der vaere foelgende filtre:
- periode (dobbelt slider)

Supplerende kravspecifikation:

- Kolonnenavne fra kildedata skal matches robust, ogsaa naar danske bogstaver forekommer som `ae/oe/aa`, som rigtige danske tegn, eller som lette encoding-afvigelser.
- Raekker som ikke repraesenterer en rigtig ugeobservation, for eksempel opsummeringsraekker som `I alt`, skal ignoreres i databehandlingen.
- Eventuelle `timestamp_...`-kolonner fra kildedata er metadata og maa ikke indgaa i visualiseringer eller aggregeringer.
