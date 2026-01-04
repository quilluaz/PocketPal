import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def create_sankey_diagram(transactions_df: pd.DataFrame, symbol: str = "$", title: str = "Cash Flow") -> go.Figure:
    if transactions_df.empty:
        return _empty_chart("No transactions to display")
    
    income_df = transactions_df[transactions_df['amount'] > 0].copy()
    expense_df = transactions_df[transactions_df['amount'] < 0].copy()
    
    income_by_cat = income_df.groupby('category')['amount'].sum().abs()
    expense_by_cat = expense_df.groupby('category')['amount'].sum().abs()
    
    if income_by_cat.empty and expense_by_cat.empty:
        return _empty_chart("No income or expenses found")
    
    nodes, node_colors, links_source, links_target, links_value, links_color = [], [], [], [], [], []
    
    income_idx = {}
    for cat in income_by_cat.index:
        income_idx[cat] = len(nodes)
        nodes.append(cat)
        node_colors.append("#22c55e")
    
    income_node_idx = len(nodes)
    nodes.append("Total Income")
    node_colors.append("#16a34a")
    
    expense_node_idx = len(nodes)
    nodes.append("Expenses")
    node_colors.append("#dc2626")
    
    expense_idx = {}
    for cat in expense_by_cat.index:
        expense_idx[cat] = len(nodes)
        nodes.append(cat)
        node_colors.append("#ef4444")
    
    for cat, amount in income_by_cat.items():
        links_source.append(income_idx[cat])
        links_target.append(income_node_idx)
        links_value.append(amount)
        links_color.append("rgba(34, 197, 94, 0.4)")
    
    total_expense = expense_by_cat.sum() if not expense_by_cat.empty else 0
    if total_expense > 0:
        links_source.append(income_node_idx)
        links_target.append(expense_node_idx)
        links_value.append(total_expense)
        links_color.append("rgba(220, 38, 38, 0.4)")
    
    for cat, amount in expense_by_cat.items():
        links_source.append(expense_node_idx)
        links_target.append(expense_idx[cat])
        links_value.append(amount)
        links_color.append("rgba(239, 68, 68, 0.4)")
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=nodes, color=node_colors),
        link=dict(source=links_source, target=links_target, value=links_value, color=links_color)
    )])
    
    fig.update_layout(title_text=title, font_size=12, height=500, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_spending_by_category_chart(transactions_df: pd.DataFrame, symbol: str = "$") -> go.Figure:
    if transactions_df.empty:
        return _empty_chart("No transactions to display")
    
    expenses = transactions_df[transactions_df['amount'] < 0].copy()
    expenses['amount'] = expenses['amount'].abs()
    
    if expenses.empty:
        return _empty_chart("No expenses found")
    
    by_category = expenses.groupby('category')['amount'].sum().sort_values(ascending=True)
    
    fig = go.Figure(data=[go.Bar(x=by_category.values, y=by_category.index, orientation='h', marker_color='#ef4444')])
    fig.update_layout(title="Spending by Category", xaxis_title=f"Amount ({symbol})", yaxis_title="", height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_spending_trend_chart(transactions_df: pd.DataFrame, symbol: str = "$") -> go.Figure:
    if transactions_df.empty:
        return _empty_chart("No transactions to display")
    
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    monthly = df.groupby('month').agg({'amount': lambda x: (x[x > 0].sum(), x[x < 0].sum().abs())}).reset_index()
    monthly['income'], monthly['expenses'] = monthly['amount'].apply(lambda x: x[0]), monthly['amount'].apply(lambda x: x[1])
    monthly['net'] = monthly['income'] - monthly['expenses']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['income'], name='Income', line=dict(color='#22c55e', width=2), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['expenses'], name='Expenses', line=dict(color='#ef4444', width=2), mode='lines+markers'))
    fig.add_trace(go.Bar(x=monthly['month'], y=monthly['net'], name='Net', marker_color=['#22c55e' if v >= 0 else '#ef4444' for v in monthly['net']], opacity=0.5))
    
    fig.update_layout(title="Monthly Income vs Expenses", xaxis_title="Month", yaxis_title=f"Amount ({symbol})", height=400, barmode='overlay', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def create_holdings_chart(holdings: list) -> go.Figure:
    if not holdings: return _empty_chart("No holdings to display")
    valid_holdings = [h for h in holdings if h.get('current_value')]
    if not valid_holdings: return _empty_chart("Unable to fetch prices")
    
    fig = go.Figure(data=[go.Pie(labels=[h['ticker'] for h in valid_holdings], values=[h['current_value'] for h in valid_holdings], hole=0.4, marker_colors=px.colors.qualitative.Set3)])
    fig.update_layout(title="Portfolio Allocation", height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def calculate_kpis(transactions_df: pd.DataFrame, portfolio_value: float = 0) -> dict:
    kpis = {"net_worth": portfolio_value, "monthly_income": 0, "monthly_expenses": 0, "burn_rate": 0, "savings_rate": 0}
    if transactions_df.empty: return kpis
    
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    three_months_ago = datetime.now() - timedelta(days=90)
    recent = df[df['date'] >= three_months_ago]
    if recent.empty: recent = df
    
    months_span = max(1, (recent['date'].max() - recent['date'].min()).days / 30)
    total_income = recent[recent['amount'] > 0]['amount'].sum()
    total_expenses = recent[recent['amount'] < 0]['amount'].sum().abs() if not recent[recent['amount'] < 0].empty else 0
    
    kpis["monthly_income"], kpis["monthly_expenses"] = total_income / months_span, total_expenses / months_span
    kpis["burn_rate"], net_cash = kpis["monthly_expenses"], total_income - total_expenses
    kpis["net_worth"] = portfolio_value + net_cash
    
    if kpis["monthly_income"] > 0:
        kpis["savings_rate"] = ((kpis["monthly_income"] - kpis["monthly_expenses"]) / kpis["monthly_income"]) * 100
    return kpis

def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray"))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig
