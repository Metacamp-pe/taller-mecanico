import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- AUTENTICACIÓN ---
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

if authentication_status == False:
    st.error("Usuario o contraseña incorrectos")
elif authentication_status == None:
    st.warning("Por favor, ingresa tus credenciales")
elif authentication_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {name} 👋")

    st.title("🚗 App de Taller Vehicular")
    st.write("Esta es la página principal del sistema de taller.")
    st.info("Puedes personalizar este contenido según el rol del usuario.")

    # --- CONEXIÓN A GOOGLE SHEETS ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # ID de la hoja de cálculo (desde st.secrets)
    sheet_id = st.secrets["GOOGLE_SHEET_ID"]
    sheet = client.open_by_key(sheet_id).worksheet("Registros")

    # --- EJEMPLO DE GUARDADO ---
    if username == "recepcion":
        st.subheader("📋 Formulario Recepción")

        with st.form("form_recepcion"):
            ruc_dni = st.text_input("RUC/DNI")
            cliente = st.text_input("Cliente")
            telefono = st.text_input("Teléfono")
            direccion = st.text_input("Dirección")
            correo = st.text_input("Correo")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            placa = st.text_input("Placa")
            fecha = st.date_input("Fecha")
            km = st.number_input("Kilometraje", step=1)

            submitted = st.form_submit_button("Guardar")

            if submitted:
                row = [ruc_dni, cliente, telefono, direccion, correo, marca, modelo, placa, str(fecha), km]
                sheet.append_row(row)
                st.success("✅ Registro guardado exitosamente")

