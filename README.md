# 📈 SaleSense — Sales Prediction App

An AI-powered sales prediction web application built with
Flask, scikit-learn, and Chart.js.

---

## 🚀 Features
- 🔐 Login & Logout Authentication
- 📂 CSV Sales Data Upload (supports BigMart dataset)
- 🤖 ML Prediction (Linear Regression, Random Forest, Gradient Boosting)
- 📊 Interactive Charts (Monthly, Quarterly, Yearly, Growth)
- 🏠 Dashboard with KPI Summary Cards
- 🌐 REST API Endpoints
- 📱 Responsive Design

---

## 📁 Project Structure
SaleSense/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── utils/
│   ├── data_processor.py   # CSV processing logic
│   ├── predictor.py        # ML training & prediction
│   └── chart_data.py       # Chart data generation
├── templates/
│   ├── base.html           # Base layout with sidebar
│   ├── login.html          # Login page
│   ├── dashboard.html      # Dashboard
│   ├── upload.html         # File upload page
│   ├── predict.html        # Prediction page
│   ├── charts.html         # Charts & analytics
│   └── 404.html            # Error page
└── static/
├── css/style.css       # All styling
├── js/main.js          # Frontend JS
└── uploads/            # Uploaded CSV files

---

## ⚙️ Setup & Run

### Step 1 — Install Python
Download from https://www.python.org/downloads/

### Step 2 — Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the app
```bash
python app.py
```

### Step 5 — Open in browser
http://127.0.0.1:5000

---

## 🔑 Default Login
| Username | Password  |
|----------|-----------|
| admin    | admin123  |
| user     | user123   |

---

## 📋 Supported CSV Format
| Column   | Type   | Example     |
|----------|--------|-------------|
| date     | Date   | 2024-01-01  |
| sales    | Number | 15000       |

Also supports **BigMart Sales Dataset** from Kaggle.

---

## 🌐 REST API Endpoints
| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | /api/summary       | Data summary & stats     |
| POST   | /api/predict       | Run prediction           |
| GET    | /api/metrics       | Model comparison metrics |
| GET    | /api/chart-data    | Chart data               |

---

## 🛠 Tech Stack
- **Backend**: Python, Flask
- **ML**: scikit-learn
- **Data**: pandas, numpy
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js