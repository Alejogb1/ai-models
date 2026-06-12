# Síntesis de modelado

## 1. Definición del modelo

NO es un simulador de marketing (no predice resultados).  
NO es un estudio de caso (no evalúa campañas existentes).  
NO es un oráculo (no da respuestas sin datos).

Es un **modelo de relación condicional** con estructura lógica `si A, entonces B; si no A, entonces no B`. Relaciona tres elementos:

```
[supuestos de tasa por etapa] → [cálculo matemático] → [usuarios verificados estimados]
```

El modelo no impone valores. **Toma los valores que el usuario ingresa** (tasas de escaneo, validación, consentimiento, acceso, retención) y **devuelve el resultado numérico** de multiplicarlos secuencialmente. Si los valores de entrada cambian, el resultado cambia. No hay opinión, hay álgebra.

---

## 2. Fórmula del modelo

```
u = U × e × (f × m × c × a) × r
```

Donde:

| Símbolo | Variable | Rango en el modelo | Fuente del valor |
|---------|----------|:------------------:|------------------|
| U | Universo total de clientes | 536.842 (fijo) | Base del equipo |
| e | Entrada al flujo (proporción que nota el QR o entra por algún canal) | 0,01 - 0,1933 (1% - 19,33%) | Según escenario |
| f | Tasa de finalización de formulario móvil | 0,25 - 0,65 | Benchmarks Tinyform |
| m | Tasa de validación de email (OTP o link) | 0,40 - 0,85 | Benchmarks Startup Stash |
| c | Tasa de consentimiento expreso | 0,50 - 0,90 | Questline / Ley 25.326 |
| a | Tasa de primer acceso a factura digital | 0,20 - 0,60 | Questline Energy Benchmarks |
| r | Tasa de retención (permanencia 3+ ciclos sin revertir) | 0,70 - 0,95 | Fiserv / estimación propia |

El producto `(f × m × c × a)` se denomina **finalización interna del flujo**: representa qué proporción de los que entran completan todas las etapas hasta convertirse en usuario digital activo.

---

## 3. Salida del modelo

El modelo produce un número concreto de **usuarios digitales verificados** para cada combinación de tasas de entrada. Con los valores actuales cargados en `scenario_inputs.csv`:

| Escenario | e (entrada) | f×m×c×a (finalización) | r (retención) | u (usuarios) | % de la meta (53.684) |
|-----------|:----------:|:---------------------:|:-------------:|:------------:|:---------------------:|
| QR solo conservador | 0,0100 | 0,0100 | 0,70 | **38** | 0,07% |
| QR solo moderado | 0,0300 | 0,0588 | 0,85 | **805** | 1,50% |
| Multicanal moderado | 0,1058 | 0,1260 | 0,85 | **6.082** | 11,33% |
| Multicanal fuerte | 0,1932 | 0,2984 | 0,95 | **29.401** | 54,77% |

El dato central: **QR solo produce entre 38 y 805 usuarios**. Es irrelevante como solución única. Para cualquier propósito práctico de conversión masiva, el QR solo no resuelve el problema.

---

## 4. Condición para alcanzar la meta del 10%

La meta es 53.684 usuarios = 10% del universo de 536.842.

Para que `u = 53.684`, se requiere que:

```
e × (f × m × c × a) × r = 0,10
```

Despejando `e` (entrada necesaria) en función de `(f × m × c × a)` (finalización) y `r` (retención):

```
e_requerida = 0,10 / (finalización × retención)
```

Valores numéricos para distintos niveles de finalización (con retención fija en 0,85):

| Si la finalización interna es | Y la retención es | Entonces la entrada necesaria es |
|:----------------------------:|:-----------------:|:-------------------------------:|
| 0,10 | 0,85 | 1,176 (imposible: supera 1,0) |
| 0,20 | 0,85 | 0,588 |
| 0,30 | 0,85 | 0,392 |
| 0,40 | 0,85 | 0,294 |
| 0,50 | 0,85 | 0,235 |
| 0,60 | 0,85 | 0,196 |
| 0,70 | 0,85 | 0,168 |
| 0,80 | 0,85 | 0,147 |
| 0,90 | 0,85 | 0,131 |
| 1,00 | 0,85 | 0,118 |

