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
    st.subheader("🛠️ Create New Column with Dropdown and Manual Input")

    new_col_name = st.text_input("New Column Name")
    sec_col_options = st.session_state.df_secondary.columns.tolist()
    sec_col_selected = st.selectbox("Choose Secondary Column for Dropdown Values", sec_col_options)

    if new_col_name and sec_col_selected:
        dropdown_values = [""] + st.session_state.df_secondary[sec_col_selected].dropna().astype(str).unique().tolist()

        edited_df = st.session_state.df_main.copy()
        dropdown_col = f"{new_col_name} (Dropdown)"
        manual_col = f"{new_col_name} (Manual)"

        if dropdown_col not in edited_df.columns:
            edited_df[dropdown_col] = ""
        if manual_col not in edited_df.columns:
            edited_df[manual_col] = ""

        edited_df.fillna("", inplace=True)

        st.markdown("---")
        st.subheader("📊 Editable Table")

        # --- Hide columns ---
        hide_columns = st.multiselect("Hide Columns", options=edited_df.columns.tolist())

        # --- AgGrid Setup ---
        gb = GridOptionsBuilder.from_dataframe(edited_df)
        gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
        gb.configure_grid_options(suppressMovableColumns=False)

        gb.configure_column(
            dropdown_col,
            editable=True,
            cellEditor="agRichSelectCellEditor",
            cellEditorParams={"values": dropdown_values},
            singleClickEdit=True,
            filter=True,
        )

        for col in hide_columns:
            gb.configure_column(col, hide=True)

        grid_response = AgGrid(
            edited_df,
            gridOptions=gb.build(),
            height=500,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode='AS_INPUT',
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            theme="streamlit"
        )

        updated_df = pd.DataFrame(grid_response["data"])

        # Combine the columns
        combined_values = updated_df[dropdown_col].astype(str).str.strip()
        manual_values = updated_df[manual_col].astype(str).str.strip()

        combined_column = combined_values + ", " + manual_values
        combined_column = combined_column.str.strip(", ")  # Remove dangling commas

        # Final export dataframe
        export_df = st.session_state.df_main.copy()
        export_df[new_col_name] = combined_column

        # --- Download Excel ---
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False)

        st.download_button(
            "📥 Download Updated Excel",
            data=buffer.getvalue(),
            file_name="updated_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
