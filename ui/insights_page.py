"""
Insights page with deterministic Red/Yellow/Green flags.

Rule-based analysis with transparent thresholds.
No AI commentary, no subjective language, no composite scoring.
"""

import streamlit as st
from engine.model import build_model
from engine.validation import session_state_to_model_inputs


def render():
    """Render the insights page with rule-based flags."""
    st.title("📊 Insights & Flags")
    
    st.markdown("""
    Deterministic analysis based on transparent rules and thresholds.
    Flags are calculated from your financial model data.
    """)
    
    st.divider()
    
    # Build model to get outputs
    model_inputs = session_state_to_model_inputs(st.session_state)
    
    try:
        with st.spinner("Analyzing model..."):
            outputs = build_model(model_inputs)
        
        # Extract key metrics
        kpis = outputs['kpis']
        income_statement = outputs['income_statement']
        cash_flow_statement = outputs['cash_flow_statement']
        loan_schedule = outputs['loan_schedule']
        
        # Get first period metrics for evaluation
        first_period_kpis = kpis.iloc[0]
        dscr = first_period_kpis.get('dscr', 0)
        gross_margin_pct = first_period_kpis.get('gross_margin_pct', 0) / 100  # Convert to decimal
        
        # Calculate cash after debt and owner
        net_income = income_statement['net_income'].iloc[0]
        debt_service = loan_schedule['payment'].iloc[0]
        cash_after_debt = net_income - debt_service
        
        owner_comp_config = model_inputs.get('owner_compensation', {'mode': 'distribution', 'amount': 0.0})
        owner_comp_mode = owner_comp_config.get('mode', 'distribution')
        owner_comp_annual = owner_comp_config.get('amount', 0.0)
        
        if model_inputs['time_mode'] == 'monthly':
            owner_comp_per_period = owner_comp_annual / 12
        else:
            owner_comp_per_period = owner_comp_annual
        
        if owner_comp_mode == 'distribution':
            cash_after_debt_and_owner = cash_after_debt - owner_comp_per_period
        else:
            cash_after_debt_and_owner = cash_after_debt
        
        # Operating cash flow
        operating_cash_flow = cash_flow_statement['operating_cash_flow'].iloc[0]
        
        # Revenue for ratio calculations
        revenue = income_statement['revenue'].iloc[0]
        
        # Rent calculation (find rent in opex_items)
        rent_amount = 0
        for item in model_inputs.get('opex_items', []):
            if item.get('name', '').lower() == 'rent':
                rent_amount = item.get('amount', 0)
                break
        
        rent_to_revenue_ratio = rent_amount / revenue if revenue > 0 else 0
        
        # Advanced mode checks
        mode = model_inputs.get('mode', 'Basic')
        is_advanced = (mode == 'Advanced')
        
        # Funding gap (Advanced only)
        funding_gap = 0
        if is_advanced:
            capital_stack = model_inputs.get('capital_stack', {})
            if capital_stack.get('enabled', False):
                uses = capital_stack.get('uses', {})
                sources = capital_stack.get('sources', {})
                
                total_uses = sum([
                    uses.get('purchase_price', 0),
                    uses.get('inventory_adjustment', 0),
                    uses.get('closing_costs', 0),
                    uses.get('working_capital', 0),
                    uses.get('capex', 0)
                ])
                
                total_sources = sum([
                    sources.get('buyer_equity', 0),
                    sources.get('community_equity', 0),
                    sources.get('donations', 0),
                    sources.get('bank_loan', {}).get('amount', 0),
                    sources.get('seller_note', {}).get('amount', 0)
                ])
                
                funding_gap = total_sources - total_uses
        
        # AR days (Advanced only)
        ar_days = model_inputs.get('ar_days', 0)
        
        # Equity injection ratio (Advanced only)
        equity_ratio = 0
        if is_advanced:
            capital_stack = model_inputs.get('capital_stack', {})
            if capital_stack.get('enabled', False):
                uses = capital_stack.get('uses', {})
                sources = capital_stack.get('sources', {})
                
                total_uses = sum([
                    uses.get('purchase_price', 0),
                    uses.get('inventory_adjustment', 0),
                    uses.get('closing_costs', 0),
                    uses.get('working_capital', 0),
                    uses.get('capex', 0)
                ])
                
                total_equity = sum([
                    sources.get('buyer_equity', 0),
                    sources.get('community_equity', 0),
                    sources.get('donations', 0)
                ])
                
                equity_ratio = total_equity / total_uses if total_uses > 0 else 0
        
        # ========================================
        # RED FLAGS
        # ========================================
        red_flags = []
        
        # Rule: DSCR < 1.0
        if dscr < 1.0:
            red_flags.append(f"DSCR below 1.0 (current: {dscr:.2f}). Debt service exceeds available cash flow.")
        
        # Rule: Cash after debt and owner < 0
        if cash_after_debt_and_owner < 0:
            red_flags.append(f"Negative cash after debt and owner compensation (${cash_after_debt_and_owner:,.2f}). Business cannot cover obligations.")
        
        # Rule: Operating cash flow < 0
        if operating_cash_flow < 0:
            red_flags.append(f"Negative operating cash flow (${operating_cash_flow:,.2f}). Operations are consuming cash.")
        
        # Rule: Advanced mode AND funding gap != 0
        if is_advanced and funding_gap != 0:
            if funding_gap > 0:
                red_flags.append(f"Capital stack funding surplus (${funding_gap:,.2f}). Sources exceed uses.")
            else:
                red_flags.append(f"Capital stack funding shortfall (${abs(funding_gap):,.2f}). Uses exceed sources.")
        
        # ========================================
        # YELLOW FLAGS
        # ========================================
        yellow_flags = []
        
        # Rule: 1.0 <= DSCR < 1.20
        if 1.0 <= dscr < 1.20:
            yellow_flags.append(f"DSCR between 1.0 and 1.20 (current: {dscr:.2f}). Minimal debt service coverage.")
        
        # Rule: Rent / Revenue > 0.12
        if rent_to_revenue_ratio > 0.12:
            yellow_flags.append(f"Rent exceeds 12% of revenue (current: {rent_to_revenue_ratio*100:.1f}%). High occupancy cost.")
        
        # Rule: Gross margin < 0.30
        if gross_margin_pct < 0.30:
            yellow_flags.append(f"Gross margin below 30% (current: {gross_margin_pct*100:.1f}%). Limited pricing power or high COGS.")
        
        # Rule: Advanced mode AND AR days > 30
        if is_advanced and ar_days > 30:
            yellow_flags.append(f"Accounts receivable days exceed 30 (current: {ar_days}). Slow customer payment cycle.")
        
        # ========================================
        # GREEN SIGNALS
        # ========================================
        green_signals = []
        
        # Rule: DSCR >= 1.25
        if dscr >= 1.25:
            green_signals.append(f"DSCR at or above 1.25 (current: {dscr:.2f}). Strong debt service coverage.")
        
        # Rule: Cash after debt and owner >= 0
        if cash_after_debt_and_owner >= 0:
            green_signals.append(f"Positive cash after debt and owner compensation (${cash_after_debt_and_owner:,.2f}). Business covers all obligations.")
        
        # Rule: Operating cash flow > 0
        if operating_cash_flow > 0:
            green_signals.append(f"Positive operating cash flow (${operating_cash_flow:,.2f}). Operations generate cash.")
        
        # Rule: Advanced mode AND equity injection >= 0.20
        if is_advanced and equity_ratio >= 0.20:
            green_signals.append(f"Equity injection at or above 20% (current: {equity_ratio*100:.1f}%). Strong equity cushion.")
        
        # ========================================
        # DISPLAY
        # ========================================
        
        # Red Flags Section
        st.markdown("### 🔴 Red Flags")
        if red_flags:
            for flag in red_flags:
                st.error(f"🔴 {flag}")
        else:
            st.success("✅ No red flags detected.")
        
        st.divider()
        
        # Yellow Flags Section
        st.markdown("### 🟡 Yellow Flags")
        if yellow_flags:
            for flag in yellow_flags:
                st.warning(f"🟡 {flag}")
        else:
            st.info("✅ No yellow flags detected.")
        
        st.divider()
        
        # Green Signals Section
        st.markdown("### 🟢 Green Signals")
        if green_signals:
            for signal in green_signals:
                st.success(f"🟢 {signal}")
        else:
            st.info("ℹ️ No green signals detected.")
        
        st.divider()
        
        # Rule Reference
        with st.expander("📋 Flag Rules Reference"):
            st.markdown("""
            **Red Flag Thresholds:**
            - DSCR < 1.0
            - Cash after debt and owner < $0
            - Operating cash flow < $0
            - Capital stack funding gap ≠ $0 (Advanced mode only)
            
            **Yellow Flag Thresholds:**
            - 1.0 ≤ DSCR < 1.20
            - Rent / Revenue > 12%
            - Gross margin < 30%
            - AR days > 30 (Advanced mode only)
            
            **Green Signal Thresholds:**
            - DSCR ≥ 1.25
            - Cash after debt and owner ≥ $0
            - Operating cash flow > $0
            - Equity injection ≥ 20% (Advanced mode only)
            
            *All thresholds are deterministic and rule-based. No subjective analysis.*
            """)
        
        st.divider()
        
        # ========================================
        # CONTROLS - SENSITIVITY TESTING
        # ========================================
        st.markdown("### 🕹 Controls — Sensitivity Testing")
        st.markdown("""
        Stress-test your model by adjusting revenue and expenses.
        This is an overlay analysis only - your base model remains unchanged.
        """)
        
        # Sliders (not persisted - local to this page)
        col1, col2 = st.columns(2)
        
        with col1:
            revenue_adjustment = st.slider(
                "Revenue Adjustment",
                min_value=-30,
                max_value=30,
                value=0,
                step=1,
                format="%d%%",
                help="Adjust revenue up or down by percentage",
                key="insights_revenue_slider"
            )
        
        with col2:
            expense_adjustment = st.slider(
                "Expense Adjustment",
                min_value=-30,
                max_value=30,
                value=0,
                step=1,
                format="%d%%",
                help="Adjust operating expenses up or down by percentage",
                key="insights_expense_slider"
            )
        
        # Scope toggle
        scope = st.radio(
            "Apply Adjustment To:",
            options=["Year 1 Only", "Entire Forecast"],
            index=0,
            horizontal=True,
            help="Choose whether to apply adjustments to Year 1 only or the entire forecast period",
            key="insights_scope_toggle"
        )
        
        st.divider()
        
        # ========================================
        # OVERLAY CALCULATIONS (NO ENGINE CHANGES)
        # ========================================
        
        # Get base case arrays (copies to avoid mutation)
        import copy
        base_revenue = income_statement['revenue'].values.copy()
        base_cogs = income_statement['cogs'].values.copy()
        base_operating_expenses = income_statement['operating_expenses'].values.copy()
        base_ebitda = income_statement['ebitda'].values.copy()
        base_depreciation = income_statement['depreciation'].values.copy()
        base_interest = income_statement['interest'].values.copy()
        base_tax = income_statement['tax'].values.copy()
        base_net_income = income_statement['net_income'].values.copy()
        base_debt_service = loan_schedule['payment'].values.copy()
        
        # Create adjusted copies
        adjusted_revenue = base_revenue.copy()
        adjusted_operating_expenses = base_operating_expenses.copy()
        
        # Determine which periods to adjust
        if scope == "Year 1 Only":
            if model_inputs['time_mode'] == 'monthly':
                periods_to_adjust = min(12, len(adjusted_revenue))
            else:
                periods_to_adjust = 1
        else:
            periods_to_adjust = len(adjusted_revenue)
        
        # Apply adjustments to selected periods
        for i in range(periods_to_adjust):
            adjusted_revenue[i] *= (1 + revenue_adjustment / 100)
            adjusted_operating_expenses[i] *= (1 + expense_adjustment / 100)
        
        # Recalculate derived metrics using same formulas as base case
        adjusted_gross_profit = adjusted_revenue - base_cogs
        adjusted_ebitda = adjusted_gross_profit - adjusted_operating_expenses
        adjusted_ebit = adjusted_ebitda - base_depreciation
        adjusted_ebt = adjusted_ebit - base_interest
        adjusted_tax = adjusted_ebt * (base_tax[0] / base_ebt[0] if base_ebt[0] != 0 else 0)
        adjusted_net_income = adjusted_ebt - adjusted_tax
        
        # Calculate adjusted cash flow (simplified: net income - debt service)
        adjusted_cash_flow = adjusted_net_income - base_debt_service
        
        # Calculate adjusted DSCR
        adjusted_dscr = []
        for i in range(len(adjusted_ebitda)):
            if base_debt_service[i] > 0:
                dscr_val = adjusted_ebitda[i] / base_debt_service[i]
            else:
                dscr_val = 0
            adjusted_dscr.append(dscr_val)
        
        # ========================================
        # DISPLAY: BASE CASE vs ADJUSTED CASE
        # ========================================
        
        st.markdown("#### 📊 Base Case vs Adjusted Case Comparison")
        
        # Get Year 1 metrics
        if model_inputs['time_mode'] == 'monthly':
            year1_periods = min(12, len(base_net_income))
            base_year1_net_income = sum(base_net_income[:year1_periods])
            base_year1_cash_flow = sum(base_net_income[:year1_periods] - base_debt_service[:year1_periods])
            base_year1_dscr = sum(base_ebitda[:year1_periods]) / sum(base_debt_service[:year1_periods]) if sum(base_debt_service[:year1_periods]) > 0 else 0
            
            adjusted_year1_net_income = sum(adjusted_net_income[:year1_periods])
            adjusted_year1_cash_flow = sum(adjusted_cash_flow[:year1_periods])
            adjusted_year1_dscr = sum(adjusted_ebitda[:year1_periods]) / sum(base_debt_service[:year1_periods]) if sum(base_debt_service[:year1_periods]) > 0 else 0
        else:
            base_year1_net_income = base_net_income[0]
            base_year1_cash_flow = base_net_income[0] - base_debt_service[0]
            base_year1_dscr = base_ebitda[0] / base_debt_service[0] if base_debt_service[0] > 0 else 0
            
            adjusted_year1_net_income = adjusted_net_income[0]
            adjusted_year1_cash_flow = adjusted_cash_flow[0]
            adjusted_year1_dscr = adjusted_ebitda[0] / base_debt_service[0] if base_debt_service[0] > 0 else 0
        
        # Two-column layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Base Case (Year 1)**")
            st.metric("Net Income", f"${base_year1_net_income:,.2f}")
            st.metric("Cash Flow", f"${base_year1_cash_flow:,.2f}")
            st.metric("DSCR", f"{base_year1_dscr:.2f}")
        
        with col2:
            st.markdown("**Adjusted Case (Year 1)**")
            
            # Net Income with delta
            ni_delta = adjusted_year1_net_income - base_year1_net_income
            st.metric("Net Income", f"${adjusted_year1_net_income:,.2f}", delta=f"${ni_delta:,.2f}")
            
            # Cash Flow with delta
            cf_delta = adjusted_year1_cash_flow - base_year1_cash_flow
            st.metric("Cash Flow", f"${adjusted_year1_cash_flow:,.2f}", delta=f"${cf_delta:,.2f}")
            
            # DSCR with delta
            dscr_delta = adjusted_year1_dscr - base_year1_dscr
            st.metric("DSCR", f"{adjusted_year1_dscr:.2f}", delta=f"{dscr_delta:+.2f}")
        
        st.divider()
        
        # ========================================
        # DELTA IMPACT SUMMARY
        # ========================================
        
        st.markdown("#### Δ Impact Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Net Income Impact**")
            if ni_delta > 0:
                st.success(f"✅ +${ni_delta:,.2f}")
            elif ni_delta < 0:
                st.error(f"⚠️ ${ni_delta:,.2f}")
            else:
                st.info(f"➖ ${ni_delta:,.2f}")
        
        with col2:
            st.markdown("**Cash Flow Impact**")
            if cf_delta > 0:
                st.success(f"✅ +${cf_delta:,.2f}")
            elif cf_delta < 0:
                st.error(f"⚠️ ${cf_delta:,.2f}")
            else:
                st.info(f"➖ ${cf_delta:,.2f}")
        
        with col3:
            st.markdown("**DSCR Change**")
            if adjusted_year1_dscr >= 1.25:
                st.success(f"🟢 {adjusted_year1_dscr:.2f} (Strong)")
            elif adjusted_year1_dscr >= 1.0:
                st.warning(f"🟡 {adjusted_year1_dscr:.2f} (Marginal)")
            else:
                st.error(f"🔴 {adjusted_year1_dscr:.2f} (Below 1.0)")
        
        st.divider()
        
        # Info box
        st.info("""
        **Note:** These adjustments are for analysis only and do not modify your saved scenario.
        Sliders reset to 0% when you refresh the page.
        """)
        
    except Exception as e:
        st.error(f"Error analyzing model: {str(e)}")
        st.info("Please ensure all required inputs are configured in the other pages.")
