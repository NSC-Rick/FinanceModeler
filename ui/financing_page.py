import streamlit as st


def render():
    """Render the financing configuration page."""
    st.title("Financing & Working Capital")
    
    st.markdown("""
    Configure loan terms and working capital assumptions.
    The loan amortization will be calculated automatically.
    """)
    
    # Mode Toggle
    st.session_state.mode = st.radio(
        "Model Mode",
        ["Basic", "Advanced"],
        index=0 if st.session_state.mode == "Basic" else 1,
        horizontal=True,
        help="Advanced mode unlocks working capital and capital stack controls"
    )
    
    if st.session_state.mode == "Advanced":
        st.info("🔧 **Advanced Mode Active:** Capital Stack and Working Capital controls are available below.")
    
    st.divider()
    
    # Capital Stack Advisory Layer (Collapsible) - Advanced Mode Only
    if st.session_state.mode == "Advanced":
        with st.expander("💼 Acquisition Capital Stack (Optional)", expanded=False):
            st.markdown("""
            **Advisory Tool:** Plan your acquisition financing structure.
            This does not automatically affect the operating model until you click **Apply**.
            """)
        
            st.subheader("Uses of Funds")
        
            col1, col2 = st.columns(2)
        
            with col1:
                purchase_price = st.number_input(
                    "Purchase Price",
                    min_value=0.0,
                    value=st.session_state.capital_stack['uses']['purchase_price'],
                    step=10000.0,
                    key="cs_purchase_price",
                    help="Total purchase price of the business"
                )
            
                inventory_adjustment = st.number_input(
                    "Inventory Adjustment",
                    min_value=0.0,
                    value=st.session_state.capital_stack['uses']['inventory_adjustment'],
                    step=1000.0,
                    key="cs_inventory",
                    help="Additional inventory to be purchased"
                )
            
                closing_costs = st.number_input(
                    "Closing Costs",
                    min_value=0.0,
                    value=st.session_state.capital_stack['uses']['closing_costs'],
                    step=1000.0,
                    key="cs_closing",
                    help="Legal, accounting, and other closing costs"
                )
        
            with col2:
                working_capital = st.number_input(
                    "Working Capital Buffer",
                    min_value=0.0,
                    value=st.session_state.capital_stack['uses']['working_capital'],
                    step=1000.0,
                    key="cs_working_capital",
                    help="Cash reserve for operations"
                )
            
                capex = st.number_input(
                    "Minor Capex",
                    min_value=0.0,
                    value=st.session_state.capital_stack['uses']['capex'],
                    step=1000.0,
                    key="cs_capex",
                    help="Minor capital expenditures needed at closing"
                )
        
            total_uses = purchase_price + inventory_adjustment + closing_costs + working_capital + capex
        
            st.metric("**Total Uses of Funds**", f"${total_uses:,.2f}")
        
            st.divider()
        
            st.subheader("Sources of Funds")
        
            st.markdown("**Equity**")
            col1, col2, col3 = st.columns(3)
        
            with col1:
                buyer_equity = st.number_input(
                    "Buyer Equity",
                    min_value=0.0,
                    value=st.session_state.capital_stack['sources']['buyer_equity'],
                    step=5000.0,
                    key="cs_buyer_equity",
                    help="Buyer's cash equity contribution"
                )
        
            with col2:
                community_equity = st.number_input(
                    "Community / Investor Equity",
                    min_value=0.0,
                    value=st.session_state.capital_stack['sources']['community_equity'],
                    step=5000.0,
                    key="cs_community_equity",
                    help="Equity from community investors or partners"
                )
        
            with col3:
                donations = st.number_input(
                    "Donations / Grants",
                    min_value=0.0,
                    value=st.session_state.capital_stack['sources']['donations'],
                    step=1000.0,
                    key="cs_donations",
                    help="Grant funding or donations"
                )
        
            st.markdown("**Debt**")
        
            col1, col2 = st.columns(2)
        
            with col1:
                st.markdown("**Bank Loan**")
                bank_amount = st.number_input(
                    "Bank Loan Amount",
                    min_value=0.0,
                    value=st.session_state.capital_stack['sources']['bank_loan']['amount'],
                    step=5000.0,
                    key="cs_bank_amount",
                    help="Bank loan amount"
                )
            
                bank_rate = st.number_input(
                    "Bank Interest Rate",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.capital_stack['sources']['bank_loan']['rate'],
                    step=0.001,
                    format="%.3f",
                    key="cs_bank_rate",
                    help="Annual interest rate (e.g., 0.06 = 6%)"
                )
            
                bank_term = st.number_input(
                    "Bank Term (Years)",
                    min_value=1,
                    max_value=30,
                    value=st.session_state.capital_stack['sources']['bank_loan']['term'],
                    step=1,
                    key="cs_bank_term",
                    help="Loan term in years"
                )
        
            with col2:
                st.markdown("**Seller Note**")
                seller_amount = st.number_input(
                    "Seller Note Amount",
                    min_value=0.0,
                    value=st.session_state.capital_stack['sources']['seller_note']['amount'],
                    step=5000.0,
                    key="cs_seller_amount",
                    help="Seller financing amount"
                )
            
                seller_rate = st.number_input(
                    "Seller Note Rate",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.capital_stack['sources']['seller_note']['rate'],
                    step=0.001,
                    format="%.3f",
                    key="cs_seller_rate",
                    help="Annual interest rate (e.g., 0.05 = 5%)"
                )
            
                seller_term = st.number_input(
                    "Seller Note Term (Years)",
                    min_value=1,
                    max_value=30,
                    value=st.session_state.capital_stack['sources']['seller_note']['term'],
                    step=1,
                    key="cs_seller_term",
                    help="Loan term in years"
                )
        
            # Update session state
            st.session_state.capital_stack['uses'] = {
                'purchase_price': purchase_price,
                'inventory_adjustment': inventory_adjustment,
                'closing_costs': closing_costs,
                'working_capital': working_capital,
                'capex': capex
            }
        
            st.session_state.capital_stack['sources'] = {
                'buyer_equity': buyer_equity,
                'community_equity': community_equity,
                'donations': donations,
                'bank_loan': {
                    'amount': bank_amount,
                    'rate': bank_rate,
                    'term': bank_term
                },
                'seller_note': {
                    'amount': seller_amount,
                    'rate': seller_rate,
                    'term': seller_term
                }
            }
        
            st.session_state.capital_stack['enabled'] = True
        
            # Calculate totals
            total_equity = buyer_equity + community_equity + donations
            total_debt = bank_amount + seller_amount
            total_sources = total_equity + total_debt
            funding_gap = total_sources - total_uses
        
            st.divider()
        
            st.subheader("Capital Stack Summary")
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.metric("Total Uses", f"${total_uses:,.2f}")
                st.metric("Total Equity", f"${total_equity:,.2f}")
        
            with col2:
                st.metric("Total Sources", f"${total_sources:,.2f}")
                st.metric("Total Debt", f"${total_debt:,.2f}")
        
            with col3:
                if funding_gap == 0:
                    st.metric("Funding Gap", f"${funding_gap:,.2f}", delta="Balanced ✓")
                elif funding_gap > 0:
                    st.metric("Funding Gap", f"${funding_gap:,.2f}", delta="Surplus")
                else:
                    st.metric("Funding Gap", f"${funding_gap:,.2f}", delta="Shortfall ⚠️")
        
            # Calculate annual debt service
            st.divider()
            st.subheader("Advisory Debt Service Analysis")
        
            # Bank loan annual payment
            if bank_amount > 0 and bank_rate > 0:
                annual_bank_payment = bank_amount * (bank_rate * (1 + bank_rate)**bank_term) / ((1 + bank_rate)**bank_term - 1)
            else:
                annual_bank_payment = 0.0
        
            # Seller note annual payment
            if seller_amount > 0 and seller_rate > 0:
                annual_seller_payment = seller_amount * (seller_rate * (1 + seller_rate)**seller_term) / ((1 + seller_rate)**seller_term - 1)
            else:
                annual_seller_payment = 0.0
        
            total_annual_debt_service = annual_bank_payment + annual_seller_payment
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.metric("Annual Bank Payment", f"${annual_bank_payment:,.2f}")
        
            with col2:
                st.metric("Annual Seller Payment", f"${annual_seller_payment:,.2f}")
        
            with col3:
                st.metric("Total Annual Debt Service", f"${total_annual_debt_service:,.2f}")
        
            st.divider()
        
            # Apply button
            st.markdown("### Apply Capital Stack to Operating Model")
            st.markdown("""
            Click the button below to populate the operating model's debt inputs with the capital stack debt structure.
            **This will overwrite existing debt settings.**
            """)
        
            if st.button("🔄 Apply Capital Stack Debt to Operating Model", type="primary"):
                # Apply bank loan
                st.session_state.loan_principal = bank_amount
                st.session_state.loan_annual_rate = bank_rate
                st.session_state.loan_term_months = bank_term * 12
            
                # Note: Seller note would need additional debt module support
                # For now, we'll show a message
                if seller_amount > 0:
                    st.warning(f"⚠️ Seller Note (${seller_amount:,.2f}) noted but current model supports single loan only. Consider combining with bank loan or tracking separately.")
            
                st.success(f"✅ Applied Bank Loan: ${bank_amount:,.2f} at {bank_rate:.1%} for {bank_term} years to Operating Model")
                st.rerun()
    
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
