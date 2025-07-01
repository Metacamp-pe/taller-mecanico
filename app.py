import streamlit as st
import pandas as pd
from fpdf import FPDF
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
import streamlit_authenticator as stauth

# Configuración de página
st.set_page_config(page_title="App de Taller Vehicular", layout="wide")

# --- Autenticación segura ---
users = {
    "usernames": {
        "recepcion": {
            "name": "recepcion",
            "password": "$2b$12$nYYGLsCKSwT6Mbk3/vnRKuPTvNdhlDBbD0QaUMtxxMXosOfxD1Rqi"
        },
        "mecanico": {
            "name": "mecanico",
            "password": "$2b$12$nYYGLsCKSwT6Mbk3/vnRKuPTvNdhlDBbD0QaUMtxxMXosOfxD1Rqi"
        },
        "supervisor": {
            "name": "supervisor",
            "password": "$2b$12$nYYGLsCKSwT6Mbk3/vnRKuPTvNdhlDBbD0QaUMtxxMXosOfxD1Rqi"
        },
    }
}

authenticator = stauth.Authenticate(
    users,
    "taller_auth",
    "abcdef",
    cookie_expiry_days=1
)

# --- Login centrado ---
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name, authentication_status, username = authenticator.login("Iniciar sesión", "main")

# --- Manejo del estado de autenticación ---
if authentication_status is False:
    st.error("Usuario o contraseña incorrectos.")
    st.stop()
elif authentication_status is None:
    st.warning("Por favor, inicie sesión con su usuario y contraseña.")
    st.stop()

# --- Contenido después del login exitoso ---
st.sidebar.success(f"Bienvenido, {name} 👋")
st.title("🚗 App de Taller Vehicular")

# Conectar con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(dict(credentials_info), scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key("1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps").sheet1
data = pd.DataFrame(sheet.get_all_records())

# --- Sección por roles ---
if username == "recepcion":
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
            nuevo_id, str(fecha), username, cliente, "", "", "", "",
            placa, "", "", "", "", "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "", "", "", "", "", ""
        ]
        sheet.append_row(nueva_fila)
        st.success("✅ Registro guardado correctamente.")
        st.experimental_rerun()

    with st.expander("📋 Ver historial de tickets recibidos"):
        st.dataframe(data[data["Recepcionista"] == username])

elif username == "mecanico":
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
            sheet.update_cell(idx, data.columns.get_loc("Mecánico") + 1, username)
            st.success("✅ Diagnóstico guardado correctamente.")
            st.experimental_rerun()

    with st.expander("📋 Historial de diagnósticos enviados"):
        st.dataframe(data[data["Mecánico"] == username])

elif username == "supervisor":
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
            supervisor = st.text_input("Supervisor", username)
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
        st.dataframe(data[data["Supervisor"] == username])
