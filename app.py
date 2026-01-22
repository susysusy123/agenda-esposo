import streamlit as st
import pandas as pd
from groq import Groq
import json
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
LLAVE_GROQ = st.secrets["GROQ_API_KEY"] 
client = Groq(api_key=LLAVE_GROQ)
ARCHIVO_DATOS = "mis_tareas.csv"

st.set_page_config(page_title="Agenda Inteligente Pro", layout="wide")

# Estilo personalizado para el título
st.markdown("<h1 style='text-align: center; color: #007BFF;'>📋 Mi Agenda Inteligente</h1>", unsafe_allow_html=True)

# --- 2. GESTIÓN DE DATOS ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        return pd.read_csv(ARCHIVO_DATOS).to_dict('records')
    return []

def guardar_datos():
    df = pd.DataFrame(st.session_state.pendientes)
    df.to_csv(ARCHIVO_DATOS, index=False)

if 'pendientes' not in st.session_state:
    st.session_state.pendientes = cargar_datos()

# --- 3. FUNCIÓN IA MEJORADA (MÁXIMA PRECISIÓN) ---
def analizar_con_ia(texto):
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    
    instruccion = f"""
    Eres un asistente de logística para construcción. Hoy es {fecha_hoy}.
    Tu misión es extraer datos del texto: "{texto}"
    
    REGLAS ESTRICTAS:
    1. PROYECTO: Acción principal (ej. 'Comprar material', 'Revisar obra').
    2. PRIORIDAD: 'Alta', 'Media' o 'Baja'. (Si dice 'urgente' es Alta).
    3. ENTREGA: Busca nombres propios o lugares. 
       - Si dice 'con Luis', 'para Pedro', 'en la Obra', extrae: 'Luis', 'Pedro' u 'Obra'.
       - NO incluyas el nombre en la columna 'proyecto'.
    4. FECHA: Calcula la fecha exacta (ej. 'mañana', 'próximo viernes').

    Responde SOLAMENTE un JSON con estas llaves: proyecto, prioridad, entrega, fecha.
    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": instruccion}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

# --- 4. INTERFAZ DE ENTRADA ---
with st.container():
    with st.form("nuevo_pendiente", clear_on_submit=True):
        st.subheader("🎙️ Dictado de Tarea")
        entrada = st.text_input("Escribe o dicta:", placeholder="Ej: Mañana llevar planos a la obra con el Arq. Daniel prioridad alta")
        boton_enviar = st.form_submit_button("Organizar y Guardar en Lista")

if boton_enviar and entrada:
    try:
        with st.spinner("La IA está clasificando..."):
            datos = analizar_con_ia(entrada)
            datos["realizado"] = "No"
            st.session_state.pendientes.append(datos)
            guardar_datos()
            st.toast("¡Tarea guardada con éxito! ✅")
            st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()

# --- 5. TABLA DE TAREAS ---
if st.session_state.pendientes:
    st.subheader("Tareas Pendientes")
    
    # Encabezados
    cols = st.columns([0.5, 2.5, 1, 1.5, 1.5, 1, 1.5])
    titulos = ["N°", "Proyecto", "Prioridad", "Encargado", "Fecha", "Status", "Acciones"]
    for col, titulo in zip(cols, titulos):
        col.write(f"**{titulo}**")

    # Filas
    for i, p in enumerate(st.session_state.pendientes):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 2.5, 1, 1.5, 1.5, 1, 1.5])
        
        c1.write(i + 1)
        
        # Tachado si está hecho
        if p['realizado'] == "Sí":
            c2.markdown(f"~~{p['proyecto']}~~")
            c6.write("✅")
        else:
            c2.write(p['proyecto'])
            c6.write("⏳")
        
        # Colores para prioridad
        prio = p['prioridad'].capitalize()
        if prio == "Alta":
            c3.markdown(f"<span style='color:red'>{prio}</span>", unsafe_allow_html=True)
        else:
            c3.write(prio)
            
        c4.write(p['entrega'])
        c5.write(p['fecha'])
        
        # Botones
        b1, b2 = c7.columns(2)
        if b1.button("✔️", key=f"h_{i}"):
            st.session_state.pendientes[i]['realizado'] = "Sí"
            guardar_datos()
            st.rerun()
        if b2.button("🗑️", key=f"b_{i}"):
            st.session_state.pendientes.pop(i)
            guardar_datos()
            st.rerun()

    st.write("")
    if st.button("🔴 Limpiar lista completa"):
        st.session_state.pendientes = []
        if os.path.exists(ARCHIVO_DATOS): os.remove(ARCHIVO_DATOS)
        st.rerun()
else:
    st.info("No hay tareas pendientes. ¡Dicta una arriba!")