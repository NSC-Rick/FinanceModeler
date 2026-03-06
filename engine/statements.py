import pandas as pd
import numpy as np


def calculate_working_capital_requirement(inventory, ar, ap):
    """
    Calculate total working capital required to operate the business.
    
    Working capital = Current Assets - Current Liabilities
    = (Inventory + Accounts Receivable) - Accounts Payable
    
    Args:
        inventory: Inventory balance
        ar: Accounts receivable balance
        ap: Accounts payable balance
    
    Returns:
        Total working capital requirement
    """
    return inventory + ar - ap


def build_income_statement(revenue_total, cogs, payroll_total, opex_total, interest_expense):
    """
    Build income statement.
    
    Args:
        revenue_total: Series of total revenue per period
        cogs: Series of COGS per period
        payroll_total: Series of total payroll per period
        opex_total: Series of total opex per period
        interest_expense: Series of interest expense per period
    
    Returns:
        DataFrame with income statement line items
    """
    gross_profit = revenue_total - cogs
    operating_expenses = payroll_total + opex_total
    ebitda = gross_profit - operating_expenses
    ebit = ebitda
    ebt = ebit - interest_expense
    net_income = ebt
    
    return pd.DataFrame({
        'revenue': revenue_total,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'payroll': payroll_total,
        'opex': opex_total,
        'operating_expenses': operating_expenses,
        'ebitda': ebitda,
        'interest_expense': interest_expense,
        'net_income': net_income
    })


def build_cash_flow_statement(net_income, loan_principal, loan_payment, ar_days, ap_days, inventory_days, 
                               revenue_total, cogs, time_mode, owner_distribution=None):
    """
    Build cash flow statement with working capital adjustments and owner distributions.
    
    Automatically injects working capital in Period 0 to prevent negative startup cash.
    
    Args:
        net_income: Series of net income per period
        loan_principal: Series of loan principal payments per period
        loan_payment: Series of total loan payments per period
        ar_days: Days sales outstanding (AR)
        ap_days: Days payable outstanding (AP)
        inventory_days: Days inventory held
        revenue_total: Series of revenue per period
        cogs: Series of COGS per period
        time_mode: 'monthly' or 'annual'
        owner_distribution: Optional Series of owner distribution per period
    
    Returns:
        DataFrame with cash flow statement including working_capital_injection row
    """
    periods = len(net_income)
    
    days_in_period = 30 if time_mode == 'monthly' else 365
    
    # Calculate working capital balances
    ar_balance = revenue_total * (ar_days / days_in_period)
    ap_balance = cogs * (ap_days / days_in_period)
    inventory_balance = cogs * (inventory_days / days_in_period)
    
    # Calculate changes in working capital
    ar_change = ar_balance.diff().fillna(ar_balance.iloc[0] if len(ar_balance) > 0 else 0)
    ap_change = ap_balance.diff().fillna(ap_balance.iloc[0] if len(ap_balance) > 0 else 0)
    inventory_change = inventory_balance.diff().fillna(inventory_balance.iloc[0] if len(inventory_balance) > 0 else 0)
    
    # Calculate working capital requirement for Period 0
    if len(ar_balance) > 0:
        period_0_inventory = inventory_balance.iloc[0]
        period_0_ar = ar_balance.iloc[0]
        period_0_ap = ap_balance.iloc[0]
        working_capital_requirement = calculate_working_capital_requirement(
            period_0_inventory, 
            period_0_ar, 
            period_0_ap
        )
    else:
        working_capital_requirement = 0
    
    # Create working capital injection series (inject in Period 0 only)
    wc_injection = pd.Series([0.0] * periods, index=range(periods))
    if working_capital_requirement > 0:
        wc_injection.iloc[0] = working_capital_requirement
    
    # Calculate operating cash flow
    operating_cash_flow = net_income - ar_change + ap_change - inventory_change
    
    # Financing cash flow includes loan principal payments
    financing_cash_flow = -loan_principal
    
    # Owner distribution
    if owner_distribution is not None:
        owner_dist = owner_distribution
    else:
        owner_dist = pd.Series([0.0] * periods, index=range(periods))
    
    # Net cash flow includes working capital injection
    net_cash_flow = operating_cash_flow + financing_cash_flow + wc_injection - owner_dist
    
    # Ending cash balance
    ending_cash = net_cash_flow.cumsum()
    
    return pd.DataFrame({
        'net_income': net_income,
        'ar_change': ar_change,
        'ap_change': ap_change,
        'inventory_change': inventory_change,
        'operating_cash_flow': operating_cash_flow,
        'working_capital_injection': wc_injection,
        'financing_cash_flow': financing_cash_flow,
        'owner_distribution': owner_dist,
        'net_cash_flow': net_cash_flow,
        'ending_cash': ending_cash
    })


