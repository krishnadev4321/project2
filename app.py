# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from collections import defaultdict
from flask_cors import CORS

# Flask app
app = Flask(__name__, static_folder="")
CORS(app)  # allow all origins

# -------------------------------
# Gemini API setup (hardcoded key)
# -------------------------------
GEMINI_API_KEY = "AIzaSyBHyiMX-EZwVo4G_NSOGGMu4itjKoguRmA"  # <- direct key
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# Track IP message count
ip_count = defaultdict(int)
MAX_MESSAGES = 20  # per IP limit

# Serve image files
@app.route("/images/<path:filename>")
def serve_images(filename):
    return send_from_directory("images", filename)

# Serve HTML pages from root folder
@app.route("/", defaults={"page": "index.html"})
@app.route("/<path:page>")
def serve_page(page):
    if os.path.exists(page):
        return send_from_directory(".", page)
    return "Page not found", 404

# Chatbot API route
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    user_ip = request.remote_addr
    ip_count[user_ip] += 1
    print(f"[LOG] IP {user_ip} message count: {ip_count[user_ip]}")

    if ip_count[user_ip] > MAX_MESSAGES:
        return jsonify({"reply": f"Limit reached: {MAX_MESSAGES} messages per day per device."})

    # Prepare Gemini API request
    data = {
        "contents": [{
            "parts": [{
                "text": f"""
You are a BCA Guide assistant for students using the BCA Guide website. 
1. agar student BCA se related kuch bhi puche, to hamesh BCA Guide ka naam batana aur website ke features explain karna (PYQs, syllabus, assignments, templates). 
2. Agar user unrelated question puche, simple short answer dena. 
3. Agar student kisi programming language ka code maange, short me example dena. 
4. Keep responses short, friendly, and relevant.
5. Reply in the same language as user.
6. Answer the user's question: {user_input}
"""
            }]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error calling Gemini API:", e)
        return jsonify({"reply": "Server error. Please try again later."})

    # Extract bot reply
    try:
        res_json = response.json()
        bot_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Error extracting reply:", e)
        bot_reply = "Sorry, I couldn't understand that."

    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
