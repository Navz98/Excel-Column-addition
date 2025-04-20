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

# --- Sheet Selector and Data Load ---
def load_excel(file):
    xls = pd.ExcelFile(file)
    sheet = st.selectbox("Select Sheet", xls.sheet_names, key=str(file))
    return pd.read_excel(xls, sheet_name=sheet)

if uploaded_main:
    st.session_state.df_main = load_excel(uploaded_main)

if uploaded_secondary:
    st.session_state.df_secondary = load_excel(uploaded_secondary)

# --- Column Mapping Interface ---
if st.session_state.df_main is not None and st.session_state.df_secondary is not None:
    st.markdown("---")
    st.subheader("🛠️ Create New Column with Dropdown Values")

    new_col_name = st.text_input("New Column Name")
    sec_col_options = st.session_state.df_secondary.columns.tolist()
    sec_col_selected = st.selectbox("Choose Secondary Column for Dropdown Values", sec_col_options)

    if new_col_name and sec_col_selected:
        dropdown_values = [""] + st.session_state.df_secondary[sec_col_selected].dropna().unique().tolist()

        edited_df = st.session_state.df_main.copy()

        if new_col_name not in edited_df.columns:
            edited_df[new_col_name] = ""

        edited_df.fillna("", inplace=True)

        st.markdown("---")
        st.subheader("📊 Interactive Table with Dropdowns")

        hide_columns = st.multiselect("Hide Columns", options=edited_df.columns.tolist())
        visible_df = edited_df.drop(columns=hide_columns)

        gb = GridOptionsBuilder.from_dataframe(visible_df)
        gb.configure_pagination(enabled=True)
        gb.configure_default_column(editable=False, resizable=True)

        gb.configure_column(new_col_name, editable=True, cellEditor="agSelectCellEditor", 
                            cellEditorParams={"values": dropdown_values})

        grid_options = gb.build()

        grid_response = AgGrid(
            visible_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True,
            enable_enterprise_modules=False,
            height=500,
            key="aggrid"
        )

        # Update the edited values back to the original df
        updated_grid_df = grid_response["data"]
        for col in updated_grid_df.columns:
            edited_df[col] = updated_grid_df[col]

        # --- Download Updated Excel ---
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            edited_df.to_excel(writer, index=False)

        st.download_button(
            "📥 Download Updated Excel",
            data=buffer.getvalue(),
            file_name="updated_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
