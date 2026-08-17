import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io

# Set page configuration
st.set_page_config(
    page_title="Maintenance OPEX Forecast",
    page_icon="💼",
    layout="wide"
)

# Application Header
st.title("💼 Maintenance OPEX Forecast")

# Dynamic Year Selection
col_y1, col_y2 = st.columns(2)
base_year = col_y1.selectbox("Select Base Year", [2023, 2024, 2025, 2026, 2027], index=2)
forecast_year = base_year + 1

st.subheader(f"1. Input {base_year} Actuals")

# Choose input method
input_method = st.radio(
    "Choose Input Method:", 
    [f"📤 Upload Actuals File (Excel/CSV)", "✍️ Enter Total Manually"], 
    horizontal=True
)

base_spend = 0.0
df_actuals = pd.DataFrame()

# Data Intake Processing
if input_method.startswith("📤 Upload Actuals"):
    uploaded_file = st.file_uploader(f"Upload {base_year} Expenditure Report", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'): 
                df_actuals = pd.read_csv(uploaded_file)
            else: 
                df_actuals = pd.read_excel(uploaded_file)
                
            if 'Total' in df_actuals.columns:
                base_spend = pd.to_numeric(df_actuals['Total'], errors='coerce').sum()
                st.success(f"✅ Data Loaded. Total Base Spend: {base_spend:,.2f}")
            else:
                st.warning("⚠️ File loaded successfully, but no 'Total' column was found.")
        except Exception as e: 
            st.error(f"Error reading file: {e}")
else:
    col_man1, col_man2 = st.columns(2)
    base_spend = col_man1.number_input(
        f"Enter Total Annual Spending ({base_year})", 
        value=1000000.0, 
        step=1000.0, 
        format="%.2f"
    )

st.markdown("---")

# Forecast Logic & Dashboard
if base_spend > 0:
    st.subheader("2. Forecast Drivers")
    c1, c2, c3, c4 = st.columns(4)
    volume_pct_input = c1.number_input("Volume Increase (%)", value=5.0) 
    inflation_pct_input = c2.number_input("Inflation Rate (%)", value=10.0) 
    forex_pct_input = c3.number_input("Forex Change (%)", value=15.0) 
    risk_amount = c4.number_input("Risk Buffer (Amount)", value=50000.0)

    volume_pct = volume_pct_input / 100.0
    inflation_pct = inflation_pct_input / 100.0
    forex_pct = forex_pct_input / 100.0

    # Core Calculations
    volume_impact = base_spend * volume_pct
    base_adjusted = base_spend + volume_impact
    
    local_portion = base_adjusted * 0.60
    import_portion = base_adjusted * 0.40
    
    local_increase = local_portion * inflation_pct
    import_increase = import_portion * forex_pct
    
    forecast_total = local_portion + local_increase + import_portion + import_increase + risk_amount
    pct_increase = (forecast_total - base_spend) / base_spend if base_spend > 0 else 0

    st.markdown("### 📊 Forecast Results")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{base_year} Actuals", f"{base_spend:,.0f}")
    m2.metric(f"{forecast_year} Forecast", f"{forecast_total:,.0f}", delta=f"{pct_increase:.1%} Increase")
    m3.metric("Budget Variance", f"{forecast_total - base_spend:,.0f}")

    tab_chart, tab_data = st.tabs(["📉 Visual Breakdown", "📋 Source Data"])
    
    with tab_chart:
        fig = go.Figure(go.Waterfall(
            name="Forecast Bridge", 
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=[f"{base_year} Base", "Volume Impact", "Inflation (Local)", "Forex (Import)", "Risk Buffer", f"{forecast_year} Forecast"],
            textposition="outside",
            text=[
                f"{base_spend/1e6:.2f}M", 
                f"+{volume_impact/1e6:.2f}M", 
                f"+{local_increase/1e6:.2f}M", 
                f"+{import_increase/1e6:.2f}M", 
                f"+{risk_amount/1e6:.2f}M", 
                f"{forecast_total/1e6:.2f}M"
            ],
            y=[
                base_spend, 
                volume_impact, 
                local_increase, 
                import_increase, 
                risk_amount, 
                forecast_total
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        fig.update_layout(title=f"OPEX Bridge: {base_year} Actual vs {forecast_year} Forecast", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    with tab_data:
        if not df_actuals.empty:
            df_actuals.index = df_actuals.index + 1
            st.dataframe(df_actuals)
        else:
            st.info("No uploaded file data available. Manual entry was used.")

    st.markdown("---")
    st.subheader("3. Export Documentation")
    
    # PDF Generation Function
    def generate_pdf_report():
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Maintenance OPEX Forecast Justification Report", ln=True, align='C')
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="1. Executive Summary", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(200, 8, txt=f"Base Year ({base_year}) Spend: ${base_spend:,.2f}", ln=True)
        pdf.cell(200, 8, txt=f"Forecasted Year ({forecast_year}) Spend: ${forecast_total:,.2f}", ln=True)
        pdf.cell(200, 8, txt=f"Total Budget Variance: ${forecast_total - base_spend:,.2f} ({pct_increase:.1%} Increase)", ln=True)
        pdf.ln(5)
        
        # Driver Breakdown
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="2. Detailed Driver Breakdown", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(200, 8, txt=f"A. Volume Impact (+{volume_pct_input}%): ${volume_impact:,.2f}", ln=True)
        pdf.cell(200, 8, txt=f"B. Local Inflation (+{inflation_pct_input}% on 60% of base): ${local_increase:,.2f}", ln=True)
        pdf.cell(200, 8, txt=f"C. Forex Impact (+{forex_pct_input}% on 40% of base): ${import_increase:,.2f}", ln=True)
        pdf.cell(200, 8, txt=f"D. Risk Buffer (Fixed Amount): ${risk_amount:,.2f}", ln=True)
        pdf.ln(5)
        
        # Justification Notes
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="3. Forecast Assumptions & Justification", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, txt=f"The forecasted OPEX for {forecast_year} builds upon the {base_year} base actuals. "
                                 f"Adjustments factor in an anticipated volume growth of {volume_pct_input}%. "
                                 f"The resulting adjusted base is split between local spend (60%) and import spend (40%). "
                                 f"Local inflation is projected at {inflation_pct_input}%, while forex fluctuations "
                                 f"affect the import portion by {forex_pct_input}%. A standardized risk buffer "
                                 f"of ${risk_amount:,.2f} has been added to mitigate unforeseen circumstances.")
        
        # Output PDF to bytes
        return bytes(pdf.output(dest='S'), encoding='latin1')

    # Download Button
    pdf_bytes = generate_pdf_report()
    st.download_button(
        label="📄 Download Full Justification Report (PDF)",
        data=pdf_bytes,
        file_name=f"OPEX_Forecast_Report_{forecast_year}.pdf",
        mime="application/pdf"
    )

else:
    st.warning("⚠️ Please upload a file or enter a manual amount to begin forecasting.")