def build_pnl_statement(revenue_total, cogs, direct_payroll, indirect_payroll, opex_total, interest_expense, 
                        annual_depreciation, tax_rate, time_mode, periods):
    """
    Build Profit & Loss statement with depreciation and taxes (A+ architecture).
    
    Args:
        revenue_total: Series of total revenue per period
        cogs: Series of COGS per period (materials only)
        direct_payroll: Series of direct payroll per period (flows to COGS)
        indirect_payroll: Series of indirect payroll per period (flows to Opex)
        opex_total: Series of total opex per period
        interest_expense: Series of interest expense per period
        annual_depreciation: Annual depreciation amount
        tax_rate: Corporate tax rate (e.g., 0.25 for 25%)
        time_mode: 'monthly' or 'annual'
        periods: Number of periods
    
    Returns:
        DataFrame with P&L line items including taxes
    """
    total_cogs = cogs + direct_payroll
    gross_profit = revenue_total - total_cogs
    operating_expenses = indirect_payroll + opex_total
    ebitda = gross_profit - operating_expenses
    
    if time_mode == 'monthly':
        depreciation_per_period = annual_depreciation / 12
    else:
        depreciation_per_period = annual_depreciation
    
    depreciation = pd.Series([depreciation_per_period] * periods, index=revenue_total.index)
    
    ebit = ebitda - depreciation
    pre_tax_income = ebit - interest_expense
    
    taxes = np.maximum(0, pre_tax_income * tax_rate)
    
    net_income = pre_tax_income - taxes
    
    return pd.DataFrame({
        'revenue': revenue_total,
        'cogs_materials': cogs,
        'cogs_direct_labor': direct_payroll,
        'cogs_total': total_cogs,
        'gross_profit': gross_profit,
        'indirect_payroll': indirect_payroll,
        'opex': opex_total,
        'operating_expenses': operating_expenses,
        'ebitda': ebitda,
        'depreciation': depreciation,
        'ebit': ebit,
        'interest': interest_expense,
        'pre_tax_income': pre_tax_income,
        'taxes': taxes,
        'net_income': net_income
    })


