import streamlit as st
import pandas as pd
from io import BytesIO
import streamlit.components.v1 as components

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
        st.subheader("📊 Table with Inline Dropdowns")

        hide_columns = st.multiselect("Hide Columns", options=edited_df.columns.tolist())

        visible_columns = [col for col in edited_df.columns if col not in hide_columns]

        # JavaScript drag-and-drop + CSS for borders
        components.html(f"""
            <style>
                .drag-table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                .drag-table th, .drag-table td {{
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }}
                .drag-table th {{
                    background-color: #f4f4f4;
                    cursor: move;
                }}
            </style>
            <script>
                function enableDrag(tableId) {{
                    const table = document.getElementById(tableId);
                    let dragSrcEl;

                    function handleDragStart(e) {{
                        dragSrcEl = this;
                        e.dataTransfer.effectAllowed = 'move';
                        e.dataTransfer.setData('text/html', this.innerHTML);
                    }}

                    function handleDrop(e) {{
                        if (dragSrcEl != this) {{
                            dragSrcEl.innerHTML = this.innerHTML;
                            this.innerHTML = e.dataTransfer.getData('text/html');
                        }}
                        return false;
                    }}

                    let cols = table.querySelectorAll("th");
                    [].forEach.call(cols, function(col) {{
                        col.setAttribute("draggable", true);
                        col.addEventListener('dragstart', handleDragStart, false);
                        col.addEventListener('drop', handleDrop, false);
                    }});
                }}
                document.addEventListener("DOMContentLoaded", function() {{ enableDrag('drag-table'); }});
            </script>
        """, height=0)

        # Render header row
        header_html = "<table class='drag-table' id='drag-table'><thead><tr>"
        for col in visible_columns:
            header_html += f"<th>{col}</th>"
        header_html += "</tr></thead><tbody>"

        # Render rows
        for i, row in edited_df.iterrows():
            header_html += "<tr>"
            for col in visible_columns:
                if col == new_col_name:
                    current_val = row[new_col_name] if row[new_col_name] in dropdown_values else ""
                    select_html = f"<select name='dropdown_{i}' disabled>"
                    for option in dropdown_values:
                        selected = "selected" if option == current_val else ""
                        select_html += f"<option value='{option}' {selected}>{option}</option>"
                    select_html += "</select>"
                    header_html += f"<td>{select_html}</td>"
                else:
                    header_html += f"<td>{str(row[col])}</td>"
            header_html += "</tr>"
        header_html += "</tbody></table>"

        components.html(header_html, height=600, scrolling=True)

        # --- Download Updated Excel ---
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            edited_df.to_excel(writer, index=False)
        st.download_button("📥 Download Updated Excel", data=buffer.getvalue(), file_name="updated_mapping.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
