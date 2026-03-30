# 🌿 Conservation Report Generator

A **multimodal AI-powered Streamlit application** for environmental conservation analysis.  
Upload field observation data (CSV/Excel) and habitat photos — Gemini 1.5 Pro analyses them together to generate a full conservation intelligence report.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📂 **Data Ingestion** | CSV / Excel upload with auto column detection |
| 📸 **Image Analysis** | Upload field photos analysed by Gemini Vision |
| 🗺️ **Interactive Map** | Folium map with colour-coded markers, popups, and clustering |
| 🌡️ **Heatmap Layer** | Toggle species concentration / risk heatmap |
| 📈 **Population Trends** | Plotly line, bar, pie, box charts |
| 🧬 **AI Conservation Analysis** | Gemini 1.5 Pro ecosystem health assessment |
| 🛡️ **Protection Recommendations** | Immediate, short-term, and long-term action plans |
| 🔄 **What Changed** | Trend detection vs. ecological baselines |
| 📄 **PDF Export** | Download a formatted stakeholder-ready PDF report |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Configure
- Enter your **Gemini API key** in the sidebar (get one at https://aistudio.google.com)
- Upload your observation **CSV/Excel** file
- Optionally upload **field photos** (JPG/PNG)
- Click **Generate Full Report**

---

## 📋 CSV Format

Your CSV/Excel file should include these columns (names are flexible — the app auto-detects them):

| Column | Required | Description |
|---|---|---|
| `latitude` | ✅ | Decimal degrees (e.g., 17.385) |
| `longitude` | ✅ | Decimal degrees (e.g., 78.486) |
| `species` | Recommended | Species name |
| `count` | Recommended | Observation count / population |
| `date` | Recommended | ISO date (YYYY-MM-DD) |
| `risk_level` | Recommended | high / medium / low / critical |
| `habitat` | Optional | Habitat type |
| `observer` | Optional | Field team name |

A sample CSV is available for download inside the app.

---

## 📁 Project Structure

```
conservation_report/
├── app.py              # Main Streamlit application (single-file, modular)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🛠️ Key Modules

- **`configure_gemini()`** — API key validation and model initialisation
- **`load_data()`** — Robust CSV/Excel loader with normalised column names
- **`build_folium_map()`** — Interactive map with clustering, popups, heatmap layer
- **`build_plotly_charts()`** — Auto-generates charts based on detected column types
- **`generate_ai_analysis()`** — Multimodal Gemini API calls (text + images)
- **`build_matplotlib_chart()`** — Matplotlib chart for PDF embedding
- **`generate_pdf_report()`** — Full stakeholder PDF using fpdf2

---

## 🔑 API Key

Get a free Gemini API key at: **https://aistudio.google.com/app/apikey**

The key is entered securely via Streamlit's `st.text_input(type="password")` and is never stored.

---

## 📦 Dependencies

- `streamlit` — Web UI framework  
- `google-generativeai` — Gemini 1.5 Pro API  
- `folium` + `streamlit-folium` — Interactive geospatial maps  
- `pandas` — Data manipulation  
- `plotly` — Interactive charts  
- `matplotlib` — Static charts for PDF  
- `Pillow` — Image processing  
- `openpyxl` — Excel file support  
- `fpdf2` — PDF generation  
