from __future__ import annotations

from datetime import date
import unicodedata

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


LAND_DATA_URL = (
    "https://steenhulthin.github.io/infectious-diseases-data/"
    "17_koen_uge_testede_positive_nye_indlaeggelser.csv"
)
CARE_HOME_DATA_URL = (
    "https://steenhulthin.github.io/infectious-diseases-data/"
    "28_plejehjem_ugeoversigt.csv"
)
DEATHS_DATA_URL = (
    "https://steenhulthin.github.io/infectious-diseases-data/"
    "07_antal_doede_pr_dag_pr_region.csv"
)
INFECTIOUS_DISEASES_DATA_URL = "https://steenhulthin.github.io/infectious-diseases-data/"
SSI_URL = "https://ssi.dk"
KL_CARE_HOME_URL = (
    "https://www.kl.dk/analyser/analyser/social-sundhed-og-aeldre/plejehjemsbeboere"
)
DST_POPULATION_URL = "https://www.dst.dk/da/Statistik/udgivelser/NytHtml?cid=55902"

CARE_HOME_POPULATION = 55_600
NATIONAL_POPULATION = 6_000_000

COUNTRY_LABEL = "Hele landet"
CARE_HOME_LABEL = "Plejehjem"

COL_WEEK = "Uge"
COL_GENDER = "Køn"
COL_YEAR = "År"
COL_DATE = "Dato"

METRIC_TESTED = "Testede pr. 100.000 borgere"
METRIC_POSITIVE = "Positive pr. 100.000 borgere"
METRIC_ADMISSIONS = "Nye indlæggelser pr. 100.000 borgere"
METRIC_DEATHS = "Døde pr. 100.000 borgere"
RAW_DEATHS_COLUMN = "Døde"

NATIONAL_METRICS = [
    METRIC_TESTED,
    METRIC_POSITIVE,
    METRIC_ADMISSIONS,
]

NATIONAL_COLUMN_KEYS = {
    "uge": COL_WEEK,
    "koen": COL_GENDER,
    "testede pr. 100.000 borgere": METRIC_TESTED,
    "positive pr. 100.000 borgere": METRIC_POSITIVE,
    "nye indlaeggelser pr. 100.000 borgere": METRIC_ADMISSIONS,
}

CARE_HOME_SOURCE_COLUMNS = {
    "antal tests blandt beboere": METRIC_TESTED,
    "bekraeftede tilfaelde beboere": METRIC_POSITIVE,
    "doedsfald blandt bekraeftede beboere": METRIC_DEATHS,
}

DEATHS_COLUMN_KEYS = {
    "dato": COL_DATE,
    "doede": RAW_DEATHS_COLUMN,
}

DANISH_CHARACTER_REPLACEMENTS = str.maketrans(
    {
        "æ": "ae",
        "Æ": "ae",
        "ø": "oe",
        "Ø": "oe",
        "å": "aa",
        "Å": "aa",
    }
)

COMMON_MOJIBAKE_REPLACEMENTS = {
    "Ã¦": "æ",
    "Ã†": "Æ",
    "Ã¸": "ø",
    "Ã˜": "Ø",
    "Ã¥": "å",
    "Ã…": "Å",
}