Interpretación: **si la finalización interna es 0,30 (30%), la entrada necesaria es 0,392 (39,2% del universo).** Con los valores actuales del modelo, el escenario multicanal fuerte produce entrada de 0,193 (19,3%). La diferencia es de 19,9 puntos porcentuales de entrada faltante.

---

## 5. Estructura lógica del modelo (si A, entonces B)

El modelo opera con esta cadena deductiva:

```
DADO QUE:
  - La tasa de escaneo QR reportada en benchmarks es 0,01 - 0,05
  - La tasa de finalización de formulario móvil reportada es 0,25 - 0,60
  - La tasa de validación de email reportada es 0,40 - 0,85
  - La tasa de consentimiento reportada es 0,50 - 0,90
  - La tasa de primer acceso reportada es 0,20 - 0,60
  - La tasa de retención reportada es 0,70 - 0,95

ENTONCES:
  - Bajo el escenario QR solo conservador: 38 usuarios
  - Bajo el escenario QR solo moderado: 805 usuarios
  - Bajo el escenario multicanal moderado: 6.082 usuarios
  - Bajo el escenario multicanal fuerte: 29.401 usuarios

SI:
  - La meta es 53.684 usuarios

ENTONCES:
  - Ningún escenario la alcanza con los valores actuales

SI:
  - Naturgy proporcionara tasas reales que duplican los benchmarks
  - (ej: escaneo QR > 0,05, finalización formulario > 0,60, primer acceso > 0,50)

ENTONCES:
  - El resultado del modelo cambiaría
  - Se podría recalcular si la meta es alcanzable

SI NO:
  - Las tasas reales están dentro del rango de los benchmarks

ENTONCES NO:
  - La meta no es alcanzable con la evidencia disponible
```

Esta estructura es explícitamente condicional. No afirma "la campaña funciona" ni "la campaña no funciona". Afirma "bajo estos supuestos, el resultado es este; si los supuestos cambian, el resultado cambia".

---

## 6. Las tasas reales de Naturgy tendrían que duplicar los benchmarks

Para que el modelo produzca 53.684 usuarios, las tasas de entrada del escenario multicanal fuerte (0,193) tendrían que aumentar a 0,392 (asumiendo finalización 0,30 y retención 0,85). Esto es un factor de **2,03×**.

Alternativamente, la finalización interna tendría que aumentar de 0,298 a aproximadamente 0,55 (asumiendo entrada 0,193 y retención 0,85). Esto es un factor de **1,84×**.

En términos de cada etapa individual (comparado con el escenario fuerte actual):

| Etapa | Valor actual (fuerte) | Valor requerido para meta | Factor |
|-------|:--------------------:|:------------------------:|:-----:|
| Entrada combinada | 0,193 | 0,392 | 2,03× |
| Finalización interna | 0,298 | ~0,55 | 1,84× |
| Retención | 0,95 | ~0,95 (ya en techo) | 1,00× |

**Ningún benchmark disponible en el deep-research-report.md reporta tasas de escaneo QR en facturas de servicios públicos superiores a 0,05. Ningún benchmark reporta finalización de formulario móvil superior a 0,63. Ningún benchmark reporta primer acceso a factura digital superior a 0,33 (salvo campañas excepcionales).**

Para que la meta sea alcanzable, las tasas reales de Naturgy tendrían que duplicar lo que la literatura reporta como máximo observado. No hay evidencia pública de que esto sea posible.

---

## 7. Lo que el modelo NO cubre

El modelo cubre solo la primera etapa del embudo: **proporción del universo que nota el QR o entra al flujo**. Los 38-805 usuarios del escenario QR solo representan personas que **notan el QR**, no personas que completan la adhesión.

El embudo completo (implementado en `main_analysis.py`) continúa:

```
nota QR [38-805] → escanea → carga email → valida email → 
da consentimiento → accede primera factura → permanece 3+ ciclos
```

Cada etapa posterior aplica su propia tasa de conversión. El modelo actual en `scenario_inputs.csv` ya incluye estas etapas como `completa_formulario`, `valida_email`, `consentimiento`, `primer_acceso`, `retencion`. El número final de **usuarios digitales verificados** (38-29.401) ya incorpora todas las etapas del embudo, no solo la notoriedad del QR.

