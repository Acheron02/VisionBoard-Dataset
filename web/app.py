from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "visionboard_default_secret")

CONFIG_PATH = "/home/jmc2/VisionBoard-Proj/config/grading_config.json"

@app.after_request
def skip_ngrok_warning(response):
    response.headers["ngrok-skip-browser-warning"] = "1"
    return response

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "DEFECT_GRADE_THRESHOLDS": {"A": 5, "B": 20, "C": 50, "F": 100},
        "MIN_BOX_WIDTH": 6,
        "MIN_BOX_HEIGHT": 6,
        "CUSTOM_DEFECT_COLORS": {
            "open": [255,0,0],
            "short": [0,0,255],
            "90": [255,255,255],
            "ps": [0,255,255],
            "sb": [255,0,255],
            "mc": [255,255,0],
            "resistor": [128,128,128],
            "capacitor": [0,128,255]
        }
    }

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def config_page():
    cfg = load_config()
    if request.method == "POST":
        try:
            thresholds = {grade: int(request.form.get(f"threshold_{grade}"))
                          for grade in ["A","B","C","F"]}
            cfg["DEFECT_GRADE_THRESHOLDS"] = thresholds
            cfg["MIN_BOX_WIDTH"] = int(request.form.get("MIN_BOX_WIDTH"))
            cfg["MIN_BOX_HEIGHT"] = int(request.form.get("MIN_BOX_HEIGHT"))
            save_config(cfg)
            flash("Configuration updated successfully!", "success")
            return redirect(url_for("config_page"))
        except Exception as e:
            flash(f"Error saving config: {e}", "danger")
    return render_template("config.html", config=cfg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
