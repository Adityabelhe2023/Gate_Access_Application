import requests
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Enable CORS for the entire app
CORS(app)

# Google Sheets setup
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VzBsVQ4heD2H-Y6UmTuECHPnneUzUAmw8zL88nXMUwo/edit"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = r"C:/Users/belhe/Downloads/gateaccess-2025-1642ff0f0d43.json"

# Telegram Bot setup
BOT_TOKEN = '8073287976:AAGhC384KVtMTsvSj94L9jdDWv59Bx3J1r4'  #  Bot's token

def send_telegram_message(chat_id, message):
    print(f"Sending to chat_id: {chat_id}, message: {message}")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, params=params)
    print(f"Telegram response: {response.text}")  # Added this to capture response from telegram
    return response.json()


# Initialize Google Sheets client
def get_sheet_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    return client

# Endpoint to handle visitor entries
@app.route("/visitor", methods=["POST"])
def handle_visitor():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    flat_number = data.get("flat_number")
    visitor_name = data.get("visitor_name")
    purpose = data.get("purpose")

    if not flat_number or not visitor_name or not purpose:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Access Google Sheet
        sheet_client = get_sheet_client()
        sheet = sheet_client.open_by_url(SHEET_URL).sheet1
        rows = sheet.get_all_records()

        owner = next((row for row in rows if str(row['Flat Number']) == flat_number), None)
        if not owner:
            return jsonify({"error": "Flat not found"}), 404

        # Forming the message to send to the owner
        message = f"Visitor {visitor_name} is at your gate for {purpose}."
        print(f"Message to send: {message}")  # Debugging print statement

        # Send Telegram message to the owner
        send_telegram_message(str(owner['Telegram ID']), message)

        return jsonify({
            "flat_number": flat_number,
            "visitor_name": visitor_name,
            "purpose": purpose,
            "owner_name": owner['Owner Name'],
            "telegram_id": owner['Telegram ID']
        }), 200

    except gspread.exceptions.APIError as e:
        return jsonify({"error": "Google Sheets error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
