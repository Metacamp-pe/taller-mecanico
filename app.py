import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from pathlib import Path

# --- CONFIGURAR USUARIOS Y CONTRASEÑAS ---
names = ["Recepción", "Mecánico", "Supervisor"]
usernames = ["recepcion", "mecanico", "supervisor"]
passwords = ["1234", "1234", "1234"]  # Puedes cambiarlas

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

# --- LOGIN ---
name, authentication_status, username = authenticator.login("Iniciar sesión", "main")

if authentication_status == False:
    st.error("Usuario o contraseña incorrectos")
elif authentication_status == None:
    st.warning("Por favor, ingresa tus credenciales")
elif authentication_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {name} 👋")

    # --- CONTENIDO PRINCIPAL DE LA APP ---
    st.title("🚗 App de Taller Vehicular")
    st.write("Esta es la página principal del sistema de taller.")
    st.info("Puedes personalizar este contenido según el rol del usuario.")

