import streamlit as st
import pandas as pd
from datetime import date
import io
import json
import os # Importamos os para gestionar archivos

# =========================================================================
# === 0. FUNCIONES ESENCIALES INICIALES Y MANEJO DE ARCHIVOS ===
# =========================================================================

# Nombres de archivos para persistencia
ORDENES_DATA_FILE = 'ordenes_data.json'
DIRECTORIO_DATA_FILE = 'directorio_data.json'
LOGO_URL = "https://yt3.googleusercontent.com/ytc/AIdro_mbSWHDUC7Kw_vwBstPvA2M0-SynIdMOdiq1oLmPP6RAGw=s900-c-k-c0x00ffffff-no-rj" 

def generar_solicitud_nro(current_num):
    """Genera el formato de solicitud (ej. '09-11') a partir del número base."""
    return f"09-{current_num:02d}"

def cargar_datos_persistentes(file_path, default_value):
    """Carga datos desde un archivo JSON o devuelve el valor por defecto si falla."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            # Si hay error al leer o el archivo está corrupto, usa el valor por defecto
            return default_value
    return default_value

def guardar_datos_persistentes(data, file_path):
    """Guarda datos en un archivo JSON."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error al guardar los datos en {file_path}: {e}")
        return False

# =========================================================================
# === 1. CONFIGURACIÓN Y ESTADO INICIAL ===
# =========================================================================

# Listas de Opciones Fijas
DEPENDENCIAS = ["Electrico", "Infraestructura", "Biomedico", "Otro"]
TIPOS_MANTENIMIENTO = ["Correctivo", "Preventivo", "Predictivo", "Inspección", "Instalación"]

SERVICIOS_SOLICITUD = [
    "UCI ADULTOS", "PEDIATRIA", "GINECOLOGIA", "CALL CENTER", 
    "CONSULTA EXTERNA", "APS", "UCI NEONATAL", "UCI INTERMEDIA", 
    "CIRUGIA", "HOSPITALIZACION", "URGENCIAS", "ODONTOLOGÍA", 
    "FISIOTERAPIA", "P Y P", "LABORATORIO", "GASTROENTEROLOGÍA", "OTRO"
]

# Directorio de Trabajadores/Firmantes INICIAL (Usado como fallback)
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


# --- Inicializar el estado de la sesión CARGANDO LOS DATOS ---

if 'directorio_personal' not in st.session_state:
    st.session_state.directorio_personal = cargar_datos_persistentes(DIRECTORIO_DATA_FILE, DIRECTORIO_TRABAJADORES_INICIAL)

if 'orden_data' not in st.session_state:
    st.session_state.orden_data = cargar_datos_persistentes(ORDENES_DATA_FILE, [])

# Determinar consecutivos a partir de los datos cargados o valores iniciales
ult_orden = max([d['Número de Orden'] for d in st.session_state.orden_data] or [928])
ult_solicitud_str = max([d['Solicitud N°'] for d in st.session_state.orden_data if d['Solicitud N°'].startswith('09-')] or ['09-10'])
try:
    ult_solicitud = int(ult_solicitud_str.split('-')[-1])
except ValueError:
    ult_solicitud = 10

if 'siguiente_orden_numero' not in st.session_state:
    st.session_state.siguiente_orden_numero = ult_orden + 1
    
if 'siguiente_solicitud_numero' not in st.session_state:
    st.session_state.siguiente_solicitud_numero = ult_solicitud + 1

# Variables para guardar los valores editados
if 'current_orden_nro_input' not in st.session_state:
    st.session_state.current_orden_nro_input = st.session_state.siguiente_orden_numero

if 'current_solicitud_nro_input' not in st.session_state:
    st.session_state.current_solicitud_nro_input = generar_solicitud_nro(st.session_state.siguiente_solicitud_numero)

# Bandera de control para la descarga
if 'mostrar_descarga_ultima_orden' not in st.session_state:
    st.session_state.mostrar_descarga_ultima_orden = False
# ---------------------------------------------


# =========================================================================
# === 2. FUNCIONES DE LÓGICA Y DESCARGA ===
# =========================================================================

