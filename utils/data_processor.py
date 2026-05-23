import pandas as pd
import numpy as np
import os

def process_csv(filepath):
    """
    Process uploaded CSV file.
    Supports both normal sales CSV and BigMart dataset.
    """
    try:
        df = pd.read_csv(filepath)
        df.columns = [c.strip() for c in df.columns]

        # ── Detect BigMart dataset ──
        is_bigmart = "Item_Outlet_Sales" in df.columns

        if is_bigmart:
            # BigMart specific processing
            sales_col = "Item_Outlet_Sales"

            # Use Outlet_Establishment_Year as time reference
            if "Outlet_Establishment_Year" in df.columns:
                df["date"] = pd.to_datetime(df["Outlet_Establishment_Year"], format="%Y")
                date_col = "date"
            else:
                df["date"] = pd.date_range(start="2010-01-01", periods=len(df), freq="MS")
                date_col = "date"

            # Clean sales column
            df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)

            # Fill missing values
            if "Item_Weight" in df.columns:
                df["Item_Weight"] = df["Item_Weight"].fillna(df["Item_Weight"].mean())
            if "Outlet_Size" in df.columns:
                df["Outlet_Size"] = df["Outlet_Size"].fillna("Medium")

        else:
            # Normal CSV processing
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

            date_col  = None
            sales_col = None

            for col in df.columns:
                if any(k in col for k in ["date", "month", "year", "time", "period"]):
                    date_col = col
                if any(k in col for k in ["sale", "revenue", "amount", "total", "price"]):
                    sales_col = col

            if date_col  is None: date_col  = df.columns[0]
            if sales_col is None: sales_col = df.columns[1]

            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])
            df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)

        df = df.sort_values(date_col)

        # Save cleaned version
        cleaned_path = filepath.replace(".csv", "_cleaned.csv")
        df.to_csv(cleaned_path, index=False)

        # Summary stats
        total_sales = float(df[sales_col].sum())
        avg_sales   = float(df[sales_col].mean())
        max_sales   = float(df[sales_col].max())
        min_sales   = float(df[sales_col].min())
        num_records = len(df)

        return {

            "success":    True,
            "rows":       num_records,
            "columns":    list(df.columns),
            "date_col":   date_col,
            "sales_col":  sales_col,
            "is_bigmart": is_bigmart,
            "summary": {
                "total_sales": round(total_sales, 2),
                "avg_sales":   round(avg_sales, 2),
                "max_sales":   round(max_sales, 2),
                "min_sales":   round(min_sales, 2),
                "num_records": num_records
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}