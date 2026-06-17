import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Excel Dashboard Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Global theme tokens ----------------
PRIMARY = "#4F46E5"
ACCENT = "#06B6D4"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
TEXT_DARK = "#1E293B"
TEXT_MUTED = "#64748B"
BORDER = "#E2E8F0"

# Premium chart palette (brand-aligned, replaces default Plotly Set2)
COLOR_SEQ = ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444",
             "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#3B82F6"]

# ---------------- Global CSS ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    .block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        padding: 2rem 2.2rem;
        border-radius: 18px;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.25);
    }
    .hero-header h1 { color: #fff; font-weight: 800; font-size: 2rem; margin: 0; }
    .hero-header p { color: rgba(255,255,255,0.88); font-size: 1rem; margin-top: 0.45rem; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; background: #F1F5F9; padding: 6px; border-radius: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 46px; white-space: pre-wrap; font-size: 14.5px; font-weight: 600;
        border-radius: 10px; color: #64748B;
    }
    .stTabs [aria-selected="true"] {
        background: #fff !important; color: #4F46E5 !important;
        box-shadow: 0 2px 8px rgba(15,23,42,0.10);
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #fff; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 14px 18px; box-shadow: 0 2px 10px rgba(15,23,42,0.04);
    }
    [data-testid="stMetricLabel"] { color: #64748B; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #1E293B; font-weight: 800; }

    /* Buttons */
    .stButton button, .stDownloadButton button {
        background: linear-gradient(135deg, #4F46E5, #06B6D4);
        color: #fff; border: none; border-radius: 10px; font-weight: 600;
        padding: 0.55rem 1.2rem; transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 16px rgba(79,70,229,0.35); color: #fff;
    }

    /* File uploader dropzone */
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #818CF8; border-radius: 14px; background: #F5F7FF;
    }

    /* Sidebar brand card */
    .sidebar-brand {
        background: linear-gradient(135deg, #4F46E5, #06B6D4);
        border-radius: 14px; padding: 16px 18px; margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(79,70,229,0.25);
    }
    .sidebar-brand h3 { color: #fff; margin: 0; font-weight: 800; font-size: 1.05rem; }
    .sidebar-brand p { color: rgba(255,255,255,0.85); margin: 4px 0 0 0; font-size: 0.82rem; }

    /* Footer */
    .footer-bar {
        text-align: center; padding: 14px; color: #64748B; font-size: 0.85rem;
        border-top: 1px solid #E2E8F0; margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- Helper functions ----------------
def style_chart(fig, height=420):
    """Apply consistent professional styling to every chart."""
    fig.update_layout(
        template="plotly_white",
        font=dict(size=13, color="#333"),
        title_font=dict(size=18, color="#1f2937"),
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eee")
    return fig


def safe_numeric_cols(d):
    return d.select_dtypes(include=[np.number]).columns.tolist()


def safe_cat_cols(d):
    return d.select_dtypes(include=['object', 'category']).columns.tolist()


def top_n_group(d, group_col, value_col, agg, n=15):
    """Group + aggregate, keep top N, bucket rest into 'Other' to keep charts readable."""
    if agg == "Count":
        g = d.groupby(group_col).size().reset_index(name="value")
    else:
        func_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Min": "min", "Max": "max"}
        g = d.groupby(group_col)[value_col].agg(func_map[agg]).reset_index()
        g.columns = [group_col, "value"]

    g = g.sort_values("value", ascending=False)
    if len(g) > n:
        top = g.iloc[:n].copy()
        other_val = g.iloc[n:]["value"].sum() if agg in ["Sum", "Count"] else g.iloc[n:]["value"].mean()
        other_row = pd.DataFrame({group_col: ["Other"], "value": [other_val]})
        g = pd.concat([top, other_row], ignore_index=True)
    return g


def kpi_card(icon, label, value, accent=PRIMARY):
    """Returns HTML for a small KPI card."""
    return f"""
    <div style="background:#FFFFFF; border:1px solid {BORDER}; border-top:4px solid {accent};
                border-radius:14px; padding:18px 20px; box-shadow:0 2px 10px rgba(15,23,42,0.05);
                min-height: 108px;">
      <div style="font-size:1.6rem; line-height:1;">{icon}</div>
      <div style="color:{TEXT_MUTED}; font-size:0.78rem; font-weight:600; text-transform:uppercase;
                  letter-spacing:0.04em; margin-top:8px;">{label}</div>
      <div style="color:{TEXT_DARK}; font-size:1.5rem; font-weight:800; margin-top:2px;">{value}</div>
    </div>
    """


def type_badge(col_name, col_type):
    """Returns HTML for a colored pill showing a column's detected type."""
    palette = {
        "📈 Numeric": ("#4F46E5", "#EEF2FF"),
        "📅 Date/Time": ("#8B5CF6", "#F5F3FF"),
        "🏷️ Categorical": ("#0D9488", "#ECFDF5"),
        "📝 Text": ("#64748B", "#F1F5F9"),
    }
    fg, bg = palette.get(col_type, ("#64748B", "#F1F5F9"))
    return (f'<span style="background:{bg}; color:{fg}; padding:5px 12px; border-radius:20px; '
             f'font-size:0.78rem; font-weight:600; margin:4px 4px 0 0; display:inline-block; '
             f'border:1px solid {fg}33;">{col_name} · {col_type}</span>')


# ---------------- Hero header ----------------
st.markdown("""
<div class="hero-header">
    <h1>📊 Excel to Pro Dashboard Generator</h1>
    <p>Apni Excel file upload karo aur seconds me professional, interactive dashboard pao — no coding needed.</p>
</div>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h3>🚀 Excel Dashboard Pro</h3>
        <p>Upload • Explore • Visualize • Export</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📁 Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload Excel with 2-50 columns"
    )
    if uploaded_file:
        st.success(f"✅ File loaded: {uploaded_file.name}")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isnull().sum().sum())
    completeness = 100 * (1 - missing_cells / total_cells) if total_cells > 0 else 100
    duplicate_rows = int(df.duplicated().sum())

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Data Overview")
    st.sidebar.write(f"**Rows:** {df.shape[0]}")
    st.sidebar.write(f"**Columns:** {df.shape[1]}")
    st.sidebar.write(f"**Missing values:** {missing_cells}")
    st.sidebar.write(f"**Duplicate rows:** {duplicate_rows}")

    # Column type detection (robust)
    col_types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_types[col] = "📈 Numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_types[col] = "📅 Date/Time"
        elif df[col].nunique(dropna=True) < 10:
            col_types[col] = "🏷️ Categorical"
        else:
            col_types[col] = "📝 Text"

    # ---- Top KPI snapshot row ----
    completeness_color = SUCCESS if completeness >= 95 else (WARNING if completeness >= 80 else DANGER)
    dup_color = SUCCESS if duplicate_rows == 0 else WARNING

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("📋", "Total Rows", f"{df.shape[0]:,}", PRIMARY), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("🧮", "Total Columns", df.shape[1], ACCENT), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("✅", "Data Completeness", f"{completeness:.1f}%", completeness_color),
                    unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("🧬", "Duplicate Rows", duplicate_rows, dup_color), unsafe_allow_html=True)

    st.write("")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Data Preview",
        "📊 Auto Dashboards",
        "📈 Charts Gallery",
        "📐 Statistics",
        "🎛️ Custom Analysis",
        "📘 How to Use"
    ])

    # ============== TAB 1: Preview ==============
    with tab1:
        st.subheader("Raw Data Preview")

        with st.expander("🔍 Column Data Types Detected", expanded=False):
            badges_html = "".join(type_badge(c, t) for c, t in col_types.items())
            st.markdown(f'<div style="line-height:2.4;">{badges_html}</div>', unsafe_allow_html=True)

        search_term = st.text_input("🔎 Search anywhere in the data", "",
                                     placeholder="Type any value, name, code etc. to filter rows...")
        if search_term:
            mask = df.astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False)).any(axis=1)
            display_df = df[mask]
        else:
            display_df = df

        st.dataframe(display_df, use_container_width=True)

        m1, m2 = st.columns(2)
        with m1:
            if search_term:
                st.metric("Rows Matching Search", f"{len(display_df):,}")
            else:
                st.metric("Total Rows", f"{df.shape[0]:,}")
        with m2:
            st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")

    # ============== TAB 2: Auto Dashboards ==============
    with tab2:
        st.subheader("🤖 Auto Dashboards")
        dashboard_type = st.selectbox(
            "Select Dashboard Type",
            ["Overview Dashboard", "Correlation Dashboard", "Distribution Dashboard"]
        )

        numeric_cols = safe_numeric_cols(df)
        cat_cols = safe_cat_cols(df)

        if dashboard_type == "Overview Dashboard":
            st.markdown("### 📊 Key Metrics Overview")
            if numeric_cols:
                cols_per_row = 3
                for i in range(0, len(numeric_cols), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(numeric_cols[i:i + cols_per_row]):
                        with cols[j]:
                            mean_val = df[col].mean()
                            std_val = df[col].std()
                            st.metric(
                                label=col,
                                value=f"{mean_val:.2f}" if pd.notna(mean_val) else "N/A",
                                delta=f"±{std_val:.2f}" if pd.notna(std_val) else None
                            )

            col1, col2 = st.columns(2)
            with col1:
                if cat_cols and numeric_cols:
                    g = top_n_group(df.dropna(subset=[cat_cols[0]]), cat_cols[0], numeric_cols[0], "Mean")
                    fig = px.bar(
                        g, x=cat_cols[0], y="value",
                        title=f"Average {numeric_cols[0]} by {cat_cols[0]} (Top 15)",
                        color=cat_cols[0], color_discrete_sequence=COLOR_SEQ, text_auto=".2s"
                    )
                    st.plotly_chart(style_chart(fig), use_container_width=True)
                else:
                    st.info("Need at least one categorical and one numeric column.")
            with col2:
                if numeric_cols:
                    fig = px.histogram(
                        df, x=numeric_cols[0],
                        title=f"Distribution of {numeric_cols[0]}",
                        marginal="box", color_discrete_sequence=COLOR_SEQ
                    )
                    st.plotly_chart(style_chart(fig), use_container_width=True)
                else:
                    st.info("No numeric column found.")

        elif dashboard_type == "Correlation Dashboard":
            st.markdown("### 🔗 Correlation Analysis")
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 1:
                corr_matrix = numeric_df.corr()
                fig = px.imshow(
                    corr_matrix, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r", title="Correlation Matrix Heatmap"
                )
                st.plotly_chart(style_chart(fig, height=550), use_container_width=True)
            else:
                st.warning("Need at least 2 numeric columns for correlation")

        elif dashboard_type == "Distribution Dashboard":
            st.markdown("### 📈 Distributions")
            if numeric_cols:
                sel_cols = st.multiselect("Select columns", numeric_cols, default=numeric_cols[:4])
                for col in sel_cols:
                    fig = px.histogram(df, x=col, title=f"Distribution of {col}",
                                        marginal="box", color_discrete_sequence=COLOR_SEQ)
                    st.plotly_chart(style_chart(fig, height=350), use_container_width=True)
            else:
                st.info("No numeric columns found.")

    # ============== TAB 3: Charts Gallery ==============
    with tab3:
        st.subheader("📈 Interactive Charts Gallery")
        numeric_cols = safe_numeric_cols(df)
        cat_cols = safe_cat_cols(df)

        chart_type = st.selectbox(
            "Chart Type",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart", "Box Plot", "Histogram", "Area Chart"]
        )

        if chart_type == "Bar Chart" and cat_cols and numeric_cols:
            x_axis = st.selectbox("X-axis (Category)", cat_cols)
            y_axis = st.selectbox("Y-axis (Value)", numeric_cols)
            agg = st.selectbox("Aggregation", ["Mean", "Sum", "Count", "Min", "Max"])
            g = top_n_group(df.dropna(subset=[x_axis]), x_axis, y_axis, agg)
            fig = px.bar(g, x=x_axis, y="value", title=f"{agg} of {y_axis} by {x_axis} (Top 15)",
                         color=x_axis, color_discrete_sequence=COLOR_SEQ, text_auto=".2s")
            st.plotly_chart(style_chart(fig), use_container_width=True)

        elif chart_type == "Line Chart" and numeric_cols:
            y_axis = st.multiselect("Select columns for line chart", numeric_cols, default=numeric_cols[:2])
            if y_axis:
                fig = px.line(df, y=y_axis, title="Line Chart", color_discrete_sequence=COLOR_SEQ)
                st.plotly_chart(style_chart(fig), use_container_width=True)

        elif chart_type == "Scatter Plot" and len(numeric_cols) >= 2:
            x_axis = st.selectbox("X-axis", numeric_cols)
            y_axis = st.selectbox("Y-axis", numeric_cols)
            color_by = st.selectbox("Color by", ["None"] + cat_cols) if cat_cols else "None"
            if color_by != "None":
                fig = px.scatter(df, x=x_axis, y=y_axis, color=color_by,
                                  title=f"{y_axis} vs {x_axis}", color_discrete_sequence=COLOR_SEQ, opacity=0.7)
            else:
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}",
                                  color_discrete_sequence=COLOR_SEQ, opacity=0.7)
            st.plotly_chart(style_chart(fig), use_container_width=True)

        elif chart_type == "Pie Chart" and cat_cols:
            pie_col = st.selectbox("Select column for pie chart", cat_cols)
            pie_data = df[pie_col].value_counts().reset_index()
            pie_data.columns = [pie_col, 'count']
            if len(pie_data) > 10:
                top = pie_data.iloc[:10].copy()
                other_sum = pie_data.iloc[10:]['count'].sum()
                top = pd.concat([top, pd.DataFrame({pie_col: ["Other"], "count": [other_sum]})], ignore_index=True)
                pie_data = top
            fig = px.pie(pie_data, values='count', names=pie_col, title=f"Distribution of {pie_col} (Top 10)",
                         color_discrete_sequence=COLOR_SEQ, hole=0.35)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(style_chart(fig), use_container_width=True)

        elif chart_type == "Box Plot" and numeric_cols:
            selected_cols = st.multiselect("Select columns for box plot", numeric_cols, default=numeric_cols[:2])
            if selected_cols:
                fig = px.box(df[selected_cols], title="Box Plot", color_discrete_sequence=COLOR_SEQ)
                st.plotly_chart(style_chart(fig), use_container_width=True)

        elif chart_type == "Histogram" and numeric_cols:
            hist_col = st.selectbox("Select column", numeric_cols)
            bins = st.slider("Number of bins", 10, 100, 30)
            fig = px.histogram(df, x=hist_col, nbins=bins, title=f"Histogram of {hist_col}",
                                marginal="box", color_discrete_sequence=COLOR_SEQ)
            st.plotly_chart(style_chart(fig), use_container_width=True)

        elif chart_type == "Area Chart" and numeric_cols:
            sel = st.multiselect("Select columns", numeric_cols, default=numeric_cols[:3])
            if sel:
                fig = px.area(df, y=sel, title="Area Chart", color_discrete_sequence=COLOR_SEQ)
                st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.info("Selected chart needs different column types than what's available in this data.")

    # ============== TAB 4: Statistics ==============
    with tab4:
        st.subheader("📐 Statistical Analysis")
        st.markdown("### 📊 Summary Statistics")
        st.dataframe(df.describe(), use_container_width=True)

        st.markdown("### 🔍 Missing Values Analysis")
        missing_df = pd.DataFrame({
            'Column': df.columns,
            'Missing Count': df.isnull().sum().values,
            'Missing Percentage': (df.isnull().sum().values / len(df)) * 100
        })
        missing_only = missing_df[missing_df['Missing Count'] > 0]
        if missing_only.empty:
            st.success("🎉 No missing values found in this dataset!")
        else:
            st.dataframe(missing_only, use_container_width=True)

        st.markdown("### 🔢 Unique Values per Column")
        unique_df = pd.DataFrame({
            'Column': df.columns,
            'Unique Values': df.nunique().values,
            'Data Type': df.dtypes.astype(str).values
        })
        st.dataframe(unique_df, use_container_width=True)

    # ============== TAB 5: Custom Analysis ==============
    with tab5:
        st.subheader("🎛️ Custom Analysis Builder")

        # ---- Dynamic filters (crash-safe) ----
        st.markdown("### 🔍 Dynamic Filters")
        filtered_df = df.copy()

        reset_col, _ = st.columns([1, 4])
        with reset_col:
            if st.button("🔄 Reset All Filters"):
                for k in list(st.session_state.keys()):
                    if k.startswith("filter_"):
                        del st.session_state[k]
                st.rerun()

        with st.expander("Show/Hide Filters", expanded=False):
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_data = df[col].dropna()
                    if col_data.empty:
                        st.caption(f"⚠️ {col}: all values missing — skipped")
                        continue
                    min_val, max_val = float(col_data.min()), float(col_data.max())
                    if min_val == max_val:
                        st.caption(f"ℹ️ {col}: constant value ({min_val}) — no filter needed")
                        continue
                    filter_range = st.slider(
                        f"Filter {col}", min_val, max_val, (min_val, max_val), key=f"filter_{col}"
                    )
                    filtered_df = filtered_df[
                        filtered_df[col].isna() |
                        ((filtered_df[col] >= filter_range[0]) & (filtered_df[col] <= filter_range[1]))
                    ]
                elif df[col].nunique(dropna=True) > 0 and df[col].nunique(dropna=True) < 20:
                    unique_vals = df[col].dropna().unique().tolist()
                    selected_vals = st.multiselect(f"Filter {col}", unique_vals, default=unique_vals, key=f"filter_cat_{col}")
                    if selected_vals:
                        filtered_df = filtered_df[filtered_df[col].isin(selected_vals) | filtered_df[col].isna()]

        st.success(f"Filtered Data: {len(filtered_df)} rows out of {len(df)}")

        # ---- Flexible group-by + aggregation builder ----
        st.markdown("### 📊 Build Your Own Chart")
        st.caption("Kisi bhi column ko group-by banao, value column choose karo, aur Count/Sum/Mean/Min/Max me se koi bhi aggregation lagao.")

        all_cols = filtered_df.columns.tolist()
        numeric_cols_f = safe_numeric_cols(filtered_df)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            group_col = st.selectbox("Group By (any column)", all_cols, key="cust_group")
        with c2:
            agg_choice = st.selectbox("Calculation", ["Count", "Sum", "Mean", "Median", "Min", "Max"], key="cust_agg")
        with c3:
            if agg_choice == "Count":
                value_col = group_col  # not used for count
                st.selectbox("Value Column", ["(not needed for Count)"], disabled=True)
            else:
                if numeric_cols_f:
                    value_col = st.selectbox("Value Column (numeric)", numeric_cols_f, key="cust_value")
                else:
                    value_col = None
                    st.warning("No numeric columns available for this calculation.")
        with c4:
            chart_choice = st.selectbox("Chart Type", ["Bar", "Line", "Pie", "Area"], key="cust_chart")

        top_n = st.slider("Show Top N categories (rest grouped as 'Other')", 5, 50, 15, key="cust_topn")

        if group_col and (agg_choice == "Count" or value_col):
            try:
                g = top_n_group(filtered_df.dropna(subset=[group_col]), group_col,
                                 value_col if agg_choice != "Count" else None, agg_choice, n=top_n)
                title = f"{agg_choice} of {value_col if agg_choice != 'Count' else 'records'} by {group_col}"

                if chart_choice == "Bar":
                    fig = px.bar(g, x=group_col, y="value", title=title, color=group_col,
                                 color_discrete_sequence=COLOR_SEQ, text_auto=".2s")
                elif chart_choice == "Line":
                    fig = px.line(g, x=group_col, y="value", title=title, markers=True,
                                  color_discrete_sequence=COLOR_SEQ)
                elif chart_choice == "Pie":
                    fig = px.pie(g, values="value", names=group_col, title=title,
                                 color_discrete_sequence=COLOR_SEQ, hole=0.35)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                else:  # Area
                    fig = px.area(g, x=group_col, y="value", title=title, color_discrete_sequence=COLOR_SEQ)

                st.plotly_chart(style_chart(fig, height=480), use_container_width=True)
                with st.expander("View underlying data"):
                    st.dataframe(g, use_container_width=True)
            except Exception as e:
                st.error(f"Couldn't build chart: {e}")

        # ---- Download filtered data ----
        st.markdown("---")
        st.markdown("### 📥 Export Filtered Data")
        d1, d2 = st.columns(2)
        with d1:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name='filtered_data.csv',
                mime='text/csv',
            )
        with d2:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
            st.download_button(
                label="📥 Download as Excel",
                data=excel_buffer.getvalue(),
                file_name='filtered_data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

    # ============== TAB 6: How to Use ==============
    with tab6:
        st.subheader("📘 Quick Guide")
        st.caption("Yaha har tab ka kaam aur use karne ka tareeka diya gaya hai.")

        guide_items = [
            ("📋 Data Preview", "Apni poori raw data dekho, column types check karo (Numeric/Date/Categorical/Text "
             "badges), search box se kisi bhi value ko turant dhundo."),
            ("📊 Auto Dashboards", "Bina kuch select kiye instant dashboard chahiye? Overview Dashboard se key "
             "metrics aur top chart milenge. Correlation Dashboard numeric columns ke beech relationship dikhata "
             "hai. Distribution Dashboard har numeric column ka spread dikhata hai."),
            ("📈 Charts Gallery", "Bar, Line, Scatter, Pie, Box, Histogram, Area — koi bhi chart type choose karo "
             "aur dropdown se columns set karo, chart turant update ho jayega."),
            ("📐 Statistics", "Summary statistics (mean, std, min, max), missing values report, aur har column "
             "ke unique values ek nazar me."),
            ("🎛️ Custom Analysis", "Sabse powerful tab. Pehle filters lagao (numeric range ya category select karo), "
             "phir koi bhi column group-by karke Count/Sum/Mean/Min/Max nikalo, chart type choose karo, aur "
             "filtered data CSV ya Excel me download karo."),
        ]
        for title, desc in guide_items:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(desc)

        st.info("💡 Tip: Charts ke top-right corner me camera icon se aap kisi bhi chart ko PNG image ke roop "
                "me bhi download kar sakte ho.")

else:
    st.info("👈 Please upload an Excel file from the sidebar to get started!")

    s1, s2, s3 = st.columns(3)
    with s1:
        with st.container(border=True):
            st.markdown("### 📋 Features")
            st.write("Auto-detect data types, interactive dashboards, multiple chart types, statistical analysis.")
    with s2:
        with st.container(border=True):
            st.markdown("### 📊 Supported Charts")
            st.write("Bar, Line, Scatter, Pie, Box, Histogram, Area, and Correlation heatmaps.")
    with s3:
        with st.container(border=True):
            st.markdown("### 🎯 Use Cases")
            st.write("Sales analysis, financial reporting, customer insights, KPI dashboards.")

    st.markdown("### 🚦 How it works")
    h1, h2, h3 = st.columns(3)
    with h1:
        with st.container(border=True):
            st.markdown("**1️⃣ Upload**")
            st.write("Sidebar se apni .xlsx/.xls file upload karo.")
    with h2:
        with st.container(border=True):
            st.markdown("**2️⃣ Explore**")
            st.write("Tabs me dashboards, charts aur stats automatically generate ho jayenge.")
    with h3:
        with st.container(border=True):
            st.markdown("**3️⃣ Export**")
            st.write("Custom Analysis tab se filtered data CSV/Excel me download karo.")

st.markdown("""
<div class="footer-bar">
    🚀 <b>Excel Dashboard Pro</b> — Auto-generate professional dashboards from Excel files
</div>
""", unsafe_allow_html=True)
