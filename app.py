import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(
    page_title="Survey DD Builder",
    layout="wide"
)

st.title("Survey DD Builder 📊")

# =====================================================
# HELPERS
# =====================================================

def create_mode(df):

    pmode_col = None
    phonetype_col = None

    for col in df.columns:

        if col.lower() == "pmode":
            pmode_col = col

        if col.lower() == "pphonetype":
            phonetype_col = col

    if pmode_col is None:
        return df

    def calc_mode(row):

        try:
            pmode = int(row[pmode_col])
        except:
            return None

        try:
            pphone = int(
                row[phonetype_col]
            )
        except:
            pphone = None

        if pmode == 1 and pphone == 1:
            return 1  # Landline

        if pmode == 1 and pphone == 2:
            return 2  # Cell

        if pmode == 3:
            return 3  # Text

        if pmode == 2:
            return 4  # Email

        return None

    df["mode"] = df.apply(
        calc_mode,
        axis=1
    )

    return df


def move_mode_next_to_pmode(df):

    if "mode" not in df.columns:
        return df

    pmode_col = None

    for col in df.columns:

        if col.lower() == "pmode":

            pmode_col = col
            break

    if pmode_col is None:
        return df

    cols = list(df.columns)

    cols.remove("mode")

    pos = cols.index(pmode_col) + 1

    cols.insert(
        pos,
        "mode"
    )

    return df[cols]


def clean_submitdate(df):

    if "submitdate" in df.columns:

        df["submitdate"] = (
            pd.to_datetime(
                df["submitdate"],
                errors="coerce"
            )
            .dt.strftime("%Y-%m-%d")
        )

    return df


def replace_run_at(df):

    obj_cols = df.select_dtypes(
        include=["object"]
    ).columns

    for col in obj_cols:

        df[col] = df[col].replace(
            r"Run at.*",
            "Test",
            regex=True
        )

    return df


def rename_arrays(df):

    rename_map = {}

    for col in df.columns:

        match = re.match(
            r"Q\d+to\d+_(\d+)",
            col
        )

        if match:

            rename_map[col] = (
                f"Q{match.group(1)}"
            )

    return df.rename(
        columns=rename_map
    )


def clean_headers(df):

    df.columns = [

        c.replace(
            "[",
            "_"
        ).replace(
            "]",
            ""
        )

        for c in df.columns

    ]

    return df


