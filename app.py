import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Excel Dashboard Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-size: 18px;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Excel to Pro Dashboard Generator")
st.markdown("---")

# Sidebar for upload
with st.sidebar:
    st.header("📁 Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload Excel with 2-50 columns"
    )
    
    if uploaded_file:
        st.success(f"✅ File loaded: {uploaded_file.name}")

# Main content
if uploaded_file:
    # Read Excel file
    df = pd.read_excel(uploaded_file)
    
    # Data overview in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Data Overview")
    st.sidebar.write(f"**Rows:** {df.shape[0]}")
    st.sidebar.write(f"**Columns:** {df.shape[1]}")
    st.sidebar.write(f"**Missing values:** {df.isnull().sum().sum()}")
    
    # Identify column data types
    col_types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_types[col] = "📈 Numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_types[col] = "📅 Date/Time"
        elif pd.api.types.is_categorical_dtype(df[col]) or df[col].nunique() < 10:
            col_types[col] = "🏷️ Categorical"
        else:
            col_types[col] = "📝 Text"
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Data Preview", 
        "📊 Auto Dashboards", 
        "📈 Charts Gallery",
        "📐 Statistics",
        "🎛️ Custom Analysis"
    ])
    
    with tab1:
        st.subheader("Raw Data Preview")
        
        # Column type display
        with st.expander("🔍 Column Data Types Detected"):
            for col, col_type in col_types.items():
                st.write(f"**{col}**: {col_type}")
        
        st.dataframe(df, use_container_width=True)
        
        # Basic info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", df.shape[0])
        with col2:
            st.metric("Total Columns", df.shape[1])
        with col3:
            st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    with tab2:
        st.subheader("🤖 AI-Powered Auto Dashboards")
        
        # Dashboard type selector
        dashboard_type = st.selectbox(
            "Select Dashboard Type",
            ["Overview Dashboard", "Correlation Dashboard", "Distribution Dashboard", "Time Series Dashboard"]
        )
        
        if dashboard_type == "Overview Dashboard":
            st.markdown("### 📊 Key Metrics Overview")
            
            # Create metrics for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                cols_per_row = 3
                for i in range(0, len(numeric_cols), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(numeric_cols[i:i+cols_per_row]):
                        with cols[j]:
                            st.metric(
                                label=col,
                                value=f"{df[col].mean():.2f}",
                                delta=f"±{df[col].std():.2f}"
                            )
            
            # Auto charts based on data types
            col1, col2 = st.columns(2)
            
            with col1:
                # First numeric vs categorical
                cat_cols = df.select_dtypes(include=['object']).columns.tolist()
                if cat_cols and numeric_cols:
                    fig = px.bar(
                        df, x=cat_cols[0], y=numeric_cols[0],
                        title=f"{numeric_cols[0]} by {cat_cols[0]}",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Distribution of first numeric column
                if numeric_cols:
                    fig = px.histogram(
                        df, x=numeric_cols[0], 
                        title=f"Distribution of {numeric_cols[0]}",
                        template="plotly_white",
                        marginal="box"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        elif dashboard_type == "Correlation Dashboard":
            st.markdown("### 🔗 Correlation Analysis")
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) > 1:
                corr_matrix = numeric_df.corr()
                fig = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="RdBu",
                    title="Correlation Matrix Heatmap"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Need at least 2 numeric columns for correlation")
    
    with tab3:
        st.subheader("📈 Interactive Charts Gallery")
        
        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            chart_type = st.selectbox(
                "Chart Type",
                ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart", "Box Plot", "Histogram", "Area Chart"]
            )
        with col2:
            color_theme = st.selectbox(
                "Color Theme",
                ["plotly", "plotly_white", "ggplot2", "seaborn", "simple_white"]
            )
        
        # Chart configuration
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if chart_type == "Bar Chart" and cat_cols and numeric_cols:
            x_axis = st.selectbox("X-axis (Category)", cat_cols)
            y_axis = st.selectbox("Y-axis (Value)", numeric_cols)
            fig = px.bar(df, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}", 
                        template=color_theme, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "Line Chart" and numeric_cols:
            y_axis = st.multiselect("Select columns for line chart", numeric_cols, default=numeric_cols[:2])
            if y_axis:
                fig = px.line(df, y=y_axis, title="Line Chart", template=color_theme)
                st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Scatter Plot" and len(numeric_cols) >= 2:
            x_axis = st.selectbox("X-axis", numeric_cols)
            y_axis = st.selectbox("Y-axis", numeric_cols)
            color_by = st.selectbox("Color by", ["None"] + cat_cols) if cat_cols else "None"
            
            if color_by != "None":
                fig = px.scatter(df, x=x_axis, y=y_axis, color=color_by, 
                               title=f"{y_axis} vs {x_axis}", template=color_theme)
            else:
                fig = px.scatter(df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}", 
                               template=color_theme)
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Pie Chart" and cat_cols:
            pie_col = st.selectbox("Select column for pie chart", cat_cols)
            pie_data = df[pie_col].value_counts().reset_index()
            pie_data.columns = [pie_col, 'count']
            fig = px.pie(pie_data, values='count', names=pie_col, title=f"Distribution of {pie_col}",
                        template=color_theme)
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Box Plot" and numeric_cols:
            selected_cols = st.multiselect("Select columns for box plot", numeric_cols, default=numeric_cols[:2])
            if selected_cols:
                fig = px.box(df[selected_cols], title="Box Plot", template=color_theme)
                st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Histogram" and numeric_cols:
            hist_col = st.selectbox("Select column", numeric_cols)
            bins = st.slider("Number of bins", 10, 100, 30)
            fig = px.histogram(df, x=hist_col, nbins=bins, title=f"Histogram of {hist_col}",
                             template=color_theme, marginal="box")
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Area Chart" and numeric_cols:
            fig = px.area(df, y=numeric_cols[:3], title="Area Chart", template=color_theme)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("📐 Statistical Analysis")
        
        # Summary statistics
        st.markdown("### 📊 Summary Statistics")
        st.dataframe(df.describe(), use_container_width=True)
        
        # Missing values analysis
        st.markdown("### 🔍 Missing Values Analysis")
        missing_df = pd.DataFrame({
            'Column': df.columns,
            'Missing Count': df.isnull().sum(),
            'Missing Percentage': (df.isnull().sum() / len(df)) * 100
        })
        st.dataframe(missing_df[missing_df['Missing Count'] > 0], use_container_width=True)
        
        # Unique values count
        st.markdown("### 🔢 Unique Values per Column")
        unique_df = pd.DataFrame({
            'Column': df.columns,
            'Unique Values': df.nunique(),
            'Data Type': df.dtypes.astype(str)
        })
        st.dataframe(unique_df, use_container_width=True)
    
    with tab5:
        st.subheader("🎛️ Custom Analysis Builder")
        
        # Dynamic filter system
        st.markdown("### 🔍 Dynamic Filters")
        
        # Create filters for each column
        filtered_df = df.copy()
        
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                filter_range = st.slider(
                    f"Filter {col}",
                    min_val, max_val,
                    (min_val, max_val),
                    key=f"filter_{col}"
                )
                filtered_df = filtered_df[
                    (filtered_df[col] >= filter_range[0]) & 
                    (filtered_df[col] <= filter_range[1])
                ]
            elif df[col].nunique() < 20:
                unique_vals = df[col].dropna().unique().tolist()
                selected_vals = st.multiselect(
                    f"Filter {col}",
                    unique_vals,
                    default=unique_vals,
                    key=f"filter_cat_{col}"
                )
                if selected_vals:
                    filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
        
        st.markdown("---")
        st.success(f"Filtered Data: {len(filtered_df)} rows out of {len(df)}")
        
        # Custom chart on filtered data
        st.markdown("### 📊 Custom Chart on Filtered Data")
        
        col1, col2 = st.columns(2)
        with col1:
            chart_custom_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Heatmap"])
        with col2:
            if filtered_df.select_dtypes(include=[np.number]).columns.tolist():
                agg_func = st.selectbox("Aggregation", ["Mean", "Sum", "Count", "Min", "Max"])
        
        if chart_custom_type == "Bar" and filtered_df.select_dtypes(include=['object']).columns.tolist():
            cat_col = st.selectbox("Category Column", filtered_df.select_dtypes(include=['object']).columns)
            num_col = st.selectbox("Value Column", filtered_df.select_dtypes(include=[np.number]).columns)
            
            if agg_func == "Mean":
                plot_df = filtered_df.groupby(cat_col)[num_col].mean().reset_index()
            elif agg_func == "Sum":
                plot_df = filtered_df.groupby(cat_col)[num_col].sum().reset_index()
            else:
                plot_df = filtered_df.groupby(cat_col).size().reset_index(name='count')
            
            fig = px.bar(plot_df, x=cat_col, y=plot_df.columns[1], title=f"{agg_func} of {num_col} by {cat_col}")
            st.plotly_chart(fig, use_container_width=True)
        
        # Download filtered data
        st.markdown("---")
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name='filtered_data.csv',
            mime='text/csv',
        )
else:
    # Show instructions when no file uploaded
    st.info("👈 Please upload an Excel file from the sidebar to get started!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 📋 Features
        - Auto-detect data types
        - Interactive dashboards
        - Multiple chart types
        - Statistical analysis
        """)
    with col2:
        st.markdown("""
        ### 📊 Supported Charts
        - Bar/Line/Scatter
        - Pie/Box/Histogram
        - Correlation heatmaps
        - Time series
        """)
    with col3:
        st.markdown("""
        ### 🎯 Use Cases
        - Sales analysis
        - Financial reporting
        - Customer insights
        - KPI dashboards
        """)

st.markdown("---")
st.markdown("🚀 **Excel Dashboard Pro** - Auto-generate professional dashboards from Excel files")
