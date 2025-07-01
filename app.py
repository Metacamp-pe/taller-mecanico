import streamlit as st
st.title("🚀 App de Prueba")
st.write("Si ves esto, Streamlit funciona correctamente.")

"""import streamlit_authenticator as stauth
from yaml import safe_load
from pathlib import Path
import pandas as pd
st.title("¡Hola Luis!")
st.write("Tu app de taller está corriendo correctamente 🚗")
# Configurar login con usuarios y roles
config = {
    'credentials': {
        'usernames': {
            'recepcion': {
                'name': 'Recepción',
                'password': stauth.Hasher(['1234']).generate()[0]
            },
            'mecanico': {
                'name': 'Mecánico',
                'password': stauth.Hasher(['1234']).generate()[0]
            },
            'supervisor': {
                'name': 'Supervisor',
                'password': stauth.Hasher(['1234']).generate()[0]
            },
        }
    },
    'cookie': {
        'name': 'taller_cookie',
        'key': 'clave_secreta',
        'expiry_days': 1
    },
    'preauthorized': {
        'emails': []
    }
}

# Crear autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login
name, authentication_status, username = authenticator.login('Iniciar sesión', 'main')

if authentication_status:
    authenticator.logout('Cerrar sesión', 'sidebar')
    st.sidebar.write(f"👤 Usuario: {name}")

    # Mostrar contenido según el usuario
    if username == 'recepcion':
        st.title("🚗 Registro de Vehículos - Recepción")
        st.write("Aquí se registran los vehículos que llegan al taller.")

    elif username == 'mecanico':
        st.title("🔧 Diagnóstico del Mecánico")
        st.write("Registra el diagnóstico y los repuestos necesarios.")

    elif username == 'supervisor':
        st.title("✅ Aprobación del Supervisor")
        st.write("Revisa los diagnósticos y da el visto bueno final.")

elif authentication_status is False:
    st.error('Usuario o contraseña incorrectos')
elif authentication_status is None:
    st.warning('Por favor, ingresa tus credenciales')
"""