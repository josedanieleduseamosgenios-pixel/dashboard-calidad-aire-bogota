# Documento de Decisiones de Visualización

**Proyecto:** Calidad del Aire en Bogotá — Dashboard para Priorización de Intervención
**Usuario objetivo:** Profesional de la Subdirección de Calidad del Aire, Auditiva y
Visual (SCAAV), Secretaría Distrital de Ambiente.

Este documento explica el **porqué** detrás de cada gráfico del dashboard: qué
pregunta responde, qué tipo de visualización se eligió y por qué, qué alternativas se
descartaron, y qué decisiones de diseño se tomaron sobre los datos antes de graficar.

---

## Principio general de diseño

Cada gráfico del dashboard debe responder **una pregunta de decisión concreta**, no
solo "mostrar datos". Antes de elegir un tipo de gráfico, se definió la pregunta que
debía responder; el gráfico se eligió después, en función de esa pregunta — nunca al
revés.

---

## Pestaña 1 — Panorama general

**Pregunta que responde:** ¿cuál es el estado general de la calidad del aire hoy, de
un vistazo?

**Gráfico elegido:** mapa de puntos geolocalizados (scatter map), coloreado por
estado (semáforo de 4 categorías).

**Por qué un mapa y no una tabla:** el usuario necesita identificar rápidamente *en
qué zona de la ciudad* está el problema. Una tabla ordenada exige leer fila por fila;
un mapa permite ubicar espacialmente los focos críticos en segundos, que es
justamente el objetivo de una pestaña de "panorama".

**Decisiones sobre el semáforo:**
- Se usó **solo PM10** para clasificar, no un promedio de PM10 y PM2.5 combinados.
  Ambos contaminantes tienen límites normativos distintos (Res. 2254/2017: 50 µg/m³
  anual para PM10, 25 µg/m³ para PM2.5); promediarlos habría producido un número sin
  significado normativo.
- Los cortes de color se basan en la norma legal colombiana (50 µg/m³ anual, límite
  para "Dañina") y en la guía de la OMS (~15 µg/m³, corte usado para "Buena") en vez
  de un umbral arbitrario. Esto hace que el semáforo sea defendible ante cualquier
  pregunta de "¿por qué ese corte y no otro?".
- Se calculó sobre el **promedio del último año disponible**, no el último día. Un
  solo día puede ser un valor atípico (por ejemplo, un evento puntual de quema) y no
  representa bien el estado estructural de una estación para una decisión de
  intervención.
- Las estaciones sin datos cruzados (2 de 19) se muestran en gris ("Sin dato") en vez
  de omitirse, para no ocultar un vacío de información real.

**Alternativa descartada:** un mapa de calor (heatmap continuo interpolado) sobre
toda la ciudad. Se descartó porque interpola valores entre estaciones sin datos
reales ahí, dando una falsa sensación de precisión donde no existe medición.

---

## Pestaña 2 — Ranking de estaciones

**Pregunta que responde:** ¿qué estaciones superan la norma con más frecuencia?

**Gráfico elegido:** barras horizontales, con el eje Y de estaciones ordenado de
mayor a menor.

**Por qué % de días que excede la norma, y no el promedio:** el promedio histórico
puede ocultar el problema real. Una estación con muchos días extremos y muchos días
buenos puede tener un promedio moderado, pero seguir siendo una fuente de riesgo
frecuente. El % de días en infracción es una métrica directamente accionable: le dice
al usuario "esta estación estuvo fuera de norma X% del tiempo".

**Por qué barras horizontales y no verticales:** con 18 nombres de estación, las
etiquetas horizontales se superponen o requieren rotarlas (dificultando la lectura).
Las barras horizontales permiten leer los nombres completos sin rotación.

**Decisión de transparencia estadística — el ajuste más importante de esta pestaña:**
las estaciones no tienen la misma cantidad de días de registro histórico (algunas
tienen +10 años, otras menos de 6 meses). Comparar un 17.7% calculado sobre 481 días
con un 50.5% calculado sobre 3.909 días como si tuvieran el mismo peso estadístico
sería engañoso. Se agregó una codificación de color (rojo = cobertura sólida,
naranja = cobertura corta) para que el usuario pondere el hallazgo según su
confiabilidad, en vez de ocultar esta limitación.

**Alternativa descartada:** excluir directamente las estaciones con poca cobertura.
Se descartó porque una de ellas (Bolivia) mostró el promedio histórico más alto de
todas las estaciones — omitirla habría escondido una señal de alerta real, aunque
limitada.

---

## Pestaña 3 — Patrones temporales

**Pregunta que responde:** ¿mejora o empeora la calidad del aire con el tiempo?
¿Hay un patrón estacional?

**Gráficos elegidos:** (a) líneas de tiempo por estación, año a año; (b) barras de
promedio por mes del año.

