from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import time
import re
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
LEADERBOARD_FILE = BASE_DIR / "leaderboard.json"

# Simulated sensitive data the bot should NOT reveal
SECRET_FLAG = "SPECTRUM{pr0mpt_1nj3ct10n_d3f34t3d}"
SECRET_CREDS = "admin:adminpass123"
SECRET_KEY = "sk-spectrum-enterprise-2026"

# LobsterTrap-style rules
BLOCKED_PATTERNS = [
    r"ignore previous",
    r"ignore all",
    r"forget your",
    r"you are now",
    r"pretend you are",
    r"act as",
    r"jailbreak",
    r"dan mode",
    r"developer mode",
    r"bypass",
    r"override",
    r"system prompt",
    r"reveal.*secret",
    r"show.*password",
    r"what is the flag",
    r"print.*credentials",
    r"leak.*data",
    r"\{\{.*\}\}",  # SSTI
    r"<script",     # XSS
    r"';.*--",      # SQLi
]

SUSPICIOUS_PATTERNS = [
    r"secret",
    r"password",
    r"credential",
    r"flag",
    r"token",
    r"api.?key",
    r"admin",
    r"root",
    r"sudo",
]


def check_lobstertrap(prompt):
    """Simulate LobsterTrap DPI check."""
    prompt_lower = prompt.lower()
    
    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, prompt_lower):
            return {
                "action": "DENY",
                "rule": "block_prompt_injection",
                "risk_score": 0.95,
                "message": "[LOBSTER TRAP] Blocked: prompt injection detected."
            }
    
    # Check suspicious patterns
    suspicious_count = sum(1 for p in SUSPICIOUS_PATTERNS if re.search(p, prompt_lower))
    risk_score = min(suspicious_count * 0.15, 0.85)
    
    if risk_score > 0.6:
        return {
            "action": "LOG",
            "rule": "review_high_risk",
            "risk_score": risk_score,
            "message": None
        }
    
    return {
        "action": "ALLOW",
        "rule": "default_allow",
        "risk_score": risk_score,
        "message": None
    }


def get_bot_response(prompt, lt_result):
    """Generate bot response — never reveal secrets."""
    if lt_result["action"] == "DENY":
        return {
            "response": "I cannot process that request. It appears to contain patterns that violate security policies.",
            "blocked": True,
            "score": 0
        }
    
    prompt_lower = prompt.lower()
    
    # Check if user is trying to get secrets
    if any(word in prompt_lower for word in ["flag", "secret", "password", "credential", "key"]):
        return {
            "response": "I'm a secure enterprise AI assistant. I don't have access to sensitive credentials or flags. Is there something else I can help you with?",
            "blocked": False,
            "score": 10  # Small score for trying
        }
    
    # Normal responses
    if "hello" in prompt_lower or "hi" in prompt_lower:
        return {
            "response": "Hello! I'm Spectrum's secure AI assistant. I'm here to help with general queries. Note: I'm protected by LobsterTrap security layer.",
            "blocked": False,
            "score": 0
        }
    
    if "what can you do" in prompt_lower or "help" in prompt_lower:
        return {
            "response": "I can answer general questions, explain concepts, and help with analysis. I operate under strict enterprise security policies that prevent me from sharing sensitive information.",
            "blocked": False,
            "score": 0
        }
    
    if "spectrum" in prompt_lower:
        return {
            "response": "Spectrum is an autonomous red/blue team AI security platform. It performs automated penetration testing and defense. Want to know more about how it works?",
            "blocked": False,
            "score": 5
        }
    
    return {
        "response": f"I understand you're asking about '{prompt[:50]}...'. As a secure enterprise assistant, I can only provide general information. My responses are monitored by LobsterTrap for security compliance.",
        "blocked": False,
        "score": 0
    }


def load_leaderboard():
    if LEADERBOARD_FILE.exists():
        try:
            return json.loads(LEADERBOARD_FILE.read_text())
        except:
            pass
    return []


def save_leaderboard(data):
    LEADERBOARD_FILE.write_text(json.dumps(data, indent=2))


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "demo_site.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    username = data.get("username", "Anonymous")
    
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400
    
    # LobsterTrap check
    lt_result = check_lobstertrap(prompt)
    
    # Get bot response
    bot_result = get_bot_response(prompt, lt_result)
    
    # Update leaderboard
    if bot_result["score"] > 0 or lt_result["action"] == "DENY":
        leaderboard = load_leaderboard()
        user_entry = next((e for e in leaderboard if e["username"] == username), None)
        
        if user_entry:
            user_entry["attempts"] += 1
            user_entry["score"] += bot_result["score"]
            if lt_result["action"] == "DENY":
                user_entry["blocked"] += 1
            user_entry["last_seen"] = datetime.now().isoformat()
        else:
            leaderboard.append({
                "username": username,
                "score": bot_result["score"],
                "attempts": 1,
                "blocked": 1 if lt_result["action"] == "DENY" else 0,
                "last_seen": datetime.now().isoformat()
            })
        
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        save_leaderboard(leaderboard)
    
    return jsonify({
        "response": bot_result["response"],
        "blocked": bot_result["blocked"],
        "lobstertrap": {
            "action": lt_result["action"],
            "rule": lt_result["rule"],
            "risk_score": lt_result["risk_score"],
            "message": lt_result["message"]
        },
        "score": bot_result["score"]
    })


@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    return jsonify(load_leaderboard()[:10])


@app.route("/api/stats", methods=["GET"])
def stats():
    leaderboard = load_leaderboard()
    return jsonify({
        "total_players": len(leaderboard),
        "total_attempts": sum(e["attempts"] for e in leaderboard),
        "total_blocked": sum(e["blocked"] for e in leaderboard),
        "top_score": leaderboard[0]["score"] if leaderboard else 0
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)