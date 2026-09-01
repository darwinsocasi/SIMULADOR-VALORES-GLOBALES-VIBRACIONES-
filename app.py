import glob
import os
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador y Diagnóstico Predictivo de Vibraciones",
    page_icon="⚙️",
    layout="wide",
)

st.title(
    "⚙️ Sistema Experto de Diagnóstico Predictivo y Trazabilidad de Vibraciones"
)
st.markdown(
    """
Este cuadro de mando interactivo permite realizar el seguimiento histórico trimestral de maquinaria rotativa, 
analizar tendencias de vibración (Velocidad, Aceleración, Desplazamiento y Envolvente) y 
diagnosticar fallas típicas mediante reglas expertas de ingeniería de confiabilidad.
"""
)

# Menú lateral para elegir el modo de trabajo
modo = st.sidebar.selectbox(
    "Selecciona el Modo de Operación:",
    [
        "Base de Datos Maestra (Histórico de Planta)",
        "Cargar Nuevo Lugar / Trimestre (Diagnóstico Interactivo)",
    ],
)

# Cargar Base Maestra de forma robusta
df_master = None
archivos_excel = glob.glob("*.xlsx")

excel_target = None
for f in archivos_excel:
  if "master_vibrations_db" in f.lower():
    excel_target = f
    break

if excel_target is None and len(archivos_excel) > 0:
  excel_target = archivos_excel[0]

if excel_target:
  try:
    df_master = pd.read_excel(excel_target)
  except Exception as e:
    st.sidebar.error(f"Error al leer {excel_target}: {e}")

if modo == "Base de Datos Maestra (Histórico de Planta)":
  st.subheader("📊 Historial y Evolución Trimestral (Últimos 2.5 Años)")

  if df_master is not None and not df_master.empty:
    maquina_sel = st.selectbox(
        "Seleccione la Máquina:", df_master["ID_Maquina"].unique()
    )
    puntos_disponibles = df_master[df_master["ID_Maquina"] == maquina_sel][
        "Punto_Medicion"
    ].unique()
    punto_sel = st.selectbox("Seleccione el Punto de Medición:", puntos_disponibles)
    eje_sel = st.radio("Seleccione el Eje de Medición:", ["X", "Y", "Z"], horizontal=True)

    df_filtrado = df_master[
        (df_master["ID_Maquina"] == maquina_sel)
        & (df_master["Punto_Medicion"] == punto_sel)
        & (df_master["Eje"] == eje_sel)
    ].sort_values("Fecha")

    if not df_filtrado.empty:
      col1, col2 = st.columns(2)

      with col1:
        st.markdown(
            "#### Tabla Histórica de Lecturas (Trimestre a Trimestre)"
        )
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
              [
                  "Velocidad_mm_s",
                  "Aceleracion_g",
                  "Desplazamiento_um",
                  "Envolvente_gE",
              ]
          ],
          use_container_width=True,
      )

      # --- MOTOR DE DIAGNÓSTICO EXPERTO (Última Lectura) ---
      st.subheader("🔍 Diagnóstico Experto Automatizado (Última Lectura)")
      ultima_fila = df_filtrado.iloc[-1]

      vel = ultima_fila.get("Velocidad_mm_s", 0)
      env = ultima_fila.get("Envolvente_gE", 0)
      desp = ultima_fila.get("Desplazamiento_um", 0)

      diagnosticos = []

      # Regla 1: Desbalance (Predominio en eje Horizontal X)
      if eje_sel == "X" and vel > 2.5:
        diagnosticos.append(
            "⚠️ **Alerta de Desbalance:** Amplitud elevada en el eje Horizontal"
            " (X). El desbalance genera una fuerza centrífuga que se manifiesta"
            " fuertemente radial en la dirección horizontal."
        )

      # Regla 2: Soltura Mecánica (Predominio en eje Vertical Z)
      if eje_sel == "Z" and vel > 2.2:
        diagnosticos.append(
            "⚠️ **Posible Soltura Mecánica o Estructural:** Niveles elevados en"
            " el eje Vertical (Z). Típico de holguras en bancadas, tornillos de"
            " anclaje flojos o juego en cojinetes."
        )

      # Regla 3: Falla de Rodamiento / Impactos (Alta Envolvente gE)
      if env > 1.5:
        diagnosticos.append(
            "🚨 **Impactos / Falla Incipiente de Rodamiento:** El valor de"
            " Envolvente de Aceleración (gE) supera el umbral, indicando"
            " fricción o impactos de alta frecuencia en las pistas o elementos"
            " rodantes."
        )

      # Regla 4: Problema de Bajas Frecuencias / Desalineación (Alto Desplazamiento)
      if desp > 50:
        diagnosticos.append(
            "⚠️ **Exceso de Desplazamiento:** Valores altos en micras (µm)"
            " sugieren frecuencias bajas asociadas a desalineación o deflexión"
            " de ejes."
        )

      if not diagnosticos:
        st.success(
            "✅ Estado Operativo Normal: Los valores se encuentran dentro de"
            " los límites aceptables de severidad vibratoria."
        )
      else:
        for diag in diagnosticos:
          st.warning(diag)

    else:
      st.warning("No hay registros para la selección realizada.")
  else:
    st.error(
        "No se encontró ningún archivo Excel (.xlsx) en el repositorio."
        " Asegúrate de haber subido 'master_vibrations_db.xlsx'."
    )

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
