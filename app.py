import streamlit as st
import pandas as pd

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

    st.subheader("⚙️ Define global rules (aplican a todos los samples)")

    # --- Match rules ---
    st.write("🔎 Match rules (para decidir coincidencias)")
    match_rules = st.data_editor(
        pd.DataFrame([{"DD Column (Match)": None, "Sample Column (Match)": None}]),
        column_config={
            "DD Column (Match)": st.column_config.SelectboxColumn("DD Column (Match)", options=list(dd.columns)),
            "Sample Column (Match)": st.column_config.SelectboxColumn(
                "Sample Column (Match)",
                options=list(set(phone.columns) | set(online.columns) | set(email.columns))
            ),
        },
        num_rows="dynamic",
        key="match_rules"
    )

    # --- Replace rules ---
    st.write("✏️ Replace rules (para sobrescribir valores)")
    replace_rules = st.data_editor(
        pd.DataFrame([{"DD Column (Replace)": None, "Sample Column (Replace)": None, "Exclusion Column": None, "Exclusion Value": None}]),
        column_config={
            "DD Column (Replace)": st.column_config.SelectboxColumn("DD Column (Replace)", options=list(dd.columns)),
            "Sample Column (Replace)": st.column_config.SelectboxColumn(
                "Sample Column (Replace)",
                options=list(set(phone.columns) | set(online.columns) | set(email.columns))
            ),
            "Exclusion Column": st.column_config.SelectboxColumn("Exclusion Column", options=list(dd.columns)),
            "Exclusion Value": st.column_config.TextColumn("Exclusion Value"),
        },
        num_rows="dynamic",
        key="replace_rules"
    )

    final_rows = []

    # Función para asignar sample según mode
    def assign_sample_row(dd_row):
        mode = dd_row.get("mode")
        if mode == 1 and "phonetypef" in phone.columns:
            return phone[phone["phonetypef"] == 1]
        elif mode == 2 and "phonetypef" in phone.columns:
            return phone[phone["phonetypef"] == 2]
        elif mode == 3:
            return online
        elif mode == 4:
            return email
        else:
            return pd.DataFrame()

    # Función para aplicar reglas
    def apply_rules(row, sample, match_rules, replace_rules):
        row_dict = row.to_dict()

        # --- Match ---
        if not sample.empty and not match_rules.empty:
            conditions = pd.Series(True, index=sample.index)
            for _, rule in match_rules.iterrows():
                d_col = rule["DD Column (Match)"]
                s_col = rule["Sample Column (Match)"]
                if pd.notna(d_col) and pd.notna(s_col) and s_col in sample.columns:
                    conditions &= (sample[s_col] == row[d_col])
            matches = sample.loc[conditions]
            if matches.empty:
                return row_dict  # no match → fila sin sample adjunto
            match = matches.iloc[0].to_dict()
        else:
            if sample.empty:
                return row_dict
            match = sample.sample(1).iloc[0].to_dict()

        # --- Reemplazo ---
        for _, rule in replace_rules.iterrows():
            d_col = rule["DD Column (Replace)"]
            s_col = rule["Sample Column (Replace)"]
            excl_col = rule["Exclusion Column"]
            excl_val = rule["Exclusion Value"]

            if pd.notna(d_col) and pd.notna(s_col) and s_col in match:
                # aplicar exclusión sobre el DDfile
                if pd.notna(excl_col) and pd.notna(excl_val):
                    if row.get(excl_col) == excl_val:
                        # 🚫 No reemplazar, dejar el valor original del DD
                        continue
                # ✅ Reemplazar si no hay exclusión
                row_dict[d_col] = match.get(s_col, row_dict[d_col])

        # Adjuntar TODAS las columnas del sample sin modificarlas
        for col in sample.columns:
            row_dict[col] = match.get(col, None)

        return row_dict

    # Procesamiento
    for _, row in dd.iterrows():
        sample = assign_sample_row(row)
        if sample.empty:
            final_rows.append(row.to_dict())
            continue

        row_dict = apply_rules(row, sample, match_rules, replace_rules)
        final_rows.append(row_dict)

    if final_rows:
        final_table = pd.DataFrame(final_rows)
        st.write("✅ Processed results:")
        st.dataframe(final_table)

        # Descargar CSV
        csv = final_table.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "final_table.csv", "text/csv")
    else:
        st.warning("⚠️ No rows were generated. Check your rules or mode.")