def guardar_orden(nueva_orden):
    """Guarda la orden, actualiza CONSECUTIVOS y GUARDA EN DISCO."""
    st.session_state.orden_data.append(nueva_orden)
    
    # Lógica para actualizar los consecutivos
    nro_orden_guardado = int(nueva_orden['Número de Orden'])
    
    try:
        solicitud_num_guardado = int(nueva_orden['Solicitud N°'].split('-')[-1]) 
    except ValueError:
        solicitud_num_guardado = 0 

    # Actualizar la Orden N°: Si el número guardado es >= al consecutivo, avanzamos el consecutivo.
    if nro_orden_guardado >= st.session_state.siguiente_orden_numero:
        st.session_state.siguiente_orden_numero = nro_orden_guardado + 1
    
    if solicitud_num_guardado >= st.session_state.siguiente_solicitud_numero:
        st.session_state.siguiente_solicitud_numero = solicitud_num_guardado + 1
        
    st.session_state.current_orden_nro_input = st.session_state.siguiente_orden_numero
    st.session_state.current_solicitud_nro_input = generar_solicitud_nro(st.session_state.siguiente_solicitud_numero)

    # --- PASO CRÍTICO: GUARDAR EN DISCO ---
    guardar_datos_persistentes(st.session_state.orden_data, ORDENES_DATA_FILE)

    st.success(f"✅ Orden de Mantenimiento #{nueva_orden['Número de Orden']} guardada con éxito y **persistencia en disco**.")

@st.cache_data
def convert_df_to_excel(df):
    """Convierte un DataFrame a un archivo Excel (xlsx) en memoria."""
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Ordenes_Mantenimiento')
    processed_data = output.getvalue()
    return processed_data

def agregar_personal(rol, nombre, profesion, cc):
    nombre_key = f"{nombre} - {profesion}"
    if nombre_key and rol:
        if nombre_key not in st.session_state.directorio_personal[rol]:
            st.session_state.directorio_personal[rol][nombre_key] = {"display": nombre_key, "cc": cc}
            sorted_keys = sorted(st.session_state.directorio_personal[rol].keys())
            st.session_state.directorio_personal[rol] = {k: st.session_state.directorio_personal[rol][k] for k in sorted_keys}
            
            # --- PASO CRÍTICO: GUARDAR DIRECTORIO EN DISCO ---
            guardar_datos_persistentes(st.session_state.directorio_personal, DIRECTORIO_DATA_FILE)
            
            st.success(f"➕ **{nombre_key}** (C.C. {cc}) agregado a la lista de **{rol}**.")
        else:
            st.warning(f"⚠️ **{nombre_key}** ya existe en la lista de **{rol}**.")

