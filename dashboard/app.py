# =============================================================================
# DASHBOARD EJECUTIVO DE RIESGO POR IDENTIDAD SINTÉTICA
# Detección de Fraude con Neo4j + Streamlit + Plotly
# =============================================================================
# Ejecución:
#   1) pip install -r requirements.txt
#   2) streamlit run app.py
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import sys

# =============================================================================
# CONFIGURACIÓN DE PÁGINA — debe ser la primera llamada a Streamlit
# =============================================================================
st.set_page_config(
    page_title="Dashboard de Riesgo | Identidad Sintética",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# PALETA FINTECH — colores coherentes en todo el dashboard
# =============================================================================
COLORS = {
    "ALTO":   "#E63946",   # rojo alerta
    "MEDIO":  "#F4A261",   # naranja precaución
    "BAJO":   "#2A9D8F",   # verde seguro
    "accent": "#1D3557",   # azul marino principal
    "accent2":"#457B9D",   # azul medio
    "bg":     "#F8F9FA",   # fondo claro
    "card":   "#FFFFFF",
    "text":   "#1D3557",
    "muted":  "#6C757D",
}

RISK_COLOR_MAP = {
    "ALTO":  COLORS["ALTO"],
    "MEDIO": COLORS["MEDIO"],
    "BAJO":  COLORS["BAJO"],
}

PLOTLY_TEMPLATE = "plotly_white"

# =============================================================================
# CSS PERSONALIZADO — estilo fintech limpio
# =============================================================================
st.markdown("""
<style>
    /* Fuente global */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #1D3557;
    }

    /* Encabezado principal */
    .main-header {
        background: linear-gradient(135deg, #1D3557 0%, #457B9D 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
        color: white;
    }
    .main-header p {
        font-size: 0.95rem;
        opacity: 0.85;
        margin: 0;
        color: white;
    }

    /* Tarjetas KPI */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 1.3rem 1.5rem;
        border-left: 4px solid #457B9D;
        box-shadow: 0 2px 8px rgba(29,53,87,0.08);
        height: 100%;
    }
    .kpi-card.alto  { border-left-color: #E63946; }
    .kpi-card.medio { border-left-color: #F4A261; }
    .kpi-card.bajo  { border-left-color: #2A9D8F; }
    .kpi-card.neutral { border-left-color: #457B9D; }

    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: #6C757D;
        margin-bottom: 0.4rem;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1D3557;
        line-height: 1;
        font-family: 'IBM Plex Mono', monospace;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #6C757D;
        margin-top: 0.3rem;
    }

    /* Secciones */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1D3557;
        letter-spacing: 0.3px;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #E9ECEF;
        margin-bottom: 1rem;
    }

    /* Alerta interpretativa */
    .insight-box {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        font-size: 0.88rem;
        color: #1D3557;
        line-height: 1.6;
    }
    .insight-box strong { color: #1D3557; }

    /* Badge de riesgo */
    .badge-alto  { background:#FFEEF0; color:#E63946; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; }
    .badge-medio { background:#FFF4E6; color:#F4A261; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; }
    .badge-bajo  { background:#E6F7F5; color:#2A9D8F; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; }

    /* Sidebar */
    .css-1d391kg { background-color: #1D3557; }
    section[data-testid="stSidebar"] { background-color: #1D3557; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stMultiSelect label { color: #A8C5DA !important; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }

    /* Tabla */
    .dataframe { font-size: 0.83rem; }

    /* Ocultar menú hamburguesa */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CONEXIÓN A NEO4J
# =============================================================================

NEO4J_URI      = "bolt://127.0.0.1:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "12345678"   # <-- cambia esto


@st.cache_resource(show_spinner=False)
def get_driver():
    """Crea y devuelve el driver de Neo4j (singleton por sesión de Streamlit)."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        return driver
    except AuthError:
        st.error("Error de autenticación con Neo4j. Verifica usuario y contraseña en app.py.")
        st.stop()
    except ServiceUnavailable:
        st.error(
            "No se pudo conectar a Neo4j. "
            "Asegúrate de que Neo4j esté corriendo en bolt://localhost:7687."
        )
        st.stop()
    except Exception as e:
        st.error(f"Error inesperado al conectar con Neo4j: {e}")
        st.stop()


def run_query(driver, query: str, params: dict = None) -> pd.DataFrame:
    """
    Ejecuta una consulta Cypher y devuelve un DataFrame.
    Maneja errores sin interrumpir el dashboard.
    """
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            records = [dict(r) for r in result]
            return pd.DataFrame(records) if records else pd.DataFrame()
    except Exception as e:
        st.warning(f"Consulta no disponible: {e}")
        return pd.DataFrame()


# =============================================================================
# CONSULTAS CYPHER
# =============================================================================

Q_KPIS = """
MATCH (p:Persona)
RETURN
  count(p)                                                              AS total_clientes,
  sum(CASE WHEN p.risk_level = 'ALTO'  THEN 1 ELSE 0 END)             AS alto_riesgo,
  sum(CASE WHEN p.risk_level = 'MEDIO' THEN 1 ELSE 0 END)             AS medio_riesgo,
  sum(CASE WHEN p.risk_level = 'BAJO'  THEN 1 ELSE 0 END)             AS bajo_riesgo,
  round(avg(p.risk_score), 2)                                           AS score_promedio,
  count(DISTINCT CASE WHEN p.risk_level = 'ALTO' THEN p.community_id END) AS comunidades_sospechosas
"""

Q_DISTRIBUCION = """
MATCH (p:Persona)
WHERE p.risk_level IS NOT NULL
RETURN p.risk_level AS nivel_riesgo, count(*) AS total
ORDER BY total DESC
"""

Q_TOP_N = """
MATCH (p:Persona)
WHERE ($nivel = 'TODOS' OR p.risk_level = $nivel)
RETURN
  p.id_persona      AS id_persona,
  p.nombre + ' ' + coalesce(p.apellido_paterno,'') + ' ' + coalesce(p.apellido_materno,'') AS nombre,
  p.risk_score      AS risk_score,
  p.risk_level      AS risk_level,
  p.risk_tel        AS risk_tel,
  p.risk_device     AS risk_device,
  p.risk_ip         AS risk_ip,
  p.risk_dom        AS risk_dom,
  p.similarity_flag AS similarity_flag,
  p.community_id    AS community_id,
  p.es_fraude       AS es_fraude
ORDER BY risk_score DESC
LIMIT $top_n
"""

Q_FACTORES = """
MATCH (p:Persona)
WHERE ($nivel = 'TODOS' OR p.risk_level = $nivel)
RETURN
  round(avg(p.risk_tel),    2) AS Telefono,
  round(avg(p.risk_device), 2) AS Dispositivo,
  round(avg(p.risk_ip),     2) AS IP,
  round(avg(p.risk_dom),    2) AS Domicilio
"""

Q_COMUNIDADES = """
MATCH (p:Persona)
WHERE p.community_id IS NOT NULL
WITH p.community_id AS community_id,
     count(*)                                                          AS total_personas,
     sum(CASE WHEN p.risk_level = 'ALTO' THEN 1 ELSE 0 END)           AS alto_riesgo,
     round(avg(p.risk_score), 2)                                        AS score_promedio
WHERE total_personas > 1
RETURN community_id, total_personas, alto_riesgo, score_promedio
ORDER BY alto_riesgo DESC, score_promedio DESC
LIMIT 15
"""

Q_FRAUDE_REAL = """
MATCH (p:Persona)
WHERE p.es_fraude IS NOT NULL AND p.risk_level IS NOT NULL
RETURN
  p.es_fraude  AS es_fraude,
  p.risk_level AS nivel_riesgo,
  count(*)     AS total
ORDER BY es_fraude DESC, nivel_riesgo
"""

Q_TIMELINE = """
MATCH (p:Persona)-[:REALIZA]->(s:Solicitud)
WHERE p.risk_level IS NOT NULL AND s.fecha_solicitud IS NOT NULL
RETURN
  toString(s.fecha_solicitud) AS fecha,
  p.risk_level               AS nivel_riesgo,
  count(*)                   AS total
ORDER BY fecha
"""

Q_SCORE_COMUNIDAD = """
MATCH (p:Persona)
WHERE p.community_id IS NOT NULL
WITH p.community_id AS community_id,
     round(avg(p.risk_score), 2) AS score_promedio,
     count(*) AS total
WHERE total > 1
RETURN community_id, score_promedio, total
ORDER BY score_promedio DESC
LIMIT 12
"""

Q_DETALLE_PERSONA = """
MATCH (p:Persona {id_persona: $id_persona})
OPTIONAL MATCH (p)-[:TIENE_TELEFONO]->(t:Telefono)
OPTIONAL MATCH (p)-[:TIENE_CORREO]->(c:Correo)
OPTIONAL MATCH (p)-[:DECLARA_DOMICILIO]->(d:Domicilio)
OPTIONAL MATCH (p)-[:REALIZA]->(s:Solicitud)-[:USA_DISPOSITIVO]->(dev:Dispositivo)
OPTIONAL MATCH (p)-[:REALIZA]->(s2:Solicitud)-[:SE_ORIGINA_EN]->(ip:IP)
RETURN
  p.id_persona      AS id_persona,
  p.nombre          AS nombre,
  p.apellido_paterno AS ap,
  p.risk_score      AS risk_score,
  p.risk_level      AS risk_level,
  p.community_id    AS community_id,
  p.es_fraude       AS es_fraude,
  t.numero          AS telefono,
  c.email           AS correo,
  d.calle + ' ' + coalesce(d.colonia,'') AS domicilio,
  dev.id_dispositivo AS dispositivo,
  ip.direccion_ip   AS ip
LIMIT 1
"""

Q_CONEXIONES_PERSONA = """
MATCH (p:Persona {id_persona: $id_persona})-[:TIENE_TELEFONO]->(t:Telefono)
      <-[:TIENE_TELEFONO]-(otros:Persona)
WHERE p <> otros
RETURN 'Telefono' AS tipo_atributo, otros.id_persona AS id_vinculado,
       otros.risk_level AS nivel_riesgo_vinculado, otros.risk_score AS score_vinculado

UNION

MATCH (p:Persona {id_persona: $id_persona})-[:DECLARA_DOMICILIO]->(d:Domicilio)
      <-[:DECLARA_DOMICILIO]-(otros:Persona)
WHERE p <> otros
RETURN 'Domicilio' AS tipo_atributo, otros.id_persona AS id_vinculado,
       otros.risk_level AS nivel_riesgo_vinculado, otros.risk_score AS score_vinculado

UNION

MATCH (p:Persona {id_persona: $id_persona})-[:REALIZA]->(:Solicitud)-[:USA_DISPOSITIVO]->(dev:Dispositivo)
      <-[:USA_DISPOSITIVO]-(:Solicitud)<-[:REALIZA]-(otros:Persona)
WHERE p <> otros
RETURN 'Dispositivo' AS tipo_atributo, otros.id_persona AS id_vinculado,
       otros.risk_level AS nivel_riesgo_vinculado, otros.risk_score AS score_vinculado

UNION

MATCH (p:Persona {id_persona: $id_persona})-[:REALIZA]->(:Solicitud)-[:SE_ORIGINA_EN]->(ip:IP)
      <-[:SE_ORIGINA_EN]-(:Solicitud)<-[:REALIZA]-(otros:Persona)
WHERE p <> otros
RETURN 'IP' AS tipo_atributo, otros.id_persona AS id_vinculado,
       otros.risk_level AS nivel_riesgo_vinculado, otros.risk_score AS score_vinculado
"""


# =============================================================================
# HELPERS DE GRÁFICOS
# =============================================================================

def chart_distribucion(df: pd.DataFrame) -> go.Figure:
    """Gráfico de dona: distribución de clientes por nivel de riesgo."""
    if df.empty:
        return None
    colors = [RISK_COLOR_MAP.get(n, "#CCC") for n in df["nivel_riesgo"]]
    fig = go.Figure(go.Pie(
        labels=df["nivel_riesgo"],
        values=df["total"],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#FFF", width=2)),
        textinfo="label+percent",
        textfont=dict(size=13, family="IBM Plex Sans"),
        hovertemplate="<b>%{label}</b><br>Clientes: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        annotations=[dict(
            text=f"<b>{df['total'].sum()}</b><br>clientes",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=15, color=COLORS["accent"], family="IBM Plex Mono"),
        )],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_top_n(df: pd.DataFrame, metrica: str, top_n: int) -> go.Figure:
    """Barras horizontales: top N clientes por métrica seleccionada."""
    if df.empty or metrica not in df.columns:
        return None
    dfs = df.nlargest(top_n, metrica)[["id_persona", "nombre", metrica, "risk_level"]].copy()
    dfs["nombre_corto"] = dfs["nombre"].str.strip().str[:28]
    colors = [RISK_COLOR_MAP.get(r, "#CCC") for r in dfs["risk_level"]]
    fig = go.Figure(go.Bar(
        x=dfs[metrica],
        y=dfs["nombre_corto"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="rgba(0,0,0,0)")),
        text=dfs[metrica].round(1),
        textposition="outside",
        textfont=dict(size=11, family="IBM Plex Mono"),
        hovertemplate="<b>%{y}</b><br>%{x}<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=max(280, top_n * 38),
        margin=dict(t=10, b=10, l=10, r=60),
        xaxis_title=metrica.replace("_", " ").title(),
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_factores(df: pd.DataFrame) -> go.Figure:
    """Barras verticales: promedio de cada factor de riesgo."""
    if df.empty:
        return None
    factores = ["Telefono", "Dispositivo", "IP", "Domicilio"]
    pesos    = [2, 3, 2, 1]   # referencia visual (pesos del score)
    valores  = [df.iloc[0].get(f, 0) for f in factores]
    colores  = [COLORS["ALTO"] if v == max(valores) else COLORS["accent2"] for v in valores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=factores, y=valores,
        marker=dict(color=colores, line=dict(color="rgba(0,0,0,0)")),
        text=[f"{v:.2f}" for v in valores],
        textposition="outside",
        textfont=dict(size=12, family="IBM Plex Mono"),
        hovertemplate="<b>%{x}</b><br>Promedio: %{y:.2f}<extra></extra>",
        name="Promedio",
    ))
    # línea de pesos para contexto
    fig.add_trace(go.Scatter(
        x=factores, y=pesos,
        mode="markers+lines",
        line=dict(color=COLORS["MEDIO"], dash="dot", width=1.5),
        marker=dict(size=6, color=COLORS["MEDIO"]),
        name="Peso en score",
        hovertemplate="Peso: %{y}<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=280,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_comunidades(df: pd.DataFrame) -> go.Figure:
    """Barras agrupadas: comunidades sospechosas."""
    if df.empty:
        return None
    df = df.copy()
    df["community_id"] = df["community_id"].astype(str)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df["community_id"], y=df["total_personas"],
        name="Total clientes",
        marker=dict(color=COLORS["accent2"], opacity=0.7),
        hovertemplate="Grupo %{x}<br>Clientes: %{y}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df["community_id"], y=df["alto_riesgo"],
        name="Alertas ALTO riesgo",
        marker=dict(color=COLORS["ALTO"]),
        hovertemplate="Grupo %{x}<br>Alertas: %{y}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["community_id"], y=df["score_promedio"],
        mode="lines+markers",
        name="Score promedio",
        line=dict(color=COLORS["MEDIO"], width=2),
        marker=dict(size=7),
        hovertemplate="Grupo %{x}<br>Score: %{y}<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        barmode="overlay",
        height=320,
        margin=dict(t=10, b=30, l=10, r=10),
        legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_yaxes(title_text="Clientes",     secondary_y=False)
    fig.update_yaxes(title_text="Score prom.",  secondary_y=True)
    return fig


def chart_fraude_real(df: pd.DataFrame) -> go.Figure:
    """Barras apiladas: fraude real vs nivel de riesgo detectado."""
    if df.empty:
        return None
    df = df.copy()
    df["es_fraude"] = df["es_fraude"].map({1: "Fraude real", 0: "Cliente legítimo"})
    pivot = df.pivot_table(index="es_fraude", columns="nivel_riesgo",
                           values="total", aggfunc="sum", fill_value=0)
    fig = go.Figure()
    for nivel, color in RISK_COLOR_MAP.items():
        if nivel in pivot.columns:
            fig.add_trace(go.Bar(
                name=nivel,
                x=pivot.index,
                y=pivot[nivel],
                marker_color=color,
                hovertemplate=f"<b>{nivel}</b><br>%{{x}}: %{{y}}<extra></extra>",
            ))
    fig.update_layout(
        barmode="stack",
        template=PLOTLY_TEMPLATE,
        height=280,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_timeline(df: pd.DataFrame) -> go.Figure:
    """Líneas temporales: solicitudes por fecha y nivel de riesgo."""
    if df.empty:
        return None
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    fig = go.Figure()
    for nivel, color in RISK_COLOR_MAP.items():
        sub = df[df["nivel_riesgo"] == nivel].sort_values("fecha")
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub["fecha"], y=sub["total"],
                mode="lines+markers",
                name=nivel,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{nivel}</b><br>%{{x|%d %b %Y}}: %{{y}} solicitudes<extra></extra>",
            ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=280,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Fecha de solicitud",
        yaxis_title="Solicitudes",
    )
    return fig


def chart_score_comunidad(df: pd.DataFrame) -> go.Figure:
    """Bubble chart: score promedio vs tamaño de comunidad."""
    if df.empty:
        return None
    df = df.copy()
    df["community_id"] = df["community_id"].astype(str)
    fig = go.Figure(go.Scatter(
        x=df["community_id"],
        y=df["score_promedio"],
        mode="markers+text",
        marker=dict(
            size=df["total"] * 8,
            color=df["score_promedio"],
            colorscale=[[0, COLORS["BAJO"]], [0.5, COLORS["MEDIO"]], [1, COLORS["ALTO"]]],
            showscale=True,
            colorbar=dict(title="Score", thickness=12, len=0.6),
            line=dict(color="white", width=1.5),
        ),
        text=df["total"].astype(str) + " cli.",
        textposition="top center",
        textfont=dict(size=10),
        hovertemplate="<b>Grupo %{x}</b><br>Score prom.: %{y}<br>Clientes: %{text}<extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=300,
        margin=dict(t=10, b=30, l=10, r=80),
        xaxis_title="Grupo sospechoso (community_id)",
        yaxis_title="Score de riesgo promedio",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# =============================================================================
# HELPERS DE INTERPRETACIÓN EJECUTIVA
# =============================================================================

def texto_interpretacion(kpis: dict, df_factores: pd.DataFrame, df_comunidades: pd.DataFrame) -> str:
    """Genera un párrafo de interpretación ejecutiva automática."""
    partes = []

    pct = kpis.get("pct_alto", 0)
    if pct >= 20:
        partes.append(f"<strong>Alerta crítica:</strong> el {pct:.1f}% de los clientes analizados presenta nivel de riesgo ALTO, lo que requiere revisión inmediata del equipo antifraude.")
    elif pct >= 5:
        partes.append(f"El {pct:.1f}% de los clientes presenta nivel de riesgo ALTO. Se recomienda priorizar su investigación.")
    else:
        partes.append(f"Solo el {pct:.1f}% de los clientes tiene nivel de riesgo ALTO. El portafolio muestra un perfil de riesgo controlado.")

    if not df_factores.empty:
        row = df_factores.iloc[0]
        factores = {"Teléfono": row.get("Telefono", 0), "Dispositivo": row.get("Dispositivo", 0),
                    "IP": row.get("IP", 0), "Domicilio": row.get("Domicilio", 0)}
        dominante = max(factores, key=factores.get)
        partes.append(f"El factor de riesgo con mayor incidencia promedio es <strong>{dominante}</strong>, lo que sugiere reutilización de {dominante.lower()} entre múltiples clientes como patrón principal de alerta.")

    if not df_comunidades.empty and df_comunidades["alto_riesgo"].sum() > 0:
        n_grupos = (df_comunidades["alto_riesgo"] > 0).sum()
        top_grupo = df_comunidades.iloc[0]["community_id"]
        partes.append(f"Se identificaron <strong>{n_grupos} grupo(s) sospechoso(s)</strong> con clientes de alto riesgo. El grupo de mayor prioridad es el <strong>grupo {top_grupo}</strong>; se recomienda iniciar la investigación por ahí.")

    return " ".join(partes)


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar(driver) -> dict:
    """Renderiza el sidebar y devuelve los filtros seleccionados."""
    with st.sidebar:
        st.markdown("## 🛡 Filtros de análisis")
        st.markdown("---")

        nivel = st.selectbox(
            "Nivel de riesgo",
            options=["TODOS", "ALTO", "MEDIO", "BAJO"],
            index=0,
        )

        # Comunidades disponibles
        df_com = run_query(driver, "MATCH (p:Persona) WHERE p.community_id IS NOT NULL RETURN DISTINCT p.community_id AS cid ORDER BY cid")
        if df_com.empty:
            st.info("community_id no disponible.\nEjecuta Louvain en Neo4j.")
            comunidades_disponibles = []
        else:
            comunidades_disponibles = sorted(df_com["cid"].dropna().unique().tolist())

        comunidad_sel = st.multiselect(
            "Grupos sospechosos (community_id)",
            options=comunidades_disponibles,
            default=[],
            placeholder="Todos los grupos",
        )

        metrica = st.selectbox(
            "Métrica principal del ranking",
            options=["risk_score", "risk_tel", "risk_device", "risk_ip", "risk_dom"],
            index=0,
            format_func=lambda x: {
                "risk_score":  "Score de riesgo total",
                "risk_tel":    "Riesgo por teléfono",
                "risk_device": "Riesgo por dispositivo",
                "risk_ip":     "Riesgo por IP",
                "risk_dom":    "Riesgo por domicilio",
            }.get(x, x),
        )

        top_n = st.slider("Top N clientes en ranking", min_value=5, max_value=50, value=15, step=5)

        st.markdown("---")
        st.markdown("**Acerca de este dashboard**")
        st.markdown(
            "<span style='font-size:0.78rem;opacity:0.8'>"
            "Monitoreo de clientes con posible fraude de identidad sintética. "
            "Los grupos sospechosos agrupan clientes que comparten teléfono, "
            "dispositivo, IP o domicilio."
            "</span>",
            unsafe_allow_html=True,
        )

    return {
        "nivel": nivel,
        "comunidades": comunidad_sel,
        "metrica": metrica,
        "top_n": top_n,
    }


# =============================================================================
# SECCIÓN: KPIs
# =============================================================================

def render_kpis(kpis: dict):
    """Renderiza los 5 KPIs principales en una fila."""
    total    = int(kpis.get("total_clientes", 0))
    alto     = int(kpis.get("alto_riesgo", 0))
    medio    = int(kpis.get("medio_riesgo", 0))
    bajo     = int(kpis.get("bajo_riesgo", 0))
    score_p  = round(float(kpis.get("score_promedio", 0)), 1)
    grupos_s = int(kpis.get("comunidades_sospechosas", 0))
    pct      = round(alto / total * 100, 1) if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card neutral">
            <div class="kpi-label">Clientes analizados</div>
            <div class="kpi-value">{total:,}</div>
            <div class="kpi-sub">Base total</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card alto">
            <div class="kpi-label">Alertas críticas</div>
            <div class="kpi-value">{alto:,}</div>
            <div class="kpi-sub">Nivel ALTO · {pct}% del total</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card medio">
            <div class="kpi-label">En revisión</div>
            <div class="kpi-value">{medio:,}</div>
            <div class="kpi-sub">Nivel MEDIO</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card neutral">
            <div class="kpi-label">Score promedio</div>
            <div class="kpi-value">{score_p}</div>
            <div class="kpi-sub">De toda la base</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card alto">
            <div class="kpi-label">Grupos sospechosos</div>
            <div class="kpi-value">{grupos_s}</div>
            <div class="kpi-sub">Con alertas ALTO</div>
        </div>""", unsafe_allow_html=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    driver  = get_driver()
    filtros = render_sidebar(driver)

    nivel  = filtros["nivel"]
    metrica = filtros["metrica"]
    top_n   = filtros["top_n"]
    comunidades_sel = filtros["comunidades"]

    # --- ENCABEZADO ---
    st.markdown("""
    <div class="main-header">
        <h1>Dashboard Ejecutivo de Riesgo por Identidad Sintética</h1>
        <p>Monitoreo de clientes, grupos sospechosos y factores de riesgo · Fintech Antifraude</p>
    </div>
    """, unsafe_allow_html=True)

    # --- CARGA DE DATOS ---
    with st.spinner("Cargando datos desde Neo4j..."):
        df_kpis_raw     = run_query(driver, Q_KPIS)
        df_dist         = run_query(driver, Q_DISTRIBUCION)
        df_top          = run_query(driver, Q_TOP_N, {"nivel": nivel, "top_n": top_n})
        df_factores     = run_query(driver, Q_FACTORES, {"nivel": nivel})
        df_comunidades  = run_query(driver, Q_COMUNIDADES)
        df_fraude_real  = run_query(driver, Q_FRAUDE_REAL)
        df_timeline     = run_query(driver, Q_TIMELINE)
        df_score_com    = run_query(driver, Q_SCORE_COMUNIDAD)

    # Verificar scoring
    if df_kpis_raw.empty or df_kpis_raw.iloc[0].get("total_clientes", 0) == 0:
        st.error("No se encontraron datos de Persona en Neo4j. Verifica que el grafo esté cargado.")
        st.stop()

    kpis_row = df_kpis_raw.iloc[0].to_dict()
    total = int(kpis_row.get("total_clientes", 0))
    alto  = int(kpis_row.get("alto_riesgo", 0))
    kpis_row["pct_alto"] = round(alto / total * 100, 1) if total else 0

    if df_dist.empty:
        st.warning(
            "No se encontró la propiedad `risk_level` en los nodos Persona. "
            "Ejecuta primero las consultas de scoring en Neo4j (ver documentación)."
        )

    # Filtrar por comunidad si se seleccionó alguna
    if comunidades_sel and not df_top.empty and "community_id" in df_top.columns:
        df_top = df_top[df_top["community_id"].isin(comunidades_sel)]

    # =========================================================================
    # KPIs
    # =========================================================================
    render_kpis(kpis_row)
    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # TABS PRINCIPALES
    # =========================================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "Panorama general",
        "Grupos sospechosos",
        "Clientes prioritarios",
        "Investigación de caso",
    ])

    # =========================================================
    # TAB 1 — PANORAMA GENERAL
    # =========================================================
    with tab1:
        col_a, col_b = st.columns([1, 1.6], gap="large")

        with col_a:
            st.markdown('<div class="section-title">Distribución por nivel de riesgo</div>', unsafe_allow_html=True)
            fig_dist = chart_distribucion(df_dist)
            if fig_dist:
                st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos de distribución.")

        with col_b:
            st.markdown('<div class="section-title">Factores de riesgo promedio · Filtro actual</div>', unsafe_allow_html=True)
            fig_fact = chart_factores(df_factores)
            if fig_fact:
                st.plotly_chart(fig_fact, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos de factores.")

        st.markdown("<br>", unsafe_allow_html=True)

        col_c, col_d = st.columns(2, gap="large")

        with col_c:
            st.markdown('<div class="section-title">Fraude real vs nivel de riesgo detectado</div>', unsafe_allow_html=True)
            fig_fr = chart_fraude_real(df_fraude_real)
            if fig_fr:
                st.plotly_chart(fig_fr, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos de validación (es_fraude).")

        with col_d:
            st.markdown('<div class="section-title">Solicitudes por fecha y nivel de riesgo</div>', unsafe_allow_html=True)
            fig_time = chart_timeline(df_timeline)
            if fig_time:
                st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos de fecha de solicitud.")

        # Interpretación ejecutiva
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Interpretación ejecutiva</div>', unsafe_allow_html=True)
        texto = texto_interpretacion(kpis_row, df_factores, df_comunidades)
        st.markdown(f'<div class="insight-box">{texto}</div>', unsafe_allow_html=True)

    # =========================================================
    # TAB 2 — GRUPOS SOSPECHOSOS
    # =========================================================
    with tab2:
        if df_comunidades.empty:
            st.warning(
                "No se encontró `community_id` en los nodos Persona. "
                "Ejecuta el algoritmo Louvain en Neo4j GDS primero."
            )
        else:
            col_e, col_f = st.columns([1.4, 1], gap="large")

            with col_e:
                st.markdown('<div class="section-title">Grupos con mayor concentración de alertas</div>', unsafe_allow_html=True)
                fig_com = chart_comunidades(df_comunidades)
                if fig_com:
                    st.plotly_chart(fig_com, use_container_width=True, config={"displayModeBar": False})

            with col_f:
                st.markdown('<div class="section-title">Score de riesgo por grupo</div>', unsafe_allow_html=True)
                fig_sc = chart_score_comunidad(df_score_com)
                if fig_sc:
                    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">Detalle de grupos sospechosos</div>', unsafe_allow_html=True)

            df_com_display = df_comunidades.copy()
            df_com_display.columns = ["Grupo", "Total clientes", "Alertas ALTO", "Score promedio"]
            df_com_display["Prioridad"] = df_com_display.apply(
                lambda r: "🔴 Crítica" if r["Alertas ALTO"] >= 4
                          else ("🟡 Media" if r["Alertas ALTO"] >= 1 else "🟢 Baja"),
                axis=1,
            )
            st.dataframe(
                df_com_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Score promedio": st.column_config.ProgressColumn(
                        "Score promedio", min_value=0, max_value=40, format="%.1f"
                    ),
                    "Alertas ALTO": st.column_config.NumberColumn("Alertas ALTO", help="Clientes con riesgo ALTO en este grupo"),
                },
            )

            st.markdown("<br>", unsafe_allow_html=True)
            top_grupo = df_comunidades.iloc[0]["community_id"] if not df_comunidades.empty else "N/A"
            st.markdown(
                f'<div class="insight-box">'
                f'Los grupos sospechosos representan clientes que comparten teléfono, dispositivo, '
                f'IP o domicilio entre sí — una señal característica del fraude de identidad sintética coordinado. '
                f'El <strong>grupo {top_grupo}</strong> concentra el mayor número de alertas y debe ser '
                f'la primera prioridad de investigación.'
                f'</div>',
                unsafe_allow_html=True,
            )

    # =========================================================
    # TAB 3 — CLIENTES PRIORITARIOS
    # =========================================================
    with tab3:
        col_g, col_h = st.columns([1.2, 1], gap="large")

        with col_g:
            st.markdown(f'<div class="section-title">Top {top_n} clientes · Métrica: {metrica}</div>', unsafe_allow_html=True)
            fig_top = chart_top_n(df_top, metrica, top_n)
            if fig_top:
                st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos para el ranking.")

        with col_h:
            st.markdown('<div class="section-title">Resumen ejecutivo de factores</div>', unsafe_allow_html=True)
            if not df_factores.empty:
                row = df_factores.iloc[0]
                factores_disp = {
                    "Teléfono compartido":   row.get("Telefono", 0),
                    "Dispositivo compartido": row.get("Dispositivo", 0),
                    "IP compartida":         row.get("IP", 0),
                    "Domicilio compartido":  row.get("Domicilio", 0),
                }
                max_val = max(factores_disp.values()) if factores_disp else 1
                for factor, val in factores_disp.items():
                    pct_bar = int(val / max_val * 100) if max_val else 0
                    color = COLORS["ALTO"] if val == max_val else COLORS["accent2"]
                    st.markdown(f"""
                    <div style="margin-bottom:14px">
                        <div style="font-size:0.8rem;font-weight:600;color:{COLORS['text']};margin-bottom:4px">{factor}</div>
                        <div style="background:#E9ECEF;border-radius:6px;height:10px;overflow:hidden">
                            <div style="background:{color};width:{pct_bar}%;height:100%;border-radius:6px;transition:width 0.4s"></div>
                        </div>
                        <div style="font-size:0.75rem;color:{COLORS['muted']};margin-top:2px">Promedio: <b style='font-family:IBM Plex Mono'>{val:.2f}</b></div>
                    </div>
                    """, unsafe_allow_html=True)

        # Tabla completa
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tabla de clientes prioritarios</div>', unsafe_allow_html=True)

        if not df_top.empty:
            df_tabla = df_top.copy()

            # Formatear columna es_fraude
            if "es_fraude" in df_tabla.columns:
                df_tabla["es_fraude"] = df_tabla["es_fraude"].map({1: "Sí", 0: "No", None: "—"}).fillna("—")

            st.dataframe(
                df_tabla.rename(columns={
                    "id_persona":    "ID",
                    "nombre":        "Nombre completo",
                    "risk_score":    "Score",
                    "risk_level":    "Nivel",
                    "risk_tel":      "Tel.",
                    "risk_device":   "Disp.",
                    "risk_ip":       "IP",
                    "risk_dom":      "Dom.",
                    "similarity_flag": "Sim.",
                    "community_id":  "Grupo",
                    "es_fraude":     "¿Fraude real?",
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Score", min_value=0, max_value=40, format="%d"
                    ),
                    "Nivel": st.column_config.TextColumn("Nivel"),
                    "¿Fraude real?": st.column_config.TextColumn("¿Fraude real?"),
                },
                height=420,
            )
            st.caption(f"Mostrando {len(df_tabla)} clientes · Filtro: {nivel} · Métrica: {metrica}")
        else:
            st.info("No se encontraron clientes con los filtros aplicados.")

    # =========================================================
    # TAB 4 — INVESTIGACIÓN DE CASO
    # =========================================================
    with tab4:
        st.markdown('<div class="section-title">Investigación individual de cliente</div>', unsafe_allow_html=True)

        # Selector de persona
        ids_disponibles = []
        if not df_top.empty and "id_persona" in df_top.columns:
            ids_disponibles = df_top["id_persona"].dropna().tolist()

        id_input = st.selectbox(
            "Selecciona un cliente para investigar",
            options=ids_disponibles if ids_disponibles else [""],
            index=0,
            help="Los IDs mostrados corresponden a los clientes del ranking actual.",
        )

        if id_input and id_input != "":
            df_det = run_query(driver, Q_DETALLE_PERSONA, {"id_persona": id_input})
            df_con = run_query(driver, Q_CONEXIONES_PERSONA, {"id_persona": id_input})

            if not df_det.empty:
                d = df_det.iloc[0]
                nivel_col = RISK_COLOR_MAP.get(str(d.get("risk_level", "")), COLORS["muted"])

                col_i, col_j = st.columns([1, 1.5], gap="large")

                with col_i:
                    st.markdown(f"""
                    <div style="background:white;border-radius:10px;padding:1.4rem;
                                box-shadow:0 2px 8px rgba(29,53,87,0.08);border-top:4px solid {nivel_col}">
                        <div style="font-size:1.1rem;font-weight:700;color:{COLORS['text']};margin-bottom:0.8rem">
                            {d.get('nombre','—')} {d.get('ap','')}
                        </div>
                        <table style="width:100%;font-size:0.85rem;border-collapse:collapse">
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">ID</td>
                                <td style="font-family:'IBM Plex Mono';font-weight:600">{d.get('id_persona','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Nivel de riesgo</td>
                                <td><span style="background:{nivel_col}22;color:{nivel_col};
                                    padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.8rem">
                                    {d.get('risk_level','—')}</span></td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Score</td>
                                <td style="font-family:'IBM Plex Mono';font-weight:700;font-size:1.1rem;color:{nivel_col}">
                                    {d.get('risk_score','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Grupo</td>
                                <td>{d.get('community_id','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">¿Fraude real?</td>
                                <td>{'Sí' if d.get('es_fraude')==1 else 'No'}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Teléfono</td>
                                <td style="font-family:'IBM Plex Mono'">{d.get('telefono','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Correo</td>
                                <td>{d.get('correo','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Domicilio</td>
                                <td>{d.get('domicilio','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">Dispositivo</td>
                                <td style="font-family:'IBM Plex Mono'">{d.get('dispositivo','—')}</td></tr>
                            <tr><td style="color:{COLORS['muted']};padding:4px 0">IP</td>
                                <td style="font-family:'IBM Plex Mono'">{d.get('ip','—')}</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                with col_j:
                    st.markdown('<div class="section-title">Clientes vinculados por atributo compartido</div>', unsafe_allow_html=True)

                    if df_con.empty:
                        st.success("Este cliente no comparte atributos con otros clientes. Bajo riesgo relacional.")
                    else:
                        df_con_display = df_con.rename(columns={
                            "tipo_atributo":         "Atributo compartido",
                            "id_vinculado":          "Cliente vinculado",
                            "nivel_riesgo_vinculado":"Nivel de riesgo",
                            "score_vinculado":       "Score",
                        })
                        st.dataframe(
                            df_con_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Score": st.column_config.ProgressColumn(
                                    "Score", min_value=0, max_value=40, format="%d"
                                ),
                            },
                        )
                        n_vic = len(df_con)
                        tipos = df_con["tipo_atributo"].unique().tolist()
                        st.markdown(
                            f'<div class="insight-box" style="margin-top:1rem">'
                            f'Este cliente comparte atributos con <strong>{n_vic} cliente(s)</strong> más. '
                            f'Los atributos en común son: <strong>{", ".join(tipos)}</strong>. '
                            f'Esta red de vínculos es la principal señal de alerta para este caso.'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.warning(f"No se encontraron datos para el cliente {id_input}.")

    # =========================================================================
    # PIE DE PÁGINA
    # =========================================================================
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:center;font-size:0.75rem;color:{COLORS['muted']};padding:1rem 0'>"
        "Dashboard Antifraude · Identidad Sintética · Neo4j + Streamlit · "
        "Los datos mostrados provienen directamente del grafo de propiedades."
        "</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    main()
