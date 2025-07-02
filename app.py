import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
from io import BytesIO
import json
import streamlit_authenticator as stauth
from datetime import datetime

st.set_page_config(page_title="App de Taller Vehicular", layout="wide")

# --- Autenticación de usuarios ---
credentials = {
    "usernames": {
        "recepcion": {"name": "recepcion", "password": "1234"},
        "mecanico": {"name": "mecanico", "password": "1234"},
        "supervisor": {"name": "supervisor", "password": "1234"},
    }
}

authenticator = stauth.Authenticate(
    credentials, "app_cookie", "abcdef", cookie_expiry_days=1
)
name, authentication_status, username = authenticator.login("Iniciar sesión", "main")

if authentication_status:
    st.session_state.rol = username

    # --- Conexión con Google Sheets ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_info = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
    client = gspread.authorize(credentials)

    sheet = client.open_by_key("1279gxeATNQw5omA6RwYH8pIS-uFu8Yagy0t4frQA0uE").sheet1
    data = pd.DataFrame(sheet.get_all_records())

    sheet_inventario = client.open_by_key("1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps").worksheet("inventario_prueba")
    data_inv = pd.DataFrame(sheet_inventario.get_all_records())

    lubricantes_predef = ["ACEITE DE MOTOR SAE 15W40 (LT)", "REFRIGERANTE", "LÍQUIDO DE FRENOS"]

    # --- RECEPCION ---
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
                nuevo_id, datetime.now().strftime("%Y-%m-%d"), username, cliente, dni_ruc, direccion, telefono,
                correo, placa, marca, modelo, color, km, "", "", "", "", "", "", "", "", "", "",
                "", "", "", "", "", "", "", "", "", ""
            ]
            sheet.append_row(nueva_fila)
            st.success("✅ Ticket registrado correctamente.")
            st.experimental_rerun()

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
                sheet.update_cell(idx, data.columns.get_loc("Mecánico") + 1, username)
                st.success("✅ Diagnóstico guardado correctamente.")
                st.experimental_rerun()

    # --- SUPERVISOR ---
    elif st.session_state.rol == "supervisor":
        st.header("Aprobación y Generación de PDF")
        pendientes = data[(data["Diagnóstico"] != "") & (data["Estado"] == "")]
        if pendientes.empty:
            st.info("No hay tickets pendientes para aprobación.")
        else:
            selected = st.selectbox("Selecciona la placa", pendientes["Placa"].unique())
            ticket = pendientes[pendientes["Placa"] == selected].iloc[0]
            with st.form("aprobacion_form"):
                comentario = st.text_area("Comentarios del supervisor")
                aprobado = st.checkbox("Aprobar")

                st.subheader("Lubricantes/Fluidos")
                lubricantes_sel = st.multiselect("Selecciona lubricantes", lubricantes_predef)
                subtotal_lub = 0
                for lub in lubricantes_sel:
                    cant = st.number_input(f"Cantidad de {lub}", min_value=1, value=1, key=f"lub_{lub}")
                    precio = st.number_input(f"Precio unitario de {lub}", min_value=0.0, value=0.0, key=f"prec_{lub}")
                    subtotal_lub += cant * precio

                st.subheader("Repuestos")
                repuestos_sel = st.multiselect("Selecciona repuestos", data_inv["Producto"].unique())
                total_repuestos = 0
                subtotal_mo = float(ticket["MO_Precio_Total"]) if ticket["MO_Precio_Total"] else 0
                detalles_repuestos = []
                for rep in repuestos_sel:
                    item = data_inv[data_inv["Producto"] == rep].iloc[0]
                    cantidad = st.number_input(f"Cantidad de {rep}", min_value=1, value=1, key=rep)
                    stock_actual = int(item["Stock Inicial"])
                    if cantidad > stock_actual:
                        st.error(f"Stock insuficiente para {rep}. Stock disponible: {stock_actual}")
                        st.stop()
                    precio_unit = float(str(item["precio"]).replace("S/", "").replace(",", "."))
                    total = cantidad * precio_unit
                    total_repuestos += total
                    detalles_repuestos.append((rep, cantidad, precio_unit, total))

                total_igv = round((subtotal_mo + total_repuestos + subtotal_lub) * 0.18, 2)
                total_final = round(subtotal_mo + total_repuestos + subtotal_lub + total_igv, 2)
                enviar = st.form_submit_button("Finalizar")

            if enviar:
                idx = data[data["Placa"] == selected].index[0] + 2
                sheet.update_cell(idx, data.columns.get_loc("Supervisor") + 1, username)
                sheet.update_cell(idx, data.columns.get_loc("Comentarios_Supervisor") + 1, comentario)
                sheet.update_cell(idx, data.columns.get_loc("Estado") + 1, "Aprobado" if aprobado else "Rechazado")
                sheet.update_cell(idx, data.columns.get_loc("Lubricante_Precio_Total") + 1, subtotal_lub)
                sheet.update_cell(idx, data.columns.get_loc("Repuesto_Precio_Total") + 1, total_repuestos)
                sheet.update_cell(idx, data.columns.get_loc("Subtotal") + 1, subtotal_mo + total_repuestos + subtotal_lub)
                sheet.update_cell(idx, data.columns.get_loc("Total_IGV") + 1, total_igv)
                sheet.update_cell(idx, data.columns.get_loc("Total") + 1, total_final)

                for rep, cantidad, _, _ in detalles_repuestos:
                    row_idx = data_inv[data_inv["Producto"] == rep].index[0] + 2
                    stock_actual = int(data_inv.loc[data_inv["Producto"] == rep, "Stock Inicial"].values[0])
                    nuevo_stock = stock_actual - cantidad
                    sheet_inventario.update_cell(row_idx, data_inv.columns.get_loc("Stock Inicial") + 1, nuevo_stock)

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Resumen Final del Servicio", ln=True, align="C")
                pdf.ln(10)
                for k, v in ticket.items():
                    pdf.cell(100, 10, txt=f"{k}: {v}", ln=True)
                pdf.ln(5)
                pdf.cell(100, 10, txt=f"Subtotal MO: S/ {subtotal_mo:.2f}", ln=True)
                pdf.cell(100, 10, txt=f"Subtotal Lubricantes: S/ {subtotal_lub:.2f}", ln=True)
                pdf.cell(100, 10, txt=f"Subtotal Repuestos: S/ {total_repuestos:.2f}", ln=True)
                pdf.cell(100, 10, txt=f"IGV: S/ {total_igv:.2f}", ln=True)
                pdf.cell(100, 10, txt=f"TOTAL: S/ {total_final:.2f}", ln=True)
                pdf_buffer = BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)

                st.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_buffer,
                    file_name=f"Ticket_{ticket['Ticket_ID']}.pdf",
                    mime="application/pdf"
                )
                st.success("✅ Ticket cerrado, inventario actualizado y PDF generado.")
                st.experimental_rerun()

else:
    st.warning("Por favor, inicia sesión para acceder a la app.")
