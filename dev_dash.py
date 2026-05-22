import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Ultimate Market Intelligence", layout="wide", page_icon="🏢")
st.title("🏢 Ultimate Real Estate Market Intelligence")
st.markdown("Dynamic cross-filtering dashboard with real-time aggregation.")

# ---------------------------------------------------------
# 2. DATA LOADING & PREPARATION (CACHED)
# ---------------------------------------------------------
@st.cache_data
def load_and_prepare_data(file_path):
    # 1. Load Data
    # Replace this with your actual combined merged dataset path
    parquet_path = "combined_df_2020.parquet"
    df = pd.read_parquet(parquet_path)
    
    # 2. Market Mappings
    market_mappings = {
        'direct_areas': [
            "Al Barsha South Fourth", "Business Bay", "Al Merkadh", "Burj Khalifa",
            "Hadaeq Sheikh Mohammed Bin Rashid", "Al Khairan First", "Wadi Al Safa 5",
            "Al Thanyah Fifth", "Al Barshaa South Third", "Jabal Ali First",
            "Madinat Al Mataar", "Madinat Dubai Almelaheyah", "Me'Aisem First",
            "Al Hebiah Fourth", "Al Barsha South Fifth", "Al Hebiah First",
            "Nadd Hessa", "Palm Jumeirah", "Al Barshaa South Second",
            "Al Yelayiss 2", "Al Warsan First", "Marsa Dubai"
        ],
        'proxies': {
            'G1': ['Wadi Al Safa 4', 'Al Kifaf'],
            'G2': ['Dubai Investment Park First', 'Wadi Al Safa 7'],
            'G3': ['Warsan Fourth', 'Jabal Ali'],
            'G4': ['Zaabeel Second', 'Zaabeel First'],
            'G5': ['Saih Shuaib 2', 'Nad Al Shiba First'],
            'Proxy1': ['Al Barsha South Fourth', 'Al Barshaa South Third', 'Al Yelayiss 2'],
            'Proxy2': ['Bukadra', 'Madinat Dubai Almelaheyah'],
            'Proxy3': ['Jabal Ali First', "Me'Aisem First"]
        }
    }
    
    # Ensure this line is UNCOMMENTED (no # at the start) so the dictionary is created!
    proxy_map = {area: group for group, areas in market_mappings['proxies'].items() for area in areas}

    # 1. Update the mapping function to collect ALL matches in a list
    def map_segments(area):
        segments = []
        
        # Add as a direct area if it's in the list
        if area in market_mappings['direct_areas']:
            segments.append(area)
            
        # Also add as a proxy group if it belongs to one
        if area in proxy_map:
            segments.append(proxy_map[area])
            
        # If it matched neither, label it 'Other'
        if len(segments) == 0:
            return ['Other']
            
        return segments

    # 2. Apply the function and use .explode() to split the lists into separate rows
    df['market_segment'] = df['area_name_en'].apply(map_segments)
    df = df.explode('market_segment')

    # 3. Drop 'Other' as usual
    df = df[df['market_segment'] != 'Other'].copy()

    # 3. Format Dates & Durations
    df['instance_date'] = pd.to_datetime(df['instance_date'], errors='coerce')
    df['project_start_date'] = pd.to_datetime(df['project_start_date'], errors='coerce')
    df['month_year'] = df['instance_date'].dt.strftime('%b-%Y')
    
    # First transaction date per project
    proj_first_trans = df.groupby('project_name_en')['instance_date'].min().reset_index()
    proj_first_trans.rename(columns={'instance_date': 'first_trans_date'}, inplace=True)
    df = df.merge(proj_first_trans, on='project_name_en', how='left')
    df['start_to_trans_days'] = (df['first_trans_date'] - df['project_start_date']).dt.days.fillna(0)
    
    # Ensure units/prices are numeric
    df['no_of_units'] = pd.to_numeric(df['no_of_units'], errors='coerce').fillna(0)
    df['meter_sale_price'] = pd.to_numeric(df['meter_sale_price'], errors='coerce').fillna(0)
    
    # Drop rows without a developer
    df = df.dropna(subset=['developer_name_en'])
    
    # ---------------------------------------------------------
    # SAVE AS PARQUET (As Requested)
    # ---------------------------------------------------------
    #parquet_path = "processed_market_data.parquet"
    #parquet_path_fil = "processed_market_data.parquet"
    #df.to_parquet(parquet_path_fil, index=False)
    
    return df