**Por qué dos gráficos separados en vez de uno solo:** la tendencia anual (mejora/
empeora) y el patrón estacional (qué mes es peor) son dos preguntas distintas con
escalas temporales distintas (años vs. meses). Combinarlas en un solo gráfico habría
requerido un eje temporal híbrido, confuso de leer.

**Decisión de alcance importante:** el proyecto original planteaba analizar
"patrones horarios y estacionales". Los datos disponibles (Mendeley) son **promedios
diarios**, no horarios, así que no es posible mostrar un patrón por hora del día con
esta fuente. Se ajustó el alcance a patrones mensuales/estacionales, que sí son
respondibles con los datos disponibles, y se documenta esta limitación explícitamente
en el dashboard (`st.caption`) en vez de forzar un gráfico con datos que no existen.

**Filtro de estaciones:** solo se incluyen en esta pestaña las estaciones con
cobertura sólida (+3.000 días de registro). Una tendencia calculada sobre pocos meses
de datos no es una "tendencia" real, es ruido.

**Línea de referencia:** se agregó una línea horizontal en 50 µg/m³ (límite anual)
en el gráfico de tendencia, para que el usuario vea de inmediato cuándo cada
estación cruza (o deja de cruzar) el límite legal a lo largo de los años.

---

## Pestaña 4 — Zona de decisión

**Pregunta que responde:** ¿en qué 2-3 zonas se debería priorizar la intervención?

**Gráfico elegido:** diagrama de dispersión (scatter plot), eje X = concentración
promedio de PM2.5, eje Y = mortalidad atribuible por 100.000 habitantes, tamaño de
punto = mortalidad total, con las 3 localidades prioritarias resaltadas en un color
distinto.

**Por qué un cruce de dos variables y no dos gráficos separados:** la pregunta no es
"¿dónde hay más contaminación?" ni "¿dónde hay más mortalidad?" por separado, sino
"¿dónde coinciden ambas?". Un scatter plot es el único formato que permite ver esa
intersección de un vistazo — las localidades en la esquina superior derecha son,
literalmente, las que combinan ambos problemas.

**Por qué un puntaje combinado (score) en vez de "por encima de la mediana en ambos
ejes":** el primer enfoque probado (mediana) dejaba 7 localidades como "prioritarias",
lejos del objetivo del proyecto de identificar 2-3 zonas concretas. Se cambió a un
puntaje normalizado (0-1) por eje, sumado, para poder ordenar de forma continua y
quedarse con un top 3 real y defendible.

**Decisión de fuente de datos:** se usó directamente la concentración de PM2.5
reportada dentro del propio dataset de mortalidad de la Secretaría de Salud, en vez
de cruzarlo con los datos de estaciones de Mendeley. Esto se debe a que el dataset de
salud ya viene agregado por localidad (nivel de análisis necesario para esta
pestaña), mientras que Mendeley está a nivel de estación — cruzarlos habría exigido
el mismo mapeo estación→localidad usado en pestañas anteriores, agregando una capa
de incertidumbre innecesaria cuando el dato ya vivía en el dataset correcto.

**Limpieza de datos aplicada:** se excluyeron filas de "TOTAL_BOGOTA" (agregados de
ciudad, no localidades reales) que de otro modo habrían distorsionado tanto el
gráfico como el cálculo del puntaje de prioridad.

**Validación cruzada como refuerzo del hallazgo:** Kennedy aparece como zona crítica
tanto en el ranking de estaciones (pestaña 2, con datos ambientales) como en esta
pestaña (con datos de salud pública) — dos fuentes independientes coincidiendo en el
mismo resultado. Esto se destaca explícitamente en el dashboard porque fortalece la
credibilidad del hallazgo frente a un usuario escéptico.

---

## Decisión transversal: recomendación ejecutiva

Se agregó un bloque de texto al inicio del dashboard (antes de las pestañas) con una
recomendación explícita en lenguaje natural, en vez de dejar que el usuario infiera
la conclusión por sí mismo cruzando las 4 pestañas mentalmente. Esta decisión
responde a un criterio de evaluación específico del proyecto: que el dashboard
permita *tomar una decisión*, no solo *observar datos*. El bloque también resuelve
explícitamente una aparente contradicción entre pestañas (por qué Carvajal-Sevillana,
la peor estación en la pestaña 2, no aparece en el top 3 de la pestaña 4), en vez de
dejar esa pregunta sin responder.

---

## Decisión transversal: honestidad sobre la vigencia de los datos

La fuente principal de series históricas (Mendeley) llega hasta febrero de 2021. En
vez de omitir esta limitación o presentar los datos como si fueran actuales, se
decidió:
1. Mostrar la fecha de corte de forma visible en el encabezado del dashboard.
2. Enlazar directamente al portal en vivo de la RMCAB para el estado en tiempo real.
3. Citar evidencia reciente (Plan Aire 2030, notas de prensa de la SDA de 2026) que
   confirma que las zonas identificadas por este análisis siguen siendo objeto de
   intervención y monitoreo activo hoy — argumentando la vigencia del diagnóstico
   estructural sin fingir tener datos que no existen.
