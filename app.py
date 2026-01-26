import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de Seguridad
try:
    # Aquí es donde estaba el error del paréntesis
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    SHEET_ID = "1qX27CJPxjB-DaOUTmNjyRwZ1fLO6JEAAZsbK6zgZwGk"
except Exception as e:
    st.error("Error de configuración: Revisa los Secrets en Streamlit.")

st.title("📋 Mi Agenda Inteligente")

# 2. Función para guardar en Google Sheets
def guardar_en_sheets(nueva_tarea, fecha):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        cliente_g = gspread.authorize(creds)
        hoja = cliente_g.open_by_key(SHEET_ID).sheet1
        hoja.append_row([nueva_tarea, fecha, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return False

# 3. Interfaz de Usuario
st.subheader("🎙️ Dictado de Tarea")
entrada = st.text_input("Escribe o dicta tu tarea:", placeholder="Ej: Comprar flores el miércoles")

if st.button("Guardar en mi Excel"):
    if entrada:
        with st.spinner("La IA está organizando tu nota..."):
            prompt = f"Extrae la tarea y la fecha de este texto. Formato: Tarea | Fecha. Texto: {entrada}"
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            respuesta = chat_completion.choices[0].message.content
            
            try:
                partes = respuesta.split("|")
                tarea_limpia = partes[0].strip()
                fecha_limpia = partes[1].strip() if len(partes) > 1 else "No indicada"
            except:
                tarea_limpia, fecha_limpia = respuesta, "No indicada"

            if guardar_en_sheets(tarea_limpia, fecha_limpia):
                st.success(f"✅ ¡Listo! Se guardó: {tarea_limpia}")
                st.balloons()
    else:
        st.warning("Escribe algo antes de guardar.")
