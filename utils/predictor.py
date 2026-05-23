import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

def load_data(filepath):
    """Load and prepare the cleaned CSV data"""
    cleaned_path = filepath.replace(".csv", "_cleaned.csv")
    target = cleaned_path if os.path.exists(cleaned_path) else filepath

    df = pd.read_csv(target)

    # ── Detect BigMart ──
    is_bigmart = "Item_Outlet_Sales" in df.columns

    if is_bigmart:
        sales_col = "Item_Outlet_Sales"
        date_col  = "date"

        if date_col not in df.columns:
            df["date"] = pd.date_range(start="2010-01-01", periods=len(df), freq="MS")

        df[date_col]  = pd.to_datetime(df[date_col], errors="coerce")
        df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)

        # Encode categorical columns
        cat_cols = ["Item_Fat_Content", "Item_Type", "Outlet_Size",
                    "Outlet_Location_Type", "Outlet_Type"]
        for col in cat_cols:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))

    else:
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

        df[date_col]  = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)

    df = df.sort_values(date_col).reset_index(drop=True)
    return df, date_col, sales_col, is_bigmart


def build_features(df, date_col, sales_col, is_bigmart):
    """Create ML features"""
    df = df.copy()
    df["time_index"] = range(len(df))
    df["month"]      = pd.to_datetime(df[date_col]).dt.month
    df["quarter"]    = pd.to_datetime(df[date_col]).dt.quarter
    df["year"]       = pd.to_datetime(df[date_col]).dt.year
    df["month_sin"]  = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"]  = np.cos(2 * np.pi * df["month"] / 12)

    feature_cols = ["time_index", "month", "quarter", "year", "month_sin", "month_cos"]

    # Add BigMart specific features
    if is_bigmart:
        extra_cols = ["Item_Weight", "Item_Visibility", "Item_MRP",
                      "Item_Fat_Content", "Item_Type", "Outlet_Size",
                      "Outlet_Location_Type", "Outlet_Type"]
        for col in extra_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                feature_cols.append(col)
    else:
        if len(df) > 3:
            df["lag_1"]          = df[sales_col].shift(1).fillna(df[sales_col].mean())
            df["lag_2"]          = df[sales_col].shift(2).fillna(df[sales_col].mean())
            df["rolling_mean_3"] = df[sales_col].rolling(3, min_periods=1).mean()
            feature_cols += ["lag_1", "lag_2", "rolling_mean_3"]

    return df, feature_cols


def train_and_predict(filepath, periods=6):
    """Train ML model and predict future sales"""
    df, date_col, sales_col, is_bigmart = load_data(filepath)
    df, feature_cols = build_features(df, date_col, sales_col, is_bigmart)

    X = df[feature_cols].values
    y = df[sales_col].values

    # Choose best model based on data size
    if len(df) < 20:
        model = LinearRegression()
    elif len(df) < 500:
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=150, random_state=42)

    model.fit(X, y)

    # Generate future dates
    last_date    = pd.to_datetime(df[date_col]).max()
    future_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=periods,
        freq="MS"
    )

    # Predict future values
    future_rows = []
    last_sales  = list(df[sales_col].values[-3:])

    for i, fd in enumerate(future_dates):
        row = {
            "time_index": len(df) + i,
            "month":      fd.month,
            "quarter":    fd.quarter,
            "year":       fd.year,
            "month_sin":  np.sin(2 * np.pi * fd.month / 12),
            "month_cos":  np.cos(2 * np.pi * fd.month / 12),
        }

        # Add average values for BigMart features
        if is_bigmart:
            extra_cols = ["Item_Weight", "Item_Visibility", "Item_MRP",
                          "Item_Fat_Content", "Item_Type", "Outlet_Size",
                          "Outlet_Location_Type", "Outlet_Type"]
            for col in extra_cols:
                if col in feature_cols:
                    row[col] = float(df[col].mean())
        else:
            if "lag_1" in feature_cols:
                row["lag_1"]          = last_sales[-1] if last_sales else 0
                row["lag_2"]          = last_sales[-2] if len(last_sales) > 1 else 0
                row["rolling_mean_3"] = np.mean(last_sales[-3:]) if last_sales else 0

        future_rows.append(row)
        pred_val = model.predict([[row[c] for c in feature_cols]])[0]
        last_sales.append(pred_val)

    X_future    = np.array([[row[c] for c in feature_cols] for row in future_rows])
    predictions = model.predict(X_future).tolist()
    predictions = [max(0, round(p, 2)) for p in predictions]

    # Group historical by month for chart
    df["period"] = pd.to_datetime(df[date_col]).dt.strftime("%b %Y")
    grouped      = df.groupby("period", sort=False)[sales_col].sum()

    historical_labels = grouped.index.tolist()
    historical_values = grouped.round(2).tolist()
    future_labels     = [d.strftime("%b %Y") for d in future_dates]

    return {
        "success":     True,
        "historical":  {"labels": historical_labels, "values": historical_values},
        "predictions": {"labels": future_labels,     "values": predictions},
        "model_type":  type(model).__name__,
        "periods":     periods
    }


def get_model_metrics(filepath):
    """Compare all 3 models"""
    df, date_col, sales_col, is_bigmart = load_data(filepath)

    if len(df) < 6:
        return {"success": False, "error": "Need at least 6 data points"}

    df, feature_cols = build_features(df, date_col, sales_col, is_bigmart)
    X = df[feature_cols].values
    y = df[sales_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest":     RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42)
    }

    results = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        results.append({
            "model": name,
            "mae":   round(mean_absolute_error(y_test, preds), 2),
            "rmse":  round(np.sqrt(mean_squared_error(y_test, preds)), 2),
            "r2":    round(r2_score(y_test, preds), 4)
        })

    return {"success": True, "metrics": results}