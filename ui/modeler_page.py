"""
Modeler page - Non-destructive simulation layer.

Allows temporary simulation of revenue and expense adjustments.
This is an overlay-only system that does NOT modify the core model engine.
"""

import streamlit as st
from engine.model import build_model
from engine.validation import session_state_to_model_inputs


def render():
    """Render the modeler page with simulation controls."""
    st.title("🎯 Modeler")
    
    st.markdown("""
    Simulate revenue and expense adjustments without modifying your base model.
    All changes are temporary and reset when you reload the page.
    """)
    
    st.divider()
    
    # Build model to get base case outputs
    model_inputs = session_state_to_model_inputs(st.session_state)
    
    try:
        with st.spinner("Loading base model..."):
            outputs = build_model(model_inputs)
        
        # Extract base case data
        income_statement = outputs['income_statement']
        cash_flow_statement = outputs['cash_flow_statement']
        loan_schedule = outputs['loan_schedule']
        kpis = outputs['kpis']
        
        # ========================================
        # ADJUSTMENT CONTROLS
        # ========================================
        st.markdown("### Adjustment Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.modeler_revenue_adj = st.slider(
                "Revenue Adjustment",
                min_value=-30.0,
                max_value=30.0,
                value=st.session_state.modeler_revenue_adj,
                step=1.0,
                format="%.0f%%",
                help="Adjust revenue up or down by percentage",
                key="modeler_revenue_slider"
            )
        
        with col2:
            st.session_state.modeler_expense_adj = st.slider(
                "Expense Adjustment",
                min_value=-30.0,
                max_value=30.0,
                value=st.session_state.modeler_expense_adj,
                step=1.0,
                format="%.0f%%",
                help="Adjust operating expenses up or down by percentage",
                key="modeler_expense_slider"
            )
        
        # Scope toggle
        st.session_state.modeler_scope = st.radio(
            "Apply Adjustment To:",
            options=["Year 1 Only", "Entire Forecast"],
            index=0 if st.session_state.modeler_scope == "Year 1 Only" else 1,
            horizontal=True,
            help="Choose whether to apply adjustments to Year 1 only or the entire forecast period",
            key="modeler_scope_radio"
        )
        
        st.divider()
        
        # ========================================
        # OVERLAY CALCULATIONS (NO ENGINE CALLS)
        # ========================================
        
        # Get base case arrays (copies to avoid mutation)
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
        adj_revenue = base_revenue.copy()
        adj_expense = base_operating_expenses.copy()
        
        # Determine which periods to adjust
        if st.session_state.modeler_scope == "Year 1 Only":
            if model_inputs['time_mode'] == 'monthly':
                periods_to_adjust = min(12, len(adj_revenue))
            else:
                periods_to_adjust = 1
        else:
            periods_to_adjust = len(adj_revenue)
        
        # Apply adjustments to selected periods
        for i in range(periods_to_adjust):
            adj_revenue[i] *= (1 + st.session_state.modeler_revenue_adj / 100)
            adj_expense[i] *= (1 + st.session_state.modeler_expense_adj / 100)
        
        # Recalculate derived metrics using base case formulas
        adj_gross_profit = adj_revenue - base_cogs
        adj_ebitda = adj_gross_profit - adj_expense
        adj_ebit = adj_ebitda - base_depreciation
        adj_ebt = adj_ebit - base_interest
        
        # Calculate adjusted tax (use same tax rate as base)
        adj_tax = adj_ebt.copy()
        for i in range(len(adj_tax)):
            if base_ebt[i] != 0:
                tax_rate = base_tax[i] / base_ebt[i]
                adj_tax[i] = adj_ebt[i] * tax_rate
            else:
                adj_tax[i] = 0
        
        adj_net_income = adj_ebt - adj_tax
        
        # Calculate adjusted cash flow
        adj_cash_flow = adj_net_income - base_debt_service
        
        # Calculate adjusted DSCR
        adj_dscr = []
        for i in range(len(adj_ebitda)):
            if base_debt_service[i] > 0:
                dscr_val = adj_ebitda[i] / base_debt_service[i]
            else:
                dscr_val = 0
            adj_dscr.append(dscr_val)
        
        # ========================================
        # DISPLAY: BASE CASE vs MODELED CASE
        # ========================================
        
        st.markdown("### 📊 Base Case vs Modeled Case Comparison")
        
        # Get Year 1 metrics
        if model_inputs['time_mode'] == 'monthly':
            year1_periods = min(12, len(base_net_income))
            
            base_year1_revenue = sum(base_revenue[:year1_periods])
            base_year1_net_income = sum(base_net_income[:year1_periods])
            base_year1_cash_flow = sum(base_net_income[:year1_periods] - base_debt_service[:year1_periods])
            base_year1_dscr = sum(base_ebitda[:year1_periods]) / sum(base_debt_service[:year1_periods]) if sum(base_debt_service[:year1_periods]) > 0 else 0
            
            adj_year1_revenue = sum(adj_revenue[:year1_periods])
            adj_year1_net_income = sum(adj_net_income[:year1_periods])
            adj_year1_cash_flow = sum(adj_cash_flow[:year1_periods])
            adj_year1_dscr = sum(adj_ebitda[:year1_periods]) / sum(base_debt_service[:year1_periods]) if sum(base_debt_service[:year1_periods]) > 0 else 0
        else:
            base_year1_revenue = base_revenue[0]
            base_year1_net_income = base_net_income[0]
            base_year1_cash_flow = base_net_income[0] - base_debt_service[0]
            base_year1_dscr = base_ebitda[0] / base_debt_service[0] if base_debt_service[0] > 0 else 0
            
            adj_year1_revenue = adj_revenue[0]
            adj_year1_net_income = adj_net_income[0]
            adj_year1_cash_flow = adj_cash_flow[0]
            adj_year1_dscr = adj_ebitda[0] / base_debt_service[0] if base_debt_service[0] > 0 else 0
        
        # Two-column layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Base Case (Year 1)**")
            st.metric("Revenue", f"${base_year1_revenue:,.2f}")
            st.metric("Net Income", f"${base_year1_net_income:,.2f}")
            st.metric("Cash Flow", f"${base_year1_cash_flow:,.2f}")
            st.metric("DSCR", f"{base_year1_dscr:.2f}")
        
        with col2:
            st.markdown("**Modeled Case (Year 1)**")
            
            # Revenue with delta
            rev_delta = adj_year1_revenue - base_year1_revenue
            st.metric("Revenue", f"${adj_year1_revenue:,.2f}", delta=f"${rev_delta:,.2f}")
            
            # Net Income with delta
            ni_delta = adj_year1_net_income - base_year1_net_income
            st.metric("Net Income", f"${adj_year1_net_income:,.2f}", delta=f"${ni_delta:,.2f}")
            
            # Cash Flow with delta
            cf_delta = adj_year1_cash_flow - base_year1_cash_flow
            st.metric("Cash Flow", f"${adj_year1_cash_flow:,.2f}", delta=f"${cf_delta:,.2f}")
            
            # DSCR with delta
            dscr_delta = adj_year1_dscr - base_year1_dscr
            st.metric("DSCR", f"{adj_year1_dscr:.2f}", delta=f"{dscr_delta:+.2f}")
        
        st.divider()
        
        # ========================================
        # IMPACT SUMMARY
        # ========================================
        
        st.markdown("### Impact Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Δ Net Income**")
            if ni_delta > 0:
                st.success(f"✅ +${ni_delta:,.2f}")
            elif ni_delta < 0:
                st.error(f"⚠️ ${ni_delta:,.2f}")
            else:
                st.info(f"➖ ${ni_delta:,.2f}")
        
        with col2:
            st.markdown("**Δ Cash Flow**")
            if cf_delta > 0:
                st.success(f"✅ +${cf_delta:,.2f}")
            elif cf_delta < 0:
                st.error(f"⚠️ ${cf_delta:,.2f}")
            else:
                st.info(f"➖ ${cf_delta:,.2f}")
        
        with col3:
            st.markdown("**DSCR Status**")
            if adj_year1_dscr >= 1.25:
                st.success(f"🟢 {adj_year1_dscr:.2f} (Strong)")
            elif adj_year1_dscr >= 1.0:
                st.warning(f"🟡 {adj_year1_dscr:.2f} (Marginal)")
            else:
                st.error(f"🔴 {adj_year1_dscr:.2f} (Below 1.0)")
        
        st.divider()
        
        # Reset button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Reset to Base Case", type="secondary"):
                st.session_state.modeler_revenue_adj = 0.0
                st.session_state.modeler_expense_adj = 0.0
                st.session_state.modeler_scope = "Year 1 Only"
                st.rerun()
        
        # Info box
        st.info("""
        **Note:** These adjustments are for simulation only and do not modify your saved scenario.
        Adjustments persist during your session but reset when you reload the page.
        """)
        
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        st.info("Please ensure all required inputs are configured in the other pages.")
