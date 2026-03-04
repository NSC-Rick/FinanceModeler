"""
Scenario export utilities for JSON and Excel formats.
"""
import json
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Optional, Union

# Check for openpyxl availability
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def export_scenario_to_excel(
    model_inputs: dict,
    income_statement_df: Optional[pd.DataFrame] = None,
    cash_flow_df: Optional[pd.DataFrame] = None,
    dscr_series_or_df: Optional[Union[pd.Series, pd.DataFrame]] = None,
    include_raw_json: bool = True
) -> bytes:
    """
    Export scenario to Excel format with multiple sheets.
    
    Raises:
        ImportError: If openpyxl is not installed
    
    Args:
        model_inputs: Dictionary of model inputs from session_state_to_model_inputs
        income_statement_df: Income statement DataFrame (reused from UI display)
        cash_flow_df: Cash flow DataFrame (reused from UI display)
        dscr_series_or_df: Optional DSCR series or DataFrame
        include_raw_json: Whether to include Raw JSON sheet
    
    Returns:
        bytes: Excel file as bytes for download
    """
    # Check if openpyxl is available
    if not OPENPYXL_AVAILABLE:
        raise ImportError(
            "openpyxl is required for Excel export. "
            "Install it with: pip install openpyxl"
        )
    
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Sheet 1: Summary (if DataFrames provided)
        if income_statement_df is not None or cash_flow_df is not None:
            _write_summary_sheet(writer, income_statement_df, cash_flow_df, dscr_series_or_df)
        
        # Sheet 2: Scenario Metadata
        _write_scenario_sheet(writer, model_inputs)
        
        # Sheet 3: Income Statement (if provided)
        if income_statement_df is not None:
            _write_income_statement_sheet(writer, income_statement_df)
        
        # Sheet 4: Cash Flow (if provided)
        if cash_flow_df is not None:
            _write_cash_flow_sheet(writer, cash_flow_df)
        
        # Sheet 5: Raw JSON (optional)
        if include_raw_json:
            _write_raw_json_sheet(writer, model_inputs)
    
    buffer.seek(0)
    return buffer.getvalue()


def build_summary_df(
    income_statement_df: Optional[pd.DataFrame],
    cash_flow_df: Optional[pd.DataFrame],
    dscr_series_or_df: Optional[Union[pd.Series, pd.DataFrame]] = None
) -> pd.DataFrame:
    """
    Build summary DataFrame with key metrics using robust label matching.
    
    Args:
        income_statement_df: Income statement DataFrame
        cash_flow_df: Cash flow DataFrame
        dscr_series_or_df: Optional DSCR series or DataFrame
    
    Returns:
        DataFrame with summary metrics
    """
    summary_data = {}
    notes = []
    
    # Get column names (periods)
    if income_statement_df is not None:
        columns = income_statement_df.columns.tolist()
    elif cash_flow_df is not None:
        columns = cash_flow_df.columns.tolist()
    else:
        columns = []
    
    # 1. Revenue
    revenue = _extract_row_by_labels(
        income_statement_df,
        ['Revenue', 'Total Revenue', 'Sales', 'Total Sales'],
        'Revenue'
    )
    if revenue is not None:
        summary_data['Revenue'] = revenue
    else:
        summary_data['Revenue'] = [None] * len(columns)
        notes.append('Revenue: Label not found in income statement')
    
    # 2. Gross Margin ($)
    gross_profit = _extract_row_by_labels(
        income_statement_df,
        ['Gross Profit', 'Gross Margin'],
        'Gross Profit'
    )
    
    if gross_profit is None and income_statement_df is not None:
        # Try to compute from Revenue - COGS
        cogs = _extract_row_by_labels(
            income_statement_df,
            ['COGS', 'Cost of Goods Sold', 'Direct Costs'],
            'COGS'
        )
        if revenue is not None and cogs is not None:
            gross_profit = revenue - cogs
    
    if gross_profit is not None:
        summary_data['Gross Margin ($)'] = gross_profit
    else:
        summary_data['Gross Margin ($)'] = [None] * len(columns)
        notes.append('Gross Margin ($): Could not compute (missing Gross Profit or Revenue/COGS)')
    
    # 3. Gross Margin (%)
    if revenue is not None and gross_profit is not None:
        # Handle divide by zero
        gm_pct = []
        for r, gp in zip(revenue, gross_profit):
            if r != 0 and r is not None and gp is not None:
                gm_pct.append(gp / r)
            else:
                gm_pct.append(None)
        summary_data['Gross Margin (%)'] = gm_pct
    else:
        summary_data['Gross Margin (%)'] = [None] * len(columns)
        notes.append('Gross Margin (%): Could not compute (missing Revenue or Gross Profit)')
    
    # 4. Net Income
    net_income = _extract_row_by_labels(
        income_statement_df,
        ['Net Income', 'Net Profit', 'Profit (Loss)'],
        'Net Income'
    )
    if net_income is not None:
        summary_data['Net Income'] = net_income
    else:
        summary_data['Net Income'] = [None] * len(columns)
        notes.append('Net Income: Label not found in income statement')
    
    # 5. DSCR
    if dscr_series_or_df is not None:
        if isinstance(dscr_series_or_df, pd.Series):
            summary_data['DSCR'] = dscr_series_or_df.tolist()
        elif isinstance(dscr_series_or_df, pd.DataFrame):
            # Try to find DSCR column
            dscr_col = None
            for col in dscr_series_or_df.columns:
                if 'DSCR' in str(col).upper():
                    dscr_col = col
                    break
            if dscr_col:
                summary_data['DSCR'] = dscr_series_or_df[dscr_col].tolist()
            else:
                summary_data['DSCR'] = [None] * len(columns)
                notes.append('DSCR: Column not found in provided DataFrame')
        else:
            summary_data['DSCR'] = [None] * len(columns)
            notes.append('DSCR: Invalid data type provided')
    else:
        summary_data['DSCR'] = [None] * len(columns)
        notes.append('DSCR: Not computed (missing debt service components)')
    
    # 6. Ending Cash
    ending_cash = _extract_row_by_labels(
        cash_flow_df,
        ['Ending Cash', 'Ending Cash Balance', 'Cash End', 'Cash Balance (End)'],
        'Ending Cash'
    )
    if ending_cash is not None:
        summary_data['Ending Cash'] = ending_cash
    else:
        summary_data['Ending Cash'] = [None] * len(columns)
        notes.append('Ending Cash: Label not found in cash flow statement')
    
    # Create DataFrame
    df = pd.DataFrame(summary_data, index=columns).T
    df.index.name = 'Metric'
    
    # Add notes as additional rows if any
    if notes:
        notes_df = pd.DataFrame({col: [''] for col in columns}, index=[''])
        notes_df = pd.concat([notes_df, pd.DataFrame({col: ['NOTES:'] for col in columns}, index=[''])])
        for note in notes:
            notes_df = pd.concat([notes_df, pd.DataFrame({col: [note] if i == 0 else [''] for i, col in enumerate(columns)}, index=[''])])
        df = pd.concat([df, notes_df])
    
    return df


