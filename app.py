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

# --- FUNCIONES MEJORADAS ---
def guardar_en_sheets(tarea, fecha, destino, prioridad):
    try:
        # Forzamos que siempre guarde 5 columnas exactas
        hoja.append_row([tarea, fecha, destino, prioridad, "Pendiente"])
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def marcar_completada(fila_real):
    try:
        # Usamos el número de fila real del Excel
        # Columna 5 es la 'E' (Estado)
        hoja.update_cell(fila_real, 5, "Completado")
        st.toast("¡Tarea completada!", icon="✅")
        time.sleep(1) # Pausa para que Google procese
        st.rerun()
    except Exception as e:
        st.error(f"No pude actualizar el Excel: {e}")

# --- INTERFAZ ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Llevar documentos a Poncho el viernes")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("Analizando..."):
        try:
            prompt = f"""Separa en: Tarea | Fecha | Entregar a | Prioridad. 
            Regla: Si hay dos nombres, el que recibe es 'Entregar a'. 
            No uses etiquetas. Texto: {entrada}"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            res = chat_completion.choices[0].message.content.strip()
            res = res.replace("Tarea:", "").replace("Fecha:", "").replace("Entregar a:", "").replace("Prioridad:", "")
            
            p = res.split("|")
            t_limpia = p[0].strip()
            f_limpia = p[1].strip() if len(p) > 1 else "No especificada"
            d_limpia = p[2].strip() if len(p) > 2 else "No especificada"
            pr_limpia = p[3].strip() if len(p) > 3 else "Normal"

            if guardar_en_sheets(t_limpia, f_limpia, d_limpia, pr_limpia):
                st.success("✅ Guardado correctamente")
                time.sleep(1)
                st.rerun()
        except: st.error("La IA no respondió a tiempo")

st.divider()

# --- LISTA CON FILTRO ROBUSTO ---
st.subheader("📂 Tareas Pendientes")
try:
    # Obtenemos todos los valores incluyendo el número de fila
    lista_completa = hoja.get_all_values()
    if len(lista_completa) > 1: # Si hay más que solo el encabezado
        encabezados = lista_completa[0]
        # Creamos el DataFrame y le sumamos el número de fila real (index + 1)
        df = pd.DataFrame(lista_completa[1:], columns=encabezados)
        df['fila_excel'] = range(2, len(df) + 2)
        
        # Filtramos solo las que dicen "Pendiente"
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
                        # Usamos la fila_excel real para no fallar
                        if st.button("✅", key=f"f_{row['fila_excel']}"):
                            marcar_completada(row['fila_excel'])
                    st.write("---")
        else:
            st.info("No hay tareas pendientes.")
    else:
        st.info("La lista está vacía.")
except Exception as e:
    st.write("Conectando con Excel...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
