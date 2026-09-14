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
| 📍 Panorama general | Mapa de estaciones con semáforo según la norma anual de PM10, evaluado con el último año de datos disponible de cada estación | 1 |
| 📊 Ranking de estaciones | % de días que cada estación excede el límite diario legal | 3 |
| 📈 Patrones temporales | Tendencia anual 2010-2026 (con hueco visible 2021-2024) y estacionalidad mensual | 2, 4 |
| 🎯 Zona de decisión | Cruce contaminación (PM2.5) vs. mortalidad atribuible, por localidad | 5 |

## Fuentes de datos

| Fuente | Contenido | Cobertura |
|---|---|---|
| [Mendeley — Air Quality Bogota](https://data.mendeley.com/datasets/z6wtdbkc5b) (DOI 10.17632/z6wtdbkc5b.3) | Serie diaria de PM10/PM2.5, 18 estaciones de Bogotá (filtradas de un dataset que incluía también estaciones de Cali) | 2010 – feb 2021 |
| IBOCA (reportes descargados directamente de la RMCAB) | Serie diaria de PM10/PM2.5 por estación, mismo formato que Mendeley tras conversión | feb 2024 – actualidad |
| [Localización de estaciones — Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co/dataset/localizacion-de-las-estaciones-calidad-del-aire-en-bogota) (SDA) | Coordenadas y metadatos de 19 estaciones | Actual |
| [Mortalidad atribuida a PM2.5 — Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co) (SDS) | Mortalidad por localidad, año y grupo de edad | 2019-2023 |
| [Prevalencia de síntomas respiratorios en menores de 5 años — Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co) (SDS) | Síntomas respiratorios y ausentismo escolar por localidad | 2019-2025 |
| [Tabla oficial de estaciones RMCAB](https://ambientebogota.gov.co/estaciones-rmcab) (SDA) | Localidad oficial de cada estación, usada para el cruce estación→localidad | — |

**Fuentes descartadas y por qué:** las capas de PM10/PM2.5/Ozono promedio anual del
portal de Datos Abiertos son formato GIS (interpolación espacial), no series por
estación, y resultaban redundantes frente a Mendeley. El portal RMCAB en vivo
(rmcab.ambientebogota.gov.co) tiene límites técnicos de exportación masiva que
impidieron construir con él una serie histórica completa por ese medio; por eso se
complementó con reportes IBOCA descargados manualmente para extender la serie más
allá de 2021.

## Limitación de vigencia de los datos — y por qué el análisis sigue siendo válido

La serie combinada (Mendeley + IBOCA) cubre **2010 hasta la fecha más reciente
disponible en el repositorio** (el dashboard lo muestra en el encabezado), pero
**no es continua**: hay un hueco entre **marzo de 2021 y enero de 2024**, período en
el que no se contaba con una fuente descargable y estructurada equivalente a
Mendeley. El monitoreo real de la RMCAB no se interrumpió en ese tramo — lo que faltó
fue una fuente estructurada para descargarlo. El dashboard muestra este hueco de
forma explícita (la línea de tendencia se corta y el tramo aparece sombreado) en vez
de interpolar valores, para no sugerir una medición que nunca ocurrió.

Esto no invalida el diagnóstico: es una herramienta de **patrones estructurales**
(qué zonas son crónicamente críticas, cuándo empeora, si mejora con los años), no de
monitoreo en tiempo real. Los patrones observados antes y después del hueco son
consistentes entre sí (las mismas estaciones críticas lo son en ambos extremos de la
serie), y su vigencia está además respaldada por evidencia reciente:

- El **Plan Aire 2030** de la SDA ya interviene activamente Kennedy, Bosa y Ciudad
  Bolívar a través de la Zona Urbana por un Mejor Aire (PIZSO) — coincidiendo con las
  zonas prioritarias identificadas en este análisis, de forma independiente.
- Una nota oficial de la SDA de marzo de 2026 confirma monitoreo activo continuo en
  Usme, Ciudad Bolívar y Tunal (localidad Tunjuelito).

Para el estado del aire en tiempo real, el dashboard enlaza directamente al
[portal en vivo de la RMCAB](https://rmcab.ambientebogota.gov.co/home/map).

## Decisiones metodológicas clave

- **Filtrado de estaciones de Cali:** el dataset de Mendeley venía mezclado con 9
  estaciones ajenas a Bogotá (red DAGMA de Cali); se identificaron y excluyeron.
- **Unificación de nombres de estación entre fuentes:** Mendeley e IBOCA nombran
  algunas estaciones de forma distinta (p. ej. `P_CAMI - FONTIBÓN` vs. `FONTIBON`,
  `EL JAZMÍN` vs. `JAZMÍN`, `CENTRO DE ALTO RENDIMIENTO` vs. `CDAR`). Sin unificar
  esos nombres, la misma estación física quedaba partida en dos series distintas,
  subestimando su historial en el Ranking y en Patrones temporales.
- **Limpieza de valores centinela:** se detectaron y excluyeron registros con
  valores idénticos y consecutivos (3+ días seguidos) muy por encima de lo
  físicamente plausible para Bogotá (>300 µg/m³, muy sobre el percentil 99.9 de toda
  la serie) — firma típica de un sensor congelado, no de un evento real. No se
  filtró por umbral solo (descartaría picos reales) ni por repetición sola (hay
  tramos legítimos con valores bajos repetidos durante períodos de calma).
- **Granularidad diaria, no horaria:** los datos de Mendeley e IBOCA son promedios
  diarios; el análisis de patrones temporales se limita a estacionalidad
  mensual/anual.
- **PM10 y PM2.5 no se promedian juntos:** tienen límites normativos distintos
  (Res. 2254/2017: 50 µg/m³ anual para PM10, 25 µg/m³ para PM2.5); mezclarlos
  distorsionaría cualquier clasificación contra la norma.
- **Confiabilidad por estación:** varias estaciones tienen menos de 3.000 días de
  registro histórico; el dashboard las marca visualmente para evitar comparaciones
  injustas frente a estaciones con +10 años de datos.
- **"Último año disponible" es relativo a cada estación, no a un año calendario
  fijo:** como no todas las estaciones tienen datos recientes de IBOCA, el Panorama
  general evalúa a cada una contra su propio año más reciente (indicado en la
  columna "Datos hasta"), para no descartar como "Sin dato" a estaciones que sí
  tienen historia real, solo que no posterior a 2021.
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
├── aire_bogota_con_localidad.csv   # Serie consolidada Mendeley + IBOCA + localidad
├── data/
│   ├── estaciones_ubicacion.csv    # Coordenadas de estaciones
│   ├── mortalidad_pm25.csv         # Mortalidad atribuible por localidad
│   └── sintomas_respiratorios_ninos.csv
├── iboca_raw/                      # Reportes .xls originales descargados de IBOCA
├── download_data.py                # Script de descarga (Datos Abiertos Bogotá)
├── descargar_estaciones.py         # Script de descarga (GeoJSON de estaciones)
├── unir_mendeley.py                # Consolidación del dataset de Mendeley
├── convertir_iboca.py              # Conversión de reportes IBOCA (.xls) al formato común
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
