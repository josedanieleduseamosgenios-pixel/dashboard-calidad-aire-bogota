"""
Dashboard de Calidad del Aire en Bogotá
Usuario objetivo: profesional de la Subdirección de Calidad del Aire,
Auditiva y Visual (SCAAV) - Secretaría Distrital de Ambiente.

Para correr: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import re

st.set_page_config(page_title="Calidad del Aire - Bogotá", page_icon="🌫️", layout="wide")

ACCENT = "#3FA7D6"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Título principal */
    h1 {{
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }}
    h1 + div p {{
        font-size: 1rem !important;
        opacity: 0.85;
    }}

    /* Tarjetas de métricas (st.metric) */
    div[data-testid="stMetric"] {{
        background-color: #161B26;
        border: 1px solid #262E3D;
        border-left: 4px solid {ACCENT};
        border-radius: 10px;
        padding: 14px 18px 10px 18px;
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 0.85rem !important;
        opacity: 0.75;
    }}
    div[data-testid="stMetricValue"] {{
        font-weight: 700 !important;
    }}

    /* Caja de "Recomendación" (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 12px !important;
        border-left: 5px solid {ACCENT} !important;
    }}

    /* Pestañas */
    button[data-baseweb="tab"] {{
        font-size: 1.02rem;
        font-weight: 600;
        padding-top: 10px;
        padding-bottom: 10px;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {ACCENT} !important;
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {ACCENT} !important;
    }}

    /* Subtítulos de sección (st.subheader) */
    h3 {{
        font-weight: 700 !important;
        margin-top: 0.4rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

LIMITE_ANUAL_PM10 = 50    # µg/m3, Res. 2254/2017
LIMITE_DIARIO_PM10 = 75   # µg/m3, Res. 2254/2017

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    # Colapsa cualquier espacio duplicado o invisible (p. ej. dos espacios
    # entre "MOVIL" y "FONTIBON", o un espacio no-separable \xa0) a uno
    # solo, para que dos fuentes con el mismo nombre pero distinto
    # espaciado no queden como estaciones distintas tras el merge.
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip().upper()

# Estaciones que llegan con nombres distintos según la fuente (Mendeley vs
# IBOCA) pero son la misma estación física. Se aplica una sola vez, apenas
# se cargan los datos, para que las 4 pestañas trabajen con nombres ya
# unificados.
#
# NOTA sobre "Móvil Fontibón": se investigó y NO se unifica con
# "P_CAMI - Fontibón". En el GeoJSON oficial de estaciones (SDA) aparecen
# como dos entradas separadas, cada una con su propio OBJECTID y sus
# propias coordenadas — igual que "Móvil 7ma" es una unidad distinta del
# resto de estaciones de su zona. Fusionarlas habría mezclado dos series
# de una estación fija y una móvil como si fueran una sola.
EQUIVALENCIAS_NOMBRE = {
    "FONTIBON": "P_CAMI - FONTIBON",
    "JAZMIN": "EL JAZMIN",
    "CDAR": "CENTRO DE ALTO RENDIMIENTO",
}

def normalizar_con_equivalencia(texto):
    n = normalizar(texto)
    return EQUIVALENCIAS_NOMBRE.get(n, n)

def a_numero(serie):
    return (
        serie.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

def limpiar_valores_centinela(df, min_repeticiones=3, umbral_valor=300):
    """Elimina series de valores IDÉNTICOS y consecutivos (mismo valor
    exacto, 3+ días seguidos) que además superan un umbral físicamente
    poco plausible para Bogotá (300 µg/m³ está muy por encima del
    percentil 99.9 de toda la serie). Esa combinación —valor repetido
    + extremo— es la firma típica de un sensor congelado o un valor
    centinela de error, no de un episodio real de contaminación.

    No se filtra por umbral solo (eso descartaría picos reales), ni por
    repetición sola (hay tramos legítimos con valores bajos repetidos,
    p. ej. durante períodos de calma).
    """
    df = df.sort_values(["estacion", "contaminante", "fecha"]).reset_index(drop=True)
    clave = ["estacion", "contaminante"]
    mismo_que_anterior = df.groupby(clave)["valor"].transform(lambda s: s == s.shift(1))
    df["_racha"] = (~mismo_que_anterior).groupby([df["estacion"], df["contaminante"]]).cumsum()
    tamano_racha = df.groupby(clave + ["_racha"])["valor"].transform("size")
    sospechoso = (tamano_racha >= min_repeticiones) & (df["valor"] > umbral_valor)
    n_eliminadas = int(sospechoso.sum())
    df = df[~sospechoso].drop(columns="_racha").reset_index(drop=True)
    return df, n_eliminadas

# ------------------------------------------------------------------
# Carga de datos (con caché para no recargar en cada interacción)
# ------------------------------------------------------------------
@st.cache_data
def cargar_datos():
    df_aire = pd.read_csv("aire_bogota_con_localidad.csv")
    df_aire["fecha"] = pd.to_datetime(df_aire["fecha"], format="mixed", errors="coerce")

    # Unificar nombres de estación ANTES de cualquier análisis, para que
    # Mendeley e IBOCA no queden partidos en series separadas.
    df_aire["estacion"] = df_aire["estacion"].apply(normalizar_con_equivalencia)

    df_aire, n_valores_centinela = limpiar_valores_centinela(df_aire)

    df_estaciones = pd.read_csv("data/estaciones_ubicacion.csv")
    df_mort = pd.read_csv("data/mortalidad_pm25.csv", sep=";", encoding="utf-8")
    df_mort["casos_atribuibles_100k"] = a_numero(df_mort["ESTIMADO_CASOS_ATRIBUIBLES_100000_HABITANTES_CENTRAL"])
    df_mort["concentracion_pm25"] = a_numero(df_mort["CONCENTRACION_PM_2_5"])
    df_mort = df_mort[~df_mort["LOCALIDAD"].str.contains("TOTAL", case=False, na=False)]
    return df_aire, df_estaciones, df_mort, n_valores_centinela

df_aire, df_estaciones, df_mort, N_VALORES_CENTINELA = cargar_datos()
df_pm10 = df_aire[df_aire["contaminante"] == "PM10"].copy()

FECHA_MIN = df_aire["fecha"].min()
FECHA_MAX = df_aire["fecha"].max()

# ------------------------------------------------------------------
# Encabezado
# ------------------------------------------------------------------
st.title("Calidad del Aire en Bogotá")
st.caption(
    f"Herramienta de apoyo a la decisión — Subdirección de Calidad del Aire, Auditiva y Visual (SCAAV), "
    f"Secretaría Distrital de Ambiente. Serie histórica de estaciones disponible hasta **{FECHA_MAX.date()}**."
)
if N_VALORES_CENTINELA > 0:
    st.caption(
        f"🧹 Se excluyeron {N_VALORES_CENTINELA} registros con valores idénticos y consecutivos "
        "muy por encima de lo físicamente plausible (probable error de sensor), antes de calcular "
        "cualquier cifra de este dashboard."
    )

with st.container(border=True):
    st.markdown("#### 🎯 Recomendación de esta herramienta")
    st.markdown(
        "Con la evidencia disponible, se recomienda priorizar intervención en **Kennedy**, "
        "**Ciudad Bolívar** y **Tunjuelito**. Kennedy es la única zona que aparece como crítica "
        "en **dos fuentes independientes**: es la segunda estación con más días fuera de norma "
        "(pestaña Ranking) y la tercera localidad con mayor mortalidad atribuible a PM2.5 "
        "(pestaña Zona de decisión). Ciudad Bolívar y Tunjuelito no cuentan con series largas "
        "de monitoreo ambiental confiables (ver Ranking), pero los datos de salud pública de la "
        "Secretaría de Salud sí muestran allí el mayor impacto — lo que sugiere reforzar el "
        "monitoreo ambiental en esas dos zonas además de intervenir. **Estas zonas siguen "
        "activamente monitoreadas por la SDA**: una nota oficial de marzo de 2026 confirma "
        "seguimiento continuo a las estaciones de Usme, Ciudad Bolívar y Tunal por su cercanía "
        "al relleno El Mochuelo, y el Plan Aire 2030 ya interviene Kennedy, Bosa y Ciudad Bolívar "
        "a través de la Zona Urbana por un Mejor Aire (PIZSO) — coincidiendo de forma "
        "independiente con lo encontrado en este análisis."
    )

tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Panorama general", "📊 Ranking de estaciones",
    "📈 Patrones temporales", "🎯 Zona de decisión"
])

# ------------------------------------------------------------------
# PESTAÑA 1 - Panorama general
# ------------------------------------------------------------------
with tab1:
    st.subheader("Estado de las estaciones — último año disponible por estación")
    st.info(
        f"⚠️ Esta vista usa la serie histórica de estaciones ({FECHA_MIN.year} - {FECHA_MAX.year}) para el "
        "diagnóstico estructural del dashboard. Para el estado del aire **en tiempo real, hoy**, "
        "consulten el [portal en vivo de la RMCAB](https://rmcab.ambientebogota.gov.co/home/map). "
        "Nota: no todas las estaciones tienen el mismo último año disponible — varias solo tienen "
        "historia de Mendeley (hasta 2021), otras ya incluyen datos recientes de IBOCA (hasta 2026). "
        "Cada estación se evalúa contra **su propio** último año de datos, no un año calendario fijo, "
        "para no descartar estaciones con historia real pero sin datos post-2021."
    )

    # Último año DE CADA ESTACIÓN (no el año máximo global), para no dejar
    # como "Sin dato" a estaciones que solo tienen historia de Mendeley.
    fecha_max_por_estacion = df_pm10.groupby("estacion")["fecha"].transform("max")
    un_anio_atras_por_estacion = fecha_max_por_estacion - pd.DateOffset(years=1)
    df_reciente = df_pm10[df_pm10["fecha"] >= un_anio_atras_por_estacion]
    promedio_reciente = (
        df_reciente.groupby("estacion")
        .agg(promedio_reciente=("valor", "mean"), fecha_referencia=("fecha", "max"))
        .reset_index()
    )
    # df_aire ya viene con nombres unificados (ver cargar_datos), así que
    # aquí basta normalizar sin aplicar equivalencias de nuevo.
    promedio_reciente["estacion_norm"] = promedio_reciente["estacion"].apply(normalizar)
    df_estaciones_copia = df_estaciones.copy()
    df_estaciones_copia["estacion_norm"] = df_estaciones_copia["estacion"].apply(normalizar_con_equivalencia)
    df_mapa = df_estaciones_copia.merge(promedio_reciente, on="estacion_norm", how="left")

    def clasificar(valor):
        if pd.isna(valor):
            return "Sin dato"
        elif valor < 25:
            return "Buena"
        elif valor < LIMITE_ANUAL_PM10:
            return "Moderada (sobre guía OMS)"
        else:
            return "Excede norma anual (Res. 2254/2017)"

    df_mapa["estado"] = df_mapa["promedio_reciente"].apply(clasificar)
    COLOR_ESTADO = {
        "Buena": "#2ecc71",
        "Moderada (sobre guía OMS)": "#f39c12",
        "Excede norma anual (Res. 2254/2017)": "#e74c3c",
        "Sin dato": "#95a5a6",
    }

    n_excede = (df_mapa["estado"] == "Excede norma anual (Res. 2254/2017)").sum()
    n_sin_dato = (df_mapa["estado"] == "Sin dato").sum()
    n_sin_coordenadas = df_mapa["latitud"].isna().sum()
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Estaciones que exceden la norma anual de PM10", f"{n_excede} de {len(df_mapa)}")
        if n_sin_dato > 0:
            if n_sin_coordenadas > 0:
                st.caption(
                    f"{n_sin_coordenadas} estación(es) sin coordenadas oficiales de la RMCAB — no se pueden ubicar en el mapa."
                )
            if n_sin_dato > n_sin_coordenadas:
                st.caption(
                    f"{n_sin_dato - n_sin_coordenadas} estación(es) con coordenadas pero sin promedio reciente "
                    "calculado — revisar si el nombre coincide entre el CSV de aire y estaciones_ubicacion.csv."
                )
        st.dataframe(
            df_mapa[["estacion_x", "promedio_reciente", "fecha_referencia", "estado"]]
            .rename(columns={
                "estacion_x": "Estación",
                "promedio_reciente": "PM10 (µg/m³)",
                "fecha_referencia": "Datos hasta",
            })
            .sort_values("PM10 (µg/m³)", ascending=False),
            hide_index=True, use_container_width=True,
        )
    with col2:
        fig1 = px.scatter_mapbox(
            df_mapa, lat="latitud", lon="longitud", color="estado",
            color_discrete_map=COLOR_ESTADO, hover_name="estacion_x",
            hover_data={
                "promedio_reciente": ":.1f",
                "fecha_referencia": True,
                "latitud": False,
                "longitud": False,
            },
            zoom=10, height=550,
        )
        fig1.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        fig1.update_traces(marker=dict(size=16))
        st.plotly_chart(fig1, use_container_width=True)
        st.caption(
            "🟢 Buena (<25 µg/m³, guía OMS) · 🟠 Moderada (25-50, dentro de norma colombiana pero sobre guía OMS) · "
            "🔴 Excede la norma legal anual (>50 µg/m³, Res. 2254/2017) · ⚪ Sin serie histórica disponible. "
            "Cada estación usa su propio último año de datos disponible (ver columna \"Datos hasta\" y el tooltip del mapa)."
        )

# ------------------------------------------------------------------
# PESTAÑA 2 - Ranking
# ------------------------------------------------------------------
with tab2:
    st.subheader("¿Qué estaciones superan la norma con más frecuencia?")

    PERIODOS = {
        f"Todo el período ({FECHA_MIN.year}-{FECHA_MAX.year})": (FECHA_MIN.year, FECHA_MAX.year),
        "2010-2012": (2010, 2012),
        "2013-2015": (2013, 2015),
        "2016-2018": (2016, 2018),
        "2019-2021": (2019, 2021),
        f"2022-{FECHA_MAX.year}": (2022, FECHA_MAX.year),
    }
    periodo_elegido = st.selectbox("Período a analizar:", list(PERIODOS.keys()))
    anio_inicio, anio_fin = PERIODOS[periodo_elegido]

    df_pm10["excede_norma"] = df_pm10["valor"] > LIMITE_DIARIO_PM10
    df_pm10_periodo = df_pm10[(df_pm10["fecha"].dt.year >= anio_inicio) & (df_pm10["fecha"].dt.year <= anio_fin)]

    resumen = (
        df_pm10_periodo.groupby("estacion")
        .agg(dias_totales=("valor", "count"), dias_excede=("excede_norma", "sum"))
        .reset_index()
    )
    resumen = resumen[resumen["dias_totales"] > 0]
    resumen["pct_dias_excede"] = (resumen["dias_excede"] / resumen["dias_totales"] * 100).round(1)
    resumen["confiabilidad"] = resumen["dias_totales"].apply(
        lambda d: "Cobertura sólida (+3.000 días)" if d >= 3000 else "Cobertura corta (interpretar con cautela)"
    )
    resumen = resumen.sort_values("pct_dias_excede", ascending=True)

    fig2 = px.bar(
        resumen, x="pct_dias_excede", y="estacion", orientation="h", color="confiabilidad",
        color_discrete_map={
            "Cobertura sólida (+3.000 días)": "#c0392b",
            "Cobertura corta (interpretar con cautela)": "#e67e22",
        },
        labels={"pct_dias_excede": "% de días que excede el límite diario de PM10 (75 µg/m³)", "estacion": "Estación", "confiabilidad": "Confiabilidad del dato"},
        text="pct_dias_excede", height=600,
        title=f"Período: {periodo_elegido}",
    )
    fig2.update_traces(texttemplate="%{text}%", textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(
        "🔴 Rojo = estación con +3.000 días de registro histórico (dato confiable). "
        "🟠 Naranja = menos de 3.000 días — interpretar con cautela, la comparación puede no ser justa "
        "frente a estaciones con más años de monitoreo. Nota: la confiabilidad de cobertura se calcula "
        "sobre el período seleccionado, así que en sub-períodos de 3 años el umbral de 3.000 días rara vez "
        "se alcanza — esa columna es más informativa en la vista de todo el período."
    )

# ------------------------------------------------------------------
# PESTAÑA 3 - Patrones temporales
# ------------------------------------------------------------------
with tab3:
    st.subheader("Tendencia y estacionalidad")

    conteo_dias = df_pm10.groupby("estacion")["valor"].count()
    estaciones_confiables = conteo_dias[conteo_dias >= 3000].index.tolist()
    df_confiables = df_pm10[df_pm10["estacion"].isin(estaciones_confiables)].copy()
    df_confiables["anio"] = df_confiables["fecha"].dt.year
    df_confiables["mes"] = df_confiables["fecha"].dt.month

    col1, col2 = st.columns(2)
    with col1:
        tendencia_anual = df_confiables.groupby(["anio", "estacion"])["valor"].mean().reset_index()

        # Reindexar a TODOS los años del rango, por estación, para que los
        # años sin ninguna medición queden como NaN explícito en vez de
        # simplemente faltar. Con connectgaps=False (default de Plotly),
        # esto corta la línea en el hueco 2021-2024 en vez de dibujar una
        # transición continua que nunca se midió.
        todos_los_anios = range(int(tendencia_anual["anio"].min()), int(tendencia_anual["anio"].max()) + 1)
        indice_completo = pd.MultiIndex.from_product(
            [todos_los_anios, tendencia_anual["estacion"].unique()], names=["anio", "estacion"]
        ).to_frame(index=False)
        tendencia_anual = indice_completo.merge(tendencia_anual, on=["anio", "estacion"], how="left")

        ESTACIONES_DESTACADAS = ["CARVAJAL - SEVILLANA", "KENNEDY"]
        fig3 = px.line(
            tendencia_anual, x="anio", y="valor", color="estacion", markers=True,
            title=f"Tendencia anual de PM10 ({tendencia_anual['anio'].min()}-{tendencia_anual['anio'].max()})",
            labels={"valor": "PM10 promedio anual (µg/m³)", "anio": "Año", "estacion": "Estación"},
            color_discrete_map={e: "#e74c3c" if e == "CARVAJAL - SEVILLANA" else "#2980b9" if e == "KENNEDY" else "#d5d8dc"
                                 for e in tendencia_anual["estacion"].unique()},
        )
        fig3.for_each_trace(
            lambda t: t.update(line=dict(width=1), opacity=0.5, showlegend=False)
            if t.name not in ESTACIONES_DESTACADAS else t.update(line=dict(width=3))
        )
        fig3.update_traces(connectgaps=False)
        fig3.add_hline(y=LIMITE_ANUAL_PM10, line_dash="dash", line_color="red",
                        annotation_text="Límite anual (Res. 2254/2017)")
        fig3.add_vrect(
            x0=2021, x1=2024, fillcolor="gray", opacity=0.15, line_width=0,
            annotation_text="Sin monitoreo (transición Mendeley → IBOCA)",
            annotation_position="top left", annotation_font_size=10,
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            "Se resaltan Carvajal-Sevillana y Kennedy (las más críticas); el resto de estaciones se muestra "
            "en gris de fondo para facilitar la lectura. **Entre 2021 y 2024 no hay datos** por el cambio de "
            "fuente de monitoreo (de Mendeley a IBOCA): la línea se corta deliberadamente en ese tramo y no "
            "debe leerse como una tendencia continua entre esos años."
        )

    with col2:
        MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        patron_mensual = df_confiables.groupby("mes")["valor"].mean().reset_index()
        patron_mensual["mes_nombre"] = patron_mensual["mes"].apply(lambda m: MESES[m - 1])
        fig4 = px.bar(
            patron_mensual, x="mes_nombre", y="valor",
            title="Patrón estacional promedio (todas las estaciones confiables)",
            labels={"valor": "PM10 promedio (µg/m³)", "mes_nombre": "Mes"},
            category_orders={"mes_nombre": MESES},
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.caption("Los datos son promedios diarios; no se dispone de granularidad horaria en la fuente.")

# ------------------------------------------------------------------
# PESTAÑA 4 - Zona de decisión
# ------------------------------------------------------------------
with tab4:
    st.subheader("¿Dónde priorizar la intervención?")
    st.caption(
        "⚠️ Esta pestaña usa **PM2.5** (no PM10 como las anteriores): es el contaminante que "
        "la Secretaría de Salud usa para medir mortalidad atribuible, por ser la partícula más "
        "asociada a impactos en salud según evidencia epidemiológica."
    )

    resumen_localidad = (
        df_mort.groupby("LOCALIDAD")
        .agg(
            concentracion_pm25_promedio=("concentracion_pm25", "mean"),
            casos_atribuibles_100k_promedio=("casos_atribuibles_100k", "mean"),
            muertes_totales=("NUMERO_MUERTES_POBLACION", "sum"),
        )
        .reset_index()
    )

    def normalizar_0_1(col):
        return (col - col.min()) / (col.max() - col.min())

    resumen_localidad["score_prioridad"] = (
        normalizar_0_1(resumen_localidad["concentracion_pm25_promedio"])
        + normalizar_0_1(resumen_localidad["casos_atribuibles_100k_promedio"])
    )
    top3 = resumen_localidad.sort_values("score_prioridad", ascending=False).head(3)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig5 = px.scatter(
            resumen_localidad, x="concentracion_pm25_promedio", y="casos_atribuibles_100k_promedio",
            size="muertes_totales", text="LOCALIDAD",
            labels={
                "concentracion_pm25_promedio": "Concentración promedio PM2.5 (µg/m³)",
                "casos_atribuibles_100k_promedio": "Mortalidad atribuible (casos por 100.000 hab.)",
            },
            height=550,
        )
        fig5.update_traces(textposition="top center")
        top3_nombres = top3["LOCALIDAD"].tolist()
        fig5.for_each_trace(lambda t: t.update(marker=dict(color=[
            "#e74c3c" if n in top3_nombres else "#3498db" for n in resumen_localidad["LOCALIDAD"]
        ])))
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        st.markdown("### Top 3 zonas prioritarias")
        for _, fila in top3.iterrows():
            st.metric(fila["LOCALIDAD"], f"{fila['casos_atribuibles_100k_promedio']:.1f} casos/100k hab.")
        st.caption(
            "Calculado combinando concentración promedio de PM2.5 y mortalidad "
            "atribuible por localidad (datos SDS, 2019-2023)."
        )
