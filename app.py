import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
import re

st.set_page_config(page_title="Agenda Esposo", page_icon="📋", layout="wide")

# --- CONEXIÓN ---
@st.cache_resource
def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

try:
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    client = Groq(api_key=api_key_groq)
    SHEET_ID = "1qX27CJPxjB-DaOUTmNjyRwZ1fLO6JEAAZsbK6zgZwGk"
    cliente_g = conectar_google()
    hoja = cliente_g.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Error de conexión: {e}")

st.title("📋 Mi Agenda Inteligente")

# --- PROCESAMIENTO DE IA ---
def procesar_con_ia(texto_usuario):
    prompt = f"""Analiza: "{texto_usuario}"
    Responde SOLO JSON: {{"t": "descripcion completa", "f": "fecha", "d": "quien recibe", "p": "Prioridad"}}
    Regla: NO resumas la tarea."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1 
        )
        respuesta = chat_completion.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        return json.loads(match.group()) if match else None
    except:
        return None

# --- INTERFAZ ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Describe la tarea...")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("Procesando..."):
        datos = procesar_con_ia(entrada)
        if datos:
            try:
                # Quitamos el mensaje de éxito estorboso y guardamos directo
                nueva_fila = [
                    datos.get("t", entrada), 
                    datos.get("f", "No especificada"),
                    datos.get("d", "No indicado"),
                    datos.get("p", "Normal"),
                    "Pendiente"
                ]
                hoja.append_row(nueva_fila)
                time.sleep(1) # Pausa para asegurar que Google escribió
                st.rerun() # Refresca la app automáticamente para ver la tarea
            except Exception as e:
                st.error("Error de conexión con Excel. Intenta de nuevo.")
        else:
            st.error("No se pudo procesar el dictado.")

st.divider()

# --- LISTA DE TAREAS ---
st.subheader("📂 Tareas Pendientes")
try:
    lista_completa = hoja.get_all_values()
    if len(lista_completa) > 1:
        # Forzamos que lea los encabezados de la fila 1
        df = pd.DataFrame(lista_completa[1:], columns=["Tarea", "Fecha", "Entregar a", "Prioridad", "Estado"])
        df['fila_excel'] = range(2, len(df) + 2)
        
        # Filtrar solo pendientes
        pendientes = df[df['Estado'].str.contains("Pendiente", case=False, na=False)]
        
        for _, row in pendientes.iterrows():
            with st.container():
                c1, c2 = st.columns([0.85, 0.15])
                with c1:
                    prio = str(row['Prioridad'])
                    emoji = "🔴" if "Alta" in prio or "alta" in prio else "🟡" if "Media" in prio or "media" in prio else "🟢"
                    st.write(f"{emoji} **{row['Tarea']}**")
                    st.caption(f"📅 {row['Fecha']} | 👤 Para: {row['Entregar a']} | ⚠️ {row['Prioridad']}")
                with c2:
                    if st.button("✅", key=f"f_{row['fila_excel']}"):
                        hoja.update_cell(int(row['fila_excel']), 5, "Completado")
                        st.rerun()
                st.write("---")
    else:
        st.info("No hay tareas pendientes.")
except Exception as e:
    st.write("Sincronizando con Excel...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
