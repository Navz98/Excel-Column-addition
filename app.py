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
if "final_df" not in st.session_state:
    st.session_state.final_df = None

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
    st.subheader("🛠️ Map Column with Dropdown + Manual Input")

    new_col_base = st.text_input("Base Column Name (for Dropdown + Manual Input)")
    sec_col_options = st.session_state.df_secondary.columns.tolist()
    sec_col_selected = st.selectbox("Choose Secondary Column for Dropdown Values", sec_col_options)

    if new_col_base and sec_col_selected:
        dropdown_values = ["" ] + st.session_state.df_secondary[sec_col_selected].dropna().astype(str).unique().tolist()

        df_main = st.session_state.df_main.copy()
        dropdown_col = f"{new_col_base}_Dropdown"
        manual_col = f"{new_col_base}_Manual"
        final_col = new_col_base

        for col in [dropdown_col, manual_col]:
            if col not in df_main.columns:
                df_main[col] = ""

        df_main[dropdown_col] = df_main[dropdown_col].astype(str)
        df_main[manual_col] = df_main[manual_col].astype(str)

        # --- Hide Columns ---
        hide_columns = st.multiselect("Hide Columns", options=df_main.columns.tolist())

        # --- AgGrid Setup ---
        gb = GridOptionsBuilder.from_dataframe(df_main)
        gb.configure_default_column(editable=False, resizable=True, sortable=True, filter=True)
        gb.configure_grid_options(suppressMovableColumns=False)

        # Configure editable dropdown column
        gb.configure_column(
            dropdown_col,
            editable=True,
            cellEditor="agRichSelectCellEditor",
            cellEditorParams={"values": dropdown_values},
            singleClickEdit=True,
            filter=True
        )

        # Configure manual input column
        gb.configure_column(manual_col, editable=True, filter=True)

        for col in hide_columns:
            gb.configure_column(col, hide=True)

        grid_response = AgGrid(
            df_main,
            gridOptions=gb.build(),
            height=500,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode='AS_INPUT',
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            theme="streamlit"
        )

        # Save updated edits
        edited_df = pd.DataFrame(grid_response["data"])

        if st.button("✅ Update and Preview Final Column"):
            edited_df[final_col] = edited_df[[dropdown_col, manual_col]].apply(
                lambda row: ', '.join(filter(None, [row[dropdown_col].strip(), row[manual_col].strip()])), axis=1
            )
            st.session_state.final_df = edited_df

    # --- Download Final Output ---
    if st.session_state.final_df is not None:
        st.markdown("### ✅ Final Output Preview")
        st.dataframe(st.session_state.final_df)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            st.session_state.final_df.to_excel(writer, index=False)

        st.download_button(
            "📥 Download Final Excel",
            data=buffer.getvalue(),
            file_name="updated_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
