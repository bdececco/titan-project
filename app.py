import streamlit as st
import pandas as pd
import json

def load_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)

def main():
    st.set_page_config(page_title="Titan MMM - Data Workbench", layout="wide")
    st.title("Titan Automotive MMM: Data Slicing & Dynamic Mapping")

    # Initialize default categories in session state if not present
    if "custom_categories" not in st.session_state:
        st.session_state.custom_categories = [
            "Digital Media",
            "Broadcast / Traditional",
            "CDP & Marketplace",
            "Control Variables",
            "Promotional Offers & Events"
        ]

    uploaded_file = st.sidebar.file_uploader("Upload Raw Workbook", type=["csv", "xlsx"])

    if uploaded_file is not None:
        raw_df = load_data(uploaded_file)
        
        # 1. Full Spreadsheet View & Row Slicing
        st.subheader("1. Spreadsheet Inspection & Row Slicing")
        
        col_slice1, col_slice2 = st.columns([1, 3])
        with col_slice1:
            total_rows = len(raw_df)
            row_range = st.slider(
                "Select Row Range (Weeks)",
                min_value=0,
                max_value=total_rows - 1,
                value=(0, total_rows - 1),
                help="Slice the dataset to isolate specific modeling periods."
            )
        
        # Slice DataFrame based on user selection
        sliced_df = raw_df.iloc[row_range[0] : row_range[1] + 1].copy()
        
        with col_slice2:
            st.caption(f"Showing rows {row_range[0]} through {row_range[1]} ({len(sliced_df)} total observations)")
            st.dataframe(sliced_df, use_container_width=True, height=200)

        st.markdown("---")

        # 2. Dynamic Bucket Management
        st.subheader("2. Manage Categorization Buckets")
        
        col_cat1, col_cat2 = st.columns([2, 2])
        with col_cat1:
            new_cat = st.text_input("Create Custom Bucket Name", placeholder="e.g., Local Sponsorships")
            if st.button("Add Bucket") and new_cat:
                if new_cat not in st.session_state.custom_categories:
                    st.session_state.custom_categories.append(new_cat)
                    st.rerun()

        with col_cat2:
            cat_to_remove = st.selectbox("Remove Bucket", ["-- Select --"] + st.session_state.custom_categories)
            if st.button("Delete Selected Bucket") and cat_to_remove != "-- Select --":
                st.session_state.custom_categories.remove(cat_to_remove)
                st.rerun()

        st.markdown("---")

        # 3. Dynamic Column Assignment
        st.subheader("3. Assign Columns to Buckets")
        columns = list(sliced_df.columns)
        
        target_col = st.selectbox("Target Variable (Sales / Units)", options=["-- Select --"] + columns)
        date_col = st.selectbox("Date / Time Column", options=["None"] + columns)
        
        unassigned_cols = [c for c in columns if c not in [target_col, date_col]]
        
        mapping_result = {
            "target": target_col if target_col != "-- Select --" else None,
            "date_col": date_col if date_col != "None" else None,
            "row_range": row_range,
            "mappings": {}
        }

        # Dynamically generate multi-select inputs for each active bucket
        for category in st.session_state.custom_categories:
            selected = st.multiselect(
                f"Bucket: **{category}**",
                options=unassigned_cols,
                key=f"bucket_{category}"
            )
            mapping_result["mappings"][category] = selected
            # Remove assigned columns from downstream options to prevent duplicate assignments
            unassigned_cols = [c for c in unassigned_cols if c not in selected]

        if unassigned_cols:
            st.info(f"Unassigned Columns Remaining: `{', '.join(unassigned_cols)}`")

        # Save to session state
        st.session_state["titan_sliced_df"] = sliced_df
        st.session_state["titan_mapping"] = mapping_result

        with st.expander("View Final Schema JSON", expanded=False):
            st.json(mapping_result)

if __name__ == "__main__":
    main()