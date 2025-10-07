import streamlit as st
import pandas as pd
from datetime import date
import io
import base64

# =========================================================================
# === 1. CONFIGURACIÓN Y ESTADO INICIAL ===
# =========================================================================

# URL del Logo proporcionada por el usuario
LOGO_URL = "https://yt3.googleusercontent.com/ytc/AIdro_mbSWHDUC7Kw_vwBstPvA2M0-SynIdMOdiq1oLmPP6RAGw=s900-c-k-c0x00ffffff-no-rj"

# Listas de Opciones Fijas
DEPENDENCIAS = ["Electrico", "Infraestructura", "Biomedico", "Otro"]
TIPOS_MANTENIMIENTO = ["Correctivo", "Preventivo", "Predictivo", "Inspección", "Instalación"]

SERVICIOS_SOLICITUD = [
    "UCI ADULTOS", "PEDIATRIA", "GINECOLOGIA", "CALL CENTER", 
    "CONSULTA EXTERNA", "APS", "UCI NEONATAL", "UCI INTERMEDIA", 
    "CIRUGIA", "HOSPITALIZACION", "URGENCIAS", "ODONTOLOGÍA", 
    "FISIOTERAPIA", "P Y P", "LABORATORIO", "GASTROENTEROLOGÍA", "OTRO"
]

# Directorio de Trabajadores/Firmantes INICIAL
# ## CAMBIO: La estructura de los datos del personal cambia a un diccionario
# ## CAMBIO: El valor será ahora un diccionario con 'display' y 'cc'
# {Rol: {Nombre_Profesion: {"display": "Nombre - Profesión", "cc": "123456"}}}

DIRECTORIO_TRABAJADORES_INICIAL = {
    "Elaboro": {
        "Magaly Gómez - Técnica": {"display": "Magaly Gómez - Técnica", "cc": "111111"},
        "Oscar Muñoz - Operario": {"display": "Oscar Muñoz - Operario", "cc": "222222"}
    },
    "Reviso": {
        "Danna Hernandez - Coordinadora Mantenimiento": {"display": "Danna Hernandez - Coordinadora Mantenimiento", "cc": "333333"},
        "Hery Peña - Biomédico": {"display": "Hery Peña - Biomédico", "cc": "444444"},
        "Jefe de Mantenimiento - Ingeniería": {"display": "Jefe de Mantenimiento - Ingeniería", "cc": "555555"}
    },
    "Aprobo": {
        "Gerente de Operaciones - Gerente": {"display": "Gerente de Operaciones - Gerente", "cc": "666666"},
        "Jefe de Almacén - Logística": {"display": "Jefe de Almacén - Logística", "cc": "777777"}
    }
}

# Inicializar el estado de la sesión
if 'orden_data' not in st.session_state:
    st.session_state.orden_data = []

if 'directorio_personal' not in st.session_state:
    st.session_state.directorio_personal = DIRECTORIO_TRABAJADORES_INICIAL

if 'siguiente_orden_numero' not in st.session_state:
    st.session_state.siguiente_orden_numero = 929 
    
if 'siguiente_solicitud_numero' not in st.session_state:
    st.session_state.siguiente_solicitud_numero = 11

# =========================================================================
# === 2. FUNCIONES DE LÓGICA Y DESCARGA ===
# =========================================================================

def generar_solicitud_nro(current_num):
    return f"09-{current_num:02d}"

def guardar_orden(nueva_orden):
    st.session_state.orden_data.append(nueva_orden)
    st.session_state.siguiente_orden_numero += 1
    st.session_state.siguiente_solicitud_numero += 1
    st.success(f"✅ Orden de Mantenimiento #{nueva_orden['Número de Orden']} guardada con éxito.")

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

## CAMBIO: Se modifica la función para recibir el 'cc' y guardarlo en el diccionario anidado.
def agregar_personal(rol, nombre, profesion, cc):
    nombre_key = f"{nombre} - {profesion}"
    if nombre_key and rol:
        if nombre_key not in st.session_state.directorio_personal[rol]:
            st.session_state.directorio_personal[rol][nombre_key] = {"display": nombre_key, "cc": cc}
            # Opcional: Para ordenar visualmente las claves del diccionario
            sorted_keys = sorted(st.session_state.directorio_personal[rol].keys())
            st.session_state.directorio_personal[rol] = {k: st.session_state.directorio_personal[rol][k] for k in sorted_keys}
            st.success(f"➕ **{nombre_key}** (C.C. {cc}) agregado a la lista de **{rol}**.")
        else:
            st.warning(f"⚠️ **{nombre_key}** ya existe en la lista de **{rol}**.")