def _extract_row_by_labels(df: Optional[pd.DataFrame], labels: list, metric_name: str) -> Optional[list]:
    """
    Extract row from DataFrame by trying multiple label matches.
    
    Args:
        df: DataFrame to search
        labels: List of possible row labels (in priority order)
        metric_name: Name of metric for logging
    
    Returns:
        List of values if found, None otherwise
    """
    if df is None:
        return None
    
    for label in labels:
        if label in df.index:
            return df.loc[label].tolist()
    
    return None


def _write_scenario_sheet(writer, model_inputs):
    """Write scenario metadata sheet with key assumptions."""
    metadata = []
    
    # Basic Info
    metadata.append(('Scenario Name', model_inputs.get('scenario_name', 'Unnamed Scenario')))
    metadata.append(('Generated At', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    metadata.append(('Time Mode', model_inputs.get('time_mode', 'monthly')))
    metadata.append(('Periods', model_inputs.get('periods', 0)))
    
    # Revenue Settings
    metadata.append(('', ''))
    metadata.append(('REVENUE SETTINGS', ''))
    metadata.append(('Global COGS %', f"{model_inputs.get('global_cogs_pct', 0) * 100:.1f}%"))
    metadata.append(('COGS Improvement per Year %', f"{model_inputs.get('cogs_improvement_pct', 0):.1f}%"))
    metadata.append(('Startup Ramp (Months)', model_inputs.get('startup_ramp_months', 0)))
    
    # Revenue Streams
    revenue_streams = model_inputs.get('revenue_streams', [])
    if revenue_streams:
        metadata.append(('', ''))
        metadata.append(('REVENUE STREAMS', ''))
        for i, stream in enumerate(revenue_streams, 1):
            metadata.append((f"Stream {i}: {stream.get('name', 'Unnamed')}", ''))
            metadata.append((f"  Price", f"${stream.get('price', 0):.2f}"))
            metadata.append((f"  Volume", f"{stream.get('volume', 0):.2f}"))
            metadata.append((f"  Growth Rate", f"{stream.get('growth_rate', 0) * 100:.1f}%"))
            if stream.get('cogs_override') is not None:
                metadata.append((f"  COGS Override", f"{stream.get('cogs_override') * 100:.1f}%"))
    
    # Financing
    metadata.append(('', ''))
    metadata.append(('FINANCING', ''))
    metadata.append(('Loan Principal', f"${model_inputs.get('loan_principal', 0):,.2f}"))
    metadata.append(('Annual Interest Rate', f"{model_inputs.get('loan_annual_rate', 0) * 100:.2f}%"))
    metadata.append(('Loan Term (Months)', model_inputs.get('loan_term_months', 0)))
    metadata.append(('Loan Start Period', model_inputs.get('loan_start_period', 0)))
    
    # Advanced Financing (if in advanced mode)
    if model_inputs.get('mode') == 'Advanced':
        metadata.append(('', ''))
        metadata.append(('ADVANCED FINANCING', ''))
        metadata.append(('Business Loan Amount', f"${model_inputs.get('business_loan_amount', 0):,.2f}"))
        metadata.append(('Business Interest Rate', f"{model_inputs.get('business_interest_rate', 0) * 100:.2f}%"))
        metadata.append(('Business Amortization (Years)', model_inputs.get('business_amort_years', 0)))
        metadata.append(('Real Estate Loan Amount', f"${model_inputs.get('real_estate_loan_amount', 0):,.2f}"))
        metadata.append(('Real Estate Interest Rate', f"{model_inputs.get('real_estate_interest_rate', 0) * 100:.2f}%"))
        metadata.append(('Real Estate Amortization (Years)', model_inputs.get('real_estate_amort_years', 0)))
    
    # Owner Compensation
    owner_comp = model_inputs.get('owner_compensation', {})
    if owner_comp:
        metadata.append(('', ''))
        metadata.append(('OWNER COMPENSATION', ''))
        metadata.append(('Mode', owner_comp.get('mode', 'distribution').title()))
        metadata.append(('Annual Amount', f"${owner_comp.get('amount', 0):,.2f}"))
    
    # Tax & Depreciation
    metadata.append(('', ''))
    metadata.append(('TAX & DEPRECIATION', ''))
    metadata.append(('Corporate Tax Rate', f"{model_inputs.get('tax_rate', 0) * 100:.1f}%"))
    metadata.append(('Annual Depreciation', f"${model_inputs.get('annual_depreciation', 0):,.2f}"))
    
    # Working Capital
    metadata.append(('', ''))
    metadata.append(('WORKING CAPITAL', ''))
    metadata.append(('AR Days', model_inputs.get('ar_days', 0)))
    metadata.append(('AP Days', model_inputs.get('ap_days', 0)))
    metadata.append(('Inventory Days', model_inputs.get('inventory_days', 0)))
    
    # Payroll
    payroll_roles = model_inputs.get('payroll_roles', [])
    if payroll_roles:
        metadata.append(('', ''))
        metadata.append(('PAYROLL', ''))
        for i, role in enumerate(payroll_roles, 1):
            metadata.append((f"Role {i}: {role.get('name', 'Unnamed')}", ''))
            metadata.append((f"  Count", role.get('count', 0)))
            metadata.append((f"  Annual Salary", f"${role.get('annual_salary', 0):,.2f}"))
            metadata.append((f"  Payroll Tax Rate", f"{role.get('payroll_tax_rate', 0) * 100:.1f}%"))
            metadata.append((f"  Category", role.get('category', 'indirect')))
    
    # Create DataFrame
    df = pd.DataFrame(metadata, columns=['Parameter', 'Value'])
    df.to_excel(writer, sheet_name='Scenario', index=False)
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Scenario']
    worksheet.column_dimensions['A'].width = 40
    worksheet.column_dimensions['B'].width = 25


def _write_summary_sheet(writer, income_statement_df, cash_flow_df, dscr_series_or_df):
    """Write summary sheet with key metrics."""
    summary_df = build_summary_df(income_statement_df, cash_flow_df, dscr_series_or_df)
    summary_df.to_excel(writer, sheet_name='Summary')
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Summary']
    worksheet.column_dimensions['A'].width = 25
    for col_idx in range(2, len(summary_df.columns) + 2):
        worksheet.column_dimensions[chr(64 + col_idx)].width = 15


def _write_income_statement_sheet(writer, income_statement_df):
    """Write income statement sheet using existing DataFrame."""
    income_statement_df.to_excel(writer, sheet_name='Income_Statement')
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Income_Statement']
    worksheet.column_dimensions['A'].width = 25
    for col_idx in range(2, len(income_statement_df.columns) + 2):
        worksheet.column_dimensions[chr(64 + col_idx)].width = 15


def _write_cash_flow_sheet(writer, cash_flow_df):
    """Write cash flow sheet using existing DataFrame."""
    cash_flow_df.to_excel(writer, sheet_name='Cash_Flow')
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Cash_Flow']
    worksheet.column_dimensions['A'].width = 25
    for col_idx in range(2, len(cash_flow_df.columns) + 2):
        worksheet.column_dimensions[chr(64 + col_idx)].width = 15


def _write_raw_json_sheet(writer, model_inputs):
    """Write raw JSON data as text for traceability."""
    json_str = json.dumps(model_inputs, indent=2)
    
    # Split JSON into lines for better readability
    lines = json_str.split('\n')
    df = pd.DataFrame({'JSON': lines})
    
    df.to_excel(writer, sheet_name='Raw_JSON', index=False)
    
    # Auto-adjust column width
    worksheet = writer.sheets['Raw_JSON']
    worksheet.column_dimensions['A'].width = 100
