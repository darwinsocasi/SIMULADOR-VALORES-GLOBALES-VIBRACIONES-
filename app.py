import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador y Diagnóstico Predictivo de Vibraciones",
    page_icon="⚙️",
    layout="wide",
)

st.title(
    "⚙️ Sistema Experto de Diagnóstico Predictivo y Espectro FFT en Línea"
)
st.markdown(
    """
Plataforma de ingeniería para el seguimiento histórico trimestral, análisis del espectro de frecuencias (FFT), 
diagnóstico por reglas expertas y pronóstico de tendencias futuras en maquinaria rotativa.
"""
)


@st.cache_data
def cargar_base_maestra():
  try:
    # Lee directamente el archivo Excel maestro guardado en el repositorio de GitHub
    df = pd.read_excel("master_vibrations_db.xlsx")
    if "Fecha" in df.columns:
      df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df
  except Exception as e:
    st.warning(
        f"No se encontró o no se pudo leer 'master_vibrations_db.xlsx' ({e})."
        " Se cargará una estructura base de respaldo."
    )
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
          mult_eje = (
              1.25
              if eje == "X" and "Ventilador" in pt
              else (1.3 if eje == "Z" else 1.0)
          )
          vel = round(np.random.uniform(1.2, 2.2) * factor_tiempo * mult_eje, 2)
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
          rows.append({
              "Fecha": pd.to_datetime(fecha),
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
        "Base de Datos Maestra (Histórico y Espectro FFT)",
        "Cargar Nuevo Trimestre / Archivo Externo (Pronóstico y Trazabilidad)",
    ],
)

if modo == "Base de Datos Maestra (Histórico y Espectro FFT)":
  st.subheader("📊 Base Maestra: Histórico de Planta y Análisis Espectral")

  if not df_master.empty:
    maquinas_disponibles = df_master["ID_Maquina"].unique()
    maquina_sel = st.selectbox(
        "Seleccione la Máquina:", maquinas_disponibles
    )

    puntos_disponibles = df_master[df_master["ID_Maquina"] == maquina_sel][
        "Punto_Medicion"
    ].unique()
    punto_sel = st.selectbox(
        "Seleccione el Punto de Medición:", puntos_disponibles
    )

    ejes_disponibles = df_master[
        (df_master["ID_Maquina"] == maquina_sel)
        & (df_master["Punto_Medicion"] == punto_sel)
    ]["Eje"].unique()
    eje_sel = st.radio(
        "Seleccione el Eje de Medición:", ejes_disponibles, horizontal=True
    )

    df_filtrado = df_master[
        (df_master["ID_Maquina"] == maquina_sel)
        & (df_master["Punto_Medicion"] == punto_sel)
        & (df_master["Eje"] == eje_sel)
    ].sort_values("Fecha")

    if not df_filtrado.empty:
      col1, col2 = st.columns(2)

      with col1:
        st.markdown("#### Histórico de Lecturas (Tabla)")
        st.dataframe(df_filtrado, use_container_width=True)

      with col2:
        st.markdown("#### Tendencia de Velocidad RMS (mm/s)")
        st.line_chart(
            df_filtrado.set_index(
                df_filtrado["Fecha"].dt.strftime("%Y-%m-%d")
            )[["Velocidad_mm_s"]],
            use_container_width=True,
        )

      # --- MÓDULO DE ESPECTRO FFT ---
      st.markdown("---")
      st.markdown(
          "### 📈 Espectro de Frecuencias FFT (Dominio de la Frecuencia)"
      )
      ultima_fila = df_filtrado.iloc[-1]
      vel_val = ultima_fila.get("Velocidad_mm_s", 2.0)

      freqs = np.linspace(0, 500, 500)
      espectro_amp = np.random.exponential(0.04, len(freqs)) + (
          0.015 * vel_val
      )
      f_1x = 29.5  # Hz nominales (aprox 1770 RPM)

      # Inyección de armónicos según el comportamiento físico del punto/eje
      espectro_amp += (
          (vel_val * 0.75)
          * np.exp(-(((freqs - f_1x) / 1.5) ** 2))
          * (1.4 if eje_sel == "X" else 0.8)
      )
      espectro_amp += (
          (vel_val * 0.35)
          * np.exp(-(((freqs - (2 * f_1x)) / 1.5) ** 2))
          * (1.3 if eje_sel == "Z" else 0.5)
      )

      df_fft = pd.DataFrame(
          {"Amplitud (mm/s)": espectro_amp},
          index=pd.Index(freqs, name="Frecuencia (Hz)"),
      )
      st.line_chart(df_fft, use_container_width=True)

      st.markdown("#### 🔬 Diagnóstico Experto por Espectro FFT:")
      if eje_sel == "X" and vel_val > 2.5:
        st.warning(
            "⚠️ **Alerta de Desbalance:** Pico dominante a 1X ("
            f"{f_1x} Hz) en el eje horizontal, indicando fuerzas"
            " centrífugas."
        )
      elif eje_sel == "Z" and vel_val > 2.2:
        st.warning(
            "⚠️ **Alerta de Soltura Mecánica:** Presencia de armónicos"
            " múltiples (1X, 2X) en el eje vertical (Z)."
        )
      else:
        st.success(
            "✅ **Espectro Saludable:** Sin anomalías críticas detectadas en"
            " las frecuencias armónicas principales."
        )
    else:
      st.warning("No hay registros para la selección realizada.")
  else:
    st.error("La base maestra está vacía.")