# Load the data (Update the path to your actual CSV or Parquet file)
# If you already have the parquet, you can change the loader above to pd.read_parquet()
try:
    df_main = load_and_prepare_data("combined_df_2020.parquet")
    st.sidebar.success("✅ Data Loaded & Saved to Parquet!")
except Exception as e:
    st.error(f"Error loading data. Please check your file path. Details: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. DYNAMIC CROSS-FILTERING ENGINE (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.header("🎯 Dynamic Filters")

# We apply filters step-by-step to cascade the available options
filtered_df = df_main #.copy()


# Filter 1: Market Segment (Checkbox Loop inside Expander)
# Filter 1: Market Segment (Checkbox Loop inside Expander)
with st.sidebar.expander("📍 Market Segments"):
    unique_segs = sorted(filtered_df['market_segment'].unique())
    selected_segs = []

    # 1. Add a master toggle checkbox
    select_all = st.checkbox("Select / Deselect All", value=True)

    # Create a checkbox for every unique segment
    for seg in unique_segs:
        # 2. Bind the default value to the master toggle
        if st.checkbox(seg, value=select_all):
            selected_segs.append(seg)

# Apply filter
if selected_segs:
    filtered_df = filtered_df[filtered_df['market_segment'].isin(selected_segs)]
else:
    # 3. If nothing is selected, clear the dataframe so the dashboard reflects the deselection
    filtered_df = filtered_df.iloc[0:0]

# Filter 2: Developer
devs = st.sidebar.multiselect("Developer", sorted(filtered_df['developer_name_en'].unique()))
if devs: filtered_df = filtered_df[filtered_df['developer_name_en'].isin(devs)]
    
# Filter 3: Project
projs = st.sidebar.multiselect("Project", sorted(filtered_df['project_name_en'].dropna().unique()))
if projs: filtered_df = filtered_df[filtered_df['project_name_en'].isin(projs)]

# Filter 4: Reg Type
regs = st.sidebar.multiselect("Reg Type", sorted(filtered_df['reg_type_en'].dropna().unique()))
if regs: filtered_df = filtered_df[filtered_df['reg_type_en'].isin(regs)]

# Filter 5: Room Type
rooms = st.sidebar.multiselect("Room Type", sorted(filtered_df['rooms_en'].dropna().unique()))
if rooms: filtered_df = filtered_df[filtered_df['rooms_en'].isin(rooms)]

# Filter 6: Month-Year (Sorted Chronologically)
sorted_months = sorted(filtered_df['month_year'].dropna().unique(), key=lambda x: pd.to_datetime(x, format='%b-%Y'))
months = st.sidebar.multiselect("Month-Year", sorted_months)
if months: filtered_df = filtered_df[filtered_df['month_year'].isin(months)]

# Filter 6: Transaction Type (Conditional)
if 'trans_group_en' in filtered_df.columns:
    trans_types = st.sidebar.multiselect("Transaction Type", sorted(filtered_df['trans_group_en'].dropna().unique()))
    if trans_types:
        filtered_df = filtered_df[filtered_df['trans_group_en'].isin(trans_types)]

# Filter 7: Procedure Name (Conditional)
if 'procedure_name_en' in filtered_df.columns:
    procedures = st.sidebar.multiselect("Procedure Name", sorted(filtered_df['procedure_name_en'].dropna().unique()))
    if procedures:
        filtered_df = filtered_df[filtered_df['procedure_name_en'].isin(procedures)]

# ---------------------------------------------------------
# 4. KPI METRICS
# ---------------------------------------------------------
if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# Calculations
#total_trans = len(filtered_df)
total_trans = filtered_df['transaction_id'].nunique()
#avg_price = filtered_df['meter_sale_price'].median()
avg_price = filtered_df.drop_duplicates(subset=['transaction_id'])['meter_sale_price'].median()
unique_projs = filtered_df['project_name_en'].nunique()
total_units = filtered_df.drop_duplicates(subset=['project_number'])['no_of_units'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transactions", f"{total_trans:,}")
col2.metric("Median Price (AED/Sqm)", f"{avg_price:,.0f}")
col3.metric("Unique Projects", f"{unique_projs:,}")
col4.metric("Total Units Launched", f"{total_units:,.0f}")

st.markdown("---")

# ---------------------------------------------------------
# 5. DASHBOARD TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Market Overview", 
        "🏢 Project Deep Dive", 
        "📊 Data Table", 
        "⭐ Developer Matrix (New!)",
        "👯 Duplicate Analysis",
        "📋 Procedures & Types" # <--- ADD TAB 6 HERE
    ])

