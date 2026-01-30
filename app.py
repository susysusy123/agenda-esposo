import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

st.set_page_config(page_title="Agenda Esposo", page_icon="📋", layout="wide")

# --- CONEXIÓN SEGURA ---
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

# --- FUNCIONES ---
def guardar_en_sheets(tarea, fecha, destino, prioridad):
    try:
        hoja.append_row([tarea, fecha, destino, prioridad, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def marcar_completada(fila_real):
    try:
        hoja.update_cell(fila_real, 5, "Completado")
        st.toast("¡Tarea completada!", icon="✅")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"No pude actualizar el Excel: {e}")

# --- INTERFAZ ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Revisar reporte con Luis y enviar a Ana mañana")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("La IA está pensando..."):
        try:
            # Añadimos un pequeño re-intento automático por si la IA está ocupada
            intentos = 0
            res = ""
            while intentos < 2:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": f"Separa en: Tarea | Fecha | Entregar a | Prioridad. Texto: {entrada}"}],
                        model="llama-3.3-70b-versatile",
                        timeout=30.0 # Le damos 30 segundos de paciencia
                    )
                    res = chat_completion.choices[0].message.content.strip()
                    break # Si responde, salimos del ciclo
                except:
                    intentos += 1
                    time.sleep(1)

            if res:
                # Limpiar etiquetas raras que a veces pone la IA
                res = res.replace("Tarea:", "").replace("Fecha:", "").replace("Entregar a:", "").replace("Prioridad:", "")
                p = res.split("|")
                t_limpia = p[0].strip() if len(p) > 0 else entrada
                f_limpia = p[1].strip() if len(p) > 1 else "No especificada"
                d_limpia = p[2].strip() if len(p) > 2 else "No especificada"
                pr_limpia = p[3].strip() if len(p) > 3 else "Normal"

                if guardar_en_sheets(t_limpia, f_limpia, d_limpia, pr_limpia):
                    st.success("✅ ¡Tarea anotada con éxito!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("⚠️ La IA está muy ocupada. Intenta de nuevo en 5 segundos.")
        except Exception as e:
            st.error(f"Hubo un detalle técnico: {e}")

st.divider()

# --- LISTA DE TAREAS ---
st.subheader("📂 Tareas Pendientes")
try:
    lista_completa = hoja.get_all_values()
    if len(lista_completa) > 1:
        df = pd.DataFrame(lista_completa[1:], columns=lista_completa[0])
        df['fila_excel'] = range(2, len(df) + 2)
        pendientes = df[df['Estado'] == 'Pendiente']
        
        if not pendientes.empty:
            for _, row in pendientes.iterrows():
                with st.container():
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        prio = str(row['Prioridad'])
                        emoji = "🔴" if "Alta" in prio else "🟡" if "Media" in prio else "🟢"
                        st.write(f"{emoji} **{row['Tarea']}**")
                        st.caption(f"📅 {row['Fecha']} | 👤 Para: {row['Entregar a']} | ⚠️ {row['Prioridad']}")
                    with col2:
                        if st.button("✅", key=f"f_{row['fila_excel']}"):
                            marcar_completada(row['fila_excel'])
                    st.write("---")
        else:
            st.info("¡Todo limpio! No hay pendientes.")
except:
    st.write("Cargando lista...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
