import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador y Diagnóstico Predictivo de Vibraciones",
    page_icon="⚙️",
    layout="wide",
)

st.title(
    "⚙️ Sistema Experto de Diagnóstico Predictivo y Trazabilidad de"
    " Vibraciones"
)
st.markdown(
    """
Este cuadro de mando interactivo permite realizar el seguimiento histórico trimestral de maquinaria rotativa, 
analizar tendencias de vibración (Velocidad, Aceleración, Desplazamiento y Envolvente) y 
diagnosticar fallas típicas mediante reglas expertas de ingeniería de confiabilidad.
"""
)


@st.cache_data
def cargar_base_maestra():
  fechas = [
      "2024-03-31",
      "2024-06-30",
      "2024-09-30",
      "2024-12-31",
      "2025-03-31",
      "2025-06-30",
      "2025-09-30",
      "2025-12-31",
      "2026-03-31",
      "2026-06-30",
  ]
  maquina = "Ventilador_Industrial_V01"
  puntos = [
      "Punto_1_Motor_Lado_Acople",
      "Punto_2_Motor_Lado_Opuesto",
      "Punto_3_Ventilador_Lado_Acople",
      "Punto_4_Ventilador_Lado_Opuesto",
  ]
  ejes = ["X", "Y", "Z"]

  rows = []
  np.random.seed(101)

  for idx, fecha in enumerate(fechas):
    factor_tiempo = 1.0 + (idx * 0.04)
    for pt in puntos:
      for eje in ejes:
        mult_eje = 1.0
        if eje == "X":
          mult_eje = 1.25 if "Ventilador" in pt else 1.1
        elif eje == "Z":
          mult_eje = 1.3 if "Motor_Lado_Opuesto" in pt else 1.05

        vel = round(
            np.random.uniform(1.2, 2.2) * factor_tiempo * mult_eje, 2
        )
        acel = round(np.random.uniform(0.15, 0.45) * factor_tiempo, 2)
        desp = round(
            np.random.uniform(25, 55)
            * factor_tiempo
            * (1.2 if eje == "X" else 1.0),
            1,
        )
        env = round(
            np.random.uniform(0.4, 1.2)
            * factor_tiempo
            * (1.4 if "Ventilador" in pt else 1.0),
            2,
        )

        if "Punto_3" in pt and idx >= 7:
          env = round(env * 2.2, 2)
          acel = round(acel * 1.8, 2)

        rows.append({
            "Fecha": fecha,
            "ID_Maquina": maquina,
            "Punto_Medicion": pt,
            "Eje": eje,
            "Velocidad_mm_s": vel,
            "Aceleracion_g": acel,
            "Desplazamiento_um": desp,
            "Envolvente_gE": env,
        })
  return pd.DataFrame(rows)


df_master = cargar_base_maestra()

modo = st.sidebar.selectbox(
    "Selecciona el Modo de Operación:",
    [
        "Base de Datos Maestra (Histórico de Planta)",
        "Cargar Nuevo Lugar / Trimestre (Diagnóstico Interactivo)",
    ],
)