def calculate_kpis(income_statement, cash_flow_statement, loan_schedule, pnl_statement=None, 
                   opex_df=None, owner_comp_config=None, time_mode='monthly'):
    """
    Calculate key performance indicators including DSCR and break-even.
    
    Args:
        income_statement: DataFrame from build_income_statement
        cash_flow_statement: DataFrame from build_cash_flow_statement
        loan_schedule: DataFrame from calculate_loan_schedule
        pnl_statement: Optional DataFrame from build_pnl_statement
        opex_df: Optional DataFrame from calculate_opex (for break-even)
        owner_comp_config: Optional dict with owner compensation config
        time_mode: 'monthly' or 'annual'
    
    Returns:
        DataFrame with KPIs per period
    """
    from .underwriting import calculate_dscr, calculate_contribution_margin, calculate_break_even_revenue
    
    ebitda = income_statement['ebitda']
    debt_service = loan_schedule['payment']
    
    dscr = calculate_dscr(ebitda, debt_service, time_mode)
    
    kpi_data = {
        'ebitda': ebitda,
        'debt_service': debt_service,
        'dscr': dscr,
        'ending_cash': cash_flow_statement['ending_cash']
    }
    
    if pnl_statement is not None:
        kpi_data['net_income'] = pnl_statement['net_income']
        kpi_data['taxes'] = pnl_statement['taxes']
        
        revenue = pnl_statement['revenue']
        gross_profit = pnl_statement['gross_profit']
        operating_expenses = pnl_statement['operating_expenses']
        
        net_margin = pd.Series(0.0, index=revenue.index)
        gross_margin = pd.Series(0.0, index=revenue.index)
        overhead_load = pd.Series(0.0, index=revenue.index)
        payroll_pct_revenue = pd.Series(0.0, index=revenue.index)
        contribution_margin = pd.Series(0.0, index=revenue.index)
        
        for i in revenue.index:
            if revenue.iloc[i] > 0:
                net_margin.iloc[i] = pnl_statement['net_income'].iloc[i] / revenue.iloc[i]
                gross_margin.iloc[i] = gross_profit.iloc[i] / revenue.iloc[i]
                overhead_load.iloc[i] = operating_expenses.iloc[i] / revenue.iloc[i]
                
                total_payroll = pnl_statement['cogs_direct_labor'].iloc[i] + pnl_statement['indirect_payroll'].iloc[i]
                payroll_pct_revenue.iloc[i] = total_payroll / revenue.iloc[i]
                
                contribution_margin.iloc[i] = (gross_profit.iloc[i] - pnl_statement['indirect_payroll'].iloc[i]) / revenue.iloc[i]
            else:
                net_margin.iloc[i] = 0
                gross_margin.iloc[i] = 0
                overhead_load.iloc[i] = 0
                payroll_pct_revenue.iloc[i] = 0
                contribution_margin.iloc[i] = 0
        
        kpi_data['net_margin'] = net_margin
        kpi_data['gross_margin'] = gross_margin
        kpi_data['overhead_load'] = overhead_load
        kpi_data['payroll_pct_revenue'] = payroll_pct_revenue
        kpi_data['contribution_margin'] = contribution_margin
        
        if opex_df is not None and owner_comp_config is not None:
            variable_costs = pnl_statement['cogs_total']
            if 'variable_total' in opex_df.columns:
                variable_costs = variable_costs + opex_df['variable_total']
            
            contrib_margin_series = calculate_contribution_margin(revenue, variable_costs)
            avg_contrib_margin = contrib_margin_series.mean()
            
            if time_mode == 'monthly':
                annual_indirect_payroll = pnl_statement['indirect_payroll'].sum()
                annual_fixed_opex = opex_df['fixed_total'].sum() if 'fixed_total' in opex_df.columns else 0
                annual_semi_fixed_opex = opex_df['semi_fixed_total'].sum() if 'semi_fixed_total' in opex_df.columns else 0
                annual_debt_service = debt_service.sum()
            else:
                annual_indirect_payroll = pnl_statement['indirect_payroll'].iloc[0] if len(pnl_statement) > 0 else 0
                annual_fixed_opex = opex_df['fixed_total'].iloc[0] if 'fixed_total' in opex_df.columns and len(opex_df) > 0 else 0
                annual_semi_fixed_opex = opex_df['semi_fixed_total'].iloc[0] if 'semi_fixed_total' in opex_df.columns and len(opex_df) > 0 else 0
                annual_debt_service = debt_service.iloc[0] if len(debt_service) > 0 else 0
            
            owner_salary_annual = owner_comp_config.get('amount', 0.0)
            
            break_even_rev = calculate_break_even_revenue(
                annual_indirect_payroll,
                annual_fixed_opex,
                annual_semi_fixed_opex,
                owner_salary_annual,
                annual_debt_service,
                avg_contrib_margin,
                time_mode
            )
            
            kpi_data['break_even_revenue'] = pd.Series([break_even_rev] * len(revenue), index=revenue.index)
            kpi_data['contribution_margin_pct'] = contrib_margin_series
            kpi_data['fixed_cost_base'] = pd.Series([annual_indirect_payroll + annual_fixed_opex + annual_semi_fixed_opex + owner_salary_annual + annual_debt_service] * len(revenue), index=revenue.index)
    
    return pd.DataFrame(kpi_data)
