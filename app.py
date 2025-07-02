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
    st.success(f"Has iniciado sesión como: {st.session_state.rol.capitalize()}")

    # --- Conexión a Google Sheets ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_info = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
    client = gspread.authorize(credentials)

    # Base principal
    sheet = client.open_by_key("1279gxeATNQw5omA6RwYH8pIS-uFu8Yagy0t4frQA0uE").sheet1
    data = pd.DataFrame(sheet.get_all_records())

    # Inventario
    sheet_inventario = client.open_by_key("1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps").worksheet("inventario_prueba")
    data_inv = pd.DataFrame(sheet_inventario.get_all_records())
    lubricantes_predef = ["ACEITE DE MOTOR SAE 15W40 (LT)", "REFRIGERANTE", "LÍQUIDO DE FRENOS"]

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
                sheet.update_cell(idx, data.columns.get_loc("Mecánico") + 1, "mecanico")
                st.success("✅ Diagnóstico guardado correctamente.")
                st.experimental_rerun()

    # --- SUPERVISOR (en construcción) ---
    elif st.session_state.rol == "supervisor":
        st.header("Aprobación y Generación de PDF")
        st.info("🚧 Módulo del supervisor en desarrollo...")

else:
    st.info("Por favor, inicia sesión para usar la aplicación.")
