import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO
import streamlit as st

def telecharger_recapitulatif(historique, nom_fichier="recap_emails_envoyes.xlsx"):
    if not historique:
        return

    df_export = pd.DataFrame(historique)

    # Forcer la présence des colonnes requises
    if "Date" not in df_export.columns:
        df_export["Date"] = ""
    if "Broker" not in df_export.columns:
        df_export["Broker"] = ""
    if "Instrument" not in df_export.columns:
        df_export["Instrument"] = ""
    if "Adresse Email" in df_export.columns:
        df_export["Email"] = df_export["Adresse Email"]
    elif "Destinataires" in df_export.columns:
        df_export["Email"] = df_export["Destinataires"]
    else:
        df_export["Email"] = ""
    if "Statut" not in df_export.columns:
        df_export["Statut"] = ""

    # Réordonner les colonnes
    df_export = df_export[["Date", "Broker", "Instrument", "Email", "Statut"]]

    # Création du fichier Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Suivi des envois"

    for r_idx, row in enumerate(dataframe_to_rows(df_export, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(wrap_text=True)

    for column_cells in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = max_len + 4

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    st.download_button(
        label="⬇️ Télécharger le récapitulatif des envois",
        data=buffer.getvalue(),
        file_name=nom_fichier,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )