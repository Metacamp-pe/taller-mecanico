import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAR USUARIOS Y CONTRASEÑAS ---
names = ["Recepción", "Mecánico", "Supervisor"]
usernames = ["recepcion", "mecanico", "supervisor"]
passwords = ["1234", "1234", "1234"]  # Reemplaza con contraseñas seguras

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

# --- FUNCIÓN PARA CONECTAR A GOOGLE SHEETS ---
def connect_to_gsheet(sheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

# --- LOGIN ---
name, authentication_status, username = authenticator.login("Iniciar sesión", "main")

if authentication_status == False:
    st.error("Usuario o contraseña incorrectos")

elif authentication_status == None:
    st.warning("Por favor, ingresa tus credenciales")

elif authentication_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {name} 👋")

    st.title("🚗 App de Taller Vehicular")

    sheet = connect_to_gsheet("formato_registro_taller") # Nombre de tu Google Sheet

    # --- FORMULARIO DIFERENCIADO POR ROL ---
    if username == "recepcion":
        st.subheader("Recepción del vehículo")
        with st.form("recepcion_form"):
            cliente = st.text_input("Nombre del cliente")
            placa = st.text_input("Placa del vehículo")
            fecha_ingreso = st.date_input("Fecha de ingreso")
            motivo = st.text_area("Motivo del ingreso")
            enviado = st.form_submit_button("Guardar")
            if enviado:
                datos = [cliente, placa, str(fecha_ingreso), motivo, "Recepción"]
                sheet.append_row(datos)
                st.success("✅ Registro guardado en Google Sheets")

    elif username == "mecanico":
        st.subheader("Diagnóstico del vehículo")
        with st.form("diagnostico_form"):
            placa = st.text_input("Placa del vehículo")
            diagnostico = st.text_area("Diagnóstico técnico")
            repuestos = st.text_area("Repuestos necesarios")
            enviado = st.form_submit_button("Guardar")
            if enviado:
                datos = ["", placa, "", "", "Mecánico", diagnostico, repuestos]
                sheet.append_row(datos)
                st.success("✅ Diagnóstico guardado")

    elif username == "supervisor":
        st.subheader("Aprobación final")
        with st.form("supervisor_form"):
            placa = st.text_input("Placa del vehículo")
            visto_bueno = st.radio("¿Todo conforme?", ["Sí", "No"])
            observaciones = st.text_area("Observaciones finales")
            enviado = st.form_submit_button("Guardar")
            if enviado:
                datos = ["", placa, "", "", "Supervisor", visto_bueno, observaciones]
                sheet.append_row(datos)
                st.success("✅ Supervisión guardada")

