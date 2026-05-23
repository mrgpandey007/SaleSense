import pandas as pd
import numpy as np
import os

def load_clean(filepath):
    """Load the cleaned CSV file"""
    cleaned = filepath.replace(".csv", "_cleaned.csv")
    target  = cleaned if os.path.exists(cleaned) else filepath

    df = pd.read_csv(target)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Find date and sales columns
    date_col  = None
    sales_col = None
    for col in df.columns:
        if any(k in col for k in ["date", "month", "year", "time", "period"]):
            date_col = col
        if any(k in col for k in ["sale", "revenue", "amount", "total", "price"]):
            sales_col = col

    if date_col  is None: date_col  = df.columns[0]
    if sales_col is None: sales_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    df[date_col]  = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)
    df = df.sort_values(date_col)

    return df, date_col, sales_col


def generate_chart_data(filepath, chart_type="monthly"):
    """Generate chart data based on type"""
    df, date_col, sales_col = load_clean(filepath)

    # Monthly chart
    if chart_type == "monthly":
        df["period"] = df[date_col].dt.strftime("%b %Y")
        grouped = df.groupby("period", sort=False)[sales_col].sum().reset_index()
        return {
            "success": True,
            "labels":  grouped["period"].tolist(),
            "values":  grouped[sales_col].round(2).tolist(),
            "title":   "Monthly Sales"
        }

    # Quarterly chart
    elif chart_type == "quarterly":
        df["quarter"] = df[date_col].dt.year.astype(str) + " Q" + df[date_col].dt.quarter.astype(str)
        grouped = df.groupby("quarter")[sales_col].sum().reset_index()
        return {
            "success": True,
            "labels":  grouped["quarter"].tolist(),
            "values":  grouped[sales_col].round(2).tolist(),
            "title":   "Quarterly Sales"
        }

    # Yearly chart
    elif chart_type == "yearly":
        df["year"] = df[date_col].dt.year
        grouped = df.groupby("year")[sales_col].sum().reset_index()
        return {
            "success": True,
            "labels":  grouped["year"].astype(str).tolist(),
            "values":  grouped[sales_col].round(2).tolist(),
            "title":   "Yearly Sales"
        }

    # Growth chart
    elif chart_type == "growth":
        df["period"] = df[date_col].dt.strftime("%b %Y")
        grouped = df.groupby("period", sort=False)[sales_col].sum()
        growth  = grouped.pct_change().fillna(0) * 100
        return {
            "success": True,
            "labels":  growth.index.tolist(),
            "values":  growth.round(2).tolist(),
            "title":   "Sales Growth (%)"
        }

    # Distribution stats
    elif chart_type == "distribution":
        return {
            "success": True,
            "stats": {
                "min":    round(float(df[sales_col].min()), 2),
                "q1":     round(float(df[sales_col].quantile(0.25)), 2),
                "median": round(float(df[sales_col].median()), 2),
                "mean":   round(float(df[sales_col].mean()), 2),
                "q3":     round(float(df[sales_col].quantile(0.75)), 2),
                "max":    round(float(df[sales_col].max()), 2)
            },
            "title": "Sales Distribution"
        }

    return {"success": False, "error": "Unknown chart type"}