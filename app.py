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
    st.error(f"Error: {e}")

st.title("📋 Mi Agenda Inteligente")

# --- FUNCIONES ---
def guardar_en_sheets(tarea, fecha, destino, prioridad):
    try:
        hoja.append_row([tarea, fecha, destino, prioridad, "Pendiente"])
        return True
    except: return False

def marcar_completada(fila_index):
    try:
        hoja.update_cell(fila_index + 2, 5, "Completado")
        st.rerun()
    except: st.error("Error al actualizar")

# --- INTERFAZ ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Revisar el coche con Juan y entregar llaves a Maria")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("Analizando quién es quién..."):
        try:
            # PROMPT REFORZADO: Aquí está el truco para los dos nombres
            prompt = f"""Analiza el texto y extrae la información siguiendo estas REGLAS ESTRICTAS:
            1. Tarea: La acción principal. Si se menciona a alguien con quien se hace la acción (ej. 'con Juan'), inclúyelo aquí.
            2. Fecha: Solo el tiempo. Si no hay, usa 'No especificada'.
            3. Entregar a: Solo la persona que recibe el beneficio final o a quien se le reporta.
            4. Prioridad: Alta, Media o Normal.
            
            RESPONDE ÚNICAMENTE con este formato (sin etiquetas extra):
            Tarea | Fecha | Entregar a | Prioridad
            
            Texto a analizar: {entrada}"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            res = chat_completion.choices[0].message.content.strip()
            
            # Limpiamos posibles etiquetas que la IA a veces insiste en poner
            res = res.replace("Tarea:", "").replace("Fecha:", "").replace("Entregar a:", "").replace("Prioridad:", "")
            
            p = res.split("|")
            t_limpia = p[0].strip()
            f_limpia = p[1].strip() if len(p) > 1 else "No especificada"
            d_limpia = p[2].strip() if len(p) > 2 else "No especificada"
            pr_limpia = p[3].strip() if len(p) > 3 else "Normal"

            if guardar_en_sheets(t_limpia, f_limpia, d_limpia, pr_limpia):
                st.success(f"✅ Anotado")
        except: st.error("Error en la IA")

st.divider()

# --- LISTA DE TAREAS ---
st.subheader("📂 Tareas Pendientes")
try:
    data = hoja.get_all_records()
    if data:
        df = pd.DataFrame(data)
        pendientes = df[df['Estado'] == 'Pendiente']
        if not pendientes.empty:
            for i, row in pendientes.iterrows():
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    emoji = "🔴" if "Alta" in str(row['Prioridad']) else "🟡" if "Media" in str(row['Prioridad']) else "🟢"
                    st.write(f"{emoji} **{row['Tarea']}**")
                    st.caption(f"📅 {row['Fecha']} | 👤 Destinatario: {row['Entregar a']} | ⚠️ {row['Prioridad']}")
                with col2:
                    if st.button("✅", key=f"btn_{i}"):
                        marcar_completada(i)
                st.write("---")
except: st.write("Cargando lista...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