else:
  st.subheader("📂 Cargar Nuevo Trimestre / Archivo de Campo Externo")
  st.markdown(
      "Sube tu archivo Excel con las nuevas mediciones trimestrales. El"
      " sistema evaluará la trazabilidad histórica de diagnósticos y"
      " proyectará el comportamiento futuro."
  )

  archivo_nuevo = st.file_uploader(
      "Selecciona el archivo Excel (.xlsx)", type=["xlsx"]
  )

  if archivo_nuevo is not None:
    try:
      df_nuevo = pd.read_excel(archivo_nuevo)
      df_nuevo["Fecha"] = pd.to_datetime(df_nuevo["Fecha"])
      df_nuevo = df_nuevo.sort_values("Fecha")
      st.success("¡Base de datos de campo cargada con éxito!")

      maq_n = st.selectbox(
          "Selecciona la Máquina:",
          df_nuevo["ID_Maquina"].unique(),
          key="maq_n",
      )
      pto_n = st.selectbox(
          "Selecciona el Punto:",
          df_nuevo[df_nuevo["ID_Maquina"] == maq_n][
              "Punto_Medicion"
          ].unique(),
          key="pto_n",
      )
      eje_n = st.radio(
          "Selecciona el Eje:",
          df_nuevo[
              (df_nuevo["ID_Maquina"] == maq_n)
              & (df_nuevo["Punto_Medicion"] == pto_n)
          ]["Eje"].unique(),
          horizontal=True,
          key="eje_n",
      )

      df_serie = df_nuevo[
          (df_nuevo["ID_Maquina"] == maq_n)
          & (df_nuevo["Punto_Medicion"] == pto_n)
          & (df_nuevo["Eje"] == eje_n)
      ].sort_values("Fecha")

      if not df_serie.empty:
        st.markdown("---")
        col_t1, col_t2 = st.columns(2)

        with col_t1:
          st.markdown("#### 📈 Tendencia Histórica de Velocidad RMS")
          st.line_chart(
              df_serie.set_index(
                  df_serie["Fecha"].dt.strftime("%Y-%m-%d")
              )[["Velocidad_mm_s"]],
              use_container_width=True,
          )
        with col_t2:
          st.markdown("#### 🔎 Evolución de Envolvente y Aceleración")
          st.line_chart(
              df_serie.set_index(
                  df_serie["Fecha"].dt.strftime("%Y-%m-%d")
              )[["Envolvente_gE", "Aceleracion_g"]],
              use_container_width=True,
          )

        # Historial de Diagnósticos por Trimestre
        st.markdown("---")
        st.markdown("### 📋 Historial de Diagnósticos por Trimestre Medido")
        historial_diag = []
        for _, row in df_serie.iterrows():
          f_str = row["Fecha"].strftime("%Y-%m-%d")
          v = row.get("Velocidad_mm_s", 0)
          en = row.get("Envolvente_gE", 0)
          e = row.get("Eje", "X")

          estado_t = "Normal ✅"
          obs_t = "Operación estable."
          if v > 3.0 and e == "X":
            estado_t = "Alerta ⚠️"
            obs_t = "Velocidad alta (Posible Desbalance)."
          elif v > 2.5 and e == "Z":
            estado_t = "Alerta ⚠️"
            obs_t = "Velocidad elevada en Z (Posible Soltura)."
          if en > 1.8:
            estado_t = "Crítico 🚨"
            obs_t = "Impactos severos en rodamientos (Envolvente alta)."

          historial_diag.append({
              "Fecha Trimestre": f_str,
              "Velocidad (mm/s)": v,
              "Envolvente (gE)": en,
              "Estado": estado_t,
              "Diagnóstico Experto": obs_t,
          })
        st.dataframe(pd.DataFrame(historial_diag), use_container_width=True)

        # Pronóstico de Tendencia Futura
        st.markdown("---")
        st.markdown(
            "### 🔮 Pronóstico y Diagnóstico Futuro (Siguiente Trimestre)"
        )
        if len(df_serie) >= 2:
          x = df_serie["Fecha"].map(pd.Timestamp.toordinal).values
          y_vel = df_serie["Velocidad_mm_s"].values
          y_env = df_serie["Envolvente_gE"].values

          slope_vel, intercept_vel = np.polyfit(x, y_vel, 1)
          slope_env, intercept_env = np.polyfit(x, y_env, 1)

          ultima_fecha = df_serie["Fecha"].max()
          fecha_futura = ultima_fecha + pd.Timedelta(days=90)
          x_futuro = fecha_futura.toordinal()

          vel_futura = slope_vel * x_futuro + intercept_vel
          env_futuro = slope_env * x_futuro + intercept_env

          col_f1, col_f2 = st.columns(2)
          with col_f1:
            st.metric(
                label=f"Proyección Velocidad ({fecha_futura.strftime('%Y-%m-%d')})",
                value=f"{round(vel_futura, 2)} mm/s",
                delta=f"{round(vel_futura - y_vel[-1], 2)} mm/s vs último",
            )
          with col_f2:
            st.metric(
                label=f"Proyección Envolvente ({fecha_futura.strftime('%Y-%m-%d')})",
                value=f"{round(env_futuro, 2)} gE",
                delta=f"{round(env_futuro - y_env[-1], 2)} gE vs último",
            )

          st.markdown("#### ⚠️ Recomendación Predictiva Anticipada:")
          if vel_futura > 3.5:
            st.warning(
                f"🔴 **Alerta de Tendencia Crítica:** Se proyecta alcanzar"
                f" {round(vel_futura, 2)} mm/s el próximo período. Se"
                f" recomienda intervención preventiva."
            )
          elif vel_futura > y_vel[-1]:
            st.warning(
                "🟡 **Degradación Gradual:** Incremento moderado previsto en"
                " la vibración global."
            )
          else:
            st.success(
                "🟢 **Tendencia Estable:** La maquinaria mantendrá niveles"
                " seguros el próximo trimestre."
            )
        else:
          st.info(
              "Se requieren al menos 2 trimestres de datos en el archivo"
              " cargado para calcular la proyección matemática."
          )
      else:
        st.warning("No hay registros para la combinación seleccionada.")
    except Exception as e:
      st.error(f"Error al procesar el archivo cargado: {e}")
  else:
    st.info("Esperando a que cargues un archivo Excel con la nueva base...")
