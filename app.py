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
        hoja.append_row([tarea, fecha, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error en Google Sheets: {e}")
        return False

st.subheader("🎙️ Dictado de Tarea")

# Usamos un formulario para que el ENTER funcione
with st.form("mi_formulario", clear_on_submit=True):
    # 'label_visibility' oculta el texto sobre el cuadro para que se vea más limpio
    # 'autocomplete="off"' evita que aparezcan las sugerencias de lo que escribiste antes
    entrada = st.text_input(
        "Introduce la tarea:", 
        placeholder="Ej: Recoger zapatos hoy",
        label_visibility="collapsed",
        key="input_tarea",
        help="Escribe y presiona Enter para guardar"
    )
    
    boton_guardar = st.form_submit_button("Guardar en mi Lista")

# Lógica después de presionar el botón o darle ENTER
if boton_guardar:
    if entrada:
        with st.spinner("Organizando..."):
            try:
                instruccion = f"Extrae Tarea | Fecha. Sé breve. No respondas nada más que el formato. Texto: {entrada}"
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": instruccion}],
                    model="llama-3.3-70b-versatile",
                )
                
                respuesta = chat_completion.choices[0].message.content.strip()
                
                if "|" in respuesta:
                    partes = respuesta.split("|")
                    tarea_limpia = partes[0].strip()
                    fecha_limpia = partes[1].strip()
                else:
                    tarea_limpia = respuesta
                    fecha_limpia = "Hoy"

                if guardar_en_sheets(tarea_limpia, fecha_limpia):
                    st.success(f"✅ ¡Guardado con éxito!")
                    st.balloons()
            except Exception as e:
                st.error(f"Error con la IA: {e}")
    else:
        st.warning("Escribe algo primero.")

# Agregamos este pequeño truco para que el navegador no sugiera tareas viejas
st.markdown("""
    <script>
        var inputs = window.parent.document.querySelectorAll('input');
        inputs.forEach(input => {
            input.setAttribute('autocomplete', 'off');
        });
    </script>
""", unsafe_content_allowed=True)
