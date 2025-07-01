import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_gsheet(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

st.title("🔧 Prueba de conexión a Google Sheets")

SHEET_ID = "1279gxeATNQw5omA6RwYH8pIS-uFu8Yagy0t4frQA0uE"

try:
    sheet = connect_to_gsheet(SHEET_ID)
    data = sheet.get_all_values()
    st.success("✅ Conexión exitosa")
    st.write(data[:5])
except Exception as e:
    st.error(f"❌ Error al conectar: {e}")
