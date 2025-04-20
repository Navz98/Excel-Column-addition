import streamlit as st
import pandas as pd
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
if "edited_df" not in st.session_state:
    st.session_state.edited_df = None

# --- Load Excel Sheet ---
def load_excel(file):
    xls = pd.ExcelFile(file)
    sheet = st.selectbox("Select Sheet", xls.sheet_names, key=str(file))
    return pd.read_excel(xls, sheet_name=sheet)

if uploaded_main:
    st.session_state.df_main = load_excel(uploaded_main)
if uploaded_secondary:
    st.session_state.df_secondary = load_excel(uploaded_secondary)

# --- Column Mapping UI ---
if st.session_state.df_main is not None and st.session_state.df_secondary is not None:
    st.markdown("---")
    st.subheader("🛠️ Create New Column with Dropdown Values")

    new_col_name = st.text_input("New Column Name")
    sec_col_options = st.session_state.df_secondary.columns.tolist()
    sec_col_selected = st.selectbox("Choose Secondary Column for Dropdown Values", sec_col_options)

    if new_col_name and sec_col_selected:
        dropdown_values = [""] + st.session_state.df_secondary[sec_col_selected].dropna().astype(str).unique().tolist()

        if st.session_state.edited_df is None or not set(st.session_state.df_main.columns).issubset(st.session_state.edited_df.columns):
            st.session_state.edited_df = st.session_state.df_main.copy()

        if new_col_name not in st.session_state.edited_df.columns:
            st.session_state.edited_df[new_col_name] = ""

        edited_df = st.session_state.edited_df.copy()
        edited_df.fillna("", inplace=True)
        edited_df[new_col_name] = edited_df[new_col_name].astype(str)

        st.markdown("---")
        st.subheader("📊 Table with Editable Dropdown Column")

        # --- Hide columns selection ---
        hide_columns = st.multiselect("Hide Columns", options=edited_df.columns.tolist())

        # --- Configure Ag-Grid ---
        gb = GridOptionsBuilder.from_dataframe(edited_df)
        gb.configure_default_column(editable=False, resizable=True, sortable=True, filter=True)
        gb.configure_grid_options(suppressMovableColumns=False)

        # Set dropdown column as editable with dropdown options
        if new_col_name in edited_df.columns:
            gb.configure_column(
                new_col_name,
                editable=True,
                cellEditor="agSelectCellEditor",
                cellEditorParams={"values": dropdown_values},
                singleClickEdit=True
            )

        # Apply column hiding
        for col in hide_columns:
            gb.configure_column(col, hide=True)

        grid_response = AgGrid(
            edited_df,
            gridOptions=gb.build(),
            height=500,
            update_mode=GridUpdateMode.MANUAL,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            theme="streamlit"
        )

        # ✅ Save updates to session
        st.session_state.edited_df = pd.DataFrame(grid_response["data"])

        # --- Download Excel ---
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            st.session_state.edited_df.to_excel(writer, index=False)

        st.download_button(
            "📥 Download Updated Excel",
            data=buffer.getvalue(),
            file_name="updated_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
