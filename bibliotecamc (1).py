import streamlit as st
import pandas as pd
from datetime import date
import io

# =========================================================================
# === 1. CONFIGURACIÓN Y ESTADO INICIAL ===
# =========================================================================

# Listas de Opciones Fijas
DEPENDENCIAS = ["Electrico", "Infraestructura", "Biomedico", "Otro"]
TIPOS_MANTENIMIENTO = ["Correctivo", "Preventivo", "Predictivo", "Inspección", "Instalación"]

# Lista de Servicios Adicionales (NUEVO)
SERVICIOS_SOLICITUD = [
    "UCI ADULTOS", "PEDIATRIA", "GINECOLOGIA", "CALL CENTER", 
    "CONSULTA EXTERNA", "APS", "UCI NEONATAL", "UCI INTERMEDIA", 
    "CIRUGIA", "HOSPITALIZACION", "URGENCIAS", "ODONTOLOGÍA", 
    "FISIOTERAPIA", "P Y P", "LABORATORIO", "GASTROENTEROLOGÍA", "OTRO"
]


# Directorio de Trabajadores/Firmantes INICIAL
DIRECTORIO_TRABAJADORES_INICIAL = {
    "Elaboro": ["Magaly Gómez - Técnica", "Oscar Muñoz - Operario"],
    "Reviso": ["Danna Hernandez - Coordinadora Mantenimiento", "Hery Peña - Biomédico", "Jefe de Mantenimiento - Ingeniería"],
    "Aprobo": ["Gerente de Operaciones - Gerente", "Jefe de Almacén - Logística"]
}

# Inicializar el estado de la sesión para persistencia de datos (mientras la app está abierta)
if 'orden_data' not in st.session_state:
    st.session_state.orden_data = []

if 'directorio_personal' not in st.session_state:
    st.session_state.directorio_personal = DIRECTORIO_TRABAJADORES_INICIAL

if 'siguiente_orden_numero' not in st.session_state:
    st.session_state.siguiente_orden_numero = 929 
    
if 'siguiente_solicitud_numero' not in st.session_state:
    st.session_state.siguiente_solicitud_numero = 11

# =========================================================================
# === 2. FUNCIONES ===
# =========================================================================

def generar_solicitud_nro(current_num):
    """Genera el siguiente número de Solicitud (Ej: 09-11)"""
    return f"09-{current_num:02d}"

def guardar_orden(nueva_orden):
    """Añade la nueva orden al registro y actualiza los números consecutivos."""
    st.session_state.orden_data.append(nueva_orden)
    st.session_state.siguiente_orden_numero += 1
    st.session_state.siguiente_solicitud_numero += 1
    st.success(f"✅ Orden de Mantenimiento #{nueva_orden['Número de Orden']} guardada con éxito.")

@st.cache_data
def convert_df_to_csv(df):
    """Convierte el DataFrame (historial) a formato CSV para la descarga."""
    return df.to_csv(index=False).encode('utf-8')

def agregar_personal(rol, nombre, profesion):
    """Agrega un nombre y profesión al directorio de personal para un rol específico."""
    nombre_completo = f"{nombre} - {profesion}"
    if nombre_completo and rol:
        if nombre_completo not in st.session_state.directorio_personal[rol]:
            st.session_state.directorio_personal[rol].append(nombre_completo)
            st.session_state.directorio_personal[rol].sort()
            st.success(f"➕ **{nombre_completo}** agregado a la lista de **{rol}**.")
        else:
            st.warning(f"⚠️ **{nombre_completo}** ya existe en la lista de **{rol}**.")

# =========================================================================
# === 3. INTERFAZ DE LA APLICACIÓN (PESTAÑAS) ===
# =========================================================================

st.title("Sistema Automatizado de Órdenes de Mantenimiento 🛠️")
st.markdown("---")

tab_orden, tab_historial, tab_personal = st.tabs(["📝 Nueva Orden", "📊 Historial y Descarga", "🧑‍💻 Gestión de Personal"])

