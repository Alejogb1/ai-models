# Síntesis de modelado — versión simple

## El modelo en 3 líneas

```
usuario_verificado = universo × (entrada) × (formulario × email × consentimiento × acceso) × (retención)
                     ↓               ↓                                                ↓
                  536.842       canales QR,          tasa de abandono en cada etapa    3 ciclos sin
                                FonoGas, app,                                        volver a papel
                                marketing,
                                incentivo
```

Cada flecha multiplica. Si una etapa es débil, arruina todo el resultado.

---

## Lo que NO es el modelo

| No es | Es |
|-------|----|
| Una predicción de cuántos usuarios van a llegar | Un **límite máximo** bajo los benchmarks disponibles |
| Un simulador de marketing | Un **framework de restricciones**: "si X, entonces Y" |
| Una respuesta "sí o no" | Un **mapa** de lo que tendría que pasar para llegar a la meta |

---

## Las 3 decisiones de modelado más importantes

### 1. Los canales son independientes

Cuando combinamos QR + FonoGas + app + marketing, usamos:

```
P(entrar) = 1 - (1-p_QR)(1-p_FonoGas)(1-p_app)(1-p_marketing)
```

Esto **maximiza** la entrada. En la vida real los canales se solapan (el mismo cliente aparece en varios). Por eso aplicamos un factor de castigo del 0,80.

### 2. Las probabilidades son fijas

Asumimos que la campaña funciona igual de bien el mes 1 que el mes 12. En la realidad, las tasas caen con el tiempo (saturación, fatiga). Esto **sobreestima** los resultados.

### 3. No hay competencia de atención

Asumimos que el cliente mira la factura con atención solo para nosotros. En la realidad recibe otras 20 comunicaciones por día. Esto **sobreestima** las tasas de escaneo y lectura.

**Conclusión:** los números del modelo son **máximos teóricos**. La realidad será peor.

---

## La tabla que lo resume todo

| Escenario | Entrada | × Finalización | × Retención | = Usuarios | ¿Meta? |
|-----------|:-------:|:--------------:|:-----------:|:----------:|:------:|
| QR solo conservador | 1% | × 1% | × 70% | **38** | No |
| QR solo moderado | 3% | × 5,9% | × 85% | **805** | No |
| Multicanal moderado | 10,6% | × 12,6% | × 85% | **6.082** | No |
| Multicanal fuerte | 19,3% | × 29,8% | × 95% | **29.401** | No |

**Ninguno llega a 53.684.**

---

## Por qué no se llega

Es matemática, no opinión:

```
Meta: 53.684 usuarios
Universo: 536.842 clientes
Tasa necesaria: 53.684 / 536.842 = 10%
```

Para llegar al 10% necesitamos que:

**entrada × finalización × retención = 10%**

Con una retención del 85%:

**entrada × finalización = 11,8%**

| Si la finalización es... | La entrada necesita ser... | ¿Alcanzable? |
|:------------------------:|:-------------------------:|:------------:|
| 10% | 118% | Imposible (no hay más del 100%) |
| 20% | 59% | Inviable |
| 30% | 39% | Multicanal fuerte da 19% |
| 50% | 24% | Multicanal fuerte da 19% |
| 80% | 15% | Posible, pero nadie reporta 80% de finalización |

No hay atajo. No alcanza con "esforzarse más".

---

## La pregunta que el modelo responde

**No** responde: "¿la campaña funciona?"

**Responde:** "¿qué tendría que ser cierto para que la campaña funcione?"

Respuesta: las tasas reales de Naturgy tendrían que duplicar los benchmarks internacionales. Si alguien tiene evidencia de que eso es posible, el modelo se recalcula. Si no, la meta del 10% no es defendible.

---

## Las 5 cosas que cambiarían el resultado

Si Naturgy diera estos datos, el modelo daría otra respuesta:

1. **Tasa de escaneo QR real** en un piloto (hoy asumimos 1-5%)
2. **Volumen FonoGas** y cuántos se adhieren en la llamada (hoy asumimos 1-5%)
3. **Usuarios activos de NaturgyPIC** y cuántos ven la factura (hoy asumimos 1-5%)
4. **Costo real por factura física** (hoy asumimos $1.500)
5. **Tasa de reenvío post-adhesión** (hoy no tenemos dato)

Sin esos 5 datos, el modelo es exploratorio, no concluyente.

---

## Traducción a una diapositiva de presentación

> El análisis muestra que el QR por sí solo es irrelevante (38 usuarios en el mejor caso conservador).
> La multicanalidad mejora los resultados 100x pero no alcanza la meta del 10%.
> Incluso duplicando los benchmarks internacionales (escenario fuerte), solo llegamos a 29.401 usuarios — el 55% de la meta.
> Para alcanzar 53.684 se necesitarían tasas que no tienen respaldo en la literatura.
> La meta del 10% debe tratarse como objetivo aspiracional, no como resultado garantizado.
> Proponemos validar con un piloto que genere los datos que hoy no existen.
