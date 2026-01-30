import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import json
import re

st.set_page_config(page_title="Agenda Esposo", page_icon="📋", layout="wide")

# --- CONEXIÓN ---
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

# --- PROCESAMIENTO DE IA ULTRA SEGURO ---
def procesar_con_ia(texto_usuario):
    # Instrucciones súper estrictas para que no escriba párrafos
    prompt = f"""Extrae datos del texto: "{texto_usuario}"
    Responde ÚNICAMENTE un objeto JSON sin texto adicional, así:
    {{"t": "solo la accion", "f": "dia", "d": "quien recibe", "p": "Alta/Media/Normal"}}
    
    Reglas:
    1. En 't' (tarea) pon la acción. Si alguien ayuda (ej. con Juan), inclúyelo ahí.
    2. En 'd' (destino) pon SOLO el nombre de quien recibe el resultado.
    3. NO escribas frases como 'Aquí tienes la información'."""
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1 # Esto la hace menos "platicadora"
        )
        respuesta = chat_completion.choices[0].message.content.strip()
        
        # Limpiador de emergencia: busca solo lo que esté entre llaves { }
        match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except:
        return None

# --- INTERFAZ ---
with st.expander("🎙️ Dictar Nueva Tarea", expanded=True):
    with st.form("mi_formulario", clear_on_submit=True):
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Revisar parámetros con Ale y entregar a Daniel el domingo")
        boton_guardar = st.form_submit_button("Guardar Tarea")

if boton_guardar and entrada:
    with st.spinner("Limpiando datos..."):
        datos = procesar_con_ia(entrada)
        if datos:
            try:
                # Mapeamos los datos del JSON a las columnas del Excel
                hoja.append_row([
                    datos.get("t", entrada),        # Tarea
                    datos.get("f", "Pendiente"),     # Fecha
                    datos.get("d", "No indicado"),   # Entregar a
                    datos.get("p", "Normal"),        # Prioridad
                    "Pendiente"                      # Estado
                ])
                st.success("✅ Guardado en columnas separadas")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al escribir en Excel: {e}")
        else:
            st.error("La IA no pudo separar los datos, intenta ser más clara.")

st.divider()

# --- LISTA DE TAREAS ---
st.subheader("📂 Tareas por Hacer")
try:
    lista_completa = hoja.get_all_values()
    if len(lista_completa) > 1:
        # Usamos los encabezados de la fila 1
        df = pd.DataFrame(lista_completa[1:], columns=lista_completa[0])
        df['fila_excel'] = range(2, len(df) + 2)
        
        # Filtramos solo las pendientes
        pendientes = df[df['Estado'].str.contains("Pendiente", case=False, na=False)]
        
        if not pendientes.empty:
            for _, row in pendientes.iterrows():
                with st.container():
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        prio = str(row['Prioridad'])
                        emoji = "🔴" if "Alta" in prio else "🟡" if "Media" in prio else "🟢"
                        st.write(f"{emoji} **{row['Tarea']}**")
                        st.caption(f"📅 {row['Fecha']} | 👤 Para: {row['Entregar a']} | ⚠️ {row['Prioridad']}")
                    with c2:
                        if st.button("✅", key=f"f_{row['fila_excel']}"):
                            hoja.update_cell(int(row['fila_excel']), 5, "Completado")
                            st.rerun()
                st.write("---")
        else:
            st.info("¡Todo listo! No hay pendientes.")
except Exception as e:
    st.write("Conectando con la base de datos...")

st.markdown("<style>input{autocomplete: off;} .stButton>button{border-radius: 20px;}</style>", unsafe_allow_html=True)
