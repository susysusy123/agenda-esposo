import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Agenda Esposo", page_icon="📋")

# Conexión Segura
try:
    # Cambiamos la forma de leer la llave para que sea más directa
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    client = Groq(api_key=api_key_groq)
    SHEET_ID = "1qX27CJPxjB-DaOUTmNjyRwZ1fLO6JEAAZsbK6zgZwGk"
except Exception as e:
    st.error(f"Error de configuración inicial: {e}")

st.title("📋 Mi Agenda Inteligente")

def guardar_en_sheets(tarea, fecha):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        cliente_g = gspread.authorize(creds)
        hoja = cliente_g.open_by_key(SHEET_ID).sheet1
        hoja.append_row([tarea, fecha, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error en Google Sheets: {e}")
        return False

st.subheader("🎙️ Dictado de Tarea")
entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Recoger zapatos hoy")

if st.button("Guardar"):
    if entrada:
        with st.spinner("Procesando..."):
            try:
                # Usamos el modelo más actualizado
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Extrae Tarea | Fecha de: {entrada}"}],
                    model="llama-3.3-70b-versatile",
                )
                respuesta = chat_completion.choices[0].message.content
                tarea_limpia = respuesta.split("|")[0].strip()
                fecha_limpia = respuesta.split("|")[1].strip() if "|" in respuesta else "Hoy"

                if guardar_en_sheets(tarea_limpia, fecha_limpia):
                    st.success(f"✅ Guardado: {tarea_limpia}")
                    st.balloons()
            except Exception as e:
                # Esto nos dirá el error real en pantalla
                st.error(f"Error con la IA: {e}")
    else:
        st.warning("Escribe algo primero.")

