# Calidad del Aire en Bogotá — Dashboard para Priorización de Intervención

Dashboard interactivo que traduce datos públicos de calidad del aire y salud en Bogotá
en una herramienta de decisión, dirigida a un profesional de la **Subdirección de
Calidad del Aire, Auditiva y Visual (SCAAV)** de la Secretaría Distrital de Ambiente.

🔗 **[Ver el dashboard en vivo](https://dashboard-calidad-aire-bogota-8rtudaipsmzwh7nrfscpyk.streamlit.app/)**

---

## ¿Qué problema resuelve?

Bogotá tiene ~20 estaciones de monitoreo de calidad del aire que llevan años midiendo
PM10, PM2.5 y otros contaminantes, pero esa información es pública y prácticamente
ilegible para quien no sea especialista. Este dashboard convierte esos datos en
respuestas concretas a preguntas que un tomador de decisiones necesita resolver:

1. ¿Qué estaciones muestran contaminación sostenida en el tiempo?
2. ¿Hay patrones estacionales que indiquen cuándo reforzar el monitoreo?
3. ¿Qué estaciones superan con más frecuencia los límites normativos?
4. ¿La calidad del aire mejora o empeora con los años?
5. ¿En qué 2-3 zonas se debería priorizar la intervención?

## Estructura del dashboard

| Pestaña | Contenido | Pregunta que responde |
|---|---|---|
| 📍 Panorama general | Mapa de estaciones con semáforo según la norma anual de PM10 | 1 |
| 📊 Ranking de estaciones | % de días que cada estación excede el límite diario legal | 3 |
| 📈 Patrones temporales | Tendencia anual 2010-2021 y estacionalidad mensual | 2, 4 |
| 🎯 Zona de decisión | Cruce contaminación (PM2.5) vs. mortalidad atribuible, por localidad | 5 |

## Fuentes de datos

| Fuente | Contenido | Cobertura |
|---|---|---|
| [Mendeley — Air Quality Bogota](https://data.mendeley.com/datasets/z6wtdbkc5b) (DOI 10.17632/z6wtdbkc5b.3) | Serie diaria de PM10/PM2.5, 18 estaciones de Bogotá (filtradas de un dataset que incluía también estaciones de Cali) | 2010 – feb 2021 |
| [IBOCA — Consulta de datos históricos](https://iboca.ambientebogota.gov.co/publicaciones/176/consulta-de-datos/) (SDA) | Serie por hora de PM10, promediada a nivel diario para mantener consistencia con Mendeley; complementa la serie histórica hasta el presente | 2024 – presente |
| [Localización de estaciones — Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co/dataset/localizacion-de-las-estaciones-calidad-del-aire-en-bogota) (SDA) | Coordenadas y metadatos de 19 estaciones | Actual |
| [Mortalidad atribuida a PM2.5 — Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co) (SDS) | Mortalidad por localidad, año y grupo de edad | 2019-2023 |
| [Prevalencia de síntomas respiratorios en menores de 5 años — Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co) (SDS) | Síntomas respiratorios y ausentismo escolar por localidad | 2019-2023 |
| [Tabla oficial de estaciones RMCAB](https://ambientebogota.gov.co/estaciones-rmcab) (SDA) | Localidad oficial de cada estación, usada para el cruce estación→localidad | — |

**Fuentes descartadas y por qué:** las capas de PM10/PM2.5/Ozono promedio anual del
portal de Datos Abiertos son formato GIS (interpolación espacial), no series por
estación, y resultaban redundantes frente a Mendeley. El portal RMCAB en vivo
(rmcab.ambientebogota.gov.co) tiene límites técnicos de exportación masiva que
impidieron construir con él una serie histórica completa. También se descargó y
evaluó el dataset de **prevalencia de síntomas respiratorios en menores de 5 años**
(SDS, 2019-2023, por localidad) como posible respaldo adicional para la pestaña de
decisión; se decidió no incluirlo en el dashboard final para mantener el eje del
proyecto enfocado en el cruce contaminación-mortalidad, evitando diluir el hallazgo
principal con un indicador adicional que no aportaba una conclusión distinta.

## Vigencia de los datos

La serie combinada (Mendeley + IBOCA) cubre **2010-2021 y 2024-presente**. Existe
un **vacío de datos entre marzo de 2021 y febrero de 2024** (~3 años) que ninguna
de las dos fuentes cubre; se documenta con honestidad en vez de ocultarlo o
interpolarlo artificialmente. El dashboard indica esta discontinuidad en la
pestaña de Patrones temporales.

A diferencia de una versión anterior de este proyecto que solo llegaba hasta 2021,
la pestaña de Panorama general ahora refleja **datos reales actualizados hasta el
día de la consulta**, gracias a la integración con IBOCA.

## Limpieza de datos aplicada al integrar IBOCA

- **Duplicados de nombre entre fuentes:** tres estaciones aparecían con nombres
  distintos en Mendeley vs. IBOCA para el mismo lugar físico (`CDAR` /
  `Centro de Alto Rendimiento`, `Jazmín` / `El Jazmín`, `Fontibon` /
  `P_CAMI - Fontibón`); se unificaron antes de cualquier análisis.
- **Granularidad inconsistente:** IBOCA reporta por hora, Mendeley por día. Se
  promedió IBOCA a nivel diario antes de combinar ambas fuentes, para que las
  comparaciones contra el límite normativo diario (75 µg/m³) siguieran siendo
  válidas.
- **Errores de sensor:** se encontraron y filtraron valores físicamente
  imposibles (un registro de 1.176.520 µg/m³ en Fontibón, y 29 días consecutivos
  con el valor idéntico 1.103 µg/m³ en Bolivia — evidencia de un código de
  "sensor caído" usado como relleno en vez de un valor vacío). Se aplicó un
  techo de 500 µg/m³ como límite físicamente razonable.


## Decisiones metodológicas clave

- **Filtrado de estaciones de Cali:** el dataset de Mendeley venía mezclado con 9
  estaciones ajenas a Bogotá (red DAGMA de Cali); se identificaron y excluyeron.
- **Granularidad diaria, no horaria:** los datos de Mendeley son promedios diarios;
  el análisis de patrones temporales se limita a estacionalidad mensual/anual.
- **PM10 y PM2.5 no se promedian juntos:** tienen límites normativos distintos
  (Res. 2254/2017: 50 µg/m³ anual para PM10, 25 µg/m³ para PM2.5); mezclarlos
  distorsionaría cualquier clasificación contra la norma.
- **Confiabilidad por estación:** varias estaciones tienen menos de 1.000 días de
  registro histórico; el dashboard las marca visualmente para evitar comparaciones
  injustas frente a estaciones con +10 años de datos.
- **Cruce estación → localidad:** construido a partir de la tabla oficial de la
  RMCAB, no del campo `sect_loc` del GeoJSON de estaciones (que estaba incompleto).

Ver el documento de decisiones de visualización para el detalle completo.

## Cómo correrlo localmente

```bash
git clone <url-del-repositorio>
cd <carpeta-del-repositorio>
pip install -r requirements.txt
streamlit run app.py
```

## Estructura del repositorio

```
├── app.py                          # Dashboard de Streamlit (4 pestañas)
├── requirements.txt                # Dependencias
├── aire_bogota_con_localidad.csv   # Serie consolidada Mendeley + localidad
├── data/
│   ├── estaciones_ubicacion.csv    # Coordenadas de estaciones
│   ├── mortalidad_pm25.csv         # Mortalidad atribuible por localidad
│   └── sintomas_respiratorios_ninos.csv  # Descargado y evaluado; no usado en el dashboard final (ver sección de fuentes)
├── download_data.py                # Script de descarga (Datos Abiertos Bogotá)
├── descargar_estaciones.py         # Script de descarga (GeoJSON de estaciones)
├── descomprimir_mendeley.py        # Descomprime el dataset de Mendeley
├── unir_mendeley.py                # Consolidación del dataset de Mendeley
├── convertir_iboca.py              # Parsea reportes de IBOCA (hora -> promedio diario)
├── unificar_nombres_estaciones.py  # Unifica nombres duplicados Mendeley/IBOCA
├── limpiar_valores_extremos.py     # Filtra errores de sensor (valores físicamente imposibles)
└── cruzar_localidad.py             # Cruce estación → localidad
```

## Equipo

- Juan Pablo Castañeda Neiva
- Hernan David Jimenez Saldaña
- Jose Daniel Ortiz Rodriguez

## Uso de Inteligencia Artificial

Este proyecto usó IA (Claude, Anthropic) como asistente durante el desarrollo del
pipeline de datos, la definición de la arquitectura del dashboard y la redacción de
esta documentación. El detalle completo del proceso, decisiones y prompts está en el
**AI Journal** incluido en la entrega.
