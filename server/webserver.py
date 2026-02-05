from flask import (
    Flask,
    render_template,
    request,
    abort,
    send_from_directory,
    redirect,
    url_for,
    send_file,
    make_response,
    flash
)
import os
import time
import hmac
import hashlib
import json
from dotenv import load_dotenv

# -------------------------------------------------
# ENVIRONMENT
# -------------------------------------------------
load_dotenv(dotenv_path=".env.local")

FLASK_SECRET = os.getenv("SECRET_KEY", "visionboard-dev-secret")
HMAC_SECRET = os.getenv("HMAC_KEY")

if not HMAC_SECRET:
    raise ValueError("HMAC_SECRET not set in .env.local")

HMAC_SECRET = HMAC_SECRET.encode()

# -------------------------------------------------
# APP
# -------------------------------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET

# -------------------------------------------------
# PATHS
# -------------------------------------------------
ANNOTATED_DIR = "/home/jmc2/VisionBoard-Proj/annotated_images"
CONFIG_PATH = "/home/jmc2/VisionBoard-Proj/config/grading_config.json"

# -------------------------------------------------
# DEFAULT CONFIG
# -------------------------------------------------
DEFAULT_CONFIG = {
    "DEFECT_GRADE_THRESHOLDS": {
        "A": 5,
        "B": 20,
        "C": 50,
        "F": 100
    },
    "MIN_BOX_WIDTH": 6,
    "MIN_BOX_HEIGHT": 6
}

# -------------------------------------------------
# NGROK WARNING SKIP
# -------------------------------------------------
@app.after_request
def skip_ngrok_warning(response):
    response.headers["ngrok-skip-browser-warning"] = "1"
    return response

# -------------------------------------------------
# CONFIG HELPERS (ATOMIC)
# -------------------------------------------------
def load_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=4)
    os.replace(tmp, CONFIG_PATH)

# -------------------------------------------------
# SIGNATURE HELPERS (DOWNLOAD SECURITY)
# -------------------------------------------------
def generate_signature(model, filename, expires):
    msg = f"{model}|{filename}|{expires}".encode()
    return hmac.new(HMAC_SECRET, msg, hashlib.sha256).hexdigest()

def verify_signature(model, filename, expires, signature):
    expected = generate_signature(model, filename, expires)
    return hmac.compare_digest(expected, signature)

# =================================================
# PROFESSOR CONFIG PAGE
# =================================================
@app.route("/config", methods=["GET", "POST"])
def config_page():
    cfg = load_config()

    # Ensure MODEL_DETECTION_CONFIGS exists
    if "MODEL_DETECTION_CONFIGS" not in cfg:
        cfg["MODEL_DETECTION_CONFIGS"] = {}

    if request.method == "POST":
        try:
            # --- Update defect grade thresholds ---
            for grade in cfg["DEFECT_GRADE_THRESHOLDS"]:
                value = request.form.get(f"threshold_{grade}")
                if value is not None:
                    cfg["DEFECT_GRADE_THRESHOLDS"][grade] = int(value)

            # --- Update model detection configs ---
            for model_name, params in cfg["MODEL_DETECTION_CONFIGS"].items():
                conf = request.form.get(f"conf_{model_name}")
                iou = request.form.get(f"iou_{model_name}")
                max_det = request.form.get(f"max_det_{model_name}")

                if conf is not None:
                    params["conf"] = float(conf)
                if iou is not None:
                    params["iou"] = float(iou)
                if max_det is not None:
                    params["max_det"] = int(max_det)

            save_config(cfg)
            flash("Configuration updated successfully!", "success")
            return redirect(url_for("config_page"))

        except Exception as e:
            flash(f"Error saving config: {e}", "danger")

    return render_template("config.html", config=cfg)

# =================================================
# STUDENT DOWNLOAD PAGE
# =================================================
@app.route("/download")
def download_page():
    model = request.args.get("model")
    filename = request.args.get("file")
    expires = request.args.get("expires")
    signature = request.args.get("sig")

    if not all([model, filename, expires, signature]):
        abort(403)

    if time.time() > float(expires):
        return "<h2>Link expired</h2>", 403

    if not verify_signature(model, filename, expires, signature):
        abort(403)

    preview_url = url_for(
        "download_file",
        model=model,
        file=filename,
        expires=expires,
        sig=signature,
        preview=1
    )

    download_url = url_for(
        "download_file",
        model=model,
        file=filename,
        expires=expires,
        sig=signature
    )

    return render_template(
        "download.html",
        filename=filename,
        preview_url=preview_url,
        download_url=download_url
    )

# =================================================
# FILE DELIVERY
# =================================================
@app.route("/download_file")
def download_file():
    model = request.args.get("model")
    filename = request.args.get("file")
    expires = request.args.get("expires")
    signature = request.args.get("sig")
    preview = request.args.get("preview") == "1"

    if not all([model, filename, expires, signature]):
        abort(403)
    if time.time() > float(expires):
        return "<h2>Link expired</h2>", 403
    if not verify_signature(model, filename, expires, signature):
        abort(403)

    file_path = os.path.join(ANNOTATED_DIR, model, filename)
    if not os.path.isfile(file_path):
        abort(404)

    if preview:
        # Use make_response + inline disposition
        response = make_response(send_file(file_path, mimetype="application/pdf"))
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'  # helps Chrome treat it as PDF
        return response
    else:
        return send_file(file_path, mimetype="application/pdf", as_attachment=True)
# =================================================
# RUN
# =================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
