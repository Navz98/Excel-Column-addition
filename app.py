import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Excel Column Mapper", layout="wide")

st.title("🧩 Excel Column Mapper")
st.markdown("A clean, minimal tool to map values from a secondary Excel sheet to a new column in a primary sheet.")

# Upload files
st.sidebar.header("📁 Upload Excel Files")
main_file = st.sidebar.file_uploader("Upload Primary Excel File", type="xlsx")
secondary_file = st.sidebar.file_uploader("Upload Secondary Excel File", type="xlsx")

# Load Excel files and list sheets
if main_file:
    main_excel = pd.ExcelFile(main_file)
    main_sheet = st.sidebar.selectbox("Select Sheet from Primary", main_excel.sheet_names)
    df_main = main_excel.parse(main_sheet)
else:
    df_main = None

if secondary_file:
    secondary_excel = pd.ExcelFile(secondary_file)
    secondary_sheet = st.sidebar.selectbox("Select Sheet from Secondary", secondary_excel.sheet_names)
    df_secondary = secondary_excel.parse(secondary_sheet)
else:
    df_secondary = None

# Proceed only if both files are loaded
if df_main is not None and df_secondary is not None:
    st.success("✅ Both tables loaded successfully.")

    new_col_name = st.text_input("Enter new column name to add to primary table")
    selected_secondary_column = st.selectbox("Select column from secondary table for dropdown values", df_secondary.columns)

    if new_col_name and selected_secondary_column:
        dropdown_values = [""] + df_secondary[selected_secondary_column].dropna().unique().tolist()
        selections = []

        st.write(f"### 🧩 Assign values to new column: `{new_col_name}`")

        for i, row in df_main.iterrows():
            col1, col2 = st.columns([3, 2])
            with col1:
                st.write(row.to_dict())
            with col2:
                choice = st.selectbox(
                    f"Row {i + 1}",
                    options=dropdown_values,
                    key=f"dropdown_{i}"
                )
                selections.append(choice)

        if st.button("✅ Apply and Show Result"):
            df_main[new_col_name] = selections
            st.success(f"New column '{new_col_name}' added.")
            st.dataframe(df_main)

            to_download = BytesIO()
            df_main.to_excel(to_download, index=False)
            to_download.seek(0)

            st.download_button(
                label="📥 Download Updated Excel File",
                data=to_download,
                file_name="updated_primary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