# -------------------------------------------------------------------------
# === PESTAÑA 1: NUEVA ORDEN DE MANTENIMIENTO ===
# -------------------------------------------------------------------------
with tab_orden:
    
    orden_actual = st.session_state.siguiente_orden_numero
    solicitud_actual = generar_solicitud_nro(st.session_state.siguiente_solicitud_numero)

    with st.form(key='orden_form'):
        st.subheader(f"Nueva Orden de Trabajo N°: {orden_actual}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_actual = date.today().strftime("%Y-%m-%d")
            st.text_input("Fecha", value=fecha_actual, disabled=True)
        with col2:
            st.text_input("Solicitud N°", value=solicitud_actual, disabled=True)
        with col3:
            dependencia_selected = st.selectbox("Dependencia Solicitante", options=DEPENDENCIAS)

        # --- Campo de Servicio (NUEVO) ---
        servicio_solicitud = st.selectbox(
            "Servicio al que Aplica la Solicitud", 
            options=SERVICIOS_SOLICITUD
        )

        # --- Motivo y Tipo de Mantenimiento ---
        motivo_orden = st.text_area("Motivo de la Orden (Descripción del trabajo/falla)", 
                                    placeholder=f"Ej: Se solicita una lámpara de sobreponer de 18w, para el servicio de {servicio_solicitud}...", 
                                    max_chars=500)
        
        tipo_mant = st.selectbox("Tipo de Mantenimiento", options=TIPOS_MANTENIMIENTO) 

        # --- Campo de Responsable (Simplificado y Flexible) ---
        st.markdown("### Responsable Designado")
        
        # Combina las listas de 'Elaboro' y 'Revisó' para dar flexibilidad
        opciones_responsable = st.session_state.directorio_personal["Elaboro"] + st.session_state.directorio_personal["Reviso"]
        
        responsable_designado = st.selectbox(
            "Responsable Designado para la Ejecución", 
            options=opciones_responsable,
            help="Puede ser cualquier persona de los roles 'Elaboró' o 'Revisó'."
        )
        
        # --- Solicitud de Materiales (Máx. 3 Ítems) ---
        st.markdown("### Solicitud de Materiales (Máx. 3 Ítems)")
        
        materiales = []
        
        for i in range(1, 4):
            st.markdown(f"**Ítem {i}:**")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                item = st.text_input(f"Ítem Solicitado {i}", key=f"item_{i}", placeholder="Ej: Bombillo LED")
            with col_m2:
                unidad = st.text_input(f"Unidad {i}", value="UNIDAD", key=f"unidad_{i}")
            with col_m3:
                cantidad = st.number_input(f"Cantidad {i}", min_value=0, step=1, value=0, key=f"cantidad_{i}")
            
            if item and cantidad > 0:
                materiales.append(f"{i}. {item} ({cantidad} {unidad})")

        st.markdown("---")

        # --- Firmas/Roles de Flujo ---
        st.subheader("Personal de Flujo y Firmas")
        
        col_e, col_r, col_a = st.columns(3)
        with col_e:
            elaboro = st.selectbox("Elaboró", options=st.session_state.directorio_personal["Elaboro"])
        with col_r:
            reviso = st.selectbox("Revisó", options=st.session_state.directorio_personal["Reviso"])
        with col_a:
            aprobo = st.selectbox("Aprobó", options=st.session_state.directorio_personal["Aprobo"])

        st.markdown("---")
        
        submit_button = st.form_submit_button(label='Guardar Orden y Generar Siguiente Consecutivo')

        if submit_button:
            if not motivo_orden or not materiales:
                st.error("Por favor, completa el Motivo de la Orden y al menos un ítem de Materiales (Cantidad > 0).")
            else:
                nueva_orden = {
                    "Número de Orden": orden_actual,
                    "Solicitud N°": solicitud_actual,
                    "Fecha": fecha_actual,
                    "Dependencia Solicitante": dependencia_selected,
                    "Servicio Aplicado": servicio_solicitud, # NUEVO CAMPO
                    "Responsable Designado": responsable_designado,
                    "Motivo": motivo_orden,
                    "Tipo de Mantenimiento": tipo_mant,
                    "Materiales Solicitados": "; ".join(materiales),
                    "Elaboró": elaboro,
                    "Revisó": reviso,
                    "Aprobó": aprobo
                }
                guardar_orden(nueva_orden)

# -------------------------------------------------------------------------
# === PESTAÑA 2: HISTORIAL Y DESCARGA ===
# -------------------------------------------------------------------------
with tab_historial:
    st.header("Historial de Órdenes Guardadas")
    
    if st.session_state.orden_data:
        df = pd.DataFrame(st.session_state.orden_data)
        st.dataframe(df, use_container_width=True)
        
        # Descarga (CSV)
        csv = convert_df_to_csv(df)
        st.download_button(
            label="⬇️ Descargar Historial (CSV)",
            data=csv,
            file_name=f'Ordenes_Mantenimiento_{date.today().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

        st.markdown("---")
        st.subheader("Descarga para Impresión")
        st.info("Para obtener un PDF, descarga el archivo TXT y usa la función de 'Imprimir a PDF' de tu sistema operativo o navegador.")
        
        # Descarga en formato TXT estructurado (para copiar/imprimir a PDF)
        markdown_data = df.to_markdown(index=False)
        st.download_button(
            label="⬇️ Descargar para Imprimir (TXT/Markdown)",
            data=markdown_data,
            file_name=f'Ordenes_Mantenimiento_Imprimir_{date.today().strftime("%Y%m%d")}.txt',
            mime='text/plain',
        )
        
    else:
        st.info("Aún no hay órdenes de mantenimiento registradas en esta sesión.")


# -------------------------------------------------------------------------
# === PESTAÑA 3: GESTIÓN DE PERSONAL ===
# -------------------------------------------------------------------------
with tab_personal:
    st.header("Administración de Personal y Firmantes")
    st.info("Ingresa el Nombre y la Profesión/Cargo. El sistema los combinará en la lista de selección.")
    
    # Formulario para Agregar Personal
    with st.form("form_agregar_personal"):
        st.subheader("Agregar Nuevo Empleado/Firmante")
        
        col_n, col_p = st.columns(2)
        with col_n:
            nombre_nuevo = st.text_input("Nombre Completo")
        with col_p:
            profesion_nueva = st.text_input("Profesión / Cargo (Ej: Técnico, Biomédico, Ing. Civil)")
            
        rol_a_modificar = st.selectbox(
            "Selecciona el Rol de Firma que tendrá",
            options=list(st.session_state.directorio_personal.keys())
        )
            
        agregar_button = st.form_submit_button("Agregar a la Lista")
        
        if agregar_button:
            if nombre_nuevo and profesion_nueva:
                agregar_personal(rol_a_modificar, nombre_nuevo, profesion_nueva)
            else:
                st.error("Debes ingresar tanto el Nombre como la Profesión/Cargo.")

    st.markdown("---")
    
    # Visualización del Directorio Actual
    st.subheader("Directorio de Firmantes Actual (Nombre - Profesión/Cargo)")
    
    data_mostrar = []
    for rol, personas in st.session_state.directorio_personal.items():
        for persona in personas:
            data_mostrar.append({"Rol de Firma": rol, "Nombre - Cargo": persona})
            
    df_directorio = pd.DataFrame(data_mostrar)
    st.dataframe(df_directorio, use_container_width=True, hide_index=True)
