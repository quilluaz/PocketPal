import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional


# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


@st.cache_data(ttl=CACHE_TTL)
def get_current_price(ticker: str) -> Optional[float]:
    try:
        stock = yf.Ticker(ticker)
        # Try to get the current price from fast_info first
        if hasattr(stock, 'fast_info') and stock.fast_info:
            price = stock.fast_info.get('lastPrice')
            if price:
                return float(price)
        
        # Fallback to history
        hist = stock.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        
        return None
    except Exception:
        return None


@st.cache_data(ttl=CACHE_TTL)
def get_price_history(ticker: str, period: str = "1mo") -> dict:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {}
        
        return {
            "dates": hist.index.strftime("%Y-%m-%d").tolist(),
            "prices": hist['Close'].tolist()
        }
    except Exception:
        return {}


@st.cache_data(ttl=CACHE_TTL)
def get_ticker_info(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName", info.get("longName", ticker)),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A")
        }
    except Exception:
        return {"name": ticker, "currency": "USD"}


def validate_ticker(ticker: str) -> bool:
    price = get_current_price(ticker)
    return price is not None


def calculate_holdings_value(holdings: list) -> list:
    """
    Calculate current value and gains for a list of holdings.
    Returns list of holdings with added current_price, current_value, gain, gain_pct.
    """
    enriched = []
    
    for holding in holdings:
        ticker = holding.get("ticker", "")
        quantity = float(holding.get("quantity", 0))
        avg_cost = float(holding.get("avg_cost", 0)) if holding.get("avg_cost") else None
        
        current_price = get_current_price(ticker)
        
        enriched_holding = {
            **holding,
            "current_price": current_price,
            "current_value": current_price * quantity if current_price else None,
        }
        
        # Calculate gain if we have cost basis
        if current_price and avg_cost and avg_cost > 0:
            cost_basis = avg_cost * quantity
            current_value = current_price * quantity
            gain = current_value - cost_basis
            gain_pct = ((current_price - avg_cost) / avg_cost) * 100
            
            enriched_holding["cost_basis"] = cost_basis
            enriched_holding["gain"] = gain
            enriched_holding["gain_pct"] = gain_pct
        else:
            enriched_holding["cost_basis"] = None
            enriched_holding["gain"] = None
            enriched_holding["gain_pct"] = None
        
        enriched.append(enriched_holding)
    
    return enriched


def get_total_portfolio_value(holdings: list) -> float:
    total = 0.0
    
    for holding in holdings:
        if "current_value" in holding and holding["current_value"]:
            total += holding["current_value"]
        else:
            # Calculate on the fly
            ticker = holding.get("ticker", "")
            quantity = float(holding.get("quantity", 0))
            price = get_current_price(ticker)
            if price:
                total += price * quantity
    
    return total


@st.cache_data(ttl=3600)
def get_usd_php_rate():
    try:
        # yfinance ticker for USD to PHP
        ticker = yf.Ticker("PHP=X")
        data = ticker.history(period="1d")
        return float(data['Close'].iloc[-1])
    except:
        return 56.0 # Fallback rate
