import streamlit as st
import pandas as pd
from fpdf import FPDF
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

# Configurar la página
st.set_page_config(page_title="App de Taller Vehicular", layout="wide")

# --- USUARIOS y LOGIN MANUAL ---
usuarios = {
    "recepcion": "1234",
    "mecanico": "1234",
    "supervisor": "1234"
}

if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "rol" not in st.session_state:
    st.session_state.rol = ""

if not st.session_state.auth_status:
    st.title("🔐 Iniciar sesión")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario in usuarios and clave == usuarios[usuario]:
            st.session_state.auth_status = True
            st.session_state.rol = usuario
            st.success("Inicio de sesión exitoso 🎉")
            st.rerun() 
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# --- CONTENIDO DE LA APP (una vez autenticado) ---
st.sidebar.success(f"Bienvenido, {st.session_state.rol} 👋")
st.title("🚗 App de Taller Vehicular")

# Conectar con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(dict(credentials_info), scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key("1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps").sheet1
data = pd.DataFrame(sheet.get_all_records())

# --- ROLES ---
if st.session_state.rol == "recepcion":
    st.header("Recepción del vehículo")
    with st.form("recepcion_form"):
        cliente = st.text_input("Nombre del cliente")
        placa = st.text_input("Placa del vehículo")
        fecha = st.date_input("Fecha de ingreso")
        motivo = st.text_area("Motivo del ingreso")
        enviado = st.form_submit_button("Guardar")
    if enviado:
        nuevo_id = len(data) + 1 if not data.empty else 1
        nueva_fila = [
            nuevo_id, str(fecha), st.session_state.rol, cliente, "", "", "", "",
            placa, "", "", "", "", "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "", "", "", "", ""
        ]
        sheet.append_row(nueva_fila)
        st.success("✅ Registro guardado correctamente.")
        st.experimental_rerun()

    with st.expander("📋 Ver historial de tickets recibidos"):
        st.dataframe(data[data["Recepcionista"] == st.session_state.rol])

elif st.session_state.rol == "mecanico":
    st.header("Diagnóstico del vehículo")
    pendientes = data[(data["Diagnóstico"] == "") & (data["Estado"] == "")]
    if pendientes.empty:
        st.info("No hay tickets pendientes para diagnóstico.")
    else:
        placa_sel = st.selectbox("Selecciona la placa", pendientes["Placa"].unique())
        with st.form("diagnostico_form"):
            diagnostico = st.text_area("Diagnóstico")
            obs = st.text_area("Observaciones del mecánico")
            mo = st.text_input("Descripción mano de obra")
            mo_cant = st.number_input("Cantidad MO", min_value=0, value=1)
            mo_precio = st.number_input("Precio Unitario MO", min_value=0.0, value=0.0)
            enviado = st.form_submit_button("Guardar diagnóstico")
        if enviado:
            idx = data[data["Placa"] == placa_sel].index[0] + 2
            sheet.update_cell(idx, data.columns.get_loc("Diagnóstico") + 1, diagnostico)
            sheet.update_cell(idx, data.columns.get_loc("Observaciones_Mecánico") + 1, obs)
            sheet.update_cell(idx, data.columns.get_loc("MO_Descripción") + 1, mo)
            sheet.update_cell(idx, data.columns.get_loc("MO_Cantidad") + 1, mo_cant)
            sheet.update_cell(idx, data.columns.get_loc("MO_Precio_Unit") + 1, mo_precio)
            sheet.update_cell(idx, data.columns.get_loc("MO_Precio_Total") + 1, mo_cant * mo_precio)
            sheet.update_cell(idx, data.columns.get_loc("Mecánico") + 1, st.session_state.rol)
            st.success("✅ Diagnóstico guardado correctamente.")
            st.experimental_rerun()

    with st.expander("📋 Historial de diagnósticos enviados"):
        st.dataframe(data[data["Mecánico"] == st.session_state.rol])

elif st.session_state.rol == "supervisor":
    st.header("Aprobación Final y PDF")
    pendientes = data[(data["Diagnóstico"] != "") & (data["Estado"] == "")]
    if pendientes.empty:
        st.info("No hay tickets pendientes para aprobación.")
    else:
        selected = st.selectbox("Selecciona la placa", pendientes["Placa"].unique())
        ticket = pendientes[pendientes["Placa"] == selected].iloc[0]
        st.write("### Resumen del ticket")
        st.json(ticket.to_dict())

        with st.form("aprobacion_form"):
            supervisor = st.text_input("Supervisor", st.session_state.rol)
            comentario = st.text_area("Comentarios")
            aprobado = st.checkbox("Aprobar")
            enviar = st.form_submit_button("Finalizar")

        if enviar:
            idx = data[data["Placa"] == selected].index[0] + 2
            sheet.update_cell(idx, data.columns.get_loc("Supervisor") + 1, supervisor)
            sheet.update_cell(idx, data.columns.get_loc("Comentarios_Supervisor") + 1, comentario)
            sheet.update_cell(idx, data.columns.get_loc("Estado") + 1, "Aprobado" if aprobado else "Rechazado")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Resumen de Servicio", ln=True, align="C")
            for k, v in ticket.items():
                pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)

            pdf_buffer = BytesIO()
            pdf.output(pdf_buffer)
            pdf_buffer.seek(0)

            st.download_button(
                "🔖 Descargar PDF",
                pdf_buffer,
                file_name=f"Ticket_{selected}.pdf",
                mime="application/pdf"
            )
            st.success("✅ Aprobación finalizada y PDF generado.")

    with st.expander("📋 Historial de aprobaciones"):
        st.dataframe(data[data["Supervisor"] == st.session_state.rol])
