import streamlit as st
import pandas as pd
import json
from fpdf import FPDF
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

# Configurar la página
st.set_page_config(page_title="App de Taller Vehicular", layout="wide")

# --- USUARIOS y LOGIN MANUAL ---
usuarios = {
    "recepcion": "1234",
    "mecanico": "1234",
    "supervisor": "1234"
}

if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "rol" not in st.session_state:
    st.session_state.rol = ""

if not st.session_state.auth_status:
    st.title("🔐 Iniciar sesión")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario in usuarios and clave == usuarios[usuario]:
            st.session_state.auth_status = True
            st.session_state.rol = usuario
            st.success("Inicio de sesión exitoso 🎉")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# --- CONTENIDO DE LA APP (una vez autenticado) ---
st.sidebar.success(f"Bienvenido, {st.session_state.rol} 👋")
st.title("🚗 App de Taller Vehicular")

# Conectar con Google Sheets (base de tickets)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key("1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps").sheet1
data = pd.DataFrame(sheet.get_all_records())

# Conectar con hoja de inventario
sheet_inventario = client.open_by_key("1-8VG4ICQ-RtN43Xn4PNtDq8fQsCmffUjFXrXkUzfbps").worksheet("inventario_prueba")
data_inv = pd.DataFrame(sheet_inventario.get_all_records())

# Lista predefinida de lubricantes
lubricantes_predef = [
    "ACEITE DE MOTOR SAE 15W40 (LT)",
    "REFRIGERANTE",
    "LÍQUIDO DE FRENOS"
]

# --- FORMULARIO SUPERVISOR ---
if st.session_state.rol == "supervisor":
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

            # Selección de lubricantes
            st.subheader("Lubricantes/Fluidos")
            lubricantes_sel = st.multiselect("Selecciona lubricantes", lubricantes_predef)
            subtotal_lub = 0
            for lub in lubricantes_sel:
                cant = st.number_input(f"Cantidad de {lub}", min_value=1, value=1, key=f"lub_{lub}")
                precio = st.number_input(f"Precio unitario de {lub}", min_value=0.0, value=0.0, key=f"prec_{lub}")
                subtotal_lub += cant * precio

            # Repuestos
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
            sheet.update_cell(idx, data.columns.get_loc("Supervisor") + 1, st.session_state.rol)
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

    with st.expander("📋 Historial de aprobaciones"):
        st.dataframe(data[data["Estado"] != ""])

