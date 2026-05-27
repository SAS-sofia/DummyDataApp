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

    # Botón para ejecutar procesamiento
    if st.button("🚀 Aplicar reglas y generar tabla final"):
        final_rows = []
        unmatched_rows = []
        used_indices = {"phone": set(), "online": set(), "email": set()}

        def get_sample(mode):
            if mode == 1:
                return phone, "phone"
            elif mode == 2:
                return phone, "phone"
            elif mode == 3:
                return online, "online"
            elif mode == 4:
                return email, "email"
            else:
                return pd.DataFrame(), None

        def apply_rules(row, sample, sample_key, match_rules, replace_rules):
            row_dict = row.to_dict()
            match = None

            # --- Match ---
            if not sample.empty and not match_rules.empty:
                conditions = pd.Series(True, index=sample.index)
                for _, rule in match_rules.iterrows():
                    d_col = rule["DD Column (Match)"]
                    s_col = rule["Sample Column (Match)"]
                    if pd.notna(d_col) and pd.notna(s_col) and s_col in sample.columns:
                        conditions &= (sample[s_col] == row[d_col])
                matches = sample.loc[conditions]
                matches = matches.loc[~matches.index.isin(used_indices[sample_key])]
                if not matches.empty:
                    match_index = matches.index[0]
                    used_indices[sample_key].add(match_index)
                    match = matches.iloc[0].to_dict()
            else:
                return None

            if match is None:
                return None

            # --- Reemplazo ---
            for _, rule in replace_rules.iterrows():
                d_col = rule["DD Column (Replace)"]
                s_col = rule["Sample Column (Replace)"]
                excl_col = rule["Exclusion Column"]
                excl_val = rule["Exclusion Value"]

                if pd.notna(d_col) and pd.notna(s_col) and s_col in match:
                    if pd.notna(excl_col) and pd.notna(excl_val):
                        if str(row.get(excl_col)) == str(excl_val):
                            # 🚫 No reemplazar
                            pass
                        else:
                            row_dict[d_col] = match.get(s_col, row_dict[d_col])
                    else:
                        row_dict[d_col] = match.get(s_col, row_dict[d_col])

            # Adjuntar TODAS las columnas del sample sin modificar las del DD
            for col in sample.columns:
                row_dict[col] = match.get(col, None)

            return row_dict

        for _, row in dd.iterrows():
            sample, sample_key = get_sample(row.get("mode"))
            if sample.empty or sample_key is None:
                unmatched_rows.append(row.to_dict())
                continue

            row_dict = apply_rules(row, sample, sample_key, match_rules, replace_rules)
            if row_dict is None:
                unmatched_rows.append(row.to_dict())
            else:
                final_rows.append(row_dict)

        all_rows = final_rows + unmatched_rows

        if all_rows:
            final_table = pd.DataFrame(all_rows)
            st.write("✅ Processed results:")
            st.dataframe(final_table)

            csv = final_table.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "final_table.csv", "text/csv")
        else:
            st.warning("⚠️ No rows were generated. Check your rules or mode.")