st.set_page_config(
    page_title="Covid-19 hos plejehjemsbeboere i Danmark",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def week_label(year: int, week_number: int) -> str:
    return f"{year}-U{week_number:02d}"


def week_start_from_label(label: str) -> pd.Timestamp:
    year_str, week_str = label.split("-U")
    return pd.Timestamp(date.fromisocalendar(int(year_str), int(week_str), 1))


def week_label_from_timestamp(timestamp: pd.Timestamp) -> str:
    iso_parts = timestamp.isocalendar()
    return week_label(int(iso_parts.year), int(iso_parts.week))


def format_rate(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Ingen data"
    return f"{value:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def read_semicolon_csv(url: str) -> pd.DataFrame:
    data = pd.read_csv(url, sep=";", decimal=",")
    timestamp_columns = [column for column in data.columns if column.startswith("timestamp_")]
    return data.drop(columns=timestamp_columns, errors="ignore")


def normalize_label(value: str) -> str:
    repaired = str(value)
    for broken_text, fixed_text in COMMON_MOJIBAKE_REPLACEMENTS.items():
        repaired = repaired.replace(broken_text, fixed_text)

    transliterated = repaired.translate(DANISH_CHARACTER_REPLACEMENTS)
    normalized = unicodedata.normalize("NFKD", transliterated)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_only.lower().split())


def rename_columns_from_normalized_map(
    frame: pd.DataFrame,
    normalized_name_map: dict[str, str],
) -> pd.DataFrame:
    normalized_columns = {normalize_label(column): column for column in frame.columns}
    rename_map: dict[str, str] = {}
    for normalized_name, target_name in normalized_name_map.items():
        match = normalized_columns.get(normalized_name)
        if match is None:
            raise KeyError(f"Kolonnen '{target_name}' blev ikke fundet i datasættet.")
        rename_map[match] = target_name
    return frame.rename(columns=rename_map)


def fill_missing_weeks(frame: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    complete_weeks = pd.date_range(
        frame["week_start"].min(),
        frame["week_start"].max(),
        freq="W-MON",
    )
    completed = (
        frame.set_index("week_start")[value_columns]
        .reindex(complete_weeks, fill_value=0)
        .rename_axis("week_start")
        .reset_index()
    )
    completed[COL_WEEK] = completed["week_start"].map(week_label_from_timestamp)
    return completed[["week_start", COL_WEEK, *value_columns]]


@st.cache_data(show_spinner="Henter landsdata...")
def load_national_data() -> pd.DataFrame:
    national = read_semicolon_csv(LAND_DATA_URL)
    national = rename_columns_from_normalized_map(national, NATIONAL_COLUMN_KEYS)
    national[COL_WEEK] = national[COL_WEEK].astype(str)
    national["week_start"] = national[COL_WEEK].map(week_start_from_label)

    complete_weeks = pd.date_range(
        national["week_start"].min(),
        national["week_start"].max(),
        freq="W-MON",
    )
    complete_index = pd.MultiIndex.from_product(
        [complete_weeks, ["K", "M"]],
        names=["week_start", COL_GENDER],
    )

    national = (
        national.set_index(["week_start", COL_GENDER])[NATIONAL_METRICS]
        .reindex(complete_index, fill_value=0)
        .reset_index()
    )
    national[COL_WEEK] = national["week_start"].map(week_label_from_timestamp)

    aggregated = (
        national.groupby(["week_start", COL_WEEK], as_index=False)[NATIONAL_METRICS]
        .mean()
        .sort_values("week_start")
    )
    return aggregated


@st.cache_data(show_spinner="Henter dødsfaldsdata...")
def load_national_deaths_data() -> pd.DataFrame:
    deaths = read_semicolon_csv(DEATHS_DATA_URL)
    deaths = rename_columns_from_normalized_map(deaths, DEATHS_COLUMN_KEYS)
    deaths[COL_DATE] = pd.to_datetime(deaths[COL_DATE], errors="coerce")
    deaths[RAW_DEATHS_COLUMN] = pd.to_numeric(deaths[RAW_DEATHS_COLUMN], errors="coerce").fillna(0)
    deaths = deaths[deaths[COL_DATE].notna()].copy()

    iso_calendar = deaths[COL_DATE].dt.isocalendar()
    deaths["week_start"] = [
        pd.Timestamp(date.fromisocalendar(int(year), int(week_number), 1))
        for year, week_number in zip(iso_calendar.year, iso_calendar.week)
    ]

    weekly_deaths = (
        deaths.groupby("week_start", as_index=False)[RAW_DEATHS_COLUMN]
        .sum()
        .sort_values("week_start")
    )
    weekly_deaths[METRIC_DEATHS] = weekly_deaths[RAW_DEATHS_COLUMN] / NATIONAL_POPULATION * 100_000
    weekly_deaths = weekly_deaths[["week_start", METRIC_DEATHS]]
    return fill_missing_weeks(weekly_deaths, [METRIC_DEATHS])


@st.cache_data(show_spinner="Henter plejehjemsdata...")
def load_care_home_data() -> pd.DataFrame:
    care_home = read_semicolon_csv(CARE_HOME_DATA_URL)
    care_home = rename_columns_from_normalized_map(
        care_home,
        {
            "aar": COL_YEAR,
            "uge": COL_WEEK,
            **{column_name: column_name for column_name in CARE_HOME_SOURCE_COLUMNS},
        },
    )
    care_home = care_home[
        pd.to_numeric(care_home[COL_YEAR], errors="coerce").notna()
        & pd.to_numeric(care_home[COL_WEEK], errors="coerce").notna()
    ].copy()

    care_home[COL_YEAR] = care_home[COL_YEAR].astype(int)
    care_home[COL_WEEK] = care_home[COL_WEEK].astype(int)
    care_home["week_start"] = [
        pd.Timestamp(date.fromisocalendar(year, week_number, 1))
        for year, week_number in zip(care_home[COL_YEAR], care_home[COL_WEEK])
    ]

    for source_column, normalized_column in CARE_HOME_SOURCE_COLUMNS.items():
        care_home[normalized_column] = care_home[source_column] / CARE_HOME_POPULATION * 100_000

    care_home = care_home[["week_start", *CARE_HOME_SOURCE_COLUMNS.values()]].sort_values("week_start")
    return fill_missing_weeks(care_home, list(CARE_HOME_SOURCE_COLUMNS.values()))


@st.cache_data(show_spinner=False)
def build_dashboard_data() -> pd.DataFrame:
    national = load_national_data().rename(
        columns={metric: f"{metric} ({COUNTRY_LABEL})" for metric in NATIONAL_METRICS}
    )
    national_deaths = load_national_deaths_data().rename(
        columns={METRIC_DEATHS: f"{METRIC_DEATHS} ({COUNTRY_LABEL})"}
    )
    care_home = load_care_home_data().rename(
        columns={
            metric: f"{metric} ({CARE_HOME_LABEL})"
            for metric in CARE_HOME_SOURCE_COLUMNS.values()
        }
    )

    combined = national.merge(
        national_deaths[["week_start", f"{METRIC_DEATHS} ({COUNTRY_LABEL})"]],
        on="week_start",
        how="outer",
    ).merge(
        care_home,
        on="week_start",
        how="outer",
    )
    combined[COL_WEEK] = combined["week_start"].map(week_label_from_timestamp)
    combined = combined.sort_values("week_start").reset_index(drop=True)

    return combined[
        [
            "week_start",
            COL_WEEK,
            f"{METRIC_TESTED} ({COUNTRY_LABEL})",
            f"{METRIC_POSITIVE} ({COUNTRY_LABEL})",
            f"{METRIC_ADMISSIONS} ({COUNTRY_LABEL})",
            f"{METRIC_DEATHS} ({COUNTRY_LABEL})",
            f"{METRIC_TESTED} ({CARE_HOME_LABEL})",
            f"{METRIC_POSITIVE} ({CARE_HOME_LABEL})",
            f"{METRIC_DEATHS} ({CARE_HOME_LABEL})",
        ]
    ]


def build_comparison_figure(data: pd.DataFrame, metric_name: str, chart_title: str) -> go.Figure:
    figure = go.Figure()
    for series_name in (COUNTRY_LABEL, CARE_HOME_LABEL):
        column_name = f"{metric_name} ({series_name})"
        figure.add_trace(
            go.Scatter(
                x=data["week_start"],
                y=data[column_name],
                mode="lines",
                name=series_name,
                customdata=data[[COL_WEEK]],
                hovertemplate=(
                    "%{customdata[0]}<br>"
                    + f"{series_name}: "
                    + "%{y:.1f} pr. 100.000<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title=chart_title,
        template="plotly_white",
        height=430,
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        margin={"l": 12, "r": 12, "t": 64, "b": 12},
        paper_bgcolor="rgba(255,255,255,0)",
    )
    figure.update_xaxes(
        title="Uge",
        tickformat="%Y",
        showgrid=False,
    )
    figure.update_yaxes(
        title="Pr. 100.000 borgere/beboere",
        zeroline=True,
    )
    return figure


def latest_kpi_row(data: pd.DataFrame) -> pd.Series:
    care_home_data_columns = [
        f"{METRIC_TESTED} ({CARE_HOME_LABEL})",
        f"{METRIC_POSITIVE} ({CARE_HOME_LABEL})",
        f"{METRIC_DEATHS} ({CARE_HOME_LABEL})",
    ]
    available_rows = data.dropna(subset=care_home_data_columns, how="all")
    if available_rows.empty:
        return data.iloc[-1]
    return available_rows.iloc[-1]


def render_header() -> None:
    st.markdown(
        """
        <section class="hero">
            <h1>Covid-19 hos plejehjemsbeboere i Danmark</h1>
            <p>
                Sammenligning af smitteudviklingen i hele landet og blandt plejehjemsbeboere.
                Landskurverne er aggregeret på tværs af køn som gennemsnit af rater pr. 100.000,
                landsdødsfald summeres til ISO-uger og normaliseres med 6.000.000 borgere,
                og plejehjemstal er normaliseret med 55.600 beboere.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(data: pd.DataFrame) -> None:
    latest = latest_kpi_row(data)
    st.markdown('<div class="metric-shell">', unsafe_allow_html=True)
    st.caption(f"Seneste uge med plejehjemsdata: {latest[COL_WEEK]}")

    st.markdown("**Hele landet**")
    country_one, country_two, country_three = st.columns(3)
    country_one.metric(
        "Testede",
        format_rate(latest[f"{METRIC_TESTED} ({COUNTRY_LABEL})"]),
    )
    country_two.metric(
        "Positive",
        format_rate(latest[f"{METRIC_POSITIVE} ({COUNTRY_LABEL})"]),
    )
    country_three.metric(
        "Døde",
        format_rate(latest[f"{METRIC_DEATHS} ({COUNTRY_LABEL})"]),
    )

    st.markdown("**Plejehjem**")
    care_one, care_two, care_three = st.columns(3)
    care_one.metric(
        "Testede",
        format_rate(latest[f"{METRIC_TESTED} ({CARE_HOME_LABEL})"]),
    )
    care_two.metric(
        "Positive",
        format_rate(latest[f"{METRIC_POSITIVE} ({CARE_HOME_LABEL})"]),
    )
    care_three.metric(
        "Døde",
        format_rate(latest[f"{METRIC_DEATHS} ({CARE_HOME_LABEL})"]),
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_sources() -> None:
    st.markdown(
        (
            "Kilde: [SSI - Statens Serum Institut]"
            f"({SSI_URL}) via [steenhulthin's infectious-diseases-data]"
            f"({INFECTIOUS_DISEASES_DATA_URL}). "
            f"Antagelse om 55.600 plejehjemsbeboere: [KL]({KL_CARE_HOME_URL}). "
            f"Antagelse om 6.000.000 borgere i hele landet: [Danmarks Statistik]({DST_POPULATION_URL})."
        )
    )


def main() -> None:
    render_header()

    try:
        dashboard_data = build_dashboard_data()
    except Exception as exc:
        st.error(f"Data kunne ikke hentes eller behandles: {exc}")
        return

    week_options = dashboard_data[COL_WEEK].tolist()

    st.sidebar.header("Vælg periode")
    selected_period = st.sidebar.select_slider(
        "Periode i uger",
        options=week_options,
        value=(week_options[0], week_options[-1]),
    )

    start_week, end_week = selected_period
    start_timestamp = week_start_from_label(start_week)
    end_timestamp = week_start_from_label(end_week)
    filtered_data = dashboard_data[
        dashboard_data["week_start"].between(start_timestamp, end_timestamp)
    ].copy()

    if filtered_data.empty:
        st.warning("Ingen data i den valgte periode.")
        return

    render_metrics(dashboard_data)
    st.markdown(
        """
        <div class="chart-caption">
            Sammenligningen viser ugentlige, normaliserede rater pr. 100.000 for hele landet og plejehjemsbeboere.
        </div>
        """,
        unsafe_allow_html=True,
    )

    test_figure = build_comparison_figure(
        filtered_data,
        METRIC_TESTED,
        METRIC_TESTED,
    )
    st.divider()
    st.plotly_chart(test_figure, width="stretch")

    positive_figure = build_comparison_figure(
        filtered_data,
        METRIC_POSITIVE,
        METRIC_POSITIVE,
    )
    st.plotly_chart(positive_figure, width="stretch")

    deaths_figure = build_comparison_figure(
        filtered_data,
        METRIC_DEATHS,
        METRIC_DEATHS,
    )
    st.plotly_chart(deaths_figure, width="stretch")

    render_sources()


if __name__ == "__main__":
    main()
