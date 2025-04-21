import streamlit as st
import pandas as pd
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(page_title="Mapping Sheet Updater", layout="wide")
st.title("Mapping Sheet Updater")
st.caption("Get your mapping done in minutes")

# --- Upload Files ---
uploaded_main = st.file_uploader("Upload Primary Excel File", type=[".xlsx"])
uploaded_secondary = st.file_uploader("Upload Secondary Excel File", type=[".xlsx"])

# --- Session State Setup ---
if "df_main" not in st.session_state:
    st.session_state.df_main = None
if "df_secondary" not in st.session_state:
    st.session_state.df_secondary = None

# --- Excel Reader ---
def load_excel(file):
    xls = pd.ExcelFile(file)
    sheet = st.selectbox("Select Sheet", xls.sheet_names, key=str(file))
    return pd.read_excel(xls, sheet_name=sheet)

if uploaded_main:
    st.session_state.df_main = load_excel(uploaded_main)
if uploaded_secondary:
    st.session_state.df_secondary = load_excel(uploaded_secondary)

# --- Main Interface ---
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

        st.markdown("---")
        st.subheader("📊 Editable Table")

        # --- Hide Columns Option ---
        hide_columns = st.multiselect("Hide Columns", options=edited_df.columns.tolist())

        # --- AgGrid Configuration ---
        gb = GridOptionsBuilder.from_dataframe(edited_df)
        gb.configure_default_column(
            editable=False,
            filter=True,
            sortable=True,
            resizable=True
        )

        # Dropdown column config with simulated autocomplete
        gb.configure_column(
            new_col_name,
            editable=True,
            cellEditor="agRichSelectCellEditor",
            cellEditorParams={"values": dropdown_values},
            singleClickEdit=True,
            filter=True
        )

        # Hide selected columns
        for col in hide_columns:
            gb.configure_column(col, hide=True)

        # Enable column drag-and-drop
        gb.configure_grid_options(suppressMovableColumns=False)

        grid_response = AgGrid(
            edited_df,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode="AS_INPUT",
            allow_unsafe_jscode=True,
            height=600,
            fit_columns_on_grid_load=True,
            theme="streamlit"
        )

        # Save edited data
        updated_df = pd.DataFrame(grid_response["data"])

        # --- Download updated Excel ---
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            updated_df.to_excel(writer, index=False)

        st.download_button(
            "📥 Download Updated Excel",
            data=buffer.getvalue(),
            file_name="updated_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
