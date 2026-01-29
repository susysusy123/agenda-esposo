import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="Agenda Esposo", page_icon="📋", layout="centered")

# --- CONEXIÓN ---
try:
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    client = Groq(api_key=api_key_groq)
    SHEET_ID = "1qX27CJPxjB-DaOUTmNjyRwZ1fLO6JEAAZsbK6zgZwGk"
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    cliente_g = gspread.authorize(creds)
    hoja = cliente_g.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Error de conexión: {e}")

st.title("📋 Mi Agenda Inteligente")

# --- FUNCIONES ---
def guardar_en_sheets(tarea, fecha, destino):
    try:
        # Ahora guardamos 4 columnas: Tarea, Fecha, Entregar a, Estado
        hoja.append_row([tarea, fecha, destino, "Pendiente"])
        return True
    except:
        return False

# --- INTERFAZ DE DICTADO ---
st.subheader("🎙️ Nueva Tarea")
with st.form("mi_formulario", clear_on_submit=True):
    entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Recoger zapatos mañana para Luis", label_visibility="collapsed")
    boton_guardar = st.form_submit_button("Guardar en mi Lista")

if boton_guardar and entrada:
    with st.spinner("Procesando datos..."):
        try:
            # Instrucción reforzada para evitar párrafos largos
            prompt = f"""Extrae los datos del texto y responde ÚNICAMENTE en este formato: 
            Tarea | Fecha | Persona
            Si no hay fecha pon 'No indicada'. Si no hay persona pon 'No indicada'.
            Texto: {entrada}"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            
            res = chat_completion.choices[0].message.content.strip()
            
            # Separamos con cuidado
            if "|" in res:
                p = res.split("|")
                t_limpia = p[0].strip()
                f_limpia = p[1].strip() if len(p) > 1 else "No indicada"
                d_limpia = p[2].strip() if len(p) > 2 else "No indicada"
            else:
                t_limpia, f_limpia, d_limpia = res, "No indicada", "No indicada"

            if guardar_en_sheets(t_limpia, f_limpia, d_limpia):
                st.success(f"✅ ¡Anotado!")
                st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")

st.divider()

# --- VER TAREAS (BOTÓN MÁGICO) ---
if st.button("📂 Ver mis Tareas Pendientes"):
    try:
        data = hoja.get_all_records()
        if data:
            df = pd.DataFrame(data)
            # Solo mostramos las que están pendientes
            pendientes = df[df['Estado'] == 'Pendiente']
            st.table(pendientes)
        else:
            st.info("Aún no hay tareas en la lista.")
    except Exception as e:
        st.error("Primero guarda una tarea para activar la tabla.")

# Estilo para evitar el historial
st.markdown("<style>input{autocomplete: off;}</style>", unsafe_allow_html=True)
