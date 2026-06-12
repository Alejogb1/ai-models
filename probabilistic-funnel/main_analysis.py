"""
Analisis de viabilidad QR vs estrategia multicanal
Naturgy Argentina - Propuesta universitaria

Modelo probabilistico de conversion digital con 5 modulos:
  A: QR solo (cadena de conversion fragil)
  B: Multicanal (entrada combinada con solapamiento)
  C: Umbral necesario para meta del 10%
  D: Escenarios (4 combinaciones)
  E: Impacto economico ajustado por retencion
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

warnings.filterwarnings("ignore")

# ============================================================
# CONSTANTES GLOBALES
# ============================================================
UNIVERSO = 536842
META_USUARIOS = 53684  # 10% del universo
RUTA_DATA = os.path.join(os.path.dirname(__file__), "data")
RUTA_OUTPUT = os.path.join(os.path.dirname(__file__), "output")
RUTA_CHARTS = os.path.join(RUTA_OUTPUT, "charts")

# ============================================================
# 0. CARGA DE DATOS
# ============================================================

def cargar_supuestos():
    path = os.path.join(RUTA_DATA, "assumptions.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df

def cargar_escenarios():
    path = os.path.join(RUTA_DATA, "scenario_inputs.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df

# ============================================================
# VALIDACIONES
# ============================================================

def validar_probabilidades(df_escenarios):
    prob_cols = [
        "entrada_QR", "entrada_FonoGas", "entrada_NaturgyPIC",
        "entrada_marketing", "entrada_incentivo", "entrada_pago_digital",
        "completa_formulario", "valida_email", "consentimiento",
        "primer_acceso", "retencion"
    ]
    errores = []
    for col in prob_cols:
        if col in df_escenarios.columns:
            vals = df_escenarios[col].values
            if np.any(vals < 0) or np.any(vals > 1):
                errores.append(f"{col}: valores fuera de [0, 1]")
    if UNIVERSO <= 0:
        errores.append("UNIVERSO debe ser positivo")
    if META_USUARIOS <= 0:
        errores.append("META_USUARIOS debe ser positivo")
    if META_USUARIOS > UNIVERSO:
        errores.append("META_USUARIOS no puede superar UNIVERSO")
    return errores

def validar_resultados(resultados):
    advertencias = []
    for _, row in resultados.iterrows():
        if row["conversion_final"] > row["entrada_al_flujo"]:
            advertencias.append(
                f"{row['escenario']}: conversion final ({row['conversion_final']:.4f}) "
                f"> entrada al flujo ({row['entrada_al_flujo']:.4f})"
            )
        if row["usuarios_verificados"] > UNIVERSO:
            advertencias.append(
                f"{row['escenario']}: usuarios verificados > universo"
            )
    return advertencias

# ============================================================
# MODULO A: MODELO QR SOLO
# ============================================================

def calcular_qr_solo(entrada_qr, p_form, p_email, p_consent, p_acceso, p_ret):
    """
    Cadena de conversion completa para QR como unico canal de entrada.
    """
    entrada = entrada_qr
    finalizacion = p_form * p_email * p_consent * p_acceso
    conversion_final = entrada * finalizacion
    verificados = UNIVERSO * conversion_final * p_ret
    return {
        "entrada_al_flujo": entrada,
        "finalizacion": finalizacion,
        "conversion_final": conversion_final,
        "usuarios_verificados": verificados,
        "retencion": p_ret
    }

# ============================================================
# MODULO B: MODELO MULTICANAL
# ============================================================

def entrada_combinada(tasas, factor_solapamiento=1.0):
    """
    Probabilidad combinada: 1 - productorio de (1 - p_i)
    Asume independencia entre canales (simplificacion).
    factor_solapamiento penaliza la sobreestimacion.
    """
    p_no_entrar = np.prod([1 - t for t in tasas])
    p_entrar = 1 - p_no_entrar
    return p_entrar * factor_solapamiento

def calcular_multicanal(row, factor_solapamiento):
    tasas = [
        row["entrada_QR"], row["entrada_FonoGas"],
        row["entrada_NaturgyPIC"], row["entrada_marketing"],
        row["entrada_incentivo"], row["entrada_pago_digital"]
    ]
    entrada = entrada_combinada(tasas, factor_solapamiento)
    p_form = row["completa_formulario"]
    p_email = row["valida_email"]
    p_consent = row["consentimiento"]
    p_acceso = row["primer_acceso"]
    p_ret = row["retencion"]
    finalizacion = p_form * p_email * p_consent * p_acceso
    conversion_final = entrada * finalizacion
    verificados = UNIVERSO * conversion_final * p_ret
    return {
        "entrada_al_flujo": entrada,
        "finalizacion": finalizacion,
        "conversion_final": conversion_final,
        "usuarios_verificados": verificados,
        "retencion": p_ret
    }

# ============================================================
# MODULO C: UMBRAL NECESARIO
# ============================================================

def calcular_umbrales():
    tasas_finalizacion = np.arange(0.10, 0.75, 0.05)
    entrada_requerida = META_USUARIOS / (UNIVERSO * tasas_finalizacion)
    df = pd.DataFrame({
        "tasa_finalizacion": tasas_finalizacion,
        "entrada_requerida": entrada_requerida
    })
    df["entrada_requerida_pct"] = df["entrada_requerida"] * 100
    return df

# ============================================================
# MODULO D: ESCENARIOS
# ============================================================

def evaluar_escenarios(df_escenarios):
    resultados = []
    for _, row in df_escenarios.iterrows():
        nombre = row["escenario"]
        es_solo_qr = "QR solo" in nombre
        if es_solo_qr:
            res = calcular_qr_solo(
                row["entrada_QR"],
                row["completa_formulario"],
                row["valida_email"],
                row["consentimiento"],
                row["primer_acceso"],
                row["retencion"]
            )
        else:
            res = calcular_multicanal(row, factor_solapamiento=0.80)
        res["escenario"] = nombre
        res["distancia_meta"] = res["usuarios_verificados"] - META_USUARIOS
        res["alcanza_meta"] = "Si" if res["usuarios_verificados"] >= META_USUARIOS else "No"
        resultados.append(res)
    df = pd.DataFrame(resultados)
    cols = [
        "escenario", "entrada_al_flujo", "finalizacion", "retencion",
        "conversion_final", "usuarios_verificados", "distancia_meta", "alcanza_meta"
    ]
    return df[cols]

# ============================================================
# MODULO E: IMPACTO ECONOMICO
# ============================================================

def _lookup(df, variable, col, default):
    try:
        return df.loc[df["variable"] == variable, col].values[0]
    except (IndexError, KeyError, TypeError):
        return default

def calcular_impacto_economico(resultados, supuestos):
    """
    Ahorro bruto sobre usuarios verificados y retenidos.
    Ahorro neto descontando incentivos, campana y asistencia.
    """
    col = "valor_moderado"
    costo_factura = _lookup(supuestos, "costo_factura_fisica_ARS", col, 1500)
    costo_incentivo = _lookup(supuestos, "costo_incentivo_por_usuario_ARS", col, 4000)
    costo_campana_total = _lookup(supuestos, "costo_campana_total_ARS", col, 5000000)
    costo_asistencia_total = _lookup(supuestos, "costo_asistencia_total_ARS", col, 3000000)

    ciclos = 6

    filas = []
    for _, row in resultados.iterrows():
        nombre = row["escenario"]
        usuarios = row["usuarios_verificados"]

        ahorro_bruto = usuarios * costo_factura * ciclos

        costo_incentivos = usuarios * costo_incentivo

        ahorro_neto = ahorro_bruto - costo_incentivos - costo_campana_total - costo_asistencia_total

        if costo_factura > 0 and ciclos > 0:
            payback_meses = costo_incentivo / (costo_factura * (ciclos / 12))
        else:
            payback_meses = float("inf")

        # Sensibilidad sobre costos de campaña y asistencia
        ahorro_neto_sin_costos = ahorro_bruto
        ahorro_neto_costos_bajos = ahorro_bruto - costo_incentivos - costo_campana_total * 0.3 - costo_asistencia_total * 0.3
        ahorro_neto_costos_altos = ahorro_bruto - costo_incentivos - costo_campana_total * 2.0 - costo_asistencia_total * 2.0

        filas.append({
            "escenario": nombre,
            "usuarios_verificados": usuarios,
            "ahorro_bruto_ARS": ahorro_bruto,
            "costo_incentivos_ARS": costo_incentivos,
            "costo_campana_ARS": costo_campana_total,
            "costo_asistencia_ARS": costo_asistencia_total,
            "ahorro_neto_ARS": ahorro_neto,
            "ahorro_neto_sin_costos_adicionales_ARS": ahorro_neto_sin_costos,
            "ahorro_neto_costos_bajos_ARS": ahorro_neto_costos_bajos,
            "ahorro_neto_costos_altos_ARS": ahorro_neto_costos_altos,
            "payback_incentivo_meses": payback_meses
        })
    return pd.DataFrame(filas)

# ============================================================
# GRAFICOS
# ============================================================

def grafico_1_comparacion(resultados):
    """Barras: usuarios verificados por escenario vs meta."""
    fig, ax = plt.subplots(figsize=(10, 6))
    nombres = resultados["escenario"].values
    valores = resultados["usuarios_verificados"].values
    colores = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]

    ax.bar(nombres, valores, color=colores, edgecolor="black", linewidth=0.5)
    ax.axhline(y=META_USUARIOS, color="red", linestyle="--", linewidth=2,
               label=f"Meta: {META_USUARIOS:,.0f} usuarios")
    ax.set_ylabel("Usuarios digitales verificados")
    ax.set_title("Escenario vs Meta de conversion (10% del universo)")
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    for i, v in enumerate(valores):
        ax.text(i, v + max(valores) * 0.01,
                f"{v:,.0f}\n({v / UNIVERSO * 100:.2f}%)",
                ha="center", fontsize=9)

    plt.xticks(rotation=15)
    plt.tight_layout()
    path = os.path.join(RUTA_CHARTS, "qr_vs_multichannel.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def grafico_2_umbral(df_umbral):
    """Linea: entrada requerida segun tasa de finalizacion."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_umbral["tasa_finalizacion"] * 100,
            df_umbral["entrada_requerida"] * 100,
            marker="o", color="#1f77b4", linewidth=2)
    ax.axhline(y=10, color="red", linestyle="--", alpha=0.5,
               label="Meta de conversion: 10%")
    ax.set_xlabel("Tasa de finalizacion despues de entrar (%)")
    ax.set_ylabel("Entrada al flujo requerida (%)")
    ax.set_title("Umbral de entrada necesario segun tasa de finalizacion")
    ax.legend()
    ax.grid(True, alpha=0.3)

    for _, row in df_umbral.iterrows():
        ax.annotate(
            f"{row['entrada_requerida_pct']:.1f}%",
            (row["tasa_finalizacion"] * 100, row["entrada_requerida"] * 100),
            textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=8)

    plt.tight_layout()
    path = os.path.join(RUTA_CHARTS, "threshold_required.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def grafico_3_embudo_qr():
    """Embudo QR: caida por etapas usando escenario moderado."""
    etapas = [
        "Universo\n536.842",
        "Nota QR\n(3%)",
        "Escanea QR\n(3%)",
        "Carga email\n(40%)",
        "Valida email\n(60%)",
        "Consentimiento\n(70%)",
        "Primer acceso\n(35%)",
        "Permanencia\n(85%)"
    ]
    universo = UNIVERSO
    valores = [
        universo,
        universo * 0.03,
        universo * 0.03,
        universo * 0.03 * 0.40,
        universo * 0.03 * 0.40 * 0.60,
        universo * 0.03 * 0.40 * 0.60 * 0.70,
        universo * 0.03 * 0.40 * 0.60 * 0.70 * 0.35,
        universo * 0.03 * 0.40 * 0.60 * 0.70 * 0.35 * 0.85
    ]

    fig, ax = plt.subplots(figsize=(12, 6))
    colors_bar = ["#1f77b4"] * 2 + ["#ff7f0e"] * 5 + ["#d62728"]
    ax.barh(etapas, valores, color=colors_bar, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Clientes")
    ax.set_title("Embudo de conversion QR solo (escenario moderado)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    for i, v in enumerate(valores):
        pct = v / universo * 100
        ax.text(v + max(valores) * 0.005, i, f"{v:,.0f} ({pct:.2f}%)",
                va="center", fontsize=9)

    plt.tight_layout()
    path = os.path.join(RUTA_CHARTS, "funnel_qr.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def grafico_4_economico(df_economico):
    """Barras: ahorro bruto vs neto por escenario."""
    fig, ax = plt.subplots(figsize=(10, 6))
    nombres = df_economico["escenario"].values
    x = np.arange(len(nombres))
    ancho = 0.35

    ax.bar(x - ancho / 2, df_economico["ahorro_bruto_ARS"].values / 1e6,
           ancho, label="Ahorro bruto", color="#2ca02c", edgecolor="black", linewidth=0.5)
    ax.bar(x + ancho / 2, df_economico["ahorro_neto_ARS"].values / 1e6,
           ancho, label="Ahorro neto", color="#1f77b4", edgecolor="black", linewidth=0.5)
    ax.axhline(y=0, color="gray", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=15)
    ax.set_ylabel("ARS (millones)")
    ax.set_title("Impacto economico: ahorro bruto vs ahorro neto")
    ax.legend()

    for i in range(len(nombres)):
        ax.text(i - ancho / 2, df_economico["ahorro_bruto_ARS"].values[i] / 1e6 + 0.5,
                f"${df_economico['ahorro_bruto_ARS'].values[i]/1e6:.1f}M",
                ha="center", fontsize=8)
        neto = df_economico["ahorro_neto_ARS"].values[i] / 1e6
        ax.text(i + ancho / 2, neto + 0.5 if neto > 0 else neto - 2,
                f"${neto:.1f}M",
                ha="center", fontsize=8, color="red" if neto < 0 else "black")

    plt.tight_layout()
    path = os.path.join(RUTA_CHARTS, "economic_impact.png")
    plt.savefig(path, dpi=150)
    plt.close()
    return path

# ============================================================
# EXPORTACION A CSV
# ============================================================

def exportar_csv(df, nombre):
    path = os.path.join(RUTA_OUTPUT, nombre)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("ANALISIS DE VIABILIDAD: QR vs ESTRATEGIA MULTICANAL")
    print("Universo:", UNIVERSO)
    print("Meta (10%):", META_USUARIOS)
    print("=" * 60)

    # --- CARGA ---
    supuestos = cargar_supuestos()
    escenarios = cargar_escenarios()
    print("\n[OK] Supuestos cargados:", len(supuestos), "variables")
    print("[OK] Escenarios cargados:", len(escenarios), "configuraciones")

    # --- VALIDACION ---
    errores = validar_probabilidades(escenarios)
    if errores:
        print("\n!!! PROBLEMAS DETECTADOS EN SUPUESTOS O DATOS:")
        for e in errores:
            print("  -", e)
        return
    print("[OK] Validaciones de probabilidad superadas")

    # --- MODULO A y B: EVALUAR ESCENARIOS ---
    resultados = evaluar_escenarios(escenarios)
    print("[OK] Escenarios evaluados")

    # --- VALIDACION DE RESULTADOS ---
    advertencias = validar_resultados(resultados)
    if advertencias:
        print("\n!!! ADVERTENCIAS EN RESULTADOS:")
        for a in advertencias:
            print("  -", a)

    # --- MODULO C: UMBRALES ---
    df_umbral = calcular_umbrales()
    print("[OK] Umbrales calculados")

    # --- MODULO E: IMPACTO ECONOMICO ---
    df_economico = calcular_impacto_economico(resultados, supuestos)
    print("[OK] Impacto economico calculado")

    # --- EXPORTAR CSVs ---
    path_supuestos = exportar_csv(supuestos, "assumptions_table.csv")
    path_resultados = exportar_csv(resultados, "scenario_results.csv")
    path_umbral = exportar_csv(df_umbral, "threshold_table.csv")
    path_economico = exportar_csv(df_economico, "economic_impact.csv")
    print("\n[OK] Archivos exportados:")
    print("  -", path_supuestos)
    print("  -", path_resultados)
    print("  -", path_umbral)
    print("  -", path_economico)

    # --- GRAFICOS ---
    p1 = grafico_1_comparacion(resultados)
    p2 = grafico_2_umbral(df_umbral)
    p3 = grafico_3_embudo_qr()
    p4 = grafico_4_economico(df_economico)
    print("[OK] Graficos generados:")
    print("  -", p1)
    print("  -", p2)
    print("  -", p3)
    print("  -", p4)

    # ============================================================
    # TABLA DE ESCENARIOS (presentacion)
    # ============================================================
    print("\n" + "=" * 60)
    print("TABLA DE ESCENARIOS")
    print("=" * 60)
    for _, row in resultados.iterrows():
        dist = row["distancia_meta"]
        dist_text = f"{(dist / META_USUARIOS * 100):+.1f}%" if META_USUARIOS > 0 else "N/A"
        print(f"\n{row['escenario']}:")
        print(f"  Entrada al flujo:   {row['entrada_al_flujo']*100:.2f}%")
        print(f"  Finalizacion:       {row['finalizacion']*100:.2f}%")
        print(f"  Retencion:          {row['retencion']*100:.0f}%")
        print(f"  Conversion final:   {row['conversion_final']*100:.4f}%")
        print(f"  Usuarios verificados: {row['usuarios_verificados']:,.0f}")
        print(f"  Distancia a meta:   {dist_text}")
        print(f"  Alcanza meta:       {row['alcanza_meta']}")

    # ============================================================
    # TABLA DE UMBRAL (presentacion)
    # ============================================================
    print("\n" + "=" * 60)
    print("TABLA DE UMBRAL: ENTRADA REQUERIDA vs FINALIZACION")
    print("=" * 60)
    print(f"{'Finalizacion':>15} | {'Entrada requerida':>18}")
    print("-" * 35)
    for _, row in df_umbral.iterrows():
        print(f"{row['tasa_finalizacion']*100:>13.0f}% | {row['entrada_requerida_pct']:>16.1f}%")

    # ============================================================
    # RESPUESTA A LAS 10 PREGUNTAS
    # ============================================================
    print("\n" + "=" * 60)
    print("RESPUESTAS A LAS 10 PREGUNTAS SELECCIONADAS")
    print("=" * 60)

    qr_cons = resultados[resultados["escenario"] == "QR solo conservador"]
    qr_mod = resultados[resultados["escenario"] == "QR solo moderado"]
    mc_mod = resultados[resultados["escenario"] == "Multicanal moderado"]
    mc_fuerte = resultados[resultados["escenario"] == "Multicanal fuerte"]

    q1 = f"1. QR solo conservador genera {qr_cons['usuarios_verificados'].values[0]:,.0f} usuarios; QR solo moderado genera {qr_mod['usuarios_verificados'].values[0]:,.0f} usuarios."
    print(q1)

    def _match_tasa(tasa):
        return df_umbral.loc[np.isclose(df_umbral["tasa_finalizacion"], tasa)]
    q2 = f"2. Para llegar a {META_USUARIOS:,} usuarios: si finalizacion=30% se necesita {_match_tasa(0.30)['entrada_requerida_pct'].values[0]:.1f}% de entrada; si finalizacion=50% se necesita {_match_tasa(0.50)['entrada_requerida_pct'].values[0]:.1f}%."
    print(q2)

    q3 = "3. Para hacer plausible la meta con entrada <20%, la finalizacion debe ser >=50%."
    print(q3)

    q4 = f"4. Multicanal moderado alcanza {mc_mod['usuarios_verificados'].values[0]:,.0f} usuarios vs {qr_mod['usuarios_verificados'].values[0]:,.0f} de QR solo moderado. La multicanalidad aumenta entrada en ~{((mc_mod['entrada_al_flujo'].values[0]/qr_mod['entrada_al_flujo'].values[0])-1)*100:.0f}%."
    print(q4)

    # Canal mas importante: sensitivity analysis
    canales = ["QR", "FonoGas", "NaturgyPIC", "Marketing", "Incentivo"]
    aportes = [0.03, 0.03, 0.02, 0.03, 0.02]
    solo_qr = 1 - (1 - 0.03)
    con_qr_fono = 1 - (1 - 0.03) * (1 - 0.03)
    con_qr_fono_natu = 1 - (1 - 0.03) * (1 - 0.03) * (1 - 0.02)
    con_qr_fono_natu_mkt = 1 - (1 - 0.03) * (1 - 0.03) * (1 - 0.02) * (1 - 0.03)
    con_todos = 1 - (1 - 0.03) * (1 - 0.03) * (1 - 0.02) * (1 - 0.03) * (1 - 0.02)
    print(f"5. Sensibilidad de canales (entrada combinada): QR solo={solo_qr*100:.1f}%, +FonoGas={con_qr_fono*100:.1f}%, +NaturgyPIC={con_qr_fono_natu*100:.1f}%, +Marketing={con_qr_fono_natu_mkt*100:.1f}%, todos={con_todos*100:.1f}%.")
    print("   El canal mas importante es el que mas contribuye a entrada y finalizacion. FonoGas y NaturgyPIC destacan porque ademas mejoran la finalizacion (asistencia).")

    q6 = f"6. Meta realista en: Multicanal fuerte ({mc_fuerte['alcanza_meta'].values[0]}, {mc_fuerte['usuarios_verificados'].values[0]:,.0f} usuarios)."
    print(q6)

    q7 = f"7. Meta demasiado optimista en: QR solo conservador ({qr_cons['alcanza_meta'].values[0]}), QR solo moderado ({qr_mod['alcanza_meta'].values[0]}), Multicanal moderado ({mc_mod['alcanza_meta'].values[0]})."
    print(q7)

    if not df_economico.empty:
        fila_ref = df_economico.iloc[0]
        q8 = f"8. Ahorro bruto maximo: ${df_economico['ahorro_bruto_ARS'].max():,.0f} ARS; ahorro neto maximo: ${df_economico['ahorro_neto_ARS'].max():,.0f} ARS."
        print(q8)

        q9 = "9. El incentivo reduce el ahorro neto. Con incentivo de $4,000 por usuario y 6 ciclos anuales a $1,500/factura, el payback es de aproximadamente 5.3 meses."
        print(q9)

    q10 = "10. Datos que Naturgy deberia proveer para validar: (a) tasa de escaneo QR real en factura piloto, (b) volumen FonoGas y tasa de conversion asistida, (c) MAU/DAU NaturgyPIC y funnel de factura digital, (d) costo real por factura fisica (impresion+distribucion), (e) tasa de reenvio post-adhesion, (f) % de clientes sin email valido."
    print(q10)

    # ============================================================
    # CONCLUSION
    # ============================================================
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print("""
Bajo estos supuestos, QR solo no alcanza la meta en ningun escenario.
Multicanal moderado multiplica la entrada (~10.6%) pero la finalizacion interna (12.6%) limita la conversion.
Multicanal fuerte es el unico que se acerca (29,401 usuarios, 45% de la meta), pero requiere tasas de finalizacion muy altas (29.8%) para lograrlo.
Ningun escenario alcanza la meta de 53,684 usuarios con los supuestos actuales.
La estrategia multicanal es necesaria pero no suficiente: se requieren tasas de entrada y finalizacion superiores a los benchmarks disponibles.

- QR actua como entrada, pero es debil si esta aislado.
- Marketing (redes, TV, pantallas) aumenta reconocimiento y confianza.
- FonoGas proporciona asistencia para adultos mayores y brecha digital.
- NaturgyPIC facilita la finalizacion y el primer acceso.
- Incentivos motivan la conversion inicial.
- Alertas y recordatorios son esenciales para la retencion.
- La meta del 10% debe tratarse como objetivo aspiracional, no como resultado garantizado.
""")


if __name__ == "__main__":
    main()
