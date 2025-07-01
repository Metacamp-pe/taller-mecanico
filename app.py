import streamlit as st
import streamlit_authenticator as stauth
from pathlib import Path
import yaml
import pandas as pd

# --- CONFIGURAR USUARIOS Y ROLES ---
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
            }
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

# --- AUTENTICADOR ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- LOGIN ---
name, authentication_status, username = authenticator.login('Iniciar sesión', 'main')

if authentication_status:
    authenticator.logout('Cerrar sesión', 'sidebar')
    st.sidebar.write(f"👤 Usuario: {name}")

    st.title("🔧 Sistema de Gestión - Taller Mecánico")

    # --- FLUJO SEGÚN ROL ---
    if username == 'recepcion':
        st.subheader("📋 Registro de Ingreso de Vehículos")
        with st.form("form_ingreso"):
            nombre_cliente = st.text_input("Nombre del cliente")
            placa = st.text_input("Placa del vehículo")
            descripcion = st.text_area("Descripción del problema")
            enviado = st.form_submit_button("Registrar ingreso")
            if enviado:
                st.success(f"Vehículo con placa {placa} registrado correctamente.")

    elif username == 'mecanico':
        st.subheader("🔧 Diagnóstico Mecánico")
        with st.form("form_diagnostico"):
            placa = st.text_input("Placa del vehículo")
            diagnostico = st.text_area("Diagnóstico realizado")
            enviado = st.form_submit_button("Guardar diagnóstico")
            if enviado:
                st.success(f"Diagnóstico para {placa} guardado correctamente.")

    elif username == 'supervisor':
        st.subheader("✅ Revisión Final y Aprobación")
        with st.form("form_supervisor"):
            placa = st.text_input("Placa del vehículo")
            visto_bueno = st.radio("¿Aprobar entrega?", ("Sí", "No"))
            enviado = st.form_submit_button("Registrar decisión")
            if enviado:
                st.success(f"Decisión registrada para el vehículo {placa}.")
else:
    st.warning("Por favor, ingresa tus credenciales correctamente.")

