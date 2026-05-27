import streamlit as st

st.title("Survey Results & Sample Matcher 📊")

# Bloque para Phone Sample
st.subheader("📞 Phone Sample Rules")
st.write("Define aquí las reglas de match y reemplazo para Phone")

# Match
phone_match_rules = st.experimental_data_editor(
    [{"DD Column": "", "Sample Column": "", "Action": "Match"}],
    num_rows="dynamic",
    key="phone_match"
)

# Reemplazo
phone_replace_rules = st.experimental_data_editor(
    [{"DD Column": "", "Sample Column": "", "Action": "Replace", "Exclusion Column": "", "Exclusion Value": ""}],
    num_rows="dynamic",
    key="phone_replace"
)

# Bloque para Online Sample
st.subheader("💻 Online Sample Rules")
st.write("Define aquí las reglas de match y reemplazo para Online")

online_match_rules = st.experimental_data_editor(
    [{"DD Column": "", "Sample Column": "", "Action": "Match"}],
    num_rows="dynamic",
    key="online_match"
)

online_replace_rules = st.experimental_data_editor(
    [{"DD Column": "", "Sample Column": "", "Action": "Replace", "Exclusion Column": "", "Exclusion Value": ""}],
    num_rows="dynamic",
    key="online_replace"
)

# Bloque para Email Sample
st.subheader("📧 Email Sample Rules")
st.write("Define aquí las reglas de match y reemplazo para Email")

email_match_rules = st.experimental_data_editor(
    [{"DD Column": "", "Sample Column": "", "Action": "Match"}],
    num_rows="dynamic",
    key="email_match"
)

email_replace_rules = st.experimental_data_editor(
    [{"DD Column": "", "Sample Column": "", "Action": "Replace", "Exclusion Column": "", "Exclusion Value": ""}],
    num_rows="dynamic",
    key="email_replace"
)

st.write("👉 Aquí defines todas las reglas. Cada fila es una regla independiente.")
