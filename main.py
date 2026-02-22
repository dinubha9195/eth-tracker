import os
import requests
import time
from datetime import datetime
import pytz
import threading
from flask import Flask

app = Flask(__name__)

# --- CONFIGURATION (2% ALERT MODE) ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf3G0bM5exgKEoYo-NNSnw023CWgNrXzGjCK4VMp3Slccowqg/formResponse"

ENTRY_IDS = {
    "time": "entry.1264040378",
    "type": "entry.1106109676",
    "price": "entry.2030424992",
    "change": "entry.1319672427"
}

ALERT_PERCENTAGE = 2.0 
# ---------------------

def save_to_google_sheet(timestamp, alert_type, price, change):
    payload = {
        ENTRY_IDS["time"]: timestamp,
        ENTRY_IDS["type"]: alert_type,
        ENTRY_IDS["price"]: str(price),
        ENTRY_IDS["change"]: f"{change:.2f}%"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        r = requests.post(FORM_URL, data=payload, headers=headers)
        if r.status_code == 200:
            print(f"[{timestamp}] ✅ SHEET UPDATED SUCCESSFULLY!")
        else:
            print(f"[{timestamp}] ⚠️ Failed! Status code: {r.status_code}")
    except Exception as e:
        print("❌ Network Error:", e)

def track_eth():
    print("🔍 Fetching Market Rate...")
    try:
        fx_res = requests.get("https://open.er-api.com/v6/latest/USD")
        USDT_TO_INR_RATE = fx_res.json()['rates']['INR']
        print(f"✅ Live Rate: ₹{USDT_TO_INR_RATE}\n")
    except:
        USDT_TO_INR_RATE = 90.95
        print("⚠️ Using Fixed Rate: ₹90.95\n")

    print("🚀 ETH TRACKER LIVE (RENDER 24/7 MODE)...\n")
    base_price_inr = None
    ist_timezone = pytz.timezone('Asia/Kolkata')

    while True:
        try:
            url = "https://api.coinbase.com/v2/prices/ETH-USD/spot"
            data = requests.get(url).json()
            usd_price = float(data['data']['amount'])
            current_price_inr = round(usd_price * USDT_TO_INR_RATE, 2)
            
            current_time = datetime.now(ist_timezone).strftime("%d-%m-%Y %I:%M:%S %p")
            
            if base_price_inr is None:
                base_price_inr = current_price_inr
                print(f"[{current_time}] 🎯 Base set: ₹{base_price_inr}")

            print(f"[{current_time}] 👉 Current Price: ₹{current_price_inr} (Waiting for 2% move...)")

            diff = current_price_inr - base_price_inr
            percent = (diff / base_price_inr) * 100
            
            if abs(percent) >= ALERT_PERCENTAGE:
                status = "UP 🟢" if percent > 0 else "DOWN 🔴"
                print(f"[{current_time}] 🔔 {status} Alert! Sending to Sheet...")
                save_to_google_sheet(current_time, status, current_price_inr, percent)
                base_price_inr = current_price_inr
                
            time.sleep(2)
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(5)

# Yeh UptimeRobot ke liye darwaza hai
@app.route('/')
def home():
    return "Tracker is Alive and Running 24/7!"

if __name__ == "__main__":
    # Background mein price check chalu karo
    tracker_thread = threading.Thread(target=track_eth)
    tracker_thread.daemon = True
    tracker_thread.start()
    
    # Web server chalu karo
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
