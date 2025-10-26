# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from collections import defaultdict  # <-- ye add karo

# Root folder as static folder
app = Flask(__name__, static_folder="")

# Gemini API setup
GEMINI_API_KEY = "AIzaSyBHyiMX-EZwVo4G_NSOGGMu4itjKoguRmA"
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

    data = {
    "contents": [{
        "parts": [{
            "text": f"""
You are a BCA Guide assistant for students using the BCA Guide website. 
1. agar student bca se related kuch bhi puche to usse hamesh Bca guide ki website ka hi naam batana ki aap yaha se taiayrri kar sakte hai isme saare pyqs and syllabus assignment templates hai jo ki aapki bca ki journey ko aasan bana sakte hai. mtlb issi tarah karke bolna
2. agar user bca se unrelated puche to ussse uksa jawab dena .
a. agar koi student kisi bhi language ka code mange to usse dena dena but short me .
3. Keep responses extra short, friendly, and focused on how students can prepare using this website.
4. User jis language me baat kare tum uss language me baat karo.
5. Never give very long answers. 
6. Answer the user's question: {user_input}
"""
        }]
    }]
}

    headers = {"Content-Type": "application/json"}

    response = requests.post(GEMINI_API_URL, headers=headers, json=data)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return jsonify({"reply": "Server error. Please try again."})

    res_json = response.json()
    try:
        bot_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Error extracting reply:", e)
        bot_reply = "Sorry, I couldn't understand that."

    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    app.run(debug=True)
