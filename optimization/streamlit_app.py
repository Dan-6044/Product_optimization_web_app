import os
import sys
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import duckdb
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "product_optimization.settings")
django.setup()

# Import your Django model after setting up Django
from optimization.models import OptimizationData  # Adjust as necessary

#######################################
# PAGE SETUP
#######################################

st.set_page_config(page_title="Sales Dashboard", page_icon=":bar_chart:", layout="wide")
st.title("Sales Streamlit Dashboard")
st.markdown("_Prototype v0.4.1_")

# Load data from the OptimizationData model
@st.cache_data
def load_data():
    optimization_data = OptimizationData.objects.all()  # Fetch all instances from the database
    return optimization_data

# Function to read the uploaded Excel file
def read_uploaded_file(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"Error reading the Excel file: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

# Get the uploaded files from the model
optimization_data_list = load_data()

# Initialize an empty DataFrame
df = pd.DataFrame()

# Display a preview of the uploaded files and their contents
with st.expander("Uploaded Files Preview"):
    for optimization_data in optimization_data_list:
        st.subheader(optimization_data.file.name)
        df = read_uploaded_file(optimization_data.file.path)  # Read each uploaded file
        st.dataframe(df)  # Show the DataFrame in Streamlit

        # Log the columns of the DataFrame for debugging
        st.write("Columns in the DataFrame:", df.columns.tolist())

# Define months for analysis
all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

#######################################
# VISUALIZATION METHODS
#######################################

def plot_metric(label, value, prefix="", suffix="", show_graph=False, color_graph=""):
    fig = go.Figure()
    fig.add_trace(
        go.Indicator(
            value=value,
            gauge={"axis": {"visible": False}},
            number={"prefix": prefix, "suffix": suffix, "font.size": 28},
            title={"text": label, "font": {"size": 24}},
        )
    )
    if show_graph:
        fig.add_trace(
            go.Scatter(
                y=random.sample(range(0, 101), 30),
                hoverinfo="skip",
                fill="tozeroy",
                fillcolor=color_graph,
                line={"color": color_graph},
            )
        )

    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)
    fig.update_layout(margin=dict(t=30, b=0), showlegend=False, plot_bgcolor="rgba(0, 0, 0, 0)", height=100)  # No background color
    st.plotly_chart(fig, use_container_width=True)

def plot_gauge(indicator_number, indicator_color, indicator_suffix, indicator_title, max_bound):
    fig = go.Figure(
        go.Indicator(
            value=indicator_number,
            mode="gauge+number",
            domain={"x": [0, 1], "y": [0, 1]},
            number={"suffix": indicator_suffix, "font.size": 26},
            gauge={"axis": {"range": [0, max_bound], "tickwidth": 1}, "bar": {"color": indicator_color}},
            title={"text": indicator_title, "font": {"size": 28}},
        )
    )
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10, pad=8), plot_bgcolor="rgba(0, 0, 0, 0)")  # No background color
    st.plotly_chart(fig, use_container_width=True)

def plot_top_right():
    sales_data = duckdb.sql(
        f"""
        -- Query to retrieve sales data for the year 2023
        WITH sales_data AS (
            UNPIVOT (
                SELECT Scenario, business_unit, {','.join(all_months)}
                FROM df
                WHERE Year='2023'
                AND Account='Sales'
            )
            ON {','.join(all_months)}
            INTO NAME month
            VALUE sales
        ),
        aggregated_sales AS (
            SELECT Scenario, business_unit, SUM(sales) AS sales
            FROM sales_data
            GROUP BY Scenario, business_unit
        )
        SELECT * FROM aggregated_sales
        """
    ).df()

    fig = px.bar(
        sales_data,
        x="business_unit",
        y="sales",
        color="Scenario",
        barmode="group",
        text_auto=".2s",
        title="Sales for Year 2023",
        height=400,
    )
    fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig.update_layout(plot_bgcolor="rgba(0, 0, 0, 0)")  # No background color
    st.plotly_chart(fig, use_container_width=True)

