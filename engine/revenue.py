import pandas as pd
import numpy as np


def calculate_revenue(revenue_streams, time_mode, periods):
    """
    Calculate revenue for multiple streams over time.
    
    Args:
        revenue_streams: List of dicts with keys: name, price, volume, growth_rate, cogs_override
        time_mode: 'monthly' or 'annual'
        periods: Number of periods
    
    Returns:
        DataFrame with period index and column per revenue stream plus total
    """
    if not revenue_streams:
        df = pd.DataFrame({'period': range(periods), 'total': [0] * periods})
        return df.set_index('period')
    
    revenue_data = {'period': range(periods)}
    
    for stream in revenue_streams:
        name = stream['name']
        price = stream['price']
        initial_volume = stream['volume']
        growth_rate = stream['growth_rate']
        
        revenues = []
        for period in range(periods):
            if time_mode == 'monthly':
                monthly_growth = (1 + growth_rate) ** (1/12) - 1
                volume = initial_volume * (1 + monthly_growth) ** period
            else:
                volume = initial_volume * (1 + growth_rate) ** period
            
            revenues.append(price * volume)
        
        revenue_data[name] = revenues
    
    df = pd.DataFrame(revenue_data)
    df['total'] = df.drop('period', axis=1).sum(axis=1)
    
    return df.set_index('period')


def calculate_cogs(revenue_df, revenue_streams, global_cogs_pct):
    """
    Calculate COGS based on revenue.
    
    Args:
        revenue_df: DataFrame from calculate_revenue
        revenue_streams: List of revenue stream dicts (with optional cogs_override)
        global_cogs_pct: Default COGS percentage (e.g., 0.30 for 30%)
    
    Returns:
        Series with COGS per period
    """
    cogs = pd.Series(0.0, index=revenue_df.index)
    
    for stream in revenue_streams:
        name = stream['name']
        cogs_override = stream.get('cogs_override')
        cogs_pct = cogs_override if cogs_override is not None else global_cogs_pct
        
        if name in revenue_df.columns:
            cogs += revenue_df[name] * cogs_pct
    
    return cogs
