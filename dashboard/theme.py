"""Tema visual do dashboard comercial Danone."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

.main .block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}

.hero {
    background: linear-gradient(135deg, #1A2B4A 0%, #2E86AB 100%);
    border-radius: 16px;
    padding: 2rem 2.2rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(26, 43, 74, 0.18);
}
.hero h1 { color: white !important; font-size: 1.85rem; margin: 0 0 0.4rem 0; font-weight: 700; }
.hero p  { color: rgba(255,255,255,0.85); margin: 0; font-size: 1rem; }

.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #E9ECEF;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    height: 100%;
}
.kpi-label { font-size: 0.78rem; color: #6C757D; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
.kpi-value { font-size: 1.55rem; font-weight: 700; color: #1A2B4A; margin: 0.3rem 0; }
.kpi-delta-pos { color: #1B5E20; font-weight: 600; font-size: 0.95rem; }
.kpi-delta-neg { color: #BF5700; font-weight: 600; font-size: 0.95rem; }

.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1A2B4A;
    margin: 1.8rem 0 0.8rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid #2E86AB;
    display: inline-block;
}

.insight-box {
    background: #F8F9FA;
    border-left: 4px solid #2E86AB;
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.92rem;
    color: #2C3E50;
}
.insight-box.pos { border-left-color: #1B5E20; background: #E8F5E9; }
.insight-box.neg { border-left-color: #BF5700; background: #FFF3E0; }

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

[data-testid="stSidebar"] {
    background: #F8F9FA;
    border-right: 1px solid #DEE2E6;
}
</style>
"""

CORES = {
    "navy": "#1A2B4A",
    "teal": "#2E86AB",
    "green": "#1B5E20",
    "orange": "#BF5700",
    "gray": "#6C7A89",
    "light": "#F8F9FA",
}

PALETA_REGIAO = ["#1A2B4A", "#2E86AB", "#4ECDC4", "#45B7D1", "#96CEB4"]
