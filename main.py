import os
import requests
import time
from datetime import datetime
import pytz
import threading
from flask import Flask
import smtplib
from email.mime.text import MIMEText

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

# ==========================================
# 🛑 YAHAN APNI DETAILS DAALEIN 🛑
# (Dhyan rakhein ki double quotes " " delete na hon)
# ==========================================

# 1. TELEGRAM DETAILS
TELEGRAM_BOT_TOKEN = "8546186406:AAH_GPECzAUEFK6mv1XKqH0Fcn1rQ3-wAcY"
TELEGRAM_CHAT_ID = "1199001402"

# 2. EMAIL DETAILS
SENDER_EMAIL = "dinesh.finance.trading@gmail.com"      # Ex: dinesh123@gmail.com
EMAIL_APP_PASSWORD = "jrhjiwkjfqxktzlz" # Ex: abcdefghijklmnop (bina space ke)
RECEIVER_EMAIL = "dinesh.finance.trading@gmail.com"    # Jispar mail chahiye (same rakh sakte hain)
# ==========================================

def send_telegram_alert(text):
    if "YAHAN" in TELEGRAM_BOT_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
        print("📱 Telegram Alert Sent!")
    except Exception as e:
        print("❌ Telegram Error:", e)

def send_email_alert(subject, body):
    if "YAHAN" in SENDER_EMAIL: return
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("📧 Email Alert Sent!")
    except Exception as e:
        print("❌ Email Error:", e)

def save_to_google_sheet(timestamp, alert_type, price, change):
    payload = {
        ENTRY_IDS["time"]: timestamp,
        ENTRY_IDS["type"]: alert_type,
        ENTRY_IDS["price"]: str(price),
        ENTRY_IDS["change"]: f"{change:.2f}%"
    }
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"}
    try:
        r = requests.post(FORM_URL, data=payload, headers=headers)
        if r.status_code == 200:
            print(f"[{timestamp}] ✅ SHEET UPDATED!")
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

    print("🚀 ETH TRACKER LIVE (TELEGRAM + EMAIL + SHEET MODE)...\n")
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
                print(f"\n[{current_time}] 🔔 {status} Alert! Firing All Systems...")
                
                # Naye text messages
                tg_msg = f"🚨 *ETH ALERT: {status}* 🚨\n\n⏰ Time: {current_time}\n💸 Price: ₹{current_price_inr}\n📊 Move: {percent:.2f}%"
                email_body = f"ETH ALERT: {status}\n\nTime: {current_time}\nPrice: Rs. {current_price_inr}\nMove: {percent:.2f}%\n\nView your Google Sheet for full logs."
                
                # Teeno jagah data bhejo
                send_telegram_alert(tg_msg)
                send_email_alert(f"ETH Alert: {status} ({percent:.2f}%)", email_body)
                save_to_google_sheet(current_time, status, current_price_inr, percent)
                
                base_price_inr = current_price_inr
                
            time.sleep(2)
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(5)

@app.route('/')
def home():
    return "Tracker is Alive and Running 24/7!"

if __name__ == "__main__":
    tracker_thread = threading.Thread(target=track_eth)
    tracker_thread.daemon = True
    tracker_thread.start()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