if modo == "Base de Datos Maestra (Histórico de Planta)":
  st.subheader("📊 Historial y Evolución Trimestral (Últimos 2.5 Años)")

  maquina_sel = st.selectbox(
      "Seleccione la Máquina:", df_master["ID_Maquina"].unique()
  )
  puntos_disponibles = df_master[df_master["ID_Maquina"] == maquina_sel][
      "Punto_Medicion"
  ].unique()
  punto_sel = st.selectbox(
      "Seleccione el Punto de Medición:", puntos_disponibles
  )
  eje_sel = st.radio(
      "Seleccione el Eje de Medición:", ["X", "Y", "Z"], horizontal=True
  )

  # Filtro corregido con paréntesis correctos
  df_filtrado = df_master[
      (df_master["ID_Maquina"] == maquina_sel)
      & (df_master["Punto_Medicion"] == punto_sel)
      & (df_master["Eje"] == eje_sel)
  ].sort_values("Fecha")

  if not df_filtrado.empty:
    col1, col2 = st.columns(2)

    with col1:
      st.markdown("#### Tabla Histórica de Lecturas (Trimestre a Trimestre)")
      st.dataframe(df_filtrado, use_container_width=True)

    with col2:
      st.markdown("#### Tendencia de Velocidad RMS (mm/s)")
      st.line_chart(
          df_filtrado.set_index("Fecha")[["Velocidad_mm_s"]],
          use_container_width=True,
      )

    st.markdown("#### Evolución Multi-Variable en el Tiempo")
    st.line_chart(
        df_filtrado.set_index("Fecha")[
            ["Velocidad_mm_s", "Aceleracion_g", "Desplazamiento_um", "Envolvente_gE"]
        ],
        use_container_width=True,
    )

    st.subheader("🔍 Diagnóstico Experto Automatizado (Última Lectura)")
    ultima_fila = df_filtrado.iloc[-1]

    vel = ultima_fila.get("Velocidad_mm_s", 0)
    env = ultima_fila.get("Envolvente_gE", 0)
    desp = ultima_fila.get("Desplazamiento_um", 0)

    diagnosticos = []

    if eje_sel == "X" and vel > 2.5:
      diagnosticos.append(
          "⚠️ **Alerta de Desbalance:** Amplitud elevada en el eje Horizontal (X)."
          " El desbalance genera una fuerza centrífuga que se manifiesta"
          " fuertemente radial en la dirección horizontal."
      )

    if eje_sel == "Z" and vel > 2.2:
      diagnosticos.append(
          "⚠️ **Posible Soltura Mecánica o Estructural:** Niveles elevados en el"
          " eje Vertical (Z). Típico de holguras en bancadas, tornillos de"
          " anclaje flojos o juego en cojinetes."
      )

    if env > 1.5:
      diagnosticos.append(
          "🚨 **Impactos / Falla Incipiente de Rodamiento:** El valor de"
          " Envolvente de Aceleración (gE) supera el umbral, indicando"
          " fricción o impactos de alta frecuencia en las pistas o elementos"
          " rodantes."
      )

    if desp > 50:
      diagnosticos.append(
          "⚠️ **Exceso de Desplazamiento:** Valores altos en micras (µm)"
          " sugieren frecuencias bajas asociadas a desalineación o deflexión de"
          " ejes."
      )

    if not diagnosticos:
      st.success(
          "✅ Estado Operativo Normal: Los valores se encuentran dentro de los"
          " límites aceptables de severidad vibratoria."
      )
    else:
      for diag in diagnosticos:
        st.warning(diag)

  else:
    st.warning("No hay registros para la selección realizada.")
else:
  st.subheader("📂 Subir Nuevo Archivo de Lecturas (Trimestral)")
  st.markdown(
      "Sube tu archivo Excel con las nuevas mediciones tomadas en campo para"
      " ejecutar el diagnóstico automático y evaluar el comportamiento"
      " actual."
  )

  archivo_nuevo = st.file_uploader(
      "Selecciona el archivo Excel de vibraciones (.xlsx)", type=["xlsx"]
  )

  if archivo_nuevo is not None:
    df_nuevo = pd.read_excel(archivo_nuevo)
    st.success("¡Archivo personalizado cargado con éxito!")
    st.dataframe(df_nuevo.head(), use_container_width=True)

    st.markdown("### 🔬 Resultados del Diagnóstico por Reglas Expertas")

    for index, row in df_nuevo.iterrows():
      p = row.get("Punto_Medicion", "Punto Desconocido")
      e = row.get("Eje", "X")
      v = row.get("Velocidad_mm_s", 0)
      en = row.get("Envolvente_gE", 0)
      d = row.get("Desplazamiento_um", 0)

      estado = "Normal ✅"
      motivo = "Comportamiento vibratorio dentro de parámetros óptimos."

      if v > 3.0 and e == "X":
        estado = "Alerta ⚠️"
        motivo = (
            f"Alta velocidad ({v} mm/s) en eje X. Posible indicio de"
            " desbalance."
        )
      elif v > 2.5 and e == "Z":
        estado = "Alerta ⚠️"
        motivo = (
            f"Elevada vibración ({v} mm/s) en eje Z. Posible soltura mecánica."
        )
      if en > 1.8:
        estado = "Crítico 🚨"
        motivo = (
            f"Envolvente de aceleración alta ({en} gE). Alerta de daño en"
            " rodamientos."
        )

      st.markdown(
          f"**Punto:** {p} | **Eje:** {e} — **Estado:** `{estado}`"
      )
      st.caption(f"Diagnóstico experto: {motivo}")
  else:
    st.info(
        "Esperando archivo Excel... Asegúrate de mantener la misma estructura"
        " de columnas de la base maestra."
    )
