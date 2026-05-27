import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Survey Results & Sample Matcher 📊")

# Subir archivos
dd_file = st.file_uploader("Upload DDfile (CSV)", type="csv")
phone_file = st.file_uploader("Upload Phone Sample (CSV)", type="csv")
online_file = st.file_uploader("Upload Online Sample (CSV)", type="csv")
email_file = st.file_uploader("Upload Email Sample (CSV)", type="csv")

if dd_file:
    dd = pd.read_csv(dd_file)
    phone = pd.read_csv(phone_file) if phone_file else pd.DataFrame()
    online = pd.read_csv(online_file) if online_file else pd.DataFrame()
    email = pd.read_csv(email_file) if email_file else pd.DataFrame()

    st.subheader("Column configuration")

    # Selección de columnas para Match
    dd_match_cols = st.multiselect("DDfile columns to match", dd.columns)
    sample_match_cols = st.multiselect("Sample columns to match", 
                                       list(phone.columns) + list(online.columns) + list(email.columns))

    # Selección de columnas para Reemplazo
    dd_replace_cols = st.multiselect("DDfile columns to replace", dd.columns)
    sample_replace_cols = st.multiselect("Sample columns to use for replacement", 
                                         list(phone.columns) + list(online.columns) + list(email.columns))

    final_rows = []

    # Función para asignar sample según mode
    def assign_sample_row(dd_row):
        mode = dd_row.get("mode")
        if mode == 1:
            return phone[phone["pPhonetype"] == 1]
        elif mode == 2:
            return phone[phone["pPhonetype"] == 2]
        elif mode == 3:
            return online
        elif mode == 4:
            return email
        else:
            return pd.DataFrame()

    # Procesamiento
    for _, row in dd.iterrows():
        sample = assign_sample_row(row)
        if sample.empty:
            continue

        row_dict = row.to_dict()

        # --- Fase 1: Match ---
        if dd_match_cols and sample_match_cols:
            conditions = True
            for d_col, s_col in zip(dd_match_cols, sample_match_cols):
                conditions &= (sample[s_col] == row[d_col])
            matches = sample[conditions]
            if not matches.empty:
                match = matches.iloc[0].to_dict()
                for d_col, s_col in zip(dd_replace_cols, sample_replace_cols):
                    row_dict[d_col] = match.get(s_col, row_dict[d_col])
                final_rows.append(row_dict)
                continue

        # --- Fase 2: Reemplazo directo ---
        match = sample.sample(1).iloc[0].to_dict()
        for d_col, s_col in zip(dd_replace_cols, sample_replace_cols):
            row_dict[d_col] = match.get(s_col, row_dict[d_col])
        final_rows.append(row_dict)

    if final_rows:
        final_table = pd.DataFrame(final_rows)
        st.write("✅ Processed results:")
        st.dataframe(final_table)

        # Descargar CSV
        csv = final_table.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "final_table.csv", "text/csv")
    else:
        st.warning("⚠️ No rows were generated. Check your column selections or mode.")
