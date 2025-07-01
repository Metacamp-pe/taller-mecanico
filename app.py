import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
import tempfile
import os
from datetime import datetime

# --- CONFIGURAR USUARIOS Y CONTRASEÑAS ---
names = ["Recepción", "Mecánico", "Supervisor"]
usernames = ["recepcion", "mecanico", "supervisor"]
passwords = ["1234", "1234", "1234"]

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[i]: {
            "name": names[i],
            "password": hashed_passwords[i]
        } for i in range(len(usernames))
    }
}

cookie = {
    "name": "taller_cookie",
    "key": "clave_secreta",
    "expiry_days": 1
}

authenticator = stauth.Authenticate(
    credentials, cookie['name'], cookie['key'], cookie['expiry_days']
)

# --- CONEXIONES ---
def connect_to_sheet(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)

# --- DATOS ---
TICKETS_SHEET_ID = "1279gxeATNQw5omA6RwYH8pIS-uFu8Yagy0t4frQA0uE"
INVENTARIO_SHEET_ID = "1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps"

# --- LOGIN ---
name, auth_status, username = authenticator.login("Iniciar sesión", "main")

if auth_status == False:
    st.error("Usuario o contraseña incorrectos")
elif auth_status == None:
    st.warning("Por favor, ingresa tus credenciales")
elif auth_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {name} \U0001F44B")
    st.title("🚗 App de Taller Vehicular")

    sheet = connect_to_sheet(TICKETS_SHEET_ID).sheet1
    inventory_sheet = connect_to_sheet(INVENTARIO_SHEET_ID).sheet1

    # Cargar inventario en DataFrame
    inventario = pd.DataFrame(inventory_sheet.get_all_records())

    if username == "recepcion":
        st.subheader("Recepción del vehículo")
        with st.form("form_recepcion"):
            cliente = st.text_input("Cliente")
            dni = st.text_input("RUC/DNI")
            direccion = st.text_input("Dirección")
            correo = st.text_input("Correo")
            telefono = st.text_input("Teléfono")
            contactar = st.text_input("Contactar a")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            placa = st.text_input("Placa")
            color = st.text_input("Color")
            fecha = st.date_input("Fecha de ingreso")
            km = st.text_input("Kilometraje")
            motivo = st.text_area("Motivo del ingreso")
            submit = st.form_submit_button("Guardar")
            if submit:
                nuevo = [cliente, dni, direccion, correo, telefono, contactar, marca, modelo,
                         placa, color, str(fecha), km, motivo, "", "", "", ""]
                sheet.append_row(nuevo)
                st.success("✅ Registro guardado")

    elif username == "mecanico":
        st.subheader("Diagnóstico y Repuestos")
        data = pd.DataFrame(sheet.get_all_records())
        placas = data[data["Diagnóstico"] == ""]["Placa"].tolist()
        if placas:
            selected = st.selectbox("Selecciona placa", placas)
            with st.form("form_mecanico"):
                diagnostico = st.text_area("Diagnóstico")
                repuestos_usados = st.multiselect("Repuestos utilizados", inventario["Producto"].unique())
                cantidades = {}
                for rep in repuestos_usados:
                    cantidades[rep] = st.number_input(f"Cantidad de {rep}", min_value=1, value=1)
                submit = st.form_submit_button("Guardar")
                if submit:
                    idx = data[data["Placa"] == selected].index[0] + 2
                    sheet.update_cell(idx, 14, diagnostico)
                    usados = ", ".join([f"{rep} ({cantidades[rep]})" for rep in repuestos_usados])
                    sheet.update_cell(idx, 15, usados)
                    for rep in repuestos_usados:
                        row = inventario[inventario["Producto"] == rep].index[0] + 2
                        col_stock = inventario.columns.get_loc("Stock Inicial") + 1
                        nuevo_stock = int(inventario.loc[row-2, "Stock Inicial"]) - cantidades[rep]
                        inventory_sheet.update_cell(row, col_stock, nuevo_stock)
                    st.success("✅ Diagnóstico y repuestos guardados")
        else:
            st.info("No hay vehículos pendientes por diagnosticar")

    elif username == "supervisor":
        st.subheader("Aprobación Final y PDF")
        data = pd.DataFrame(sheet.get_all_records())
        placas = sorted(data[(data["Diagnóstico"] != "") & (data["Estado"] == "")]["Placa"].unique().tolist())
        if placas:
            selected = st.selectbox("Selecciona placa para aprobar", placas)
            registro = data[data["Placa"] == selected].iloc[0]
            with st.form("form_supervisor"):
                aprobacion = st.radio("¿Todo conforme?", ["Sí", "No"])
                observaciones = st.text_area("Observaciones")
                generar = st.form_submit_button("Finalizar y generar PDF")
                if generar:
                    idx = data[data["Placa"] == selected].index[0] + 2
                    sheet.update_cell(idx, 16, aprobacion)
                    sheet.update_cell(idx, 17, observaciones)

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    for campo in registro.index:
                        pdf.cell(200, 10, txt=f"{campo}: {registro[campo]}", ln=True)
                    pdf.cell(200, 10, txt=f"Aprobación: {aprobacion}", ln=True)
                    pdf.cell(200, 10, txt=f"Observaciones: {observaciones}", ln=True)

                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("🔖 Descargar PDF", f, file_name=f"Ticket_{selected}.pdf")
                    os.unlink(tmp.name)
        else:
            st.info("No hay vehículos pendientes de aprobación")
