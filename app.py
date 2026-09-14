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

st.set_page_config(page_title="Calidad del Aire - Bogotá", layout="wide")

LIMITE_ANUAL_PM10 = 50    # µg/m3, Res. 2254/2017
LIMITE_DIARIO_PM10 = 75   # µg/m3, Res. 2254/2017

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.strip().upper()

EQUIVALENCIAS_NOMBRE = {
    "FONTIBON": "P_CAMI - FONTIBON",
    "JAZMIN": "EL JAZMIN",
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

# ------------------------------------------------------------------
# Carga de datos (con caché para no recargar en cada interacción)
# ------------------------------------------------------------------
@st.cache_data
def cargar_datos():
    df_aire = pd.read_csv("aire_bogota_con_localidad.csv", parse_dates=["fecha"])
    df_estaciones = pd.read_csv("data/estaciones_ubicacion.csv")
    df_mort = pd.read_csv("data/mortalidad_pm25.csv", sep=";", encoding="utf-8")
    df_mort["casos_atribuibles_100k"] = a_numero(df_mort["ESTIMADO_CASOS_ATRIBUIBLES_100000_HABITANTES_CENTRAL"])
    df_mort["concentracion_pm25"] = a_numero(df_mort["CONCENTRACION_PM_2_5"])
    df_mort = df_mort[~df_mort["LOCALIDAD"].str.contains("TOTAL", case=False, na=False)]
    return df_aire, df_estaciones, df_mort

df_aire, df_estaciones, df_mort = cargar_datos()
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
    st.subheader("Estado de las estaciones — último año disponible")
    st.info(
        f"⚠️ Esta vista usa la serie histórica de estaciones ({FECHA_MIN.year} - {FECHA_MAX.year}) para el "
        "diagnóstico estructural del dashboard. Para el estado del aire **en tiempo real, hoy**, "
        "consulten el [portal en vivo de la RMCAB](https://rmcab.ambientebogota.gov.co/home/map)."
    )

    un_anio_atras = FECHA_MAX - pd.DateOffset(years=1)
    df_reciente = df_pm10[df_pm10["fecha"] >= un_anio_atras]
    promedio_reciente = (
        df_reciente.groupby("estacion")["valor"].mean().reset_index()
        .rename(columns={"valor": "promedio_reciente"})
    )
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
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Estaciones que exceden la norma anual de PM10", f"{n_excede} de {len(df_mapa)}")
        st.dataframe(
            df_mapa[["estacion_x", "promedio_reciente", "estado"]]
            .rename(columns={"estacion_x": "Estación", "promedio_reciente": "PM10 (µg/m³)"})
            .sort_values("PM10 (µg/m³)", ascending=False),
            hide_index=True, use_container_width=True,
        )
    with col2:
        fig1 = px.scatter_mapbox(
            df_mapa, lat="latitud", lon="longitud", color="estado",
            color_discrete_map=COLOR_ESTADO, hover_name="estacion_x",
            hover_data={"promedio_reciente": ":.1f", "latitud": False, "longitud": False},
            zoom=10, height=550,
        )
        fig1.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        fig1.update_traces(marker=dict(size=16))
        st.plotly_chart(fig1, use_container_width=True)
        st.caption(
            "🟢 Buena (<25 µg/m³, guía OMS) · 🟠 Moderada (25-50, dentro de norma colombiana pero sobre guía OMS) · "
            "🔴 Excede la norma legal anual (>50 µg/m³, Res. 2254/2017) · ⚪ Sin serie histórica disponible."
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
        fig3.add_hline(y=LIMITE_ANUAL_PM10, line_dash="dash", line_color="red",
                        annotation_text="Límite anual (Res. 2254/2017)")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Se resaltan Carvajal-Sevillana y Kennedy (las más críticas); el resto de estaciones se muestra en gris de fondo para facilitar la lectura.")

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
