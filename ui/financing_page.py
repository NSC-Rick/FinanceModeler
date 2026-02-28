import streamlit as st


def render():
    """Render the financing configuration page."""
    st.title("Financing & Working Capital")
    
    st.markdown("""
    Configure loan terms and working capital assumptions.
    The loan amortization will be calculated automatically.
    """)
    
    st.divider()
    
    st.subheader("Term Loan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        loan_principal = st.number_input(
            "Loan Principal",
            min_value=0.0,
            value=st.session_state.loan_principal,
            step=1000.0,
            key="loan_principal_input",
            help="Total loan amount"
        )
        st.session_state.loan_principal = loan_principal
        
        loan_annual_rate = st.number_input(
            "Annual Interest Rate",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.loan_annual_rate,
            step=0.001,
            format="%.3f",
            key="loan_rate_input",
            help="Annual interest rate (e.g., 0.06 = 6%)"
        )
        st.session_state.loan_annual_rate = loan_annual_rate
    
    with col2:
        loan_term_months = st.number_input(
            "Loan Term (Months)",
            min_value=1,
            value=st.session_state.loan_term_months,
            step=12,
            key="loan_term_input",
            help="Loan term in months"
        )
        st.session_state.loan_term_months = loan_term_months
        
        max_start_period = st.session_state.periods - 1
        loan_start_period = st.number_input(
            "Start Period (0-indexed)",
            min_value=0,
            max_value=max_start_period,
            value=min(st.session_state.loan_start_period, max_start_period),
            step=1,
            key="loan_start_input",
            help="Period when loan disbursement occurs (0 = first period)"
        )
        st.session_state.loan_start_period = loan_start_period
    
    if loan_principal > 0 and loan_annual_rate > 0:
        if st.session_state.time_mode == 'monthly':
            monthly_rate = loan_annual_rate / 12
            payment = loan_principal * (monthly_rate * (1 + monthly_rate)**loan_term_months) / ((1 + monthly_rate)**loan_term_months - 1)
            st.info(f"**Estimated Monthly Payment:** ${payment:,.2f}")
        else:
            payment_years = int((loan_term_months + 11) / 12)
            payment = loan_principal * (loan_annual_rate * (1 + loan_annual_rate)**payment_years) / ((1 + loan_annual_rate)**payment_years - 1)
            st.info(f"**Estimated Annual Payment:** ${payment:,.2f}")
    
    st.divider()
    
    st.subheader("Owner Compensation")
    
    st.markdown("""
    Configure how owner compensation is treated in the financial model.
    - **Payroll**: Included in EBITDA, affects profitability metrics
    - **Distribution**: Deducted from cash after Net Income, does not affect EBITDA
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        owner_mode = st.radio(
            "Treat Owner Compensation As:",
            options=['distribution', 'payroll'],
            index=0 if st.session_state.owner_compensation.get('mode', 'distribution') == 'distribution' else 1,
            key="owner_comp_mode",
            help="Payroll: affects EBITDA and profitability. Distribution: affects only cash flow."
        )
    
    with col2:
        owner_amount = st.number_input(
            "Annual Owner Compensation",
            min_value=0.0,
            value=st.session_state.owner_compensation.get('amount', 0.0),
            step=5000.0,
            key="owner_comp_amount",
            help="Annual amount for owner compensation"
        )
    
    st.session_state.owner_compensation = {
        'mode': owner_mode,
        'amount': owner_amount
    }
    
    if owner_mode == 'payroll':
        st.info("💼 Owner compensation will be included as indirect payroll, affecting EBITDA and profitability metrics.")
    else:
        st.info("💰 Owner compensation will be deducted from cash flow after Net Income, preserving EBITDA for underwriting.")
    
    st.divider()
    
    st.subheader("Tax & Depreciation")
    
    st.markdown("""
    Configure corporate tax rate and annual depreciation for P&L statement.
    Taxes are calculated as a flat percentage of pre-tax income (zero if negative).
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        tax_rate = st.number_input(
            "Corporate Tax Rate",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.tax_rate,
            step=0.01,
            format="%.2f",
            key="tax_rate_input",
            help="Corporate tax rate as decimal (e.g., 0.25 = 25%)"
        )
        st.session_state.tax_rate = tax_rate
    
    with col2:
        annual_depreciation = st.number_input(
            "Annual Depreciation",
            min_value=0.0,
            value=st.session_state.annual_depreciation,
            step=1000.0,
            key="annual_depreciation_input",
            help="Annual depreciation amount (will be divided by 12 for monthly mode)"
        )
        st.session_state.annual_depreciation = annual_depreciation
    
    st.divider()
    
    st.subheader("Working Capital")
    
    st.markdown("""
    Working capital assumptions affect cash flow timing.
    These are converted to cash flow adjustments based on changes in AR, AP, and Inventory.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ar_days = st.number_input(
            "Accounts Receivable Days",
            min_value=0,
            value=st.session_state.ar_days,
            step=1,
            key="ar_days_input",
            help="Average days to collect payment from customers"
        )
        st.session_state.ar_days = ar_days
    
    with col2:
        ap_days = st.number_input(
            "Accounts Payable Days",
            min_value=0,
            value=st.session_state.ap_days,
            step=1,
            key="ap_days_input",
            help="Average days to pay suppliers"
        )
        st.session_state.ap_days = ap_days
    
    with col3:
        inventory_days = st.number_input(
            "Inventory Days",
            min_value=0,
            value=st.session_state.inventory_days,
            step=1,
            key="inventory_days_input",
            help="Average days inventory is held"
        )
        st.session_state.inventory_days = inventory_days
