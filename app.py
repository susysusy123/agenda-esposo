import streamlit as st
from groq import Groq
import pandas as pd
from gspread_pandas import Spread, conf

# Configuración de la página
st.set_page_config(page_title="Mi Agenda Inteligente", page_icon="📋")

# 1. Conexión con los Secrets (Groq y Google)
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # Configuración de credenciales de Google
    creds_dict = dict(st.secrets["gcp_service_account"])
    # ID de tu hoja de cálculo (extraído de tu link)
    SHEET_ID = "1qX27CJPxjB-DaOUTmNjyRwZ1fLO6JEAAZsbK6zgZwGk"
except Exception as e:
    st.error("Error en la configuración de seguridad. Revisa los Secrets.")

st.title("📋 Mi Agenda Inteligente")

# Función para guardar en Google Sheets
def guardar_en_sheets(nueva_tarea, fecha):
    try:
        # Conectar a la hoja usando las credenciales de los Secrets
        c = conf.get_config(conf_dir=".", file_name="creds.json") 
        # Nota: gspread_pandas es un poco técnico, usaremos una versión más directa para ti:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        cliente_g = gspread.authorize(creds)
        
        hoja = cliente_g.open_by_key(SHEET_ID).sheet1
        hoja.append_row([nueva_tarea, fecha, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# Interfaz de usuario
st.subheader("🎙️ Dictado de Tarea")
entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Mañana a las 10am cita con el médico")

if st.button("Organizar y Guardar en Lista"):
    if entrada:
        with st.spinner("Procesando con IA..."):
            # La IA organiza la frase
            prompt = f"Extrae la tarea y la fecha de este texto y devuélvelo en formato 'Tarea | Fecha': {entrada}"
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            respuesta = chat_completion.choices[0].message.content
            
            # Intentar separar tarea y fecha
            try:
                tarea_limpia = respuesta.split("|")[0].strip()
                fecha_limpia = respuesta.split("|")[1].strip()
            except:
                tarea_limpia = respuesta
                fecha_limpia = "No especificada"

            # Guardar en Google Sheets
            if guardar_en_sheets(tarea_limpia, fecha_limpia):
                st.success(f"✅ ¡Guardado en Google Sheets!: {tarea_limpia}")
                st.balloons()
    else:
        st.warning("Por favor, escribe algo primero.")

st.divider()
st.info("Nota: Las tareas se guardan permanentemente en tu Google Sheet.")
