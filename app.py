import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from io import BytesIO
import json
from datetime import datetime

st.set_page_config(page_title="App de Taller Vehicular", layout="wide")

# --- Login simplificado ---
if "rol" not in st.session_state:
    st.title("Iniciar sesión")
    rol = st.selectbox("Selecciona tu perfil", ["", "recepcion", "mecanico", "supervisor"])
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if password == "1234" and rol in ["recepcion", "mecanico", "supervisor"]:
            st.session_state.rol = rol
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrecta")

# --- Si ya ha iniciado sesión ---
if "rol" in st.session_state:
    st.success(f"Sesión iniciada como: {st.session_state.rol}")
    if st.button("Cerrar sesión"):
        del st.session_state.rol
        st.rerun()

    # --- Conexión a Google Sheets ---
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials_info = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
        client = gspread.authorize(credentials)

        # Conectarse a la hoja Sheet1 del archivo
        sheet = client.open_by_key("1279gxeATNQw5omA6RwYH8pIS-uFu8Yagy0t4frQA0uE").worksheet("Sheet1")
        data = pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error("❌ Error accediendo a la hoja de Google Sheets. Revisa si el archivo existe, el ID es correcto y tienes acceso.")
        st.stop()

    # --- RECEPCIONISTA ---
    if st.session_state.rol == "recepcion":
        st.header("Registro de Ingreso del Vehículo")
        with st.form("recepcion_form"):
            cliente = st.text_input("Cliente")
            dni_ruc = st.text_input("DNI o RUC")
            direccion = st.text_input("Dirección")
            telefono = st.text_input("Teléfono")
            correo = st.text_input("Correo electrónico")
            placa = st.text_input("Placa del vehículo")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            color = st.text_input("Color")
            km = st.number_input("Kilometraje", min_value=0)
            enviado = st.form_submit_button("Registrar")

        if enviado:
            nuevo_id = len(data) + 1 if not data.empty else 1
            nueva_fila = [
                nuevo_id, datetime.now().strftime("%Y-%m-%d"), "recepcion", cliente, dni_ruc, direccion, telefono,
                correo, placa, marca, modelo, color, km, "", "", "", "", "", "", "", "", "", "",
                "", "", "", "", "", "", "", "", ""
            ]
            sheet.append_row(nueva_fila)
            st.success("✅ Ticket registrado correctamente.")
            st.rerun()

    # --- MECÁNICO ---
    elif st.session_state.rol == "mecanico":
        st.header("Diagnóstico y Mano de Obra")
        pendientes = data[(data["Diagnóstico"] == "") & (data["Estado"] == "")]
        if pendientes.empty:
            st.info("No hay tickets pendientes para diagnóstico.")
        else:
            placa_sel = st.selectbox("Selecciona una placa", pendientes["Placa"].unique())
            ticket = pendientes[pendientes["Placa"] == placa_sel].iloc[0]
            with st.form("diagnostico_form"):
                diagnostico = st.text_area("Diagnóstico")
                mantenimiento = st.text_input("Mantenimiento (1,000 km)")
                obs = st.text_area("Observaciones del mecánico")
                mo_desc = st.text_input("Descripción mano de obra")
                mo_cant = st.number_input("Cantidad MO", min_value=1, value=1)
                mo_precio = st.number_input("Precio unitario MO", min_value=0.0, value=0.0)
                enviar = st.form_submit_button("Guardar diagnóstico")

            if enviar:
                idx = data[data["Placa"] == placa_sel].index[0] + 2
                sheet.update_cell(idx, data.columns.get_loc("Diagnóstico") + 1, diagnostico)
                sheet.update_cell(idx, data.columns.get_loc("Mantenimiento_1_000_KM") + 1, mantenimiento)
                sheet.update_cell(idx, data.columns.get_loc("Observaciones_Mecánico") + 1, obs)
                sheet.update_cell(idx, data.columns.get_loc("MO_Descripción") + 1, mo_desc)
                sheet.update_cell(idx, data.columns.get_loc("MO_Cantidad") + 1, mo_cant)
                sheet.update_cell(idx, data.columns.get_loc("MO_Precio_Unit") + 1, mo_precio)
                sheet.update_cell(idx, data.columns.get_loc("MO_Precio_Total") + 1, mo_cant * mo_precio)
                sheet.update_cell(idx, data.columns.get_loc("Mecánico") + 1, "mecanico")
                st.success("✅ Diagnóstico guardado correctamente.")
                st.rerun()

    # --- SUPERVISOR ---
    elif st.session_state.rol == "supervisor":
        st.header("Aprobación del Servicio")
        pendientes = data[(data["Diagnóstico"] != "") & (data["Estado"] == "")]
        if pendientes.empty:
            st.info("No hay tickets pendientes para aprobación.")
        else:
            placa_sel = st.selectbox("Selecciona una placa pendiente", pendientes["Placa"].unique())
            ticket = pendientes[pendientes["Placa"] == placa_sel].iloc[0]
            st.write("### Información del ticket")
            st.json(ticket.to_dict())

            with st.form("form_supervision"):
                comentario = st.text_area("Comentario del supervisor")
                estado = st.selectbox("Estado final", ["Aprobado", "Rechazado"])
                enviar = st.form_submit_button("Finalizar")

            if enviar:
                idx = data[data["Placa"] == placa_sel].index[0] + 2
                sheet.update_cell(idx, data.columns.get_loc("Supervisor") + 1, "supervisor")
                sheet.update_cell(idx, data.columns.get_loc("Comentarios_Supervisor") + 1, comentario)
                sheet.update_cell(idx, data.columns.get_loc("Estado") + 1, estado)

                st.success("✅ Ticket finalizado correctamente. Puedes descargar el PDF abajo.")

                # --- Generar PDF ---
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.cell(200, 10, txt="Resumen del Servicio - Taller Mecánico", ln=True, align="C")
                pdf.ln(10)

                for key, value in ticket.items():
                    pdf.cell(0, 10, f"{key}: {value}", ln=True)

                pdf.cell(0, 10, f"Supervisor: supervisor", ln=True)
                pdf.cell(0, 10, f"Comentario: {comentario}", ln=True)
                pdf.cell(0, 10, f"Estado final: {estado}", ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output, 'F')
                pdf_output.seek(0)

                st.download_button(
                    label="📄 Descargar PDF del Ticket",
                    data=pdf_output,
                    file_name=f"ticket_{ticket['Placa']}.pdf",
                    mime="application/pdf"
    )

else:
    st.info("Por favor, inicia sesión para usar la aplicación.")

