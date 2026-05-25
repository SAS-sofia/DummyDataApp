import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Survey Results & Sample Matcher 📊")

# Solo mostrar si los archivos existen
if dd_file is not None:
    dd = pd.read_csv(dd_file)
    st.write("📂 DDfile preview:")
    st.write(dd.head())

if phone_file is not None:
    phone = pd.read_csv(phone_file)
    st.write("📂 Phone Sample preview:")
    st.write(phone.head())

if online_file is not None:
    online = pd.read_csv(online_file)
    st.write("📂 Online Sample preview:")
    st.write(online.head())



# Selector de modo
mode = st.radio("Choose processing mode:", ["Match", "Direct Replacement"])

if dd_file and phone_file and online_file:
    dd = pd.read_csv(dd_file)
    phone = pd.read_csv(phone_file)
    online = pd.read_csv(online_file)

    st.subheader("Column configuration")

    # Mostrar columnas disponibles
    dd_cols = dd.columns.tolist()
    phone_cols = phone.columns.tolist()
    online_cols = online.columns.tolist()

    # El usuario elige columnas para match
    dd_match_cols = st.multiselect("DDfile columns to compare", dd_cols)
    phone_match_cols = st.multiselect("Phone Sample columns to compare", phone_cols)
    online_match_cols = st.multiselect("Online Sample columns to compare", online_cols)

    # Columnas de reemplazo
    dd_gender_col = st.selectbox("Gender column in DDfile", dd_cols)
    dd_age_col = st.selectbox("Age column in DDfile", dd_cols)
    sample_gender_col = st.selectbox("Gender column in Sample", phone_cols + online_cols)
    sample_birthyear_col = st.selectbox("BirthYear column in Sample", phone_cols + online_cols)

    final_rows = []

    for _, row in dd.iterrows():
        if row.get("pMode") == 1:  # Phone Sample
            sample = phone
            match_cols = phone_match_cols
        elif row.get("pMode") == 3:  # Online Sample
            sample = online
            match_cols = online_match_cols
        else:
            sample = pd.DataFrame()
            match_cols = []

        if not sample.empty:
            if mode == "Match" and dd_match_cols and match_cols:
                # Construir condición dinámica
                conditions = True
                for d_col, s_col in zip(dd_match_cols, match_cols):
                    conditions &= (sample[s_col] == row[d_col])
                matches = sample[conditions]
                if not matches.empty:
                    match = matches.iloc[0].to_dict()
                    row_dict = row.to_dict()
                    row_dict[dd_gender_col] = match.get(sample_gender_col, row_dict[dd_gender_col])
                    if sample_birthyear_col in match:
                        row_dict[dd_age_col] = datetime.now().year - int(match[sample_birthyear_col])
                    final_rows.append(row_dict)
            elif mode == "Direct Replacement":
                match = sample.iloc[0].to_dict()
                row_dict = row.to_dict()
                row_dict[dd_gender_col] = match.get(sample_gender_col, row_dict[dd_gender_col])
                if sample_birthyear_col in match:
                    row_dict[dd_age_col] = datetime.now().year - int(match[sample_birthyear_col])
                final_rows.append(row_dict)

    final_table = pd.DataFrame(final_rows)
    st.write("✅ Processed results:")
    st.dataframe(final_table)

    # Descargar CSV
    csv = final_table.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "final_table.csv", "text/csv")