# Función para generar solo el HTML (MANTENIDA con el formato INSTITUCIONAL)
def generar_html_orden(orden):
    """Genera una página HTML estructurada para la impresión a PDF, incluyendo el logo y formato institucional."""
    
    # Función de ayuda para buscar el CC del firmante.
    def get_cc(rol, display_name):
        directorio = st.session_state.directorio_personal.get(rol, {})
        for key, value in directorio.items():
            if value.get("display") == display_name:
                return value.get("cc", "N/A")
        return "N/A"

    # --- Procesamiento de Materiales ---
    materiales_html = ""
    try:
        if orden['Materiales Solicitados']:
            items_raw = orden['Materiales Solicitados'].split('; ')
            for item_full in items_raw:
                if not item_full: continue 
                try:
                    nombre_y_resto = item_full.split('. ', 1)[-1].strip()
                    parts = nombre_y_resto.rsplit(' (', 1)
                    nombre_material = parts[0].strip()
                    cantidad_unidad = parts[1].replace(')', '').strip() if len(parts) > 1 else 'N/A'
                    
                    cantidad_parts = cantidad_unidad.split(' ', 1)
                    cantidad = cantidad_parts[0]
                    unidad = cantidad_parts[1] if len(cantidad_parts) > 1 else 'UNIDAD'

                    materiales_html += f"<tr><td>{nombre_material}</td><td>{unidad}</td><td>{cantidad}</td><td></td><td></td><td></td></tr>"
                except Exception:
                    materiales_html += f"<tr><td>{item_full}</td><td>N/A</td><td>N/A</td><td></td><td></td><td></td></tr>"
        else:
            materiales_html = "".join(["<tr><td></td><td></td><td></td><td></td><td></td><td></td></tr>"] * 3)
            
    except Exception:
        materiales_html = "".join(["<tr><td>Error al cargar</td><td></td><td></td><td></td><td></td><td></td></tr>"] * 3)

    # --- Obtener C.C. del personal de firma ---
    elaboro_cc = get_cc("Elaboro", orden['Elaboró'])
    reviso_cc = get_cc("Reviso", orden['Revisó'])
    aprobo_cc = get_cc("Aprobo", orden['Aprobó'])
    
    style_content = """
        body { font-family: Arial, sans-serif; font-size: 9pt; padding: 10px 20px; }
        .container { border: 1px solid #000; padding: 0; }
        h2, h3 { color: #333; margin: 0; padding: 0; text-align: center; font-size: 11pt; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 5px; }
        th, td { border: 1px solid #000; padding: 4px; text-align: left; font-size: 9pt; vertical-align: middle; }
        th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
        .header-table td { border: none; padding: 2px 4px; font-size: 8pt; }
        .logo-cell { width: 15%; text-align: center; }
        .logo-cell img { max-width: 80px; height: auto; }
        .title-cell { width: 50%; text-align: center; font-size: 12pt; font-weight: bold; }
        .info-cell { width: 35%; }
        .info-table td { border: 1px solid #000; padding: 4px; }
        .signature-area { display: flex; justify-content: space-around; margin-top: 20px; text-align: center; }
        .signature-box { width: 30%; padding-top: 5px; margin-top: 15px; }
        .signature-line { border-top: 1px solid #000; padding-top: 5px; margin-bottom: 5px; }
        .firma-info { font-size: 8pt; }
        .celda-vacia { height: 20px; }
        .recepcion-box { 
            margin-top: 10px; 
            font-size: 9pt; 
            border: 1px solid #000; 
            padding: 5px;
            /* Estilo específico para la línea de recibido */
            display: flex;
            justify-content: space-between;
        }
        .recepcion-text {
             white-space: nowrap; 
             overflow: hidden; 
             text-overflow: clip;
             flex-grow: 1;
        }
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orden de Mantenimiento N° {orden['Número de Orden']}</title>
        <style>
            {style_content}
        </style>
    </head>
    <body>

        <div class="container">
            <table class="header-table">
                <tr>
                    <td rowspan="4" class="logo-cell" style="border-right: 1px solid #000;">
                        <img src="{LOGO_URL}" alt="Logo del Hospital">
                    </td>
                    <td colspan="2" class="title-cell" style="border-bottom: 1px solid #000;">
                        HOSPITAL REGIONAL ALFONSO JARAMILLO SALAZAR
                    </td>
                    <td class="info-cell" style="width: 20%;">
                        <strong>Código:</strong> GTAF-A-05-P-EEC-FPA-01
                    </td>
                </tr>
                <tr>
                    <td colspan="2" class="title-cell" style="border-bottom: 1px solid #000;">
                        GESTIÓN DE LA TECNOLOGÍA Y DEL AMBIENTE FÍSICO
                    </td>
                    <td class="info-cell">
                        <strong>Versión:</strong> 02
                    </td>
                </tr>
                <tr>
                    <td colspan="2" class="title-cell">
                        FORMATO: ORDEN DE MANTENIMIENTO
                    </td>
                    <td class="info-cell">
                        <strong>Fecha Aprobación:</strong> 2014/01/02
                    </td>
                </tr>
            </table>

            <table>
                <tr>
                    <td style="width: 50%;"><strong>DEPENDENCIA SOLICITANTE:</strong> {orden['Dependencia Solicitante']}</td>
                    <td style="width: 25%;"><strong>FECHA:</strong> {orden['Fecha']}</td>
                    <td style="width: 25%;"><strong>SOLICITUD N°:</strong> {orden['Solicitud N°']}</td>
                </tr>
                <tr>
                    <td colspan="3"><strong>SERVICIO APLICADO:</strong> {orden['Servicio Aplicado']}</td>
                </tr>
                <tr>
                    <td colspan="3" class="celda-vacia"></td>
                </tr>
                <tr>
                    <td colspan="3" style="text-align: center; background-color: #f0f0f0;"><strong>ORDEN DE MANTENIMIENTO N°:</strong> {orden['Número de Orden']}</td>
                </tr>
                <tr>
                    <td colspan="3"><strong>RESPONSABLE DESIGNADO:</strong> {orden['Responsable Designado']}</td>
                </tr>
                <tr>
                    <td colspan="3"><strong>TIPO DE MANTENIMIENTO:</strong> {orden['Tipo de Mantenimiento']}</td>
                </tr>
                <tr>
                    <td colspan="3"><strong>MOTIVO / DESCRIPCIÓN DEL TRABAJO:</strong> {orden['Motivo']}</td>
                </tr>
            </table>

            <h3>MATERIALES SOLICITADOS (PEDIDO ALMACÉN)</h3>
            <table>
                <tr>
                    <th style="width: 35%;">DETALLE</th>
                    <th style="width: 15%;">UNIDAD DE MEDIDA</th>
                    <th style="width: 10%;">CANTIDAD PEDIDA</th>
                    <th style="width: 10%;">CANTIDAD DESPACHADA</th>
                    <th style="width: 10%;">VALOR UNITARIO</th>
                    <th style="width: 20%;">VALOR TOTAL</th>
                </tr>
                {materiales_html}
            </table>
            
            <div style="padding: 5px;">
                <p style="font-size: 9pt;"><strong>OBSERVACIONES / CONCLUSIONES:</strong> __________________________________________________________________________________________________________________________________________________________</p>
                
                <table style="margin-top: 15px; border: none;">
                    <tr style="border: none;">
                        <td style="width: 33%; border: 1px solid #000; text-align: center; padding-bottom: 15px;">
                            <div class="signature-line"></div>
                            <span class="firma-info"><strong>ELABORÓ:</strong> {orden['Elaboró']}</span><br>
                            <span class="firma-info">C.C.: {elaboro_cc}</span>
                        </td>
                        <td style="width: 34%; border: 1px solid #000; text-align: center; padding-bottom: 15px;">
                            <div class="signature-line"></div>
                            <span class="firma-info"><strong>REVISÓ:</strong> {orden['Revisó']}</span><br>
                            <span class="firma-info">C.C.: {reviso_cc}</span>
                        </td>
                        <td style="width: 33%; border: 1px solid #000; text-align: center; padding-bottom: 15px;">
                            <div class="signature-line"></div>
                            <span class="firma-info"><strong>APROBÓ:</strong> {orden['Aprobó']}</span><br>
                            <span class="firma-info">C.C.: {aprobo_cc}</span>
                        </td>
                    </tr>
                </table>
                
                <div class="recepcion-box">
                    <span style="white-space: nowrap;">RECIBIDO POR: ____________________________________________________________________</span>
                    <span style="white-space: nowrap;">C.C.: _______________________________________________________________________</span>
                </div>

            </div>
            
        </div>
    </body>
    </html>
    """
    return html_content

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
    
    if 'ultima_orden_guardada' not in st.session_state and st.session_state.mostrar_descarga_ultima_orden:
        st.session_state.mostrar_descarga_ultima_orden = False


    with st.form(key='orden_form'):
        
        # --- Campo de Número de Orden EDITABLE ---
        col_title_1, col_title_2 = st.columns([0.6, 0.4])
        with col_title_1:
             st.subheader("Datos de la Orden")
        with col_title_2:
            st.session_state.current_orden_nro_input = st.number_input(
                "**Número de Orden** (Editable)", 
                min_value=1,
                value=int(st.session_state.current_orden_nro_input),
                step=1,
                key='orden_nro_input',
                help="Puedes cambiar el número si necesitas reasignar un consecutivo."
            )
            
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_actual = date.today().strftime("%Y-%m-%d")
            st.text_input("Fecha", value=fecha_actual, disabled=True)
        with col2:
            # --- Campo de Solicitud N° EDITABLE ---
            st.session_state.current_solicitud_nro_input = st.text_input(
                "**Solicitud N°** (Editable)", 
                value=st.session_state.current_solicitud_nro_input, 
                help="Formato: 09-XX. ¡Edita si necesitas reasignar!",
                key='solicitud_nro_input'
            )
            
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
        
        opciones_elaboro = [data["display"] for data in st.session_state.directorio_personal["Elaboro"].values()]
        opciones_reviso = [data["display"] for data in st.session_state.directorio_personal["Reviso"].values()]
        opciones_responsable = sorted(list(set(opciones_elaboro + opciones_reviso)))
        
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
            
            # --- Validaciones ---
            try:
                orden_nro_final = int(st.session_state.current_orden_nro_input)
                if orden_nro_final <= 0:
                     st.error("El Número de Orden debe ser un número entero positivo.")
                     st.stop()
            except ValueError:
                st.error("El Número de Orden debe ser un número entero válido.")
                st.stop()
                
            solicitud_nro_final = st.session_state.current_solicitud_nro_input
            if not solicitud_nro_final.startswith('09-') or not solicitud_nro_final.split('-')[-1].isdigit():
                st.error("El Número de Solicitud debe seguir el formato '09-XX'.")
                st.stop()
                
            nros_existentes = [d["Número de Orden"] for d in st.session_state.orden_data]
            solicitudes_existentes = [d["Solicitud N°"] for d in st.session_state.orden_data]
            
            if orden_nro_final in nros_existentes:
                 st.error(f"El Número de Orden **{orden_nro_final}** ya existe. Por favor, elige otro o revísalo.")
                 st.stop()
            
            if solicitud_nro_final in solicitudes_existentes:
                 st.error(f"El Número de Solicitud **{solicitud_nro_final}** ya existe. Por favor, elige otro o revísalo.")
                 st.stop()
                 
            if not motivo_orden or not materiales:
                st.error("Por favor, completa el Motivo de la Orden y al menos un ítem de Materiales (Cantidad > 0).")
                st.stop()
            
            # --- Guardar ---
            nueva_orden = {
                "Número de Orden": orden_nro_final,
                "Solicitud N°": solicitud_nro_final,
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
            st.session_state.mostrar_descarga_ultima_orden = True
            
            st.rerun() 

    # Botón para descargar/imprimir la última orden guardada
    if st.session_state.get('mostrar_descarga_ultima_orden') and st.session_state.get('ultima_orden_guardada'):
        st.markdown("---")
        st.subheader(f"Orden #{st.session_state.ultima_orden_guardada['Número de Orden']} lista para descargar:")
        
        html_content = generar_html_orden(st.session_state.ultima_orden_guardada)

        st.download_button(
            label="⬇️ Descargar Orden (Archivo HTML para Imprimir a PDF)",
            data=html_content.encode('utf-8'),
            file_name=f'Orden_Mantenimiento_N_{st.session_state.ultima_orden_guardada["Número de Orden"]}.html',
            mime='text/html',
            key='download_html_orden'
        )
        st.info("💡 **Instrucción:** Descarga el archivo **HTML**, ábrelo con tu navegador (doble clic) y luego usa **CTRL+P** o 'Imprimir' para seleccionar **'Guardar como PDF'** y obtener el documento final con el logo y el C.C.")
        
        if st.button("Crear una Nueva Orden (Limpiar sección de descarga)"):
            if 'ultima_orden_guardada' in st.session_state:
                del st.session_state.ultima_orden_guardada
            st.session_state.mostrar_descarga_ultima_orden = False
            st.rerun()


# -------------------------------------------------------------------------
# === PESTAÑA 2: HISTORIAL Y DESCARGA (Excel XLSX) ===
# -------------------------------------------------------------------------
with tab_historial:
    st.header("Historial de Órdenes Guardadas")
    
    if st.session_state.orden_data:
        df = pd.DataFrame(st.session_state.orden_data)
        st.dataframe(df, use_container_width=True)
        
        # Descarga (Excel)
        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="⬇️ Descargar Historial Completo (Excel XLSX)",
            data=excel_data,
            file_name=f'Ordenes_Mantenimiento_{date.today().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
        )
        
    else:
        st.info("Aún no hay órdenes de mantenimiento registradas en esta sesión.")


