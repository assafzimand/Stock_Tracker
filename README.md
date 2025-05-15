
# Stock Pattern Detection POC

# Project Description

This project is a local proof-of-concept (POC) stock tracker and recommendation system. It collects real-time stock prices for seven major companies, stores the data, and analyzes it to detect the classic "cup and handle" technical pattern. The application runs locally, includes an automated scheduler, and exposes an interactive API for pattern detection and debugging.

The README includes full setup instructions, API usage examples, expected responses, troubleshooting tips, and even visual examples of detected patterns.

For any questions, issues, or feedback, please contact Assaf Zimand via GitHub or email - assafzimand@gmail.com

## 🧰 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/assafzimand/Stock_Tracker.git
cd Stock_Tracker
```

### 2. Create and Activate a Virtual Environment
#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python main.py
```

This will:
- Start the stock price fetch scheduler (runs every 5 mins during US trading hours)
- Open your browser to the Swagger API docs automatically

---

## 🌐 Using the API

Once the server is running, go to:
```
http://127.0.0.1:8000/docs
```

Use the `/detect-pattern` endpoint to check for a **cup and handle** pattern.

### Request Body Example:
```json
{
  "company": "Apple",
  "include_plot": true
}
```

> 🔸 `company` must be one of:  
> `Apple`, `Microsoft`, `Alphabet`, `Amazon`, `Nvidia`, `Meta`, `Tesla`

---

### ✅ Successful Response:
```json
{
  "company": "Apple",
  "pattern_detected": true,
  "plot_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```
## 🖼️ How to View the Plot

If `include_plot` is set to `true`, the response will contain a `plot_base64` string.  
This is an image encoded in base64 format (PNG).

### To view it:

#### Option 1: Use an online viewer
1. Copy the `plot_base64` string from the response
2. Go to a site like https://codebeautify.org/base64-to-image-converter
3. Paste it into the input box
4. Click **View** or **Convert**

#### Option 2: Programmatically decode it (Python)
```python
import base64

b64_str = "your_base64_string_here"
with open("plot.png", "wb") as f:
    f.write(base64.b64decode(b64_str))
```

This saves the plot as `plot.png` on your machine.

---

## ⚠️ Errors You Might See

| Status | Message | What It Means |
|--------|---------|----------------|
| 400 | "As for now, there is not enough data to analyze a pattern for company: Apple" | Not enough data was collected yet |
| 400 | "company: value is not a valid enumeration member" | Company name is invalid — must be one of the 7 |
| 422 | "Unprocessable Entity" | Request body is malformed (e.g., wrong JSON format) |

---

## ❌ Stopping the App

Press `CTRL+C` in the terminal to stop the server.  
The app will gracefully shut down the background scheduler.

You’ll see:
```
[INFO] Scheduler stopped.
INFO:     Application shutdown complete.
```

---

## 📊 Example Pattern Visuals

Here are sample plots of detected patterns:

| Pattern Not Detected | Pattern Detected |
|----------------------|------------------|
| ![79](./app/docs/78.png) | ![87](./app/docs/87.png) |
| ![91](./app/docs/79.png) | ![80](./app/docs/80.png) |
