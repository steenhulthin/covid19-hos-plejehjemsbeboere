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
CARE_HOME_POPULATION = 55_600
COUNTRY_LABEL = "Hele landet"
CARE_HOME_LABEL = "Plejehjem"
COL_WEEK = "Uge"
COL_GENDER = "Køn"
COL_YEAR = "År"
NATIONAL_METRICS = [
    "Testede pr. 100.000 borgere",
    "Positive pr. 100.000 borgere",
    "Nye indlæggelser pr. 100.000 borgere",
]
NATIONAL_COLUMN_KEYS = {
    "uge": COL_WEEK,
    "koen": COL_GENDER,
    "testede pr. 100.000 borgere": NATIONAL_METRICS[0],
    "positive pr. 100.000 borgere": NATIONAL_METRICS[1],
    "nye indlaeggelser pr. 100.000 borgere": NATIONAL_METRICS[2],
}
CARE_HOME_SOURCE_COLUMNS = {
    "antal tests blandt beboere": "Testede pr. 100.000 borgere",
    "bekraeftede tilfaelde beboere": "Positive pr. 100.000 borgere",
    "doedsfald blandt bekraeftede beboere": "Dødsfald pr. 100.000 borgere",
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
CHART_COLORS = {
    COUNTRY_LABEL: "#0f766e",
    CARE_HOME_LABEL: "#ea580c",
}


st.set_page_config(
    page_title="Covid-19 hos plejehjemsbeboere i Danmark",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_style() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(15, 118, 110, 0.14), transparent 32%),
                    radial-gradient(circle at top right, rgba(234, 88, 12, 0.12), transparent 28%),
                    linear-gradient(180deg, #f8fbfc 0%, #eef4f3 100%);
                color: #11212a;
                font-family: "Aptos", "Segoe UI", sans-serif;
            }
            [data-testid="stSidebar"] {
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(10px);
                border-right: 1px solid rgba(17, 33, 42, 0.08);
            }
            .hero {
                padding: 1.8rem 2rem;
                border: 1px solid rgba(17, 33, 42, 0.08);
                border-radius: 24px;
                background:
                    linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(246, 250, 250, 0.9));
                box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 2.2rem;
                line-height: 1.15;
                font-family: "Bahnschrift", "Aptos", sans-serif;
            }
            .hero p {
                margin: 0.7rem 0 0;
                max-width: 65rem;
                color: #37505c;
                font-size: 1rem;
            }
            .metric-shell {
                padding: 0.2rem 0 1rem;
            }
            [data-testid="metric-container"] {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(17, 33, 42, 0.08);
                padding: 0.9rem 1rem;
                border-radius: 18px;
                box-shadow: 0 12px 26px rgba(15, 23, 42, 0.06);
            }
            .chart-caption {
                color: #4b6470;
                font-size: 0.9rem;
                margin-top: -0.3rem;
                margin-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
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
    normalized_columns = {
        normalize_label(column): column
        for column in frame.columns
    }
    rename_map = {}
    for normalized_name, target_name in normalized_name_map.items():
        match = normalized_columns.get(normalized_name)
        if match is None:
            raise KeyError(f"Kolonnen '{target_name}' blev ikke fundet i datasættet.")
        rename_map[match] = target_name
    return frame.rename(columns=rename_map)


@st.cache_data(show_spinner="Henter landsdata...")
def load_national_data() -> pd.DataFrame:
    national = read_semicolon_csv(LAND_DATA_URL)
    national = rename_columns_from_normalized_map(
        national,
        NATIONAL_COLUMN_KEYS,
    )
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

    care_home = care_home[
        ["week_start", *CARE_HOME_SOURCE_COLUMNS.values()]
    ].sort_values("week_start")

    complete_weeks = pd.date_range(
        care_home["week_start"].min(),
        care_home["week_start"].max(),
        freq="W-MON",
    )
    care_home = (
        care_home.set_index("week_start")
        .reindex(complete_weeks, fill_value=0)
        .rename_axis("week_start")
        .reset_index()
    )
    care_home[COL_WEEK] = care_home["week_start"].map(week_label_from_timestamp)
    return care_home[["week_start", COL_WEEK, *CARE_HOME_SOURCE_COLUMNS.values()]]


@st.cache_data(show_spinner=False)
def build_dashboard_data() -> pd.DataFrame:
    national = load_national_data().rename(
        columns={metric: f"{metric} ({COUNTRY_LABEL})" for metric in NATIONAL_METRICS}
    )
    care_home = load_care_home_data().rename(
        columns={
            metric: f"{metric} ({CARE_HOME_LABEL})"
            for metric in CARE_HOME_SOURCE_COLUMNS.values()
        }
    )

    combined = national.merge(care_home, on="week_start", how="outer")
    combined[COL_WEEK] = combined["week_start"].map(week_label_from_timestamp)
    combined = combined.sort_values("week_start").reset_index(drop=True)
    return combined[
        [
            "week_start",
            COL_WEEK,
            f"Testede pr. 100.000 borgere ({COUNTRY_LABEL})",
            f"Positive pr. 100.000 borgere ({COUNTRY_LABEL})",
            f"Nye indlæggelser pr. 100.000 borgere ({COUNTRY_LABEL})",
            f"Testede pr. 100.000 borgere ({CARE_HOME_LABEL})",
            f"Positive pr. 100.000 borgere ({CARE_HOME_LABEL})",
            f"Dødsfald pr. 100.000 borgere ({CARE_HOME_LABEL})",
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
                line={"color": CHART_COLORS[series_name], "width": 3},
                customdata=data[["Uge"]],
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
        plot_bgcolor="rgba(255,255,255,0.92)",
    )
    figure.update_xaxes(
        title="Uge",
        tickformat="%Y",
        showgrid=False,
    )
    figure.update_yaxes(
        title="Pr. 100.000 borgere/beboere",
        zeroline=True,
        zerolinecolor="rgba(17, 33, 42, 0.12)",
        gridcolor="rgba(17, 33, 42, 0.08)",
    )
    return figure


def render_header() -> None:
    st.markdown(
        """
        <section class="hero">
            <h1>Covid-19 hos plejehjemsbeboere i Danmark</h1>
            <p>
                Sammenligning af smitteudviklingen i hele landet og blandt plejehjemsbeboere.
                Landskurverne er aggregeret på tværs af køn som gennemsnit af rater pr. 100.000,
                mens plejehjemstal er normaliseret med 55.600 beboere.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(filtered_data: pd.DataFrame) -> None:
    latest = filtered_data.iloc[-1]
    st.markdown('<div class="metric-shell">', unsafe_allow_html=True)
    column_one, column_two, column_three, column_four = st.columns(4)
    column_one.metric("Seneste uge", latest["Uge"])
    column_two.metric(
        "Tests, hele landet",
        format_rate(latest[f"Testede pr. 100.000 borgere ({COUNTRY_LABEL})"]),
    )
    column_three.metric(
        "Tests, plejehjem",
        format_rate(latest[f"Testede pr. 100.000 borgere ({CARE_HOME_LABEL})"]),
    )
    column_four.metric(
        "Positive, plejehjem",
        format_rate(latest[f"Positive pr. 100.000 borgere ({CARE_HOME_LABEL})"]),
    )
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    apply_custom_style()
    render_header()

    try:
        dashboard_data = build_dashboard_data()
    except Exception as exc:
        st.error(f"Data kunne ikke hentes eller behandles: {exc}")
        return

    week_options = dashboard_data["Uge"].tolist()

    st.sidebar.header("Filtre")
    selected_period = st.sidebar.select_slider(
        "Periode",
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

    render_metrics(filtered_data)
    st.markdown(
        """
        <div class="chart-caption">
            Sammenligningen viser rater pr. 100.000 i samme ugeakse for hele landet og plejehjemsbeboere.
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_one, chart_two = st.columns(2)
    with chart_one:
        test_figure = build_comparison_figure(
            filtered_data,
            "Testede pr. 100.000 borgere",
            "Testede pr. 100.000 borgere",
        )
        st.plotly_chart(test_figure, use_container_width=True)

    with chart_two:
        positive_figure = build_comparison_figure(
            filtered_data,
            "Positive pr. 100.000 borgere",
            "Positive pr. 100.000 borgere",
        )
        st.plotly_chart(positive_figure, use_container_width=True)

    st.caption(
        "Kilde: infectious-diseases-data. Plejehjemstal er normaliseret til 55.600 beboere."
    )


if __name__ == "__main__":
    main()