---

## 8. Actualización del modelo por Naturgy

El modelo está diseñado para ser recalibrado. Naturgy puede reemplazar cualquier valor de `data/scenario_inputs.csv` con datos reales y re-ejecutar `main_analysis.py` para obtener resultados actualizados. Los valores reemplazables son:

| Archivo | Columna | Valor actual (moderado) | Datos que Naturgy debería proveer |
|---------|---------|:----------------------:|-----------------------------------|
| assumptions.csv | p_escanea_QR | 0,03 | Tasa de escaneo real en factura piloto con QR trackeable |
| assumptions.csv | p_aporte_FonoGas | 0,03 | Volumen de llamadas FonoGas / universo; tasa de adhesión asistida |
| assumptions.csv | p_aporte_NaturgyPIC | 0,03 | MAU/DAU de la app; tasa de conversión desde app a factura digital |
| assumptions.csv | costo_factura_fisica_ARS | 1.500 | Costo real por factura impresa + distribuida + gestionada |
| scenario_inputs.csv | retencion | 0,85 | Tasa de reenvío post-adhesión; tasa de retorno a papel a 6 meses |

El mecanismo de actualización es: modificar el valor en el CSV, ejecutar `python main_analysis.py`, leer los nuevos resultados en `output/scenario_results.csv`. No requiere modificar código.

---

## 9. Resumen de valores exactos y su origen

| Variable | Valor conservador | Valor moderado | Valor fuerte | Fuente exacta |
|----------|:----------------:|:--------------:|:-----------:|---------------|
| p_escanea_QR | 0,01 | 0,03 | 0,05 | Ramin Zamani Direct Mail QR; How Advertising Matters OOH 2026 |
| p_completa_formulario | 0,25 | 0,40 | 0,60 | Tinyform: finalización móvil 31,3%; optimizado hasta 63% |
| p_valida_email | 0,40 | 0,60 | 0,80 | Startup Stash: 30% abandono en verificación de email |
| p_consentimiento | 0,50 | 0,70 | 0,85 | Questline Opt-Out Case; ENARGAS Res 17/2025 |
| p_primer_acceso | 0,20 | 0,35 | 0,50 | Questline: open rate 19,2%; campañas dirigidas hasta 31,9% |
| p_retencion | 0,70 | 0,85 | 0,95 | Fiserv: 12,5% menos propensos a abandonar |
| factor_no_solapamiento | 0,65 | 0,80 | 0,90 | Supuesto del equipo (metodología de atribución multicanal) |

Ninguno de estos valores proviene de datos internos de Naturgy. Todos provienen de fuentes externas citadas en el `deep-research-report.md`. La confianza asignada a cada variable es baja (6 de 17 variables) o media (11 de 17), según la columna `confianza` del archivo `data/assumptions.csv`.

---

## 10. Aplicación directa a la presentación

Los resultados del modelo se aplican a las siguientes páginas del deck:

| Página del deck | Contenido actual | Aplicación del modelo |
|:---------------:|-----------------|----------------------|
| 2 y 5 | QR en factura física | El modelo cuantifica el alcance máximo del QR: 38-805 usuarios en escenarios realistas. No es solución única. |
| 3 | Clasificación de clientes | El modelo no segmenta por tipo de cliente. Requiere datos adicionales de Naturgy para segmentar. |
| 4 | Clientes sin email | El modelo captura este grupo en la etapa `valida_email` (tasa 0,40-0,85). No hay email → no hay validación → el cliente no avanza. |
| 6 | Difusión/redes | El modelo captura este canal como `entrada_marketing` (0,01-0,05). Aumenta la entrada combinada vía probabilidad de unión. |
| 7 | Beneficios para clientes con email | El modelo captura estos beneficios en las tasas de retención (0,70-0,95). Clientes con incentivo tienen mayor probabilidad de permanecer. |
| 8 | Meta del 10% mensual | El modelo muestra que ningún escenario alcanza 53.684. La meta debe replantearse como objetivo aspiracional o calibrarse con datos de un piloto. |

