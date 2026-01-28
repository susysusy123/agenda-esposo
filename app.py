import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Agenda Esposo", page_icon="📋")

# Conexión Segura
try:
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    client = Groq(api_key=api_key_groq)
    SHEET_ID = "1qX27CJPxjB-DaOUTmNjyRwZ1fLO6JEAAZsbK6zgZwGk"
except Exception as e:
    st.error(f"Error de configuración: {e}")

st.title("📋 Mi Agenda Inteligente")

def guardar_en_sheets(tarea, fecha):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        cliente_g = gspread.authorize(creds)
        hoja = cliente_g.open_by_key(SHEET_ID).sheet1
        # Guardamos: Tarea, Fecha, Estado
        hoja.append_row([tarea, fecha, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error en Google Sheets: {e}")
        return False

st.subheader("🎙️ Dictado de Tarea")
entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Recoger zapatos hoy")

if st.button("Guardar"):
    if entrada:
        with st.spinner("Organizando..."):
            try:
                # Instrucción ultra-estricta para la IA
                instruccion = f"Extrae la tarea y la fecha del siguiente texto. Responde ÚNICAMENTE con este formato: Tarea | Fecha. No escribas nada más, ni saludos ni explicaciones. Texto: {entrada}"
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": instruccion}],
                    model="llama-3.3-70b-versatile",
                )
                
                respuesta = chat_completion.choices[0].message.content.strip()
                
                # Separamos la respuesta
                if "|" in respuesta:
                    partes = respuesta.split("|")
                    tarea_limpia = partes[0].strip()
                    fecha_limpia = partes[1].strip()
                else:
                    tarea_limpia = respuesta
                    fecha_limpia = "No indicada"

                if guardar_en_sheets(tarea_limpia, fecha_limpia):
                    st.success(f"✅ ¡Guardado con éxito!")
                    st.info(f"Tarea: {tarea_limpia}\nFecha: {fecha_limpia}")
                    st.balloons() # ¡Ahora sí deberían salir!
            except Exception as e:
                st.error(f"Error con la IA: {e}")
    else:
        st.warning("Escribe algo primero.")