def create_rotation(n):

    values = [1, 2] * ((n // 2) + 1)

    values = values[:n]

    np.random.shuffle(values)

    return values


def move_rotation_next_to_mode(
    df,
    rotation_name
):

    if (
        rotation_name not in df.columns
        or "mode" not in df.columns
    ):
        return df

    cols = list(df.columns)

    cols.remove(rotation_name)

    pos = cols.index("mode") + 1

    cols.insert(
        pos,
        rotation_name
    )

    return df[cols]


def find_empty_columns(df):

    empty = []

    for col in df.columns:

        values = (
            df[col]
            .replace("", pd.NA)
            .dropna()
        )

        if len(values) == 0:

            empty.append(col)

    return empty


def show_expected_samples(df):

    if "mode" not in df.columns:
        return

    modes = sorted(
        df["mode"]
        .dropna()
        .unique()
        .tolist()
    )

    st.subheader(
        "📋 Expected Samples"
    )

    if 1 in modes or 2 in modes:

        st.success(
            "Phone Sample Required"
        )

    if 3 in modes:

        st.success(
            "Online Sample Required"
        )

    if 4 in modes:

        st.success(
            "Email Sample Required"
        )


# =====================================================
# TABS
# =====================================================

tab_prepare, tab_match = st.tabs(
    [
        "Prepare DD",
        "Matching"
    ]
)

# =====================================================
# PREPARE DD
# =====================================================

with tab_prepare:

    st.header(
        "Prepare DD"
    )

    dd_file = st.file_uploader(
        "Raw Survey CSV",
        type="csv",
        key="rawdd"
    )

    add_rotation = st.checkbox(
        "Add TrackRotation"
    )

    rotation_name = st.text_input(
        "Rotation Column Name",
        value="TrackRotation"
    )

    if (
        st.button("Prepare DD")
        and dd_file is not None
    ):

        dd = pd.read_csv(dd_file)

        prep = dd.copy()

        prep = create_mode(prep)

        prep = move_mode_next_to_pmode(prep)

        prep = clean_submitdate(prep)

        prep = replace_run_at(prep)

        prep = rename_arrays(prep)

        prep = clean_headers(prep)

        if add_rotation:

            prep[
                rotation_name
            ] = create_rotation(
                len(prep)
            )

            prep = move_rotation_next_to_mode(
                prep,
                rotation_name
            )

        show_expected_samples(
            prep
        )

        empty_cols = (
            find_empty_columns(prep)
        )

        st.session_state[
            "empty_cols"
        ] = empty_cols

        st.session_state[
            "prepared_dd"
        ] = prep

    if "prepared_dd" in st.session_state:

        prep = st.session_state[
            "prepared_dd"
        ]

        # =====================================
        # COLUMN CLEANUP
        # =====================================

        st.subheader(
            "🧹 Column Cleanup"
        )

        technical_columns = [

            "lastpage",
            "startlanguage",
            "startdate",
            "datestamp",
            "ipaddr",
            "interviewtime",
            "RefusedSplit",
            "pSetter",

            "pMode",
            "pPhoneType",
            "pPhonetype"

        ]

        existing_technical = [

            c

            for c in technical_columns

            if c in prep.columns

        ]

        empty_cols = [

            c

            for c in st.session_state.get(
                "empty_cols",
                []
            )

            if c in prep.columns

        ]

        review_first = [

            "pMode",
            "pPhoneType",
            "pPhonetype"

        ]

        default_remove = [

            c

            for c in list(
                set(
                    existing_technical
                    + empty_cols
                )
            )

            if c not in review_first

        ]

        recommended_keep = [

            c

            for c in empty_cols

            if (
                c.startswith("Q")
                or c.startswith("D")
                or "other" in c.lower()
            )

        ]

        # =====================================
        # MODE VALIDATION
        # =====================================

        validation_cols = [

            c

            for c in [
                "pMode",
                "mode",
                "pPhoneType",
                "pPhonetype"
            ]

            if c in prep.columns

        ]

        if validation_cols:

            st.subheader(
                "✅ Mode Validation"
            )

            validation_df = (
                prep[validation_cols]
                .drop_duplicates()
            )
            
            st.subheader("✅ Mode Mapping")
            
            st.table(
                validation_df
            )

        st.info(
            """
Review pMode / pPhoneType against mode first.
Once validated, add them to the removal list.
"""
        )

        if "preview_dd" not in st.session_state:

            st.session_state[
                "preview_dd"
            ] = prep.copy()

            priority_cols = [
            
                "pMode",
                "pPhoneType",
                "pPhonetype"
            
            ]
            
            ordered_options = [
            
                c
                for c in priority_cols
                if c in prep.columns
            
            ] + [
            
                c
                for c in prep.columns
                if c not in priority_cols
            
            ]
            
            columns_to_remove = st.multiselect(
            
                "Columns To Remove",
            
                options=ordered_options,

            default=[

                c

                for c in default_remove

                if (
                    c not in recommended_keep
                    and c in prep.columns
                )

            ],

            key="columns_to_remove"

        )

        preview_df = prep.drop(

            columns=columns_to_remove,

            errors="ignore"

        )

        st.session_state[
            "preview_dd"
        ] = preview_df

        st.subheader(
            "Preview"
        )

        st.dataframe(
            preview_df,
            use_container_width=True
        )

        csv = (
            st.session_state[
                "preview_dd"
            ]
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "Download Clean DD",
            csv,
            "clean_dd.csv",
            "text/csv"
        )

# =====================================================
# MATCHING
# =====================================================

with tab_match:

    st.header(
        "Matching"
    )

    if (
        "prepared_dd"
        not in st.session_state
    ):

        st.info(
            "Prepare DD first."
        )

    else:

        prepared_dd = (
            st.session_state[
                "prepared_dd"
            ]
        )

        st.success(
            f"{len(prepared_dd)} rows loaded from Prepare DD"
        )

        phone_file = st.file_uploader(
            "Phone Sample",
            type="csv"
        )

        online_file = st.file_uploader(
            "Online Sample",
            type="csv"
        )

        email_file = st.file_uploader(
            "Email Sample",
            type="csv"
        )

        phone = (
            pd.read_csv(phone_file)
            if phone_file
            else pd.DataFrame()
        )

        online = (
            pd.read_csv(online_file)
            if online_file
            else pd.DataFrame()
        )

        email = (
            pd.read_csv(email_file)
            if email_file
            else pd.DataFrame()
        )

        st.info(
            "Matching V1 pendiente de integrar completamente."
        )

        st.write(
            "La preparación del DD ya está funcional."
        )
