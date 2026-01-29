import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="Agenda Esposo", page_icon="📋", layout="wide")

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
        hoja.append_row([tarea, fecha, destino, "Pendiente"])
        return True
    except: return False

def marcar_completada(fila_index):
    try:
        # Sumamos 2 porque las filas de Google Sheets empiezan en 1 y la fila 1 son encabezados
        hoja.update_cell(fila_index + 2, 4, "Completado")
        st.rerun()
    except Exception as e:
        st.error(f"Error al borrar: {e}")

# --- INTERFAZ DE DICTADO ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Ir a consulta con Sandy y entregar reporte a Ezequiel el jueves")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("La IA está separando los nombres..."):
        try:
            prompt = f"""Analiza el texto y separa:
            1. Tarea: La acción principal (ej: 'Ir a consulta con Sandy').
            2. Fecha: Solo el día o fecha mencionada. Si no hay, pon 'Pendiente'.
            3. Entregar a: El nombre de la persona que recibe el resultado final (ej: 'Ezequiel').
            Responde SOLO con este formato: Tarea | Fecha | Entregar a
            Texto: {entrada}"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            res = chat_completion.choices[0].message.content.strip()
            
            p = res.split("|")
            t_limpia = p[0].strip()
            f_limpia = p[1].strip() if len(p) > 1 else "Pendiente"
            d_limpia = p[2].strip() if len(p) > 2 else "No indicado"

            if guardar_en_sheets(t_limpia, f_limpia, d_limpia):
                st.success(f"✅ Anotado: {t_limpia}")
                st.balloons()
        except Exception as e:
            st.error(f"Error IA: {e}")

st.divider()

# --- TABLA DE TAREAS PENDIENTES ---
st.subheader("📂 Tareas por Hacer")
try:
    data = hoja.get_all_records()
    if data:
        df = pd.DataFrame(data)
        # Filtramos solo las pendientes
        pendientes = df[df['Estado'] == 'Pendiente']
        
        if not pendientes.empty:
            # Creamos columnas para poner el botón al lado de cada tarea
            for i, row in pendientes.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{row['Tarea']}** (Para: {row['Entregar a']} - Fecha: {row['Fecha']})")
                with col2:
                    if st.button("✅ Hecho", key=f"btn_{i}"):
                        marcar_completada(i)
        else:
            st.info("¡Felicidades! No hay tareas pendientes.")
    else:
        st.info("La lista está vacía.")
except Exception as e:
    st.write("Cargando lista...")

# Evitar autocompletado
st.markdown("<style>input{autocomplete: off;} .stButton>button{width:100%}</style>", unsafe_allow_html=True)
