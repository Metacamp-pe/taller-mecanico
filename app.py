import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd

st.set_page_config(page_title="App de Taller", page_icon="🛠")

st.title("🚗 App de Taller Vehicular")

# --- CONFIGURAR USUARIOS Y ROLES ---
usernames = ["recepcion", "mecanico", "supervisor"]
names = ["Recepción", "Mecánico", "Supervisor"]
passwords = ["1234", "1234", "1234"]  # Puedes cambiar luego

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": hashed_passwords[0]},
        usernames[1]: {"name": names[1], "password": hashed_passwords[1]},
        usernames[2]: {"name": names[2], "password": hashed_passwords[2]},
    }
}

cookie = {"name": "taller_cookie", "key": "clave_secreta", "expiry_days": 1}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name=cookie["name"],
    key=cookie["key"],
    expiry_days=cookie["expiry_days"]
)

name, auth_status, username = authenticator.login("Iniciar sesión", "main")

if auth_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"👤 Usuario: {name}")
    st.success("Tu app está funcionando correctamente. 🎉")
elif auth_status is False:
    st.error("Usuario o contraseña incorrectos")
elif auth_status is None:
    st.warning("Por favor inicia sesión")

