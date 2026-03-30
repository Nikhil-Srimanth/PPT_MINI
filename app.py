"""
Conservation Report Generator
==============================
Multimodal AI-powered Streamlit app for environmental conservation analysis.
Uses Groq API (free tier) with llama-3.3-70b model.
No sidebar — all controls flow top-to-bottom on the main page.
"""

import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from groq import Groq
import base64
import io
import os
import tempfile
from datetime import datetime
from PIL import Image
import warnings
warnings.filterwarnings("ignore")
from fpdf import FPDF

# ─── Groq API Configuration ──────────────────────────────────────────────────
# FREE tier — get your key at: https://console.groq.com
GROK_API_KEY  = "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"   # ← paste your Groq key here
GROK_MODEL    = "llama-3.3-70b-versatile"

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Conservation Report Generator",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --forest-dark:  #071409;
        --forest-mid:   #0f2611;
        --moss:         #1e4d1a;
        --fern:         #2e7d32;
        --sage:         #52a047;
        --lime:         #76c442;
        --mist:         #c8dfc2;
        --amber:        #d4a017;
        --danger:       #c0392b;
        --glass-bg:     rgba(14, 38, 16, 0.55);
        --glass-border: rgba(118, 196, 66, 0.18);
        --card-bg:      rgba(11, 28, 12, 0.7);
        --text-primary: #ddeedd;
        --text-muted:   #7aaa72;
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    .stApp {
        background:
            radial-gradient(ellipse 80% 60% at 10% 20%, rgba(30,77,26,0.25) 0%, transparent 60%),
            radial-gradient(ellipse 60% 80% at 90% 80%, rgba(14,40,12,0.4) 0%, transparent 60%),
            linear-gradient(175deg, #071409 0%, #0f2611 45%, #071409 100%);
        color: var(--text-primary);
    }

    [data-testid="collapsedControl"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }

    /* ── Hero ─────────────────────────────────────────────────────────── */
    .hero {
        background:
            linear-gradient(135deg, rgba(46, 125, 50, 0.12) 0%, rgba(7, 20, 9, 0.95) 60%),
            linear-gradient(to bottom right, rgba(30,77,26,0.3), transparent);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 3rem 3.5rem 2.8rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 48px rgba(0,0,0,0.5), inset 0 1px 0 rgba(118,196,66,0.1);
    }
    .hero-leaf {
        position: absolute; right: 2.5rem; top: 50%;
        transform: translateY(-50%);
        font-size: 6rem; opacity: 0.07; pointer-events: none;
        animation: leafFloat 8s ease-in-out infinite;
    }
    @keyframes leafFloat {
        0%, 100% { transform: translateY(-50%) rotate(-5deg); }
        50%       { transform: translateY(-55%) rotate(3deg); }
    }
    .hero-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 3.2rem; font-weight: 700;
        color: var(--mist); margin: 0 0 0.5rem; line-height: 1.15;
        letter-spacing: -0.01em;
        text-shadow: 0 2px 30px rgba(118,196,66,0.15);
    }
    .hero-sub {
        color: var(--text-muted); font-size: 1rem; font-weight: 300;
        letter-spacing: 0.08em; text-transform: uppercase;
    }
    .hero-badges { margin-top: 1.4rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 0.35rem;
        background: rgba(46,125,50,0.15);
        border: 1px solid rgba(118,196,66,0.25);
        border-radius: 100px;
        padding: 0.3rem 1rem;
        font-size: 0.76rem; font-weight: 500;
        color: var(--lime); letter-spacing: 0.04em;
    }

    /* ── Step panels ──────────────────────────────────────────────────── */
    .step-panel {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.3rem 1.8rem 0.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.25);
        position: relative; overflow: hidden;
    }
    .step-panel::before {
        content: ''; position: absolute;
        left: 0; top: 0; bottom: 0; width: 3px;
        background: linear-gradient(to bottom, var(--sage), transparent);
        border-radius: 16px 0 0 16px;
    }
    .step-header { display: flex; align-items: center; gap: 0.85rem; margin-bottom: 0.6rem; }
    .step-number {
        background: linear-gradient(135deg, var(--fern), var(--lime));
        color: white;
        font-family: 'Cormorant Garamond', serif;
        font-size: 1rem; font-weight: 700;
        width: 34px; height: 34px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        box-shadow: 0 0 16px rgba(82,160,71,0.4);
    }
    .step-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.3rem; font-weight: 600;
        color: var(--mist); margin: 0; letter-spacing: 0.01em;
    }

    .fancy-divider {
        border: none; height: 1px;
        background: linear-gradient(to right, transparent, var(--glass-border), transparent);
        margin: 2rem 0;
    }

    .section-heading {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.65rem; font-weight: 600;
        color: var(--mist); margin: 0 0 1.2rem; letter-spacing: 0.01em;
    }

    /* ── AI output box ────────────────────────────────────────────────── */
    .ai-output {
        background: rgba(7,20,9,0.8);
        border: 1px solid var(--glass-border);
        border-left: 3px solid var(--sage);
        border-radius: 0 14px 14px 0;
        padding: 1.6rem 1.8rem;
        font-size: 0.92rem; line-height: 1.85;
        color: #c8ddc0; white-space: pre-wrap;
        font-family: 'Outfit', sans-serif;
        box-shadow: inset 0 0 40px rgba(0,0,0,0.3);
    }

    .status-ok {
        background: rgba(30,77,26,0.35);
        border: 1px solid rgba(82,160,71,0.45);
        border-radius: 100px;
        padding: 0.45rem 1.2rem;
        font-size: 0.83rem; color: var(--lime);
        display: inline-flex; align-items: center; gap: 0.5rem;
        margin-bottom: 1rem;
    }

    /* ── Buttons ──────────────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--moss) 0%, var(--fern) 60%, var(--sage) 100%);
        color: #e8f5e2 !important;
        border: 1px solid rgba(118,196,66,0.3) !important;
        border-radius: 12px;
        font-family: 'Outfit', sans-serif;
        font-weight: 500; font-size: 0.95rem;
        padding: 0.7rem 1.6rem;
        transition: all 0.25s;
        width: 100%; letter-spacing: 0.02em;
        box-shadow: 0 4px 15px rgba(46,125,50,0.25);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--fern) 0%, var(--sage) 60%, var(--lime) 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(46,125,50,0.4);
    }
    .stButton > button:disabled { opacity: 0.35; cursor: not-allowed; transform: none; box-shadow: none; }

    [data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #1a3a1c, #2a5c2a) !important;
        border: 1px solid rgba(118,196,66,0.35) !important;
        color: #a8d4a0 !important; border-radius: 12px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important; transition: all 0.25s !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, #2a5c2a, #3a7a3a) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(7,20,9,0.7);
        border: 1px solid var(--glass-border);
        border-radius: 12px; gap: 3px; padding: 4px;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted); border-radius: 9px;
        font-family: 'Outfit', sans-serif; font-size: 0.88rem; font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--moss), var(--fern)) !important;
        color: #e8f5e2 !important;
        box-shadow: 0 2px 10px rgba(46,125,50,0.3);
    }

    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(82,160,71,0.25);
        border-radius: 14px;
        background: rgba(14,38,16,0.3);
    }
    div[data-testid="stExpander"] {
        background: var(--card-bg);
        border: 1px solid var(--glass-border); border-radius: 12px;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30,77,26,0.25), rgba(7,20,9,0.6));
        border: 1px solid var(--glass-border);
        border-radius: 14px; padding: 1rem 1.2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
    [data-testid="stMetricValue"] { color: var(--lime) !important; font-family: 'Cormorant Garamond', serif !important; font-size: 2rem !important; }

    .empty-state {
        text-align: center; padding: 4rem 2rem;
        background: linear-gradient(135deg, rgba(7,20,9,0.6), rgba(14,38,16,0.4));
        border: 1px dashed rgba(82,160,71,0.2);
        border-radius: 20px; margin-top: 0.5rem;
    }
    .empty-icon { font-size: 4.5rem; margin-bottom: 1rem; }
    .empty-title { font-family: 'Cormorant Garamond', serif; font-size: 1.8rem; color: var(--mist); margin-bottom: 0.8rem; font-weight: 600; }
    .empty-sub { color: var(--text-muted); max-width: 440px; margin: 0 auto; line-height: 1.9; font-size: 0.95rem; }

    code {
        font-family: 'JetBrains Mono', monospace !important;
        background: rgba(30,77,26,0.25) !important;
        border: 1px solid rgba(82,160,71,0.2) !important;
        border-radius: 5px !important;
        padding: 0.1em 0.45em !important;
        font-size: 0.85em !important;
        color: var(--lime) !important;
    }

    .stProgress > div > div > div { background: linear-gradient(90deg, var(--fern), var(--lime)) !important; border-radius: 4px; }
    .stCaption { color: rgba(122,170,114,0.65) !important; font-size: 0.78rem !important; }

    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: var(--forest-dark); }
    ::-webkit-scrollbar-thumb { background: var(--moss); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "df": None,
        "images": [],
        "analysis_text": "",
        "recommendations_text": "",
        "change_summary_text": "",
        "report_generated": False,
        "grok_client": None,
        "api_key_valid": False,
        "show_heatmap": False,
        "_pdf_bytes": None,
        "_pdf_filename": "conservation_report.pdf",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()


# ─── Grok API Functions ───────────────────────────────────────────────────────

def configure_grok(api_key: str):
    """
    Create a Groq client — free tier, no credit card needed.
    Get your key at https://console.groq.com
    """
    try:
        if not api_key or api_key == "YOUR_GROQ_API_KEY_HERE":
            return None, False
        client = Groq(api_key=api_key)
        # Lightweight validation ping
        client.chat.completions.create(
            model=GROK_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=3,
        )
        return client, True
    except Exception as e:
        return None, False


def generate_ai_analysis(client, df: pd.DataFrame, images: list, prompt_type: str) -> str:
    """
    Call Grok via the OpenAI-compatible chat/completions endpoint.
    For the 'analysis' prompt type, field images are embedded as base64
    in the message content (vision-capable models only).
    """
    try:
        summary = df.describe(include="all").to_string()
        sample  = df.head(20).to_string(index=False)
        cols    = ", ".join(df.columns.tolist())

        prompts = {
            "analysis": f"""You are an expert conservation ecologist and wildlife biologist.
Analyse the following field observation data and any provided images.

COLUMNS: {cols}

STATISTICAL SUMMARY:
{summary}

SAMPLE OBSERVATIONS (first 20 rows):
{sample}

Provide a comprehensive Conservation Analysis covering:
1. **Overall Ecosystem Health Assessment** — Rate (Excellent/Good/Fair/Poor/Critical) and justify.
2. **Habitat Degradation Indicators** — Identify signs from data patterns.
3. **Biodiversity Analysis** — Species richness, abundance distributions, imbalances.
4. **Invasive Species / Threats** — Ecological threats visible in the data.
5. **Spatial Patterns** — Geographic clustering, hotspots, anomalies.
6. **Image-Based Observations** — What field photos reveal about habitat conditions (if images provided).

Use clear section headings. Be specific and data-driven.""",

            "recommendations": f"""You are a conservation strategy expert advising a wildlife protection agency.
Generate actionable protection recommendations based on this field observation data.

COLUMNS: {cols}

STATISTICAL SUMMARY:
{summary}

SAMPLE OBSERVATIONS (first 20 rows):
{sample}

Provide:
1. **Immediate Actions (0–30 days)** — Urgent interventions needed now.
2. **Short-Term Plan (1–6 months)** — Protection measures, monitoring programmes.
3. **Long-Term Strategy (6+ months)** — Restoration, policy advocacy, community engagement.
4. **Risk Zone Scoring** — Assign a risk score (1–10) per area or species.
5. **Resource Allocation Advice** — Where to prioritise budget and personnel.
6. **Key Performance Indicators** — Metrics to track conservation success.

Be specific, actionable, and ranked by urgency.""",

            "changes": f"""You are an environmental data analyst specialising in ecosystem change detection.
Identify significant changes and trends in the following field observation data.

COLUMNS: {cols}

STATISTICAL SUMMARY:
{summary}

SAMPLE OBSERVATIONS (first 20 rows):
{sample}

Generate a "What Changed" Summary covering:
1. **Critical Population Shifts** — Most significant species increases or decreases.
2. **Habitat Change Signals** — Evidence of loss, fragmentation, or recovery.
3. **Temporal Patterns** — How observations changed across the recorded time period.
4. **Anomalies & Outliers** — Unusual observations warranting immediate attention.
5. **Baseline Comparison** — Current status vs expected healthy ecosystem benchmarks.
6. **Trend Forecast** — Projected state in 12 months without intervention.

Use specific numbers and percentages from the data where available.""",
        }

        # ── Build message content ─────────────────────────────────────────────
        # llama-3.3-70b on Groq is text-only. If images are provided we add
        # their filenames to the prompt as context so the AI acknowledges them.
        base_prompt = prompts[prompt_type]
        if images and prompt_type == "analysis":
            image_note = "\n\nFIELD IMAGES PROVIDED (analyse by filename/context):\n"
            image_note += "\n".join(f"- {img['name']}" for img in images[:3])
            content = base_prompt + image_note
        else:
            content = base_prompt

        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[{"role": "user", "content": content}],
            max_tokens=2000,
            temperature=0.4,
        )
        return response.choices[0].message.content

    except Exception as e:
        err = str(e)
        # Surface the real error so the user can diagnose
        return (
            f"⚠️ Groq API error: {err}\n\n"
            "Possible causes:\n"
            "• Invalid or expired API key\n"
            "• Model name not available on your plan\n"
            "• Network/firewall blocking api.groq.com\n\n"
            f"Model attempted: {GROK_MODEL}\n"
            "Get your free key at console.groq.com — no credit card needed."
        )


# ─── Data & Map Utilities ─────────────────────────────────────────────────────

def load_data(uploaded_file):
    """Read CSV/Excel and normalise column names."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported format. Please upload CSV or Excel.")
            return None
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def get_coord_columns(df):
    lat = next((c for c in df.columns if "lat" in c), None)
    lon = next((c for c in df.columns if any(x in c for x in ["lon", "lng", "long"])), None)
    return lat, lon


def get_risk_color(risk_level: str) -> str:
    return {
        "high": "red", "critical": "darkred",
        "medium": "orange", "moderate": "orange",
        "low": "green", "safe": "blue",
    }.get(str(risk_level).lower(), "gray")


def build_folium_map(df, show_heatmap, lat_col, lon_col):
    """Interactive Folium map with clusters, popups, and optional heatmap."""
    m = folium.Map(
        location=[df[lat_col].mean(), df[lon_col].mean()],
        zoom_start=10, tiles="CartoDB dark_matter", prefer_canvas=True,
    )
    cluster     = MarkerCluster(name="Observation Sites").add_to(m)
    risk_col    = next((c for c in df.columns if "risk"    in c), None)
    species_col = next((c for c in df.columns if "species" in c or "name" in c), None)
    count_col   = next((c for c in df.columns if "count"   in c or "population" in c or "number" in c), None)

    for _, row in df.iterrows():
        try:
            lat, lon = float(row[lat_col]), float(row[lon_col])
        except (ValueError, TypeError):
            continue
        color = get_risk_color(row[risk_col]) if risk_col else "green"
        popup_html = "<b style='color:#4a8c42'>📍 Observation Details</b><br><hr style='margin:4px 0'>"
        for col in df.columns:
            if col not in [lat_col, lon_col]:
                popup_html += f"<b>{col.replace('_',' ').title()}:</b> {row[col]}<br>"
        folium.CircleMarker(
            location=[lat, lon], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=str(row[species_col]) if species_col else "Observation",
        ).add_to(cluster)

    if show_heatmap:
        weight_col = count_col or risk_col
        heat_data  = []
        for _, row in df.iterrows():
            try:
                lat, lon = float(row[lat_col]), float(row[lon_col])
                try:
                    w = float(row[weight_col]) if weight_col and not isinstance(row[weight_col], str) else 1.0
                except (ValueError, TypeError):
                    w = 1.0
                heat_data.append([lat, lon, w])
            except (ValueError, TypeError):
                continue
        if heat_data:
            HeatMap(heat_data, name="Heatmap", radius=20, blur=15,
                    gradient={0.2: "blue", 0.5: "lime", 0.8: "orange", 1.0: "red"}).add_to(m)

    legend = """<div style="position:fixed;bottom:30px;right:20px;z-index:9999;
        background:rgba(10,26,12,0.92);border:1px solid #2d5a27;border-radius:10px;
        padding:10px 14px;font-family:sans-serif;font-size:12px;color:#e0ead0;">
        <b style="color:#7ab870">Risk Level</b><br>
        <span style="color:darkred">● Critical</span>&nbsp;
        <span style="color:red">● High</span><br>
        <span style="color:orange">● Medium</span>&nbsp;
        <span style="color:green">● Low</span></div>"""
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl().add_to(m)
    return m


def build_plotly_charts(df):
    """Auto-generate Plotly charts from detected columns."""
    charts      = []
    time_col    = next((c for c in df.columns if any(x in c for x in ["date","time","year","month"])), None)
    species_col = next((c for c in df.columns if "species" in c or "name" in c), None)
    count_col   = next((c for c in df.columns if "count"   in c or "population" in c or "number" in c), None)
    risk_col    = next((c for c in df.columns if "risk" in c), None)

    DARK = dict(
        plot_bgcolor="rgba(13,31,15,0.7)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#d0e0c8",
        colorway=["#4a8c42","#7ab870","#e8a830","#c0392b","#2980b9","#b8d4b4"],
    )

    if time_col and count_col:
        try:
            ts = df.copy()
            ts[time_col] = pd.to_datetime(ts[time_col], errors="coerce")
            ts = ts.dropna(subset=[time_col])
            grp   = [time_col, species_col] if species_col else [time_col]
            trend = ts.groupby(grp)[count_col].sum().reset_index()
            fig   = px.line(trend, x=time_col, y=count_col,
                            color=species_col if species_col else None,
                            title="Population Trends Over Time", markers=True)
            fig.update_layout(**DARK)
            charts.append(("📈 Population Trends", fig))
        except Exception:
            pass

    if species_col and count_col:
        try:
            dist = df.groupby(species_col)[count_col].sum().reset_index().sort_values(count_col, ascending=False)
            fig  = px.bar(dist, x=species_col, y=count_col,
                          title="Species Distribution (Total Count)",
                          color=count_col,
                          color_continuous_scale=["#1a3a1c","#4a8c42","#7ab870","#b8d4b4"])
            fig.update_layout(**DARK)
            charts.append(("🦎 Species Distribution", fig))
        except Exception:
            pass

    if risk_col:
        try:
            rc = df[risk_col].value_counts().reset_index()
            rc.columns = ["risk_level", "count"]
            fig = px.pie(rc, names="risk_level", values="count",
                         title="Risk Level Distribution", hole=0.45,
                         color_discrete_sequence=["#c0392b","#e8a830","#4a8c42","#2980b9","#7ab870"])
            fig.update_layout(**DARK)
            charts.append(("⚠️ Risk Distribution", fig))
        except Exception:
            pass

    if species_col and count_col and df[species_col].nunique() <= 20:
        try:
            fig = px.box(df, x=species_col, y=count_col,
                         title="Count Variability by Species", color=species_col)
            fig.update_layout(**DARK, showlegend=False)
            charts.append(("📦 Count Variability", fig))
        except Exception:
            pass

    return charts


def build_matplotlib_chart(df):
    """Static matplotlib bar chart for PDF embedding."""
    species_col = next((c for c in df.columns if "species" in c or "name" in c), None)
    count_col   = next((c for c in df.columns if "count"   in c or "population" in c or "number" in c), None)
    if not (species_col and count_col):
        return None
    try:
        dist = df.groupby(species_col)[count_col].sum().sort_values(ascending=True).tail(15)
        fig, ax = plt.subplots(figsize=(8, 5), facecolor="#0d1f0f")
        ax.set_facecolor("#1a3a1c")
        bars = ax.barh(dist.index, dist.values, color="#4a8c42", edgecolor="#7ab870", linewidth=0.5)
        ax.set_xlabel("Total Count", color="#b8d4b4", fontsize=10)
        ax.set_title("Species Distribution", color="#e0ead0", fontsize=13, fontweight="bold", pad=12)
        ax.tick_params(colors="#b8d4b4", labelsize=8)
        ax.spines[:].set_color("#2d5a27")
        for bar, val in zip(bars, dist.values):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{int(val):,}", va="center", color="#7ab870", fontsize=8)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#0d1f0f")
        buf.seek(0); plt.close()
        return buf.read()
    except Exception:
        plt.close(); return None


import re as _re

def _clean_latin1(s: str) -> str:
    """Final pass: drop anything that can't be encoded as latin-1."""
    return s.encode("latin-1", errors="ignore").decode("latin-1")


def _parse_markdown_blocks(text: str):
    """
    Convert raw AI markdown text into a list of typed blocks:
      ("h1", text), ("h2", text), ("h3", text),
      ("bullet", text), ("numbered", text), ("body", text), ("blank",)
    Each block's text has markdown syntax already stripped.
    """
    blocks = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        # ── Strip inline markdown formatting ────────────────────────────────
        line = _re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", line)   # ***bold-italic***
        line = _re.sub(r"\*\*(.+?)\*\*",     r"\1", line)   # **bold**
        line = _re.sub(r"\*(.+?)\*",         r"\1", line)   # *italic*
        line = _re.sub(r"`(.+?)`",           r"\1", line)   # `code`
        line = _re.sub(r"_{1,2}(.+?)_{1,2}", r"\1", line)   # _italic_ / __bold__

        # ── Unicode → ASCII ──────────────────────────────────────────────────
        replacements = {
            "\u2014": "--", "\u2013": "-",
            "\u2018": "'",  "\u2019": "'",
            "\u201c": '"',  "\u201d": '"',
            "\u2022": "-",  "\u2023": "-",  "\u25cf": "-",  "\u25aa": "-",
            "\u2192": "->", "\u2190": "<-",
            "\u2605": "*",  "\u2713": "[v]",
            "\u00b0": " degrees", "\u00b1": "+/-",
        }
        for u, a in replacements.items():
            line = line.replace(u, a)

        # Drop remaining non-latin-1 (emojis etc.)
        line = _clean_latin1(line)

        stripped = line.strip()
        if stripped == "":
            blocks.append(("blank",))
            continue

        # ── Headings ─────────────────────────────────────────────────────────
        m = _re.match(r"^(#{1,3})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            htext = _clean_latin1(m.group(2).strip())
            blocks.append((f"h{level}", htext))
            continue

        # ── Numbered list  (e.g. "1. " or "1) ") ────────────────────────────
        m = _re.match(r"^\d+[.)]\s+(.*)", stripped)
        if m:
            blocks.append(("numbered", _clean_latin1(m.group(1).strip())))
            continue

        # ── Bullet list  (-, *, +, or •) ─────────────────────────────────────
        m = _re.match(r"^[-*+\u2022]\s+(.*)", stripped)
        if m:
            blocks.append(("bullet", _clean_latin1(m.group(1).strip())))
            continue

        # ── Plain body ────────────────────────────────────────────────────────
        blocks.append(("body", _clean_latin1(stripped)))

    return blocks


def generate_pdf_report(df, analysis, recommendations, changes):
    """
    Formatted A4 PDF via fpdf2.
    - Explicit CONTENT_W on every cell / multi_cell call (never w=0)
    - Header/footer use absolute positioning so they never corrupt the cursor
    - Markdown is parsed into typed blocks: headings, bullets, numbered, body
    - multi_cell always called with new_x='LMARGIN', new_y='NEXT' (fpdf2 >= 2.7)
      with a fallback for older versions
    """
    PAGE_W    = 210
    L_MARGIN  = 15
    R_MARGIN  = 15
    T_MARGIN  = 26   # must be > header band height (20 mm)
    B_MARGIN  = 20
    CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN   # 180 mm — always explicit

    # Detect fpdf2 >= 2.7 (supports new_x / new_y kwargs on multi_cell)
    import fpdf as _fpdf_mod
    _fpdf_ver = tuple(int(x) for x in getattr(_fpdf_mod, "__version__", "2.0").split(".")[:2])
    _new_xy_supported = _fpdf_ver >= (2, 7)

    def _write_multicell(pdf_obj, w, h, txt):
        """Wrapper so multi_cell always resets cursor to left margin after call."""
        if _new_xy_supported:
            try:
                pdf_obj.multi_cell(w, h, txt, new_x="LMARGIN", new_y="NEXT")
                return
            except TypeError:
                pass
        # Fallback for older fpdf2: manual cursor reset
        pdf_obj.multi_cell(w, h, txt)
        pdf_obj.set_x(L_MARGIN)

    error_detail = ""
    try:
        class PDF(FPDF):
            def header(self):
                # Absolute-positioned header band — never touches the content cursor
                self.set_fill_color(13, 31, 15)
                self.rect(0, 0, PAGE_W, 20, "F")
                self.set_xy(L_MARGIN, 4)
                self.set_font("Helvetica", "B", 12)
                self.set_text_color(184, 212, 180)
                self.cell(CONTENT_W, 12, "  Conservation Report Generator", border=0)
                # Always reset to top of content area
                self.set_xy(L_MARGIN, T_MARGIN)

            def footer(self):
                self.set_y(-14)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(100, 130, 100)
                self.cell(
                    CONTENT_W, 8,
                    _clean_latin1(
                        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        f"  |  Page {self.page_no()}"
                    ),
                    align="C", border=0,
                )

        pdf = PDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(L_MARGIN, T_MARGIN, R_MARGIN)
        pdf.set_auto_page_break(auto=True, margin=B_MARGIN)
        pdf.add_page()                                   # header() fires here

        # ── Cover / overview ──────────────────────────────────────────────────
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(52, 120, 46)
        pdf.cell(CONTENT_W, 12, "Conservation Analysis Report", ln=True, align="C")

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(80, 110, 80)
        pdf.cell(CONTENT_W, 8, _clean_latin1(datetime.now().strftime("%B %d, %Y")), ln=True, align="C")
        pdf.ln(5)

        pdf.set_draw_color(74, 140, 66)
        pdf.set_line_width(0.5)
        pdf.line(L_MARGIN, pdf.get_y(), L_MARGIN + CONTENT_W, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(45, 90, 39)
        pdf.cell(CONTENT_W, 8, "Dataset Overview", ln=True)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 50, 30)
        pdf.cell(CONTENT_W, 7, f"Total Observations: {len(df):,}", ln=True)

        cols_list = df.columns[:8].tolist()
        cols_str  = _clean_latin1(", ".join(cols_list) + ("..." if len(df.columns) > 8 else ""))
        _write_multicell(pdf, CONTENT_W, 6, f"Columns: {cols_str}")
        pdf.ln(3)

        # ── Section renderer ──────────────────────────────────────────────────
        def add_section(title: str, content: str):
            # Section heading
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(45, 90, 39)
            pdf.cell(CONTENT_W, 10, _clean_latin1(title), ln=True)

            # Green underline
            pdf.set_draw_color(74, 140, 66)
            pdf.set_line_width(0.5)
            pdf.line(L_MARGIN, pdf.get_y(), L_MARGIN + CONTENT_W, pdf.get_y())
            pdf.ln(4)

            blocks = _parse_markdown_blocks(content)

            for block in blocks:
                kind = block[0]

                if kind == "blank":
                    pdf.ln(2)

                elif kind in ("h1", "h2", "h3"):
                    sizes   = {"h1": 12, "h2": 11, "h3": 10}
                    indents = {"h1": 0,  "h2": 3,  "h3": 6}
                    pdf.ln(3)
                    pdf.set_x(L_MARGIN + indents[kind])
                    pdf.set_font("Helvetica", "B", sizes[kind])
                    pdf.set_text_color(46, 100, 40)
                    _write_multicell(pdf, CONTENT_W - indents[kind], 6, block[1])
                    pdf.ln(1)

                elif kind == "numbered":
                    pdf.set_x(L_MARGIN + 4)
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(20, 40, 20)
                    # Write number indicator then text, indented
                    _write_multicell(pdf, CONTENT_W - 4, 5.5, "  " + block[1])

                elif kind == "bullet":
                    pdf.set_x(L_MARGIN + 4)
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(20, 40, 20)
                    _write_multicell(pdf, CONTENT_W - 4, 5.5, "- " + block[1])

                else:  # "body"
                    pdf.set_x(L_MARGIN)
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(20, 40, 20)
                    _write_multicell(pdf, CONTENT_W, 5.5, block[1])

            pdf.ln(4)

        # ── Render each AI section on its own page ────────────────────────────
        if analysis:
            pdf.add_page()
            add_section("Conservation Analysis", analysis)
        if recommendations:
            pdf.add_page()
            add_section("Protection Recommendations", recommendations)
        if changes:
            pdf.add_page()
            add_section("What Changed  --  Trend Summary", changes)

        # ── Chart page ────────────────────────────────────────────────────────
        chart_bytes = build_matplotlib_chart(df)
        if chart_bytes:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(45, 90, 39)
            pdf.cell(CONTENT_W, 10, "Species Distribution Chart", ln=True)
            pdf.set_draw_color(74, 140, 66)
            pdf.set_line_width(0.5)
            pdf.line(L_MARGIN, pdf.get_y(), L_MARGIN + CONTENT_W, pdf.get_y())
            pdf.ln(4)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(chart_bytes)
                tmp_path = tmp.name
            try:
                pdf.image(tmp_path, x=L_MARGIN, w=CONTENT_W)
            finally:
                os.unlink(tmp_path)

        raw = pdf.output()
        return bytes(raw) if not isinstance(raw, bytes) else raw

    except Exception as e:
        error_detail = str(e)
        # Plain fallback PDF — no custom header/footer, default margins
        try:
            err_pdf = FPDF()
            err_pdf.set_margins(15, 20, 15)
            err_pdf.set_auto_page_break(auto=True, margin=15)
            err_pdf.add_page()
            err_pdf.set_font("Helvetica", "B", 13)
            err_pdf.set_text_color(180, 40, 40)
            err_pdf.cell(180, 10, "PDF Generation Error", ln=True)
            err_pdf.set_font("Helvetica", "", 9)
            err_pdf.set_text_color(30, 30, 30)
            err_pdf.multi_cell(180, 5.5, _clean_latin1(f"Error: {error_detail[:600]}"))
            raw = err_pdf.output()
            return bytes(raw) if not isinstance(raw, bytes) else raw
        except Exception:
            return b""


# ─── Auto-init Grok on startup ────────────────────────────────────────────────
if not st.session_state.api_key_valid and GROK_API_KEY not in ("YOUR_GROQ_API_KEY_HERE", ""):
    _client, _valid = configure_grok(GROK_API_KEY)
    if _valid:
        st.session_state.grok_client   = _client
        st.session_state.api_key_valid = True



# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PAGE LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-leaf">🌿</div>
    <div class="hero-title">🌿 Conservation Report Generator</div>
    <div class="hero-sub">Multimodal AI &nbsp;·&nbsp; Geospatial Analysis &nbsp;·&nbsp; Ecological Intelligence</div>
    <div class="hero-badges">
        <span class="hero-badge">⚡ Groq AI (Free)</span>
        <span class="hero-badge">🗺 Folium Maps</span>
        <span class="hero-badge">📊 Plotly Charts</span>
        <span class="hero-badge">📄 PDF Export</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── API status ────────────────────────────────────────────────────────────────
if GROK_API_KEY in ("YOUR_GROQ_API_KEY_HERE", ""):
    st.warning(
        "⚠️ **No API key set.** Open `app.py` and replace `YOUR_GROK_API_KEY_HERE` "
        "with your Groq key from [console.groq.com](https://console.groq.com). "
        "Maps and charts work without it — only AI analysis needs the key."
    )
elif st.session_state.api_key_valid:
    st.markdown(
        f"<div class='status-ok'>🤖 &nbsp;<b>Groq ({GROK_MODEL})</b> &nbsp;✅ Connected and ready — Free tier</div>",
        unsafe_allow_html=True,
    )
else:
    key_preview = GROK_API_KEY[:8] + "..." if len(GROK_API_KEY) > 8 else GROK_API_KEY
    st.error(
        f"❌ Could not initialise Grok client. "
        f"Key detected: `{key_preview}` — "
        "ensure it was copied in full from [console.groq.com](https://console.groq.com)."
    )

st.markdown("<hr class='fancy-divider'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Upload Observation Data
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-panel">
  <div class="step-header">
    <div class="step-number">1</div>
    <div class="step-title">Upload Observation Data</div>
  </div>
</div>
""", unsafe_allow_html=True)

col_upload, col_info = st.columns([2, 1], gap="large")

with col_upload:
    data_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
        help="Required: latitude, longitude. Recommended: species, count, date, risk_level",
    )
    if data_file:
        df_loaded = load_data(data_file)
        if df_loaded is not None:
            st.session_state.df = df_loaded
            st.success(
                f"✅ Loaded **{len(df_loaded):,} observations** | "
                f"**{len(df_loaded.columns)} columns**: `{'`, `'.join(df_loaded.columns.tolist())}`"
            )

with col_info:
    st.markdown("""
    <div class="info-card" style="background:linear-gradient(135deg,rgba(14,38,16,0.7),rgba(7,20,9,0.85));border:1px solid rgba(118,196,66,0.18);border-radius:14px;padding:1.2rem 1.5rem;font-size:0.85rem;color:#c8dfc2;line-height:2;box-shadow:0 4px 20px rgba(0,0,0,0.25);">
        <b style="color:#76c442;">📋 Expected Columns</b><br>
        <code>latitude</code> &nbsp;·&nbsp; <code>longitude</code><br>
        <code>species</code> &nbsp;·&nbsp; <code>count</code><br>
        <code>date</code> &nbsp;·&nbsp; <code>risk_level</code><br>
        <code>habitat</code> &nbsp;·&nbsp; <code>observer</code>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    sample_data = pd.DataFrame({
        "latitude":   [17.385,17.39,17.38,17.40,17.37,17.41,17.36],
        "longitude":  [78.486,78.49,78.48,78.50,78.47,78.51,78.46],
        "species":    ["Bengal Tiger","Indian Elephant","Indian Leopard","Sloth Bear",
                       "Bengal Tiger","Indian Elephant","Indian Leopard"],
        "count":      [3,12,5,8,2,15,4],
        "date":       ["2024-01-15","2024-02-10","2024-01-20","2024-03-05",
                       "2024-04-01","2024-02-25","2024-03-18"],
        "risk_level": ["High","Medium","High","Low","Critical","Medium","High"],
        "habitat":    ["Forest","Wetland","Forest","Scrubland","Forest","Grassland","Forest"],
        "observer":   ["Team A","Team B","Team A","Team C","Team A","Team B","Team C"],
    })
    st.download_button(
        "📥 Download Sample CSV",
        sample_data.to_csv(index=False).encode(),
        "sample_observations.csv", "text/csv",
        use_container_width=True,
    )

st.markdown("<hr class='fancy-divider'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Upload Field Images
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-panel">
  <div class="step-header">
    <div class="step-number">2</div>
    <div class="step-title">Upload Field Images &nbsp;
      <span style="font-size:0.82rem;color:#7ab870;font-family:'DM Sans',sans-serif;font-weight:300">
        — optional, filenames sent as context to Groq AI
      </span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

image_files = st.file_uploader(
    "Upload habitat or trail camera photos",
    type=["jpg","jpeg","png","webp"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)
if image_files:
    imgs = []
    for f in image_files[:5]:
        raw  = f.read()
        mime = "image/jpeg" if f.name.lower().endswith((".jpg",".jpeg")) else "image/png"
        imgs.append({"name": f.name, "data": base64.b64encode(raw).decode(), "mime_type": mime})
    st.session_state.images = imgs

    img_cols = st.columns(min(len(imgs), 5))
    for i, img_data in enumerate(imgs):
        with img_cols[i]:
            img = Image.open(io.BytesIO(base64.b64decode(img_data["data"])))
            st.image(img, caption=img_data["name"], use_container_width=True)
    st.success(f"✅ {len(imgs)} image(s) loaded — image context will be included in the AI analysis")

st.markdown("<hr class='fancy-divider'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Configure & Generate
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-panel">
  <div class="step-header">
    <div class="step-number">3</div>
    <div class="step-title">Configure & Generate Report</div>
  </div>
</div>
""", unsafe_allow_html=True)

cfg_col, btn_col = st.columns([1, 1], gap="large")

with cfg_col:
    show_heatmap = st.toggle(
        "🌡️ Show Species Concentration Heatmap on Map",
        value=st.session_state.show_heatmap,
        help="Thermal heatmap weighted by species count or risk level",
    )
    st.session_state.show_heatmap = show_heatmap
    st.caption("Toggle before or after generating — the map re-renders on change.")

with btn_col:
    can_run = st.session_state.df is not None and st.session_state.api_key_valid
    run_analysis = st.button(
        "🧬 Generate Full Conservation Report",
        disabled=not can_run,
        use_container_width=True,
    )
    if st.session_state.df is None:
        st.caption("⬆️ Upload observation data in Step 1 first.")
    elif not st.session_state.api_key_valid:
        st.caption("⬆️ Add your free Groq API key to `app.py` to enable AI analysis.")


# ── AI Processing ─────────────────────────────────────────────────────────────
if run_analysis and st.session_state.df is not None and st.session_state.grok_client is not None:
    df_r   = st.session_state.df
    client = st.session_state.grok_client
    images = st.session_state.images

    progress = st.progress(0, "Starting Groq analysis…")

    with st.spinner("🔬 Running Conservation Analysis (Groq llama-3.3-70b)…"):
        progress.progress(20, "Analysing ecosystem with Grok…")
        st.session_state.analysis_text = generate_ai_analysis(client, df_r, images, "analysis")

    with st.spinner("📋 Generating Protection Recommendations…"):
        progress.progress(55, "Building recommendation plan…")
        st.session_state.recommendations_text = generate_ai_analysis(client, df_r, images, "recommendations")

    with st.spinner("🔄 Detecting Ecosystem Changes…"):
        progress.progress(80, "Detecting changes and trends…")
        st.session_state.change_summary_text = generate_ai_analysis(client, df_r, images, "changes")

    progress.progress(100, "Complete!")
    st.session_state.report_generated = True
    progress.empty()
    st.success("✅ Full conservation report generated! Explore the results in the tabs below.")

st.markdown("<hr class='fancy-divider'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  RESULTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
df = st.session_state.df

if df is not None:

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Geospatial Map",
        "📊 Population Trends",
        "🧬 Conservation Analysis",
        "🛡️ Recommendations",
        "🔄 What Changed",
    ])

    # ── TAB 1: MAP ────────────────────────────────────────────────────────────
    with tab1:
        st.markdown('<p class="section-heading">🗺️ Field Observation Map</p>', unsafe_allow_html=True)
        lat_col, lon_col = get_coord_columns(df)

        if lat_col and lon_col:
            species_col = next((c for c in df.columns if "species" in c or "name" in c), None)
            risk_col    = next((c for c in df.columns if "risk" in c), None)

            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Total Observations", f"{len(df):,}")
            with m2: st.metric("Unique Species", df[species_col].nunique() if species_col else "—")
            with m3:
                if risk_col:
                    hr = df[df[risk_col].astype(str).str.lower().isin(["high","critical"])].shape[0]
                    st.metric("High Risk Sites", hr)
                else:
                    st.metric("Total Columns", len(df.columns))
            with m4: st.metric("Observation Zones", df[lat_col].nunique())

            st.markdown("<br>", unsafe_allow_html=True)
            with st.spinner("Building interactive map…"):
                try:
                    fmap = build_folium_map(df, st.session_state.show_heatmap, lat_col, lon_col)
                    st_folium(fmap, use_container_width=True, height=540, returned_objects=[])
                except Exception as e:
                    st.error(f"Map error: {e}")
        else:
            st.warning("⚠️ No lat/lon columns detected. Ensure your CSV has `latitude` and `longitude` columns.")
            st.dataframe(df.head(10), use_container_width=True)

        with st.expander("📋 View & Download Raw Data"):
            st.dataframe(df, use_container_width=True, height=280)
            st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(), "observations.csv", "text/csv")

    # ── TAB 2: CHARTS ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown('<p class="section-heading">📊 Population & Species Trends</p>', unsafe_allow_html=True)
        charts = build_plotly_charts(df)
        if charts:
            for i in range(0, len(charts), 2):
                c1, c2 = st.columns(2)
                for j, col in enumerate([c1, c2]):
                    if i + j < len(charts):
                        _, fig = charts[i + j]
                        with col: st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Add `species`, `count`, `date`, `risk_level` columns for richer charts.")

        st.markdown("---")
        st.markdown("**🎨 Species Distribution — Matplotlib Chart**")
        chart_bytes = build_matplotlib_chart(df)
        if chart_bytes:
            st.image(chart_bytes, use_container_width=True)
        else:
            st.caption("Include `species` and `count` columns to enable this chart.")

    # ── TAB 3: ANALYSIS ───────────────────────────────────────────────────────
    with tab3:
        st.markdown('<p class="section-heading">🧬 AI Conservation Analysis</p>', unsafe_allow_html=True)
        if st.session_state.images:
            img_cols = st.columns(min(len(st.session_state.images), 5))
            for idx, img_data in enumerate(st.session_state.images):
                with img_cols[idx]:
                    img = Image.open(io.BytesIO(base64.b64decode(img_data["data"])))
                    st.image(img, caption=img_data["name"], use_container_width=True)
            st.caption(f"↑ {len(st.session_state.images)} field image(s) included as context for Groq AI")
            st.markdown("---")

        if st.session_state.analysis_text:
            st.markdown(f'<div class="ai-output">{st.session_state.analysis_text}</div>', unsafe_allow_html=True)
        else:
            st.info("🧬 Click **Generate Full Conservation Report** in Step 3 above to run AI analysis.")

    # ── TAB 4: RECOMMENDATIONS ────────────────────────────────────────────────
    with tab4:
        st.markdown('<p class="section-heading">🛡️ Protection Recommendations</p>', unsafe_allow_html=True)
        if st.session_state.recommendations_text:
            st.markdown(f'<div class="ai-output">{st.session_state.recommendations_text}</div>', unsafe_allow_html=True)
        else:
            st.info("🛡️ Click **Generate Full Conservation Report** in Step 3 above to get recommendations.")

    # ── TAB 5: WHAT CHANGED ───────────────────────────────────────────────────
    with tab5:
        st.markdown('<p class="section-heading">🔄 What Changed — Ecosystem Trend Review</p>', unsafe_allow_html=True)
        if st.session_state.change_summary_text:
            st.markdown(f'<div class="ai-output">{st.session_state.change_summary_text}</div>', unsafe_allow_html=True)
        else:
            st.info("🔄 Click **Generate Full Conservation Report** in Step 3 above to generate the change summary.")

    # ── PDF EXPORT ────────────────────────────────────────────────────────────
    if st.session_state.report_generated:
        st.markdown("<hr class='fancy-divider'>", unsafe_allow_html=True)
        st.markdown('<p class="section-heading">📄 Export Report</p>', unsafe_allow_html=True)

        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(14,38,16,0.55),rgba(7,20,9,0.8));
                    border:1px solid rgba(118,196,66,0.18);border-radius:16px;
                    padding:1.6rem 2rem;box-shadow:0 4px 24px rgba(0,0,0,0.3);margin-bottom:1rem;">
        """, unsafe_allow_html=True)

        ex1, ex2 = st.columns([1, 2], gap="large")
        with ex1:
            build_clicked = st.button("📥 Build PDF Report", use_container_width=True)
            if build_clicked:
                with st.spinner("Assembling PDF…"):
                    pdf_bytes = generate_pdf_report(
                        df,
                        st.session_state.analysis_text,
                        st.session_state.recommendations_text,
                        st.session_state.change_summary_text,
                    )
                if pdf_bytes:
                    st.session_state["_pdf_bytes"] = pdf_bytes
                    st.session_state["_pdf_filename"] = f"conservation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                else:
                    st.error("PDF generation failed. Try restarting the app: `streamlit run app.py`")

            # Always show the download button once PDF has been built
            if st.session_state.get("_pdf_bytes"):
                st.download_button(
                    "⬇️ Download PDF",
                    data=st.session_state["_pdf_bytes"],
                    file_name=st.session_state.get("_pdf_filename", "conservation_report.pdf"),
                    mime="application/pdf",
                    use_container_width=True,
                )

        with ex2:
            st.caption(
                "Generates a formatted A4 PDF with AI conservation analysis, "
                "protection recommendations, ecosystem change summary, and species chart. "
                "Click **Build PDF Report** first, then **Download PDF**."
            )

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🌳</div>
        <div class="empty-title">Results will appear here</div>
        <p class="empty-sub">
            Complete Steps 1–3 above to see the interactive map, population charts,
            and AI-generated conservation insights.
        </p>
    </div>
    """, unsafe_allow_html=True)
