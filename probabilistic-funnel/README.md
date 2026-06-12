# Análisis de Viabilidad: QR vs Estrategia Multicanal

**Proyecto:** Naturgy Argentina — Propuesta universitaria
**Objetivo:** Evaluar si una estrategia basada en QR en factura física, reforzada por marketing multicanal, FonoGas, NaturgyPIC e incentivos, puede hacer plausible una meta de conversión digital del 10% mensual (53,684 usuarios).

## Estructura del proyecto

```
probabilistic-funnel/
├── data/
│   ├── assumptions.csv          # Supuestos en 3 niveles (conservador, moderado, fuerte)
│   └── scenario_inputs.csv     # Inputs para los 4 escenarios
├── output/
│   ├── assumptions_table.csv   # Tabla de supuestos completa
│   ├── scenario_results.csv    # Resultados por escenario
│   ├── threshold_table.csv     # Umbral de entrada requerida vs finalización
│   ├── economic_impact.csv     # Impacto económico ajustado
│   └── charts/
│       ├── qr_vs_multichannel.png   # Barras: escenarios vs meta
│       ├── threshold_required.png   # Línea: entrada requerida según finalización
│       ├── funnel_qr.png            # Embudo QR etapa por etapa
│       └── economic_impact.png      # Ahorro bruto vs neto
├── main_analysis.py            # Código principal de análisis
└── README.md
```

## Metodología

### 5 módulos de análisis

| Módulo | Descripción |
|--------|-------------|
| **A: QR solo** | Cadena de conversión frágil: entrada × formulario × validación email × consentimiento × primer acceso × retención |
| **B: Multicanal** | Entrada combinada: 1 − ∏(1 − p_i) con penalización por solapamiento |
| **C: Umbral** | Entrada requerida = meta / (universo × tasa_finalización) |
| **D: Escenarios** | 4 escenarios (QR conservador, QR moderado, multicanal moderado, multicanal fuerte) |
| **E: Impacto económico** | Ahorro bruto − incentivos − campaña − asistencia. Payback del incentivo |

### Fuentes de datos

Los supuestos se basan en el `deep-research-report.md` que compila benchmarks de:
- Tasa de escaneo QR: Ramin Zamani, How Advertising Matters
- Abandono de formularios móviles: Tinyform, Zuko
- Validación de email: Startup Stash, Medium Case Study
- Consentimiento opt-in: Questline Digital
- Primer acceso: Questline Energy Benchmarks
- Retención paperless: Fiserv
- Incentivos: EPAS Neuquén, Camuzzi
- Costos: Servicios Públicos, Paylode, Facebook CPM, WhatsApp Business API

## Resultados clave

### Escenarios evaluados

| Escenario | Entrada | Finalización | Conversión | Usuarios | ¿Alcanza meta? |
|-----------|:------:|:-----------:|:----------:|:--------:|:--------------:|
| QR solo conservador | 1.0% | 1.0% | 0.010% | 38 | No |
| QR solo moderado | 3.0% | 5.9% | 0.176% | 805 | No |
| Multicanal moderado | 10.6% | 12.6% | 1.33% | 6,082 | No |
| Multicanal fuerte | 19.3% | 29.8% | 5.76% | 29,401 | No |

### Umbral necesario

Para alcanzar la meta de 53,684 usuarios:
- Si la finalización es del 30% → se necesita 33.3% de entrada
- Si la finalización es del 50% → se necesita 20.0% de entrada

### Impacto económico

- Ahorro bruto máximo (multicanal fuerte): $264.6M ARS/año
- Ahorro neto (con costos moderados): $139.0M ARS/año
- Payback del incentivo ($4,000/usuario): ~5.3 meses

## Conclusiones

1. **QR solo es insuficiente** en todos los escenarios. La cadena de conversión es demasiado frágil.
2. **La multicanalidad multiplica la entrada** (~3x a ~6x vs QR solo), pero no es suficiente por sí sola.
3. **Ningún escenario alcanza la meta del 10%** con los supuestos actuales basados en benchmarks.
4. **El escenario multicanal fuerte se acerca** (45% de la meta), pero requiere tasas de finalización muy superiores a los benchmarks disponibles.
5. **La meta del 10% debe tratarse como objetivo aspiracional**, no como resultado garantizado.
6. **Se necesita un piloto** con datos reales de Naturgy para calibrar los supuestos.

## Resumen ejecutivo (para presentación)

> El análisis evalúa la crítica de que el QR físico puede pasar desapercibido.
> Modelamos QR solo como una cadena de conversión y lo comparamos contra una entrada multicanal.
> Los escenarios muestran que QR solo requiere tasas de escaneo muy altas para alcanzar la meta.
> La estrategia multicanal se justifica si aumenta entrada y finalización mediante reconocimiento, FonoGas, NaturgyPIC e incentivos.
> Bajo los supuestos actuales (basados en benchmarks), ningún escenario alcanza la meta de 53,684 usuarios.
> El multicanal fuerte llega a 29,401 (45% de la meta), lo que muestra que el objetivo del 10% es muy ambicioso.
> La meta debe tratarse como objetivo validable, no como resultado garantizado.
> Se recomienda un piloto con datos reales para calibrar tasas de escaneo, validación y retención.
> El ahorro neto máximo estimado es de ~$139M ARS/año, con payback de incentivo en 5.3 meses.

## Preguntas respondidas

| # | Pregunta | Respuesta |
|---|----------|-----------|
| 10 | ¿Qué % notaría el QR? | Modelado como p_escanea_QR: 1-5% según escenario |
| 14 | ¿Qué % escanearía el QR? | 1% conservador, 3% moderado, 5% fuerte |
| 35 | ¿Entrada necesaria si completa 30%? | 33.3% del universo debe entrar al flujo |
| 38 | ¿QR solo puede generar esa entrada? | No. QR solo genera máximo 3% de entrada |
| 43 | ¿Solapamiento de canales? | Modelado con factor 0.80 (moderado), 0.65 (alto) |
| 45 | ¿Conversión con QR bajo? | 0.01% (38 usuarios) en escenario conservador |
| 46 | ¿Multicanal duplica entrada? | Sí: 10.6% vs 3%, más de 3x de aumento |
| 53 | ¿En cuál escenario llega al 10%? | En ninguno con los supuestos actuales |
| 58 | ¿Ahorro sobre papel evitado? | $264.6M ARS bruto/año en escenario fuerte |
| 65 | ¿Punto de equilibrio incentivo? | ~5.3 meses para recuperar $4,000 por usuario |

## Cómo ejecutar

```bash
cd probabilistic-funnel
python main_analysis.py
```

## Requisitos

- Python 3.8+
- pandas
- numpy
- matplotlib