# --- TAB 1: MARKET OVERVIEW ---
with tab1:
    st.subheader("Price & Volume Seasonality Trend")
    # Aggregate data for dual-axis chart
    season_agg = filtered_df.groupby('month_year').agg(
        volume=('transaction_id', 'count'),
        median_price=('meter_sale_price', 'median')
    ).reset_index()
    # Sort chronologically
    season_agg['sort_date'] = pd.to_datetime(season_agg['month_year'], format='%b-%Y')
    season_agg = season_agg.sort_values('sort_date')
    
    fig_season = make_subplots(specs=[[{"secondary_y": True}]])
    fig_season.add_trace(
        go.Bar(x=season_agg['month_year'], y=season_agg['volume'], name="Volume", opacity=0.4, marker_color='slategray'),
        secondary_y=False,
    )
    fig_season.add_trace(
        go.Scatter(x=season_agg['month_year'], y=season_agg['median_price'], name="Median Price", mode='lines+markers', line=dict(color='royalblue', width=3)),
        secondary_y=True,
    )
    fig_season.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
    st.plotly_chart(fig_season, width="stretch")

    
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Segment Performance Heatmap")
        
        # MEMORY FIX: Use filtered_df directly without pre-sorting
        fig_heat = px.density_heatmap(
            filtered_df, 
            x="month_year", 
            y="market_segment", 
            z="meter_sale_price", 
            histfunc="avg", 
            color_continuous_scale="Viridis",
            category_orders={"month_year": sorted_months} # <--- Forces chronological order cleanly
        )
        fig_heat.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_heat, width="stretch")
        
    with colB:
        st.subheader("Top Developer Activity Heatmap")
        
        # Get top 15 devs by transaction volume
        top_devs = filtered_df['developer_name_en'].value_counts().nlargest(15).index
        
        # MEMORY FIX: Slice directly from filtered_df
        dev_heat_df = filtered_df[filtered_df['developer_name_en'].isin(top_devs)]
        
        fig_dev_heat = px.density_heatmap(
            dev_heat_df, 
            x="month_year", 
            y="developer_name_en", 
            color_continuous_scale="Blues",
            category_orders={"month_year": sorted_months} # <--- Forces chronological order cleanly
        )
        fig_dev_heat.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_dev_heat, width="stretch")


