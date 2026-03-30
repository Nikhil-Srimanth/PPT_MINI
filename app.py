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
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    :root {
        --forest-dark: #0d1f0f;
        --forest-mid: #1a3a1c;
        --moss:  #2d5a27;
        --fern:  #4a8c42;
        --sage:  #7ab870;
        --mist:  #b8d4b4;
        --amber: #e8a830;
        --danger:#c0392b;
        --card-bg: rgba(255,255,255,0.04);
        --border:  rgba(122,184,112,0.2);
    }

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .stApp {
        background: linear-gradient(160deg, #0d1f0f 0%, #1a3a1c 50%, #0a1a0c 100%);
        color: #e0ead0;
    }

    [data-testid="collapsedControl"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }

    /* ── Hero ─────────────────────────────────────────────────────────── */
    .hero {
        background: linear-gradient(135deg, rgba(45,90,39,0.5) 0%, rgba(13,31,15,0.9) 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 3rem 3.5rem;
        margin-bottom: 2.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: '🌿';
        position: absolute;
        right: 3rem; top: 50%;
        transform: translateY(-50%);
        font-size: 7rem;
        opacity: 0.12;
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem; font-weight: 700;
        color: var(--mist); margin: 0 0 0.4rem 0; line-height: 1.2;
    }
    .hero-sub  { color: var(--sage); font-size: 1.05rem; font-weight: 300; letter-spacing: 0.03em; }
    .hero-badge {
        display: inline-block;
        background: rgba(74,140,66,0.2);
        border: 1px solid rgba(122,184,112,0.4);
        border-radius: 20px;
        padding: 0.2rem 0.9rem;
        font-size: 0.78rem; color: var(--sage);
        margin-top: 1rem; margin-right: 0.5rem;
    }

    /* ── Step panels ──────────────────────────────────────────────────── */
    .step-panel {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.2rem 1.8rem 0.4rem 1.8rem;
        margin-bottom: 0.8rem;
    }
    .step-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
    .step-number {
        background: linear-gradient(135deg, var(--moss), var(--fern));
        color: white;
        font-family: 'Playfair Display', serif;
        font-size: 1rem; font-weight: 700;
        width: 32px; height: 32px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .step-title { font-family: 'Playfair Display', serif; font-size: 1.25rem; color: var(--mist); margin: 0; }

    .fancy-divider { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }

    .section-heading {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem; color: var(--mist); margin: 0 0 1.2rem 0;
    }

    /* ── AI output box ────────────────────────────────────────────────── */
    .ai-output {
        background: rgba(13,31,15,0.7);
        border-left: 3px solid var(--fern);
        border-radius: 0 10px 10px 0;
        padding: 1.4rem 1.6rem;
        font-size: 0.95rem; line-height: 1.8;
        color: #d0e0c8; white-space: pre-wrap;
    }

    .status-ok {
        background: rgba(45,90,39,0.3);
        border: 1px solid #4a8c42;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem; color: #7ab870;
        display: inline-block; margin-bottom: 1rem;
    }

    /* ── Buttons ──────────────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--moss), var(--fern));
        color: white !important; border: none;
        border-radius: 10px;
        font-family: 'DM Sans', sans-serif; font-weight: 500; font-size: 1rem;
        padding: 0.65rem 1.6rem;
        transition: all 0.2s ease; width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--fern), var(--sage));
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(74,140,66,0.35);
    }
    .stButton > button:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(13,31,15,0.6);
        border-radius: 10px; gap: 4px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"]  { color: var(--mist); border-radius: 7px; }
    .stTabs [aria-selected="true"] { background: var(--moss) !important; color: white !important; }

    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border);
        border-radius: 10px;
        background: rgba(45,90,39,0.06);
    }
    div[data-testid="stExpander"] {
        background: var(--card-bg);
        border: 1px solid var(--border); border-radius: 10px;
    }
    [data-testid="stMetric"] {
        background: rgba(45,90,39,0.2);
        border: 1px solid var(--border); border-radius: 10px; padding: 0.8rem 1rem;
    }
    ::-webkit-scrollbar { width: 6px; }
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


def generate_pdf_report(df, analysis, recommendations, changes):
    """Formatted A4 PDF via fpdf2."""
    try:
        class PDF(FPDF):
            def header(self):
                self.set_fill_color(13, 31, 15); self.rect(0, 0, 210, 20, "F")
                self.set_font("Helvetica", "B", 13); self.set_text_color(184, 212, 180)
                self.cell(0, 18, "  Conservation Report Generator", ln=True)
            def footer(self):
                self.set_y(-15); self.set_font("Helvetica", "I", 8); self.set_text_color(120, 140, 120)
                self.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Page {self.page_no()}", align="C")

        pdf = PDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18); pdf.set_margins(18, 22, 18); pdf.add_page()

        pdf.set_font("Helvetica", "B", 22); pdf.set_text_color(74, 140, 66); pdf.ln(10)
        pdf.cell(0, 12, "Conservation Analysis Report", ln=True, align="C")
        pdf.set_font("Helvetica", "", 11); pdf.set_text_color(100, 130, 100)
        pdf.cell(0, 8, datetime.now().strftime("%B %d, %Y"), ln=True, align="C"); pdf.ln(8)

        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(45, 90, 39)
        pdf.cell(0, 9, "Dataset Overview", ln=True)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(40, 60, 40)
        pdf.cell(0, 7, f"Total Observations: {len(df):,}", ln=True)
        pdf.cell(0, 7, f"Columns: {', '.join(df.columns[:8].tolist())}{'...' if len(df.columns)>8 else ''}", ln=True)
        pdf.ln(5)

        def add_section(title, content):
            pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(45, 90, 39)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_draw_color(74, 140, 66); pdf.set_line_width(0.4)
            pdf.line(18, pdf.get_y(), 192, pdf.get_y()); pdf.ln(3)
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(30, 50, 30)
            pdf.multi_cell(0, 5.5, content.replace("**","").replace("##","").replace("*","-"))
            pdf.ln(6)

        if analysis:      pdf.add_page(); add_section("Conservation Analysis",        analysis)
        if recommendations: pdf.add_page(); add_section("Protection Recommendations", recommendations)
        if changes:       pdf.add_page(); add_section("What Changed — Trend Summary", changes)

        chart_bytes = build_matplotlib_chart(df)
        if chart_bytes:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(45, 90, 39)
            pdf.cell(0, 10, "Species Distribution Chart", ln=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(chart_bytes); tmp_path = tmp.name
            pdf.image(tmp_path, x=18, w=174); os.unlink(tmp_path)

        return bytes(pdf.output())
    except Exception as e:
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
    <div class="hero-title">🌿 Conservation Report Generator</div>
    <div class="hero-sub">Multimodal AI · Geospatial Analysis · Ecological Intelligence</div>
    <div style="margin-top:1rem">
        <span class="hero-badge">Groq AI (Free)</span>
        <span class="hero-badge">Folium Maps</span>
        <span class="hero-badge">Plotly Charts</span>
        <span class="hero-badge">PDF Export</span>
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
    <div style="background:rgba(45,90,39,0.15);border:1px solid var(--border);
                border-radius:10px;padding:1rem 1.2rem;font-size:0.85rem;color:#b8d4b4;line-height:1.9">
        <b style="color:#7ab870">📋 Expected Columns</b><br>
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

        ex1, ex2 = st.columns([1, 2], gap="large")
        with ex1:
            if st.button("📥 Build PDF Report", use_container_width=True):
                with st.spinner("Assembling PDF…"):
                    pdf_bytes = generate_pdf_report(
                        df,
                        st.session_state.analysis_text,
                        st.session_state.recommendations_text,
                        st.session_state.change_summary_text,
                    )
                if pdf_bytes:
                    st.download_button(
                        "⬇️ Download PDF", data=pdf_bytes,
                        file_name=f"conservation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf", use_container_width=True,
                    )
                else:
                    st.error(f"PDF generation failed. Try restarting the app: `streamlit run app.py`")
        with ex2:
            st.caption(
                "Generates a formatted A4 PDF with AI conservation analysis, "
                "protection recommendations, ecosystem change summary, and species chart."
            )

else:
    st.markdown("""
    <div style="text-align:center;padding:3rem 2rem;background:rgba(255,255,255,0.02);
                border:1px dashed var(--border);border-radius:14px;margin-top:0.5rem">
        <div style="font-size:4rem;margin-bottom:1rem">🌳</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.6rem;color:var(--mist);margin-bottom:0.8rem">
            Results will appear here
        </div>
        <p style="color:#7ab870;max-width:480px;margin:0 auto;line-height:1.8;font-size:0.95rem">
            Complete Steps 1–3 above to see the interactive map, population charts,
            and AI-generated conservation insights.
        </p>
    </div>
    """, unsafe_allow_html=True)