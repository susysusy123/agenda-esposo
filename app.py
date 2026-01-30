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

# --- PROCESAMIENTO DE IA (VERSIÓN DETALLADA) ---
def procesar_con_ia(texto_usuario):
    # Instrucción ajustada para NO resumir
    prompt = f"""Analiza el texto: "{texto_usuario}"
    Responde ÚNICAMENTE un objeto JSON así:
    {{"t": "descripcion detallada", "f": "fecha", "d": "quien recibe", "p": "Prioridad"}}
    
    REGLAS DE ORO:
    1. En 't' (tarea) pon la acción COMPLETA. NO resumas, mantén todos los detalles del usuario.
    2. Si menciona 'con alguien', inclúyelo en 't'.
    3. En 'd' (destino) pon SOLO el nombre de quien recibe.
    4. Responde SOLO el JSON, sin texto extra."""
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1 
        )
        respuesta = chat_completion.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except:
        return None

# --- INTERFAZ ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Describe la tarea con todos los detalles...")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("Guardando con detalles..."):
        datos = procesar_con_ia(entrada)
        if datos:
            try:
                hoja.append_row([
                    datos.get("t", entrada),        # Aquí ahora irá el texto completo
                    datos.get("f", "No especificada"),
                    datos.get("d", "No indicado"),
                    datos.get("p", "Normal"),
                    "Pendiente"
                ])
                st.success("✅ ¡Guardado con todos los detalles!")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Error al escribir en Excel")
        else:
            st.error("No se pudo procesar, intenta de nuevo.")

st.divider()

# --- LISTA DE TAREAS ---
st.subheader("📂 Tareas Pendientes")
try:
    lista_completa = hoja.get_all_values()
    if len(lista_completa) > 1:
        df = pd.DataFrame(lista_completa[1:], columns=lista_completa[0])
        df['fila_excel'] = range(2, len(df) + 2)
        pendientes = df[df['Estado'].str.contains("Pendiente", case=False, na=False)]
        
        for _, row in pendientes.iterrows():
            with st.container():
                c1, c2 = st.columns([0.85, 0.15])
                with c1:
                    prio = str(row['Prioridad'])
                    emoji = "🔴" if "Alta" in prio else "🟡" if "Media" in prio else "🟢"
                    st.write(f"{emoji} **{row['Tarea']}**")
                    st.caption(f"📅 {row['Fecha']} | 👤 Para: {row['Entregar a']} | ⚠️ {row['Prioridad']}")
                with c2:
                    if st.button("✅", key=f"f_{row['fila_excel']}"):
                        hoja.update_cell(int(row['fila_excel']), 5, "Completado")
                        st.rerun()
                st.write("---")
    else:
        st.info("No hay tareas pendientes.")
except:
    st.write("Cargando...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