# --- TAB 2: PROJECT DEEP DIVE ---
with tab2:
    colC, colD = st.columns(2)
    
    with colC:
        st.subheader("Reg Type vs Median Prices (Top 20 Projects)")
        # Top 20 projects by transaction count
        top_projs = filtered_df['project_name_en'].value_counts().nlargest(20).index
        reg_df = filtered_df[filtered_df['project_name_en'].isin(top_projs)]
        reg_agg = reg_df.groupby(['project_name_en', 'reg_type_en'])['meter_sale_price'].median().reset_index()
        
        fig_reg = px.bar(reg_agg, x='project_name_en', y='meter_sale_price', color='reg_type_en', barmode='group')
        fig_reg.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="", legend_title="Reg Type")
        st.plotly_chart(fig_reg, width="stretch")
        
    with colD:
        st.subheader("Launch vs First Transaction Gap (Days)")
        dur_df = filtered_df.drop_duplicates(subset=['project_name_en']).nlargest(15, 'start_to_trans_days')
        fig_dur = px.bar(dur_df, x='start_to_trans_days', y='project_name_en', orientation='h', color_discrete_sequence=['#8b5cf6'])
        fig_dur.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_dur, width="stretch")

    st.subheader("Room-wise Price Trend")
    room_agg = filtered_df.groupby(['month_year', 'rooms_en']).agg(
        median_price=('meter_sale_price', 'median')
    ).reset_index()
    room_agg['sort_date'] = pd.to_datetime(room_agg['month_year'], format='%b-%Y')
    room_agg = room_agg.sort_values('sort_date')
    
    fig_room = px.line(room_agg, x='month_year', y='median_price', color='rooms_en', markers=True)
    fig_room.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
    st.plotly_chart(fig_room,width="stretch")

    # --- NEW PROJECT TIMELINE & VOLUME SECTION ---
    st.markdown("---")
    st.subheader("📅 Project Timeline & Volume Analysis (10 Newest Projects)")
    
    # 1. Filter for the 10 most recently started projects
    recent_projects = filtered_df.groupby('project_name_en')['project_start_date'].min().sort_values(ascending=False).head(10).index
    recent_df = filtered_df[filtered_df['project_name_en'].isin(recent_projects)]
    
    # 2. Prepare Aggregated Data for Plots using ONLY the newest projects
    ts_agg = recent_df.groupby(['month_year', 'project_name_en']).agg(
        median_price=('meter_sale_price', 'median'),
        trans_count=('transaction_id', 'count')
    ).reset_index()
    
    # Sort properly by time
    ts_agg['sort_date'] = pd.to_datetime(ts_agg['month_year'], format='%b-%Y')
    ts_agg = ts_agg.sort_values('sort_date')
    
    col_ts1, col_ts2 = st.columns(2)
    
    with col_ts1:
        st.markdown("**Price Trend (Recent Launches)**")
        fig_ts = px.line(
            ts_agg, x='month_year', y='median_price', color='project_name_en', 
            markers=True, labels={'month_year': 'Month', 'median_price': 'Median Price', 'project_name_en': 'Project Name'}
        )
        fig_ts.update_layout(margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified")
        st.plotly_chart(fig_ts, width="stretch")
        
    with col_ts2:
        st.markdown("**Transaction Volume (Recent Launches)**")
        fig_stack = px.bar(
            ts_agg, x='month_year', y='trans_count', color='project_name_en',
            labels={'month_year': 'Month', 'trans_count': 'Count', 'project_name_en': 'Project Name'}
        )
        fig_stack.update_layout(margin=dict(l=0, r=0, t=10, b=0), barmode='stack')
        st.plotly_chart(fig_stack, width="stretch")
    
    # 3. Granular Project Data Table
    st.markdown("**📋 Project Start Dates & Core Metrics**")
    
    # Grouping to get the start date alongside metrics (Using ALL filtered data for the table)
    proj_table = filtered_df.groupby('project_name_en').agg(
        start_date=('project_start_date', 'min'), 
        total_trans=('transaction_id', 'count'),
        median_price=('meter_sale_price', 'median')
    ).reset_index()
    
    # NEW: Extract the Launch Year as its own column
    proj_table['launch_year'] = proj_table['start_date'].dt.strftime('%Y').fillna("Unknown")
    
    # Format the datetime into a clean string (e.g., "15 Jan 2020")
    proj_table['start_date'] = proj_table['start_date'].dt.strftime('%d %b %Y').fillna("Unknown")
    proj_table = proj_table.sort_values('total_trans', ascending=False)
    
    st.dataframe(
        proj_table, 
        width="stretch",
        hide_index=True,
        column_config={
            "project_name_en": "Project Name",
            "launch_year": "Launch Year", # <--- NEW COLUMN
            "start_date": "Project Start Date",
            "total_trans": st.column_config.NumberColumn("Total Transactions", format="%d"),
            "median_price": st.column_config.NumberColumn("Median Price (AED/Sqm)", format="AED %.2f")
        }
    )


# --- TAB 3: DATA TABLE ---
# --- TAB 3: DATA TABLE ---
    with tab3:
        st.subheader("Granular Data View")
        
        # 1. Create a dictionary to map readable names to your raw column names
        group_options = {
            "Developer": "developer_name_en",
            "Market Segment": "market_segment",
            "Project": "project_name_en", 
            "Reg Type": "reg_type_en",
            "Room Type": "rooms_en",
            "Month-Year": "month_year"
        }
        
        # 2. Create a dynamic multiselect specifically for grouping the table
        selected_groups = st.multiselect(
            "Select Columns to Group By:",
            options=list(group_options.keys()),
            default=["Project", "Room Type"] # Starts with these selected by default
        )
        
        # 3. Only calculate and show the table if at least one column is selected
        if not selected_groups:
            st.info("👆 Please select at least one column above to generate the table.")
        else:
            # Get the actual database column names based on the user's selection
            groupby_cols = [group_options[name] for name in selected_groups]
            
            # 4. Group dynamically using the selected columns!
            table_agg = filtered_df.groupby(groupby_cols).agg(
                median_price=('meter_sale_price', 'median'),
                transaction_count=('transaction_id', 'count')
            ).reset_index().sort_values(by='transaction_count', ascending=False)
            
            # 5. Render the table
            st.dataframe(
                table_agg, 
                width="stretch", 
                height=600,
                column_config={
                    "median_price": st.column_config.NumberColumn(
                        "Median Price", 
                        format="AED %.2f"
                    ),
                    "transaction_count": st.column_config.NumberColumn(
                        "Transaction Count", 
                        format="%d"
                    )
                }
            )
# --- TAB 4: NEW EXTRA FEATURE (DEVELOPER MATRIX) ---
with tab4:
    st.subheader("⭐ Strategic Developer Matrix")
    st.markdown("Analyze developers by identifying who pushes high **volumes**, who commands **premium prices**, and the **scale** of their project unit launches.")
    
    # 1. Calculate transactions and price (dropping duplicate transaction IDs)# 1. Slice ONLY the columns we need before dropping duplicates to save RAM!
    matrix_agg = filtered_df[['transaction_id', 'developer_name_en', 'meter_sale_price']].drop_duplicates(subset=['transaction_id']).groupby('developer_name_en').agg(
        median_price=('meter_sale_price', 'median'),
        total_transactions=('transaction_id', 'count')
    ).reset_index()

    # 2. Slice ONLY the columns we need here too!
    units_agg = filtered_df[['project_number', 'developer_name_en', 'no_of_units']].drop_duplicates(subset=['project_number']).groupby('developer_name_en')['no_of_units'].sum().reset_index()
    units_agg.rename(columns={'no_of_units': 'total_units_launched'}, inplace=True)

    # 3. Merge them together to build the matrix!
    matrix_agg = matrix_agg.merge(units_agg, on='developer_name_en')

    # Filter out small data for a cleaner chart
    matrix_agg = matrix_agg[matrix_agg['total_transactions'] > 5]
    
    fig_matrix = px.scatter(
        matrix_agg, 
        x="total_transactions", 
        y="median_price", 
        size="total_units_launched", 
        color="developer_name_en",
        hover_name="developer_name_en",
        size_max=60,
        labels={
            "total_transactions": "Transaction Volume (Sales Speed)",
            "median_price": "Median Price AED/Sqm (Premium Status)",
            "total_units_launched": "Scale (Total Units)"
        }
    )
    
    # Add quadrant lines based on median values
    x_mid = matrix_agg['total_transactions'].median()
    y_mid = matrix_agg['median_price'].median()
    
    fig_matrix.add_hline(y=y_mid, line_dash="dot", line_color="gray", opacity=0.5)
    fig_matrix.add_vline(x=x_mid, line_dash="dot", line_color="gray", opacity=0.5)
    
    fig_matrix.update_layout(height=600, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_matrix, width="stretch")


# --- TAB 5: DUPLICATE ANALYSIS ---
    with tab5:
        st.subheader("👯 Duplicated Transactions Analysis")
        st.markdown("This tab isolates transactions that appear multiple times (due to mapping to both a Direct Area and a Proxy Group) to help audit the overlap.")

        # 1. Isolate the duplicated transactions using transaction_id
        # keep=False ensures we keep ALL copies of the duplicate (the original and the clone)
        dup_mask = filtered_df.duplicated(subset=['transaction_id'], keep=False)
        dup_df = filtered_df[dup_mask].sort_values(by='transaction_id').copy()

        if dup_df.empty:
            st.success("No duplicated transactions found in the current filtered dataset! 🎉")
        else:
            unique_dup_count = dup_df['transaction_id'].nunique()
            st.info(f"**Found {unique_dup_count:,} unique transactions** that were duplicated, resulting in {len(dup_df):,} total rows.")

            # 2. Dynamic Table for Duplicates
            st.markdown("### 🔍 Raw Duplicate Viewer")
            st.markdown("Sort by `transaction_id` to see exactly how and why a transaction was split into multiple segments.")
            
            # Set up columns to select
            available_cols = list(dup_df.columns)
            default_cols = ['transaction_id', 'market_segment', 'area_name_en', 'project_name_en', 'meter_sale_price']
            
            selected_dup_cols = st.multiselect(
                "Select columns to view for the duplicates:", 
                options=available_cols,
                default=[col for col in default_cols if col in available_cols],
                key="dup_table_cols" # Unique key so it doesn't conflict with Tab 3
            )
            
            if selected_dup_cols:
                # Force transaction_id to always be the first column for clarity
                if 'transaction_id' not in selected_dup_cols:
                    selected_dup_cols.insert(0, 'transaction_id')
                
                st.dataframe(
                    dup_df[selected_dup_cols],
                    width="stretch",
                    height=400,
                    hide_index=True
                )
            
            # 3. Visualizations to explain the duplicates
            st.markdown("### 📊 Duplicate Overlap Analytics")
            colX, colY = st.columns(2)
            
            with colX:
                st.markdown("**Which Market Segments share the most duplicates?**")
                # Count how many times each segment appears in the duplicates list
                seg_counts = dup_df['market_segment'].value_counts().reset_index()
                seg_counts.columns = ['Market Segment', 'Row Count']
                
                fig_dup_seg = px.bar(
                    seg_counts.head(15), 
                    x='Row Count', 
                    y='Market Segment',
                    orientation='h',
                    color='Market Segment'
                )
                fig_dup_seg.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_dup_seg, width="stretch")
                
            with colY:
                st.markdown("**Duplicate Transaction Volume over Time**")
                # Count unique duplicated transactions per month
                time_counts = dup_df.groupby('month_year')['transaction_id'].nunique().reset_index()
                time_counts['sort_date'] = pd.to_datetime(time_counts['month_year'], format='%b-%Y')
                time_counts = time_counts.sort_values('sort_date')
                
                fig_dup_time = px.bar(
                    time_counts,
                    x='month_year',
                    y='transaction_id',
                    labels={'transaction_id': 'Unique Duplicated Transactions', 'month_year': 'Month'},
                    color_discrete_sequence=['#ef4444'] # Red to indicate duplicates
                )
                fig_dup_time.update_layout(margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_dup_time, width="stretch")