# -------------------------------------------------------------------------
# === PESTAÑA 3: GESTIÓN DE PERSONAL ===
# -------------------------------------------------------------------------
with tab_personal:
    st.header("Administración de Personal y Firmantes")
    
    # 1. FORMULARIO PARA AGREGAR PERSONAL 
    st.info("Ingresa el Nombre, el Cargo y el Número de Identificación para añadir un nuevo firmante. Para eliminar, usa la tabla de abajo.")
    with st.form("form_agregar_personal"):
        st.subheader("Agregar Nuevo Empleado/Firmante")
        
        col_n, col_p, col_c = st.columns(3)
        with col_n:
            nombre_nuevo = st.text_input("Nombre Completo")
        with col_p:
            profesion_nueva = st.text_input("Profesión / Cargo (Ej: Técnico, Biomédico)")
        with col_c:
            cc_nuevo = st.text_input("Número de Identificación (C.C.)", max_chars=15)
            
        rol_a_modificar = st.selectbox(
            "Selecciona el Rol de Firma que tendrá",
            options=list(st.session_state.directorio_personal.keys())
        )
            
        agregar_button = st.form_submit_button("Agregar a la Lista")
        
        if agregar_button:
            if nombre_nuevo and profesion_nueva and cc_nuevo:
                agregar_personal(rol_a_modificar, nombre_nuevo, profesion_nueva, cc_nuevo)
            else:
                st.error("Debes ingresar el Nombre, la Profesión/Cargo y el Número de Identificación.")

    st.markdown("---")
    
    # 2. DIRECTORIO ACTUAL CON EDICIÓN Y ELIMINACIÓN HABILITADA
    st.subheader("Directorio de Firmantes Actual (Edita o usa el icono de 'cubo de basura' para eliminar)")
    
    data_mostrar = []
    for rol, personas_dict in st.session_state.directorio_personal.items():
        nombre_rol_display = rol.replace('o', 'ó').replace('e', 'e') 
        for key, data in personas_dict.items():
            data_mostrar.append({
                "ID_Rol": rol, 
                "Rol de Firma": nombre_rol_display, 
                "Nombre - Cargo": data["display"], 
                "CC": data["cc"]
            })
            
    df_directorio = pd.DataFrame(data_mostrar)
    
    edited_df = st.data_editor(
        df_directorio,
        column_config={
            "ID_Rol": st.column_config.Column(disabled=True, width="small"),
            "Rol de Firma": st.column_config.SelectboxColumn(
                "Rol de Firma", 
                options=["Elaboro", "Reviso", "Aprobo"]
            ),
            "Nombre - Cargo": st.column_config.Column(required=True),
            "CC": st.column_config.Column("C.C.", required=True, width="small")
        },
        hide_index=False, 
        num_rows="dynamic", 
        use_container_width=True,
        key='data_editor_directorio'
    )
    
    # 3. Lógica para GUARDAR los cambios del editor de datos
    if st.button("Guardar Cambios Editados del Directorio", type="primary"):
        nuevo_directorio = {"Elaboro": {}, "Reviso": {}, "Aprobo": {}}
        
        for index, row in edited_df.iterrows():
            
            if pd.isna(row["Nombre - Cargo"]) or pd.isna(row["CC"]):
                continue 

            rol_key = row["Rol de Firma"].replace('ó', 'o').replace('é', 'e')
            
            if rol_key not in nuevo_directorio:
                 st.warning(f"Rol '{row['Rol de Firma']}' no válido. Omitiendo empleado.")
                 continue

            nombre_key = row["Nombre - Cargo"]
            
            nuevo_directorio[rol_key][nombre_key] = {
                "display": nombre_key,
                "cc": str(row["CC"]) 
            }
        
        st.session_state.directorio_personal = nuevo_directorio
        
        # --- PASO CRÍTICO: GUARDAR DIRECTORIO EN DISCO ---
        guardar_datos_persistentes(st.session_state.directorio_personal, DIRECTORIO_DATA_FILE)
        
        st.success("💾 Directorio de personal actualizado y guardado con éxito.")
        st.rerun()