def plot_bottom_left():
    sales_data = duckdb.sql(
        f"""
        -- Query to retrieve monthly sales for the Software business unit in 2023
        SELECT Scenario, {','.join(all_months)}
        FROM df
        WHERE Year='2023'
        AND Account='Sales'
        AND business_unit='Software'
        """
    ).df()

    sales_data = sales_data.melt(id_vars=["Scenario"], var_name="month", value_name="sales")

    fig = px.line(
        sales_data,
        x="month",
        y="sales",
        color="Scenario",
        markers=True,
        text="sales",
        title="Monthly Budget vs Forecast 2023",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(plot_bgcolor="rgba(0, 0, 0, 0)")  # No background color
    st.plotly_chart(fig, use_container_width=True)

def plot_bottom_right():
    sales_data = duckdb.sql(
        f"""
        -- Query to retrieve actual yearly sales data for accounts other than 'Sales'
        WITH sales_data AS (
            UNPIVOT (
                SELECT Account, Year, {','.join([f'ABS({month}) AS {month}' for month in all_months])}
                FROM df
                WHERE Scenario='Actuals'
                AND Account!='Sales'
            )
            ON {','.join(all_months)}
            INTO NAME year
            VALUE sales
        ),
        aggregated_sales AS (
            SELECT Account, Year, SUM(sales) AS sales
            FROM sales_data
            GROUP BY Account, Year
        )
        SELECT * FROM aggregated_sales
        """
    ).df()

    fig = px.bar(
        sales_data,
        x="Year",
        y="sales",
        color="Account",
        title="Actual Yearly Sales Per Account",
    )
    fig.update_layout(plot_bgcolor="rgba(0, 0, 0, 0)")  # No background color
    st.plotly_chart(fig, use_container_width=True)

def plot_monthly_sales_distribution():
    # Query for monthly sales data
    sales_data = duckdb.sql(
        f"""
        -- Query to retrieve the monthly sales for 2023
        SELECT {','.join(all_months)}  -- Select each month's sales
        FROM df
        WHERE Account='Sales' AND Year='2023'
        """
    ).df()

    # Ensure the DataFrame is not empty
    if not sales_data.empty:
        # Melt the DataFrame to convert months into rows
        sales_data = sales_data.melt(value_vars=all_months, var_name="month", value_name="sales")

        # Create a pie chart for sales distribution
        fig = px.pie(sales_data, names='month', values='sales', title='Monthly Sales Distribution for 2023')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(plot_bgcolor="rgba(0, 0, 0, 0)")  # No background color
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No sales data available for the year 2023.")



#######################################
# STREAMLIT LAYOUT
#######################################

# Create one row for gauges
# Create one row for gauges
gauge_col1, gauge_col2, gauge_col3, gauge_col4 = st.columns(4)

with gauge_col1:
    plot_metric("Total Accounts Receivable", 6621280, prefix="$", suffix="", show_graph=True, color_graph="rgba(0, 104, 201, 0.2)")
    plot_gauge(1.86, "#0068C9", "%", "Current Ratio", 3)

with gauge_col2:
    plot_metric("Total Sales Amount", 1031280, prefix="$", suffix="", show_graph=True, color_graph="rgba(131, 136, 248, 0.2)")
    plot_gauge(8.14, "#8388F8", "%", "Profit Margin", 12)

with gauge_col3:
    plot_metric("Total Operating Income", 51280, prefix="$", suffix="", show_graph=True, color_graph="rgba(255, 186, 90, 0.2)")
    plot_gauge(1.96, "#FFBA5A", "%", "Operating Ratio", 5)

with gauge_col4:
    plot_metric("Total Cost", 731280, prefix="$", suffix="", show_graph=True, color_graph="rgba(255, 90, 95, 0.2)")
    plot_gauge(0.58, "#FF5A5F", "%", "Debt/Equity Ratio", 1)

# Row for detailed sales analysis
top_left, top_right = st.columns(2)

with top_left:
    plot_monthly_sales_distribution()  # Updated function for monthly sales

with top_right:
    plot_top_right()

bottom_left, bottom_right = st.columns(2)

with bottom_left:
    plot_bottom_left()

with bottom_right:
    plot_bottom_right()