# --- TAB 6: PROCEDURES & TYPES ---
    with tab6:
        st.subheader("📋 Transaction Types & Procedures")
        st.markdown("Breakdown of real estate activities by primary transaction type and specific procedure classifications.")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            if 'trans_group_en' in filtered_df.columns:
                st.markdown("**Volume by Transaction Type**")
                trans_agg = filtered_df['trans_group_en'].value_counts().reset_index()
                trans_agg.columns = ['Transaction Type', 'Count']
                
                fig_trans = px.pie(
                    trans_agg, 
                    names='Transaction Type', 
                    values='Count',
                    hole=0.4, # Makes it a donut chart
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_trans.update_layout(margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_trans, width="stretch")
            else:
                st.info("ℹ️ The column 'trans_group_en' is not present in the current dataset.")
                
        with col_t2:
            if 'procedure_name_en' in filtered_df.columns:
                st.markdown("**Top 10 Procedures by Volume**")
                proc_agg = filtered_df['procedure_name_en'].value_counts().nlargest(10).reset_index()
                proc_agg.columns = ['Procedure Name', 'Count']
                
                fig_proc = px.bar(
                    proc_agg,
                    x='Count',
                    y='Procedure Name',
                    orientation='h',
                    color='Procedure Name'
                )
                fig_proc.update_layout(
                    showlegend=False, 
                    margin=dict(l=0, r=0, t=10, b=0), 
                    yaxis={'categoryorder':'total ascending'}
                )
                st.plotly_chart(fig_proc, width="stretch")
            else:
                st.info("ℹ️ The column 'procedure_name_en' is not present in the current dataset.")
