import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Mapping Sheet Updater", layout="wide")
st.title("Mapping Sheet Updater")
st.caption("Get your mapping done in minutes")

# --- File Upload ---
uploaded_main = st.file_uploader("Upload Primary Excel File", type=[".xlsx"])
uploaded_secondary = st.file_uploader("Upload Secondary Excel File", type=[".xlsx"])

# --- Session State ---
if "df_main" not in st.session_state:
    st.session_state.df_main = None
if "df_secondary" not in st.session_state:
    st.session_state.df_secondary = None

# --- Load Excel Sheet ---
def load_excel(file):
    xls = pd.ExcelFile(file)
    sheet = st.selectbox("Select Sheet", xls.sheet_names, key=str(file))
    return pd.read_excel(xls, sheet_name=sheet)

if uploaded_main:
    st.session_state.df_main = load_excel(uploaded_main)
if uploaded_secondary:
    st.session_state.df_secondary = load_excel(uploaded_secondary)

# --- Mapping UI ---
if st.session_state.df_main is not None and st.session_state.df_secondary is not None:
    st.markdown("---")
    st.subheader("🛠️ Create New Column with Dropdown Values")

    new_col_name = st.text_input("New Column Name")
    sec_col_options = st.session_state.df_secondary.columns.tolist()
    sec_col_selected = st.selectbox("Choose Secondary Column for Dropdown Values", sec_col_options)

    if new_col_name and sec_col_selected:
        dropdown_values = [""] + st.session_state.df_secondary[sec_col_selected].dropna().astype(str).unique().tolist()

        edited_df = st.session_state.df_main.copy()
        if new_col_name not in edited_df.columns:
            edited_df[new_col_name] = ""

        edited_df.fillna("", inplace=True)
        edited_df[new_col_name] = edited_df[new_col_name].astype(str)

        # --- Column Hiding ---
        st.markdown("### 👀 Hide Columns")
        hide_columns = st.multiselect("Select columns to hide", options=edited_df.columns.tolist())
        visible_columns = [col for col in edited_df.columns if col not in hide_columns]

        st.markdown("---")
        st.subheader("📋 Editable Table")

        # Render column headers
        header_cols = st.columns(len(visible_columns))
        for i, col in enumerate(visible_columns):
            header_cols[i].markdown(f"**{col}**")

        # Render table rows
        for i, row in edited_df.iterrows():
            row_cols = st.columns(len(visible_columns))
            for j, col in enumerate(visible_columns):
                if col == new_col_name:
                    current_val = row[new_col_name] if row[new_col_name] in dropdown_values else ""
                    selected = row_cols[j].selectbox(
                        label="",
                        options=dropdown_values,
                        index=dropdown_values.index(current_val),
                        key=f"{i}_{col}"
                    )
                    edited_df.at[i, new_col_name] = selected
                else:
                    row_cols[j].markdown(str(row[col]))

        # --- Download Excel ---
        st.markdown("---")
        st.subheader("📥 Download Updated Excel")

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            edited_df.to_excel(writer, index=False)

        st.download_button(
            label="Download Excel File",
            data=buffer.getvalue(),
            file_name="updated_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
