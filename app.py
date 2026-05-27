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

    st.subheader("⚙️ Define rules per sample")

    # --- Phone rules ---
    st.markdown("### 📞 Phone Sample")
    phone_match_rules = st.data_editor(
        pd.DataFrame([{"DD Column": None, "Sample Column": None}]),
        column_config={
            "DD Column": st.column_config.SelectboxColumn("DD Column", options=list(dd.columns)),
            "Sample Column": st.column_config.SelectboxColumn("Sample Column", options=list(phone.columns)),
        },
        num_rows="dynamic",
        key="phone_match"
    )
    phone_replace_rules = st.data_editor(
        pd.DataFrame([{"DD Column": None, "Sample Column": None, "Exclusion Column": None, "Exclusion Value": None}]),
        column_config={
            "DD Column": st.column_config.SelectboxColumn("DD Column", options=list(dd.columns)),
            "Sample Column": st.column_config.SelectboxColumn("Sample Column", options=list(phone.columns)),
            "Exclusion Column": st.column_config.SelectboxColumn("Exclusion Column", options=list(phone.columns)),
            "Exclusion Value": st.column_config.TextColumn("Exclusion Value"),
        },
        num_rows="dynamic",
        key="phone_replace"
    )

    # --- Online rules ---
    st.markdown("### 💻 Online Sample")
    online_match_rules = st.data_editor(
        pd.DataFrame([{"DD Column": None, "Sample Column": None}]),
        column_config={
            "DD Column": st.column_config.SelectboxColumn("DD Column", options=list(dd.columns)),
            "Sample Column": st.column_config.SelectboxColumn("Sample Column", options=list(online.columns)),
        },
        num_rows="dynamic",
        key="online_match"
    )
    online_replace_rules = st.data_editor(
        pd.DataFrame([{"DD Column": None, "Sample Column": None, "Exclusion Column": None, "Exclusion Value": None}]),
        column_config={
            "DD Column": st.column_config.SelectboxColumn("DD Column", options=list(dd.columns)),
            "Sample Column": st.column_config.SelectboxColumn("Sample Column", options=list(online.columns)),
            "Exclusion Column": st.column_config.SelectboxColumn("Exclusion Column", options=list(online.columns)),
            "Exclusion Value": st.column_config.TextColumn("Exclusion Value"),
        },
        num_rows="dynamic",
        key="online_replace"
    )

    # --- Email rules ---
    st.markdown("### 📧 Email Sample")
    email_match_rules = st.data_editor(
        pd.DataFrame([{"DD Column": None, "Sample Column": None}]),
        column_config={
            "DD Column": st.column_config.SelectboxColumn("DD Column", options=list(dd.columns)),
            "Sample Column": st.column_config.SelectboxColumn("Sample Column", options=list(email.columns)),
        },
        num_rows="dynamic",
        key="email_match"
    )
    email_replace_rules = st.data_editor(
        pd.DataFrame([{"DD Column": None, "Sample Column": None, "Exclusion Column": None, "Exclusion Value": None}]),
        column_config={
            "DD Column": st.column_config.SelectboxColumn("DD Column", options=list(dd.columns)),
            "Sample Column": st.column_config.SelectboxColumn("Sample Column", options=list(email.columns)),
            "Exclusion Column": st.column_config.SelectboxColumn("Exclusion Column", options=list(email.columns)),
            "Exclusion Value": st.column_config.TextColumn("Exclusion Value"),
        },
        num_rows="dynamic",
        key="email_replace"
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
            conditions = pd.Series([True] * len(sample))
            for _, rule in match_rules.iterrows():
                d_col = rule["DD Column"]
                s_col = rule["Sample Column"]
                if pd.notna(d_col) and pd.notna(s_col) and s_col in sample.columns:
                    conditions &= (sample[s_col] == row[d_col])
            matches = sample[conditions]
            if matches.empty:
                return row_dict  # no match → fila sin sample adjunto
            match = matches.iloc[0].to_dict()
        else:
            if sample.empty:
                return row_dict
            match = sample.sample(1).iloc[0].to_dict()

        # --- Reemplazo ---
        for _, rule in replace_rules.iterrows():
            d_col = rule["DD Column"]
            s_col = rule["Sample Column"]
            excl_col = rule["Exclusion Column"]
            excl_val = rule["Exclusion Value"]

            if pd.notna(d_col) and pd.notna(s_col) and s_col in match:
                # aplicar exclusión
                if pd.notna(excl_col) and pd.notna(excl_val) and match.get(excl_col) == excl_val:
                    continue
                row_dict[d_col] = match.get(s_col, row_dict[d_col])

        # Adjuntar solo las columnas usadas del sample
        used_cols = [c for c in list(match_rules["Sample Column"].dropna()) + list(replace_rules["Sample Column"].dropna())]
        for col in used_cols:
            if col in match:
                row_dict[col] = match[col]

        return row_dict

    # Procesamiento
    for _, row in dd.iterrows():
        sample = assign_sample_row(row)
        if sample.empty:
            final_rows.append(row.to_dict())
            continue

        if row.get("mode") in [1, 2]:
            row_dict = apply_rules(row, sample, phone_match_rules, phone_replace_rules)
        elif row.get("mode") == 3:
            row_dict = apply_rules(row, sample, online_match_rules, online_replace_rules)
        elif row.get("mode") == 4:
            row_dict = apply_rules(row, sample, email_match_rules, email_replace_rules)
        else:
            row_dict = row.to_dict()

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