## CAMBIO: Se modifica la función para incluir el C.C. en el HTML.
def generar_html_orden(orden):
    """Genera una página HTML estructurada para la impresión a PDF, incluyendo el logo."""
    
    materiales_html = ""
    # Esta función asume que Materiales Solicitados es una cadena separada por '; '
    try:
        for item in orden['Materiales Solicitados'].split('; '):
            # Intenta parsear cada ítem
            if '(' in item and ')' in item:
                nombre_material = item.split('(')[0].split('. ', 1)[-1].strip()
                cantidad_unidad = item.split('(')[1].replace(')', '')
                materiales_html += f"<tr><td>{nombre_material}</td><td></td><td>{cantidad_unidad}</td></tr>"
            else:
                 materiales_html += f"<tr><td>{item}</td><td></td><td>N/A</td></tr>"
    except Exception:
          materiales_html = "<tr><td colspan='3'>Error al cargar detalles de materiales.</td></tr>"

    # Obtener C.C. del personal de firma
    # Se debe buscar la información completa del personal en el directorio
    
    # Función de ayuda para buscar el CC del firmante.
    def get_cc(rol, display_name):
        directorio = st.session_state.directorio_personal.get(rol, {})
        # Buscamos la clave del directorio que coincide con el 'display_name' guardado
        # Iteramos sobre las claves (nombre - profesión) para encontrar la coincidencia.
        for key, value in directorio.items():
            if value["display"] == display_name:
                return value["cc"]
        return "N/A"

    elaboro_cc = get_cc("Elaboro", orden['Elaboró'])
    reviso_cc = get_cc("Reviso", orden['Revisó'])
    aprobo_cc = get_cc("Aprobo", orden['Aprobó'])

    # El código HTML se mantiene similar, pero se añade el C.C.

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orden de Mantenimiento N° {orden['Número de Orden']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 10pt; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ccc; padding-bottom: 10px; margin-bottom: 20px; }}
            .header img {{ max-width: 100px; height: auto; border-radius: 50%; }}
            .header-info {{ text-align: right; }}
            h2 {{ color: #333; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .signature-area {{ display: flex; justify-content: space-around; margin-top: 40px; text-align: center; }}
            .signature-box {{ width: 30%; padding-top: 5px; }}
            .signature-line {{ border-top: 1px solid #000; padding-top: 5px; display: inline-block; width: 80%; }}
        </style>
    </head>
    <body>

        <div class="header">
            <img src="{LOGO_URL}" alt="Logo del Hospital">
            <div class="header-info">
                <h2>HOSPITAL REGIONAL ALFONSO JARAMILLO SALAZAR</h2>
                <strong>ORDEN DE MANTENIMIENTO</strong><br>
                Código: GTAF-A-05-P-EEC-FPA-01
            </div>
        </div>

        <h3>DATOS DE LA ORDEN</h3>
        <table>
            <tr><th>Número de Orden</th><td>{orden['Número de Orden']}</td><th>Fecha</th><td>{orden['Fecha']}</td></tr>
            <tr><th>Solicitud N°</th><td>{orden['Solicitud N°']}</td><th>Dependencia Solicitante</th><td>{orden['Dependencia Solicitante']}</td></tr>
            <tr><th>Servicio Aplicado</th><td colspan="3">{orden['Servicio Aplicado']}</td></tr>
            <tr><th>Responsable Designado</th><td colspan="3">{orden['Responsable Designado']}</td></tr>
            <tr><th>Tipo de Mantenimiento</th><td colspan="3">{orden['Tipo de Mantenimiento']}</td></tr>
        </table>
        
        <h3>MOTIVO DE LA ORDEN</h3>
        <table>
            <tr><td colspan="3">{orden['Motivo']}</td></tr>
        </table>

        <h3>MATERIALES SOLICITADOS</h3>
        <table>
            <tr><th>DETALLE</th><th>VALOR UNITARIO</th><th>CANTIDAD Y UNIDAD</th></tr>
            {materiales_html}
        </table>

        <div class="signature-area">
            <div class="signature-box">
                <div class="signature-line"></div><br>
                {orden['Elaboró']}<br>
                **C.C.: {elaboro_cc}**<br>
                Elaboró
            </div>
            <div class="signature-box">
                <div class="signature-line"></div><br>
                {orden['Revisó']}<br>
                **C.C.: {reviso_cc}**<br>
                Revisó
            </div>
            <div class="signature-box">
                <div class="signature-line"></div><br>
                {orden['Aprobó']}<br>
                **C.C.: {aprobo_cc}**<br>
                Aprobó
            </div>
        </div>
        <p style="margin-top: 50px;">Recibido por: ___________________________________ C.C.: ______________________</p>
    </body>
    </html>
    """
    # Codificar el HTML para incrustarlo en un enlace data URI
    b64_html = base64.b64encode(html_content.encode('utf-8')).decode()
    
    ## CAMBIO: El enlace genera un archivo PDF al nombrarlo '.pdf', aunque usa la función de impresión de HTML.
    ## Esto es para mejorar la experiencia del usuario y que se vea el nombre de archivo sugerido.
    return f'<a href="data:text/html;base64,{b64_html}" target="_blank" style="text-decoration: none; padding: 10px; background-color: #4CAF50; color: white; border-radius: 5px;">📄 Abrir Orden para Imprimir a PDF</a>'
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
    
    orden_guardada_recientemente = False

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

        servicio_solicitud = st.selectbox(
            "Servicio al que Aplica la Solicitud", 
            options=SERVICIOS_SOLICITUD
        )

        motivo_orden = st.text_area("Motivo de la Orden (Descripción del trabajo/falla)", 
                                    placeholder=f"Ej: Se solicita una lámpara de sobreponer de 18w, para el servicio de {servicio_solicitud}...", 
                                    max_chars=500)
        
        tipo_mant = st.selectbox("Tipo de Mantenimiento", options=TIPOS_MANTENIMIENTO) 

        # --- Campo de Responsable (Flexible) ---
        st.markdown("### Responsable Designado")
        
        ## CAMBIO: Obtener solo el valor 'display' (Nombre - Profesión) para la selección
        opciones_elaboro = [data["display"] for data in st.session_state.directorio_personal["Elaboro"].values()]
        opciones_reviso = [data["display"] for data in st.session_state.directorio_personal["Reviso"].values()]
        opciones_responsable = opciones_elaboro + opciones_reviso
        
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
        
        ## CAMBIO: Obtener solo el valor 'display' para los selectbox
        opciones_aprobo = [data["display"] for data in st.session_state.directorio_personal["Aprobo"].values()]
        
        col_e, col_r, col_a = st.columns(3)
        with col_e:
            elaboro = st.selectbox("Elaboró", options=opciones_elaboro)
        with col_r:
            reviso = st.selectbox("Revisó", options=opciones_reviso)
        with col_a:
            aprobo = st.selectbox("Aprobó", options=opciones_aprobo)

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
                    "Servicio Aplicado": servicio_solicitud,
                    "Responsable Designado": responsable_designado,
                    "Motivo": motivo_orden,
                    "Tipo de Mantenimiento": tipo_mant,
                    "Materiales Solicitados": "; ".join(materiales),
                    "Elaboró": elaboro,
                    "Revisó": reviso,
                    "Aprobó": aprobo
                }
                guardar_orden(nueva_orden)
                st.session_state.ultima_orden_guardada = nueva_orden
                orden_guardada_recientemente = True

    # Botón para descargar/imprimir la última orden guardada
    if st.session_state.get('ultima_orden_guardada') and orden_guardada_recientemente:
        st.markdown("---")
        st.subheader(f"Orden #{st.session_state.ultima_orden_guardada['Número de Orden']} lista para imprimir:")
        
        st.markdown(
            generar_html_orden(st.session_state.ultima_orden_guardada), 
            unsafe_allow_html=True
        )
        st.info("Presiona el botón para abrir la orden en una nueva ventana. Luego usa **CTRL+P** o 'Imprimir' y selecciona **'Guardar como PDF'** en tu navegador para generar el archivo final con el logo y el C.C.")


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
        
    else:
        st.info("Aún no hay órdenes de mantenimiento registradas en esta sesión.")


# -------------------------------------------------------------------------
# === PESTAÑA 3: GESTIÓN DE PERSONAL ===
# -------------------------------------------------------------------------
with tab_personal:
    st.header("Administración de Personal y Firmantes")
    st.info("Ingresa el Nombre, el Cargo y el Número de Identificación. El sistema los combinará.")
    
    with st.form("form_agregar_personal"):
        st.subheader("Agregar Nuevo Empleado/Firmante")
        
        col_n, col_p, col_c = st.columns(3) ## CAMBIO: Nueva columna para C.C.
        with col_n:
            nombre_nuevo = st.text_input("Nombre Completo")
        with col_p:
            profesion_nueva = st.text_input("Profesión / Cargo (Ej: Técnico, Biomédico)")
        with col_c: ## CAMBIO: Campo de entrada para C.C.
            cc_nuevo = st.text_input("Número de Identificación (C.C.)", max_chars=15)
            
        rol_a_modificar = st.selectbox(
            "Selecciona el Rol de Firma que tendrá",
            options=list(st.session_state.directorio_personal.keys())
        )
            
        agregar_button = st.form_submit_button("Agregar a la Lista")
        
        if agregar_button:
            if nombre_nuevo and profesion_nueva and cc_nuevo: ## CAMBIO: Se valida cc_nuevo
                agregar_personal(rol_a_modificar, nombre_nuevo, profesion_nueva, cc_nuevo)
            else:
                st.error("Debes ingresar el Nombre, la Profesión/Cargo y el Número de Identificación.")

    st.markdown("---")
    
    st.subheader("Directorio de Firmantes Actual")
    
    data_mostrar = []
    for rol, personas_dict in st.session_state.directorio_personal.items(): ## CAMBIO: Se itera sobre el diccionario anidado
        nombre_rol_display = rol.replace('o', 'ó').replace('e', 'é')
        
        for key, data in personas_dict.items():
            data_mostrar.append({
                "Rol de Firma": nombre_rol_display, 
                "Nombre - Cargo": data["display"], 
                "C.C.": data["cc"] ## CAMBIO: Se añade el C.C. para mostrar en el directorio.
            })
            
    df_directorio = pd.DataFrame(data_mostrar)
    st.dataframe(df_directorio, use_container_width=True, hide_index=True)
