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
def guardar_en_sheets(tarea, fecha, destino, prioridad):
    try:
        # Guardamos: Tarea, Fecha, Entregar a, Prioridad, Estado
        hoja.append_row([tarea, fecha, destino, prioridad, "Pendiente"])
        return True
    except: return False

def marcar_completada(fila_index):
    try:
        # El Estado está en la columna 5 (E)
        hoja.update_cell(fila_index + 2, 5, "Completado")
        st.rerun()
    except Exception as e:
        st.error(f"Error al marcar como hecho: {e}")

# --- INTERFAZ DE DICTADO ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Recoger zapatos de mamacita hoy con prioridad alta")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("Analizando detalles..."):
        try:
            prompt = f"""Analiza el texto y separa los datos.
            Responde ÚNICAMENTE en este formato: Tarea | Fecha | Entregar a | Prioridad
            - Prioridad: Puede ser Alta, Media o Normal. Si no se menciona, pon 'Normal'.
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
            pr_limpia = p[3].strip() if len(p) > 3 else "Normal"

            if guardar_en_sheets(t_limpia, f_limpia, d_limpia, pr_limpia):
                st.success(f"✅ Anotado: {t_limpia}")
                # ELIMINAMOS LA LÍNEA DE LOS GLOBOS AQUÍ
        except Exception as e:
            st.error(f"Error IA: {e}")

st.divider()

# --- TABLA DE TAREAS PENDIENTES ---
st.subheader("📂 Tareas por Hacer")
try:
    data = hoja.get_all_records()
    if data:
        df = pd.DataFrame(data)
        pendientes = df[df['Estado'] == 'Pendiente']
        
        if not pendientes.empty:
            for i, row in pendientes.iterrows():
                # Estilo de tarjeta para cada tarea
                with st.container():
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        emoji = "🔴" if "Alta" in str(row['Prioridad']) else "🟡" if "Media" in str(row['Prioridad']) else "🟢"
                        st.write(f"{emoji} **{row['Tarea']}**")
                        st.caption(f"📅 {row['Fecha']} | 👤 Para: {row['Entregar a']} | ⚠️ {row['Prioridad']}")
                    with col2:
                        if st.button("✅", key=f"btn_{i}"):
                            marcar_completada(i)
                st.write("---")
        else:
            st.info("¡Todo listo! No hay pendientes.")
    else:
        st.info("La lista está vacía.")
except Exception as e:
    st.write("Cargando lista actualizada...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
