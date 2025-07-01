import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
import datetime

# --- CONFIGURACIÓN DE USUARIOS ---
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

cookie = {"name": "taller_cookie", "key": "clave_secreta", "expiry_days": 1}
authenticator = stauth.Authenticate(credentials, cookie['name'], cookie['key'], cookie['expiry_days'])

# --- LOGIN ---
name, authentication_status, username = authenticator.login("Iniciar sesión", "main")

# --- CONEXIÓN A GOOGLE SHEETS ---
def connect_to_gsheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

# --- INTERFAZ DESPUÉS DEL LOGIN ---
if authentication_status == False:
    st.error("Usuario o contraseña incorrectos")
elif authentication_status == None:
    st.warning("Por favor, ingresa tus credenciales")
elif authentication_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {name} 👋")

    st.title("🚗 App de Taller Vehicular")
    sheet = connect_to_gsheet("Registro de taller - Mecanico")  # Nombre exacto de tu Sheet

    if username == "recepcion":
        st.subheader("📋 Registro de Recepción")
        with st.form("form_recepcion"):
            ruc = st.text_input("RUC/DNI")
            cliente = st.text_input("Cliente")
            direccion = st.text_input("Dirección")
            correo = st.text_input("Correo")
            telefono = st.text_input("Teléfono")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            placa = st.text_input("Placa")
            fecha = st.date_input("Fecha de ingreso")
            km = st.text_input("Kilometraje")
            contacto = st.selectbox("¿Autoriza contacto?", ["Sí", "No"])
            submit_recepcion = st.form_submit_button("Guardar Recepción")

        if submit_recepcion:
            fila = [str(datetime.datetime.now()), ruc, cliente, direccion, correo, telefono, marca, modelo, placa, fecha.strftime("%Y-%m-%d"), km, contacto, "", ""]
            sheet.append_row(fila)
            st.success("✅ Registro guardado exitosamente")

    elif username == "mecanico":
        st.subheader("🔧 Diagnóstico del Mecánico")
        with st.form("form_mecanico"):
            placa = st.text_input("Placa del vehículo")
            diagnostico = st.text_area("Diagnóstico del vehículo")
            submit_diag = st.form_submit_button("Guardar Diagnóstico")

        if submit_diag:
            fila = [str(datetime.datetime.now()), "", "", "", "", "", "", "", placa, "", "", "", diagnostico, ""]
            sheet.append_row(fila)
            st.success("✅ Diagnóstico guardado")

    elif username == "supervisor":
        st.subheader("✅ Revisión del Supervisor")
        with st.form("form_supervisor"):
            placa = st.text_input("Placa del vehículo")
            visto_bueno = st.radio("¿Aprobado?", ["Sí", "No"])
            submit_sup = st.form_submit_button("Guardar Revisión")

        if submit_sup:
            fila = [str(datetime.datetime.now()), "", "", "", "", "", "", "", placa, "", "", "", "", visto_bueno]
            sheet.append_row(fila)
            st.success("✅ Revisión registrada")
