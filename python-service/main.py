"""
Farmer Advisory API — crop recommendation, yield estimate, image heuristics,
tool suggestions, and weather via Open-Meteo (no API key).
Flask keeps installs lightweight on Windows/Python 3.14+.
"""

from __future__ import annotations

import io
import os
from typing import Any

import httpx
from flask import Flask, abort, jsonify, request
from flask_cors import CORS
from PIL import Image, ImageStat
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)


# --- Crop recommendation (weighted rules) ---

CROPS: list[dict[str, Any]] = [
    {
        "name": "Rice (paddy)",
        "ph": (5.5, 7.5),
        "rain": (1000, 3500),
        "temp": (20, 35),
        "soil": {"clay", "clay loam", "loam"},
        "season": {"kharif", "year-round"},
    },
    {
        "name": "Wheat",
        "ph": (6.0, 7.5),
        "rain": (450, 900),
        "temp": (15, 25),
        "soil": {"loam", "clay loam", "silt"},
        "season": {"rabi", "year-round"},
    },
    {
        "name": "Maize (corn)",
        "ph": (5.8, 7.0),
        "rain": (500, 1200),
        "temp": (18, 32),
        "soil": {"loam", "sandy loam", "clay loam"},
        "season": {"kharif", "rabi", "zaid", "year-round"},
    },
    {
        "name": "Cotton",
        "ph": (6.0, 8.0),
        "rain": (500, 1250),
        "temp": (21, 35),
        "soil": {"black cotton", "clay", "clay loam", "loam"},
        "season": {"kharif"},
    },
    {
        "name": "Soybean",
        "ph": (6.0, 7.5),
        "rain": (450, 900),
        "temp": (20, 30),
        "soil": {"loam", "clay loam"},
        "season": {"kharif"},
    },
    {
        "name": "Chickpea (gram)",
        "ph": (6.0, 8.5),
        "rain": (600, 1000),
        "temp": (15, 28),
        "soil": {"loam", "sandy loam"},
        "season": {"rabi"},
    },
    {
        "name": "Potato",
        "ph": (5.0, 6.5),
        "rain": (500, 900),
        "temp": (15, 25),
        "soil": {"sandy loam", "loam"},
        "season": {"rabi", "zaid"},
    },
    {
        "name": "Sorghum (jowar)",
        "ph": (6.0, 8.5),
        "rain": (400, 800),
        "temp": (25, 35),
        "soil": {"clay", "sandy loam", "loam"},
        "season": {"kharif", "rabi"},
    },
]


def _normalize_soil(s: str) -> str:
    return s.strip().lower().replace("_", " ")


def _normalize_season(s: str) -> str:
    return s.strip().lower()


def score_crop(req: dict[str, Any], spec: dict[str, Any]) -> tuple[float, str]:
    reasons: list[str] = []
    score = 0.0

    soil = _normalize_soil(str(req["soil_type"]))
    if soil in spec["soil"] or any(s in soil for s in spec["soil"]):
        score += 35
        reasons.append("soil type fits typical rooting and water behavior")
    else:
        score += 10
        reasons.append("soil is workable but not ideal; consider amendments")

    soil_ph = float(req["soil_ph"])
    ph_lo, ph_hi = spec["ph"]
    if ph_lo <= soil_ph <= ph_hi:
        score += 25
        reasons.append(f"pH {soil_ph} sits in the preferred band")
    else:
        dist = min(abs(soil_ph - ph_lo), abs(soil_ph - ph_hi))
        score += max(0, 15 - dist * 3)
        reasons.append("pH may need correction with lime or sulfur depending on direction")

    rain = float(req["annual_rainfall_mm"])
    r_lo, r_hi = spec["rain"]
    if r_lo <= rain <= r_hi:
        score += 25
        reasons.append("rainfall aligns with water demand")
    else:
        if rain < r_lo:
            score += 8
            reasons.append("rainfall is on the low side—supplemental irrigation may be needed")
        else:
            score += 8
            reasons.append("rainfall is high—focus on drainage and disease management")

    temp = float(req["avg_temperature_c"])
    t_lo, t_hi = spec["temp"]
    if t_lo <= temp <= t_hi:
        score += 15
        reasons.append("temperature range suits phenology")
    else:
        score += 5
        reasons.append("temperature stress possible; choose adapted varieties")

    season = _normalize_season(str(req["season"]))
    if season in spec["season"]:
        score += 10
        reasons.append("season matches common sowing window")
    else:
        score += 3
        reasons.append("season is non-standard—verify local calendar")

    return score, "; ".join(reasons)


def _require_json() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Expected JSON object body.")
    return data


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


@app.post("/api/crop-recommendation")
def crop_recommendation():
    body = _require_json()
    required = ["soil_type", "soil_ph", "annual_rainfall_mm", "avg_temperature_c", "season"]
    missing = [k for k in required if k not in body]
    if missing:
        abort(400, f"Missing fields: {', '.join(missing)}")

    req = {
        "soil_type": body["soil_type"],
        "soil_ph": _clamp(float(body["soil_ph"]), 0, 14),
        "annual_rainfall_mm": _clamp(float(body["annual_rainfall_mm"]), 0, 6000),
        "avg_temperature_c": _clamp(float(body["avg_temperature_c"]), -5, 50),
        "season": body["season"],
        "region_hint": body.get("region_hint", ""),
    }

    ranked: list[tuple[float, str, str]] = []
    for spec in CROPS:
        s, why = score_crop(req, spec)
        ranked.append((s, spec["name"], why))
    ranked.sort(key=lambda x: x[0], reverse=True)
    out = [{"crop": n, "score": round(min(100, s / 1.1), 1), "rationale": w} for s, n, w in ranked[:5]]
    return jsonify(out)


# --- Yield prediction ---

BASE_YIELD_Q_PER_ACRE: dict[str, float] = {
    "rice": 22,
    "paddy": 22,
    "wheat": 18,
    "maize": 30,
    "corn": 30,
    "cotton": 12,
    "soybean": 14,
    "chickpea": 10,
    "gram": 10,
    "potato": 90,
    "sorghum": 14,
    "jowar": 14,
}


def yield_prediction(body: dict[str, Any]) -> dict[str, Any]:
    crop = str(body["crop"]).strip().lower()
    area = float(body["field_area_acres"])
    irrigation = str(body["irrigation"]).strip().lower()
    fertilizer = str(body["fertilizer_level"]).strip().lower()
    om = float(body.get("soil_organic_matter_pct", 1.5))

    base = BASE_YIELD_Q_PER_ACRE.get(crop, 15)
    irr = {"rainfed": 0.85, "drip": 1.12, "sprinkler": 1.08, "flood": 1.0}.get(irrigation, 0.95)
    fert = {"low": 0.88, "medium": 1.0, "high": 1.1}.get(fertilizer, 0.95)
    om_factor = min(1.15, 0.95 + min(om, 8) * 0.025)

    est_q_per_acre = base * irr * fert * om_factor
    total_quintals = round(est_q_per_acre * area, 2)
    total_tonnes = round(total_quintals * 0.1, 3)

    return {
        "estimated_yield_quintals_per_acre": round(est_q_per_acre, 2),
        "estimated_total_quintals": total_quintals,
        "estimated_total_metric_tonnes": total_tonnes,
        "disclaimer": "Planning estimate from heuristics, not a substitute for field trials or official forecasts.",
    }


@app.post("/api/yield-prediction")
def yield_prediction_route():
    body = _require_json()
    for k in ("crop", "field_area_acres", "irrigation", "fertilizer_level"):
        if k not in body:
            abort(400, f"Missing field: {k}")
    try:
        area = float(body["field_area_acres"])
    except (TypeError, ValueError):
        abort(400, "field_area_acres must be a number.")
    if area <= 0 or area > 5000:
        abort(400, "field_area_acres must be between 0 and 5000 (exclusive of 0).")
    try:
        result = yield_prediction(body)
    except (TypeError, ValueError) as exc:
        abort(400, f"Invalid yield inputs: {exc}")
    return jsonify(result)


# --- Crop health ---


def analyze_leaf_image(img: Image.Image) -> dict[str, Any]:
    img = img.convert("RGB").resize((256, 256))
    stat = ImageStat.Stat(img)
    r_m, g_m, b_m = [c / 255.0 for c in stat.mean]
    r_s, g_s, b_s = [c / 255.0 for c in stat.stddev]

    excess_red = max(0.0, r_m - g_m)
    greenness = g_m - 0.5 * (r_m + b_m)
    brightness = (r_m + g_m + b_m) / 3.0
    contrast = (r_s + g_s + b_s) / 3.0

    health_index = max(
        0,
        min(
            100,
            50 + greenness * 120 - excess_red * 80 + (0.35 - abs(brightness - 0.45)) * 30,
        ),
    )

    issues: list[str] = []
    if excess_red > 0.12:
        issues.append("Elevated red/brown channel—possible senescence, stress, or disease-like discoloration.")
    if greenness < 0.02:
        issues.append("Low green dominance—check for chlorosis, nutrient deficiency, or poor lighting in the photo.")
    if contrast < 0.08:
        issues.append("Very flat image—retake with sharper focus and natural light for a clearer assessment.")

    if health_index >= 72:
        verdict = "Likely healthy canopy/leaf color balance"
    elif health_index >= 55:
        verdict = "Mixed signals—monitor closely and compare with healthy leaves from the same variety"
    else:
        verdict = "Stress or damage signals—inspect in person and consider extension support"

    return {
        "health_score": round(health_index, 1),
        "verdict": verdict,
        "notes": issues
        or ["Heuristic only: not a certified diagnosis. Combine with field scouting."],
        "metrics": {
            "greenness_index": round(greenness, 4),
            "stress_red_index": round(excess_red, 4),
            "mean_brightness": round(brightness, 4),
            "texture_contrast": round(contrast, 4),
        },
    }


@app.post("/api/crop-health")
def crop_health():
    if "file" not in request.files:
        abort(400, "Missing multipart field 'file'.")
    upload = request.files["file"]
    if not upload:
        abort(400, "Empty file upload.")
    raw = upload.read()
    if not raw:
        abort(400, "Empty file upload.")
    mime = (upload.mimetype or "").lower()
    name = (upload.filename or "").lower()
    magic = raw[:12]
    sniff = (
        magic.startswith(b"\x89PNG\r\n\x1a\n")
        or magic[:3] == b"\xff\xd8\xff"
        or magic[:4] in (b"RIFF", b"GIF8")
        or magic[8:12] == b"WEBP"
    )
    looks_image = (
        mime.startswith("image/")
        or name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"))
        or sniff
    )
    if not looks_image:
        abort(400, "Upload an image file (JPEG/PNG/WebP).")
    if upload.filename:
        _ = secure_filename(upload.filename)
    if len(raw) > 6 * 1024 * 1024:
        abort(400, "Image too large (max 6 MB).")
    try:
        image = Image.open(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        abort(400, f"Could not read image: {exc}")
    return jsonify(analyze_leaf_image(image))


# --- Tools recommendation ---

TOOLS_BY_TASK: dict[str, list[str]] = {
    "land_prep": [
        "Heavy-duty moldboard or disc plough (soil dependent)",
        "Rotary tiller / rototiller for fine seedbed",
        "Laser land leveler (where available) for water efficiency",
    ],
    "sowing": [
        "Seed drill or pneumatic planter for uniform depth",
        "Dibbler or manual planter for small plots",
        "Soil moisture probe to time sowing",
    ],
    "weeding": [
        "Wheel hoe or ergonomic hand hoe",
        "Mechanical cultivator between rows",
        "Mulching film or straw mulch to suppress weeds",
    ],
    "spraying": [
        "Knapsack sprayer with calibrated nozzles",
        "Boom sprayer for medium/large fields",
        "PPE kit (gloves, goggles, mask) — mandatory",
    ],
    "harvest": [
        "Serrated sickle or crop-specific harvester",
        "Field bins or tarps to reduce grain loss",
        "Moisture meter before storage",
    ],
    "storage": [
        "Hermetic bags or silos with aeration",
        "Temperature/humidity logger",
        "Cleaning winnow for grain lots",
    ],
}

CROP_SPECIFIC: dict[str, list[str]] = {
    "rice": ["Paddy transplanter or drum seeder", "AWD pipe set for water-saving paddy"],
    "wheat": ["Combine harvester with stripper front (large farms)", "Seed-cum-fertilizer drill"],
    "maize": ["Corn picker header or manual cob picking tools", "Soil ripper if compaction is present"],
    "corn": ["Corn picker header or manual cob picking tools", "Soil ripper if compaction is present"],
    "cotton": ["Spindle picker maintenance kit", "Defoliation sprayer timing guide"],
    "potato": ["Potato planter and digger/harvester", "Grader for tuber sizing"],
}


@app.post("/api/tools-recommendation")
def tools_recommendation():
    body = _require_json()
    if "crop" not in body or "primary_task" not in body:
        abort(400, "Fields 'crop' and 'primary_task' are required.")
    task = str(body["primary_task"]).strip().lower().replace(" ", "_")
    crop = str(body["crop"]).strip().lower()
    base = TOOLS_BY_TASK.get(
        task,
        [
            "Soil test kit",
            "Measuring wheel for spacing trials",
            "Weather app alerts for spray windows",
        ],
    )
    extra: list[str] = []
    for k, v in CROP_SPECIFIC.items():
        if k in crop:
            extra = v
            break
    return jsonify(
        {
            "crop": body["crop"],
            "primary_task": body["primary_task"],
            "recommended_tools": extra + base,
        }
    )


# --- Weather ---


def _idx(series: Any, i: int) -> Any:
    if isinstance(series, list) and i < len(series):
        return series[i]
    return None


@app.post("/api/weather")
def local_weather():
    body = _require_json()
    for k in ("latitude", "longitude"):
        if k not in body:
            abort(400, f"Missing field: {k}")
    lat = _clamp(float(body["latitude"]), -90, 90)
    lon = _clamp(float(body["longitude"]), -180, 180)
    days = int(body.get("days", 5))
    days = max(1, min(8, days))

    url = "https://api.open-meteo.com/v1/forecast"
    daily_vars = [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "weather_code",
    ]
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(daily_vars),
        "timezone": "auto",
        "forecast_days": days,
    }
    try:
        r = httpx.get(url, params=params, timeout=20.0)
        r.raise_for_status()
    except httpx.HTTPError as exc:
        abort(502, f"Weather service error: {exc}")

    data = r.json()
    daily = data.get("daily", {})
    days_out: list[dict[str, Any]] = []
    dates = daily.get("time") or []
    for i, d in enumerate(dates):
        days_out.append(
            {
                "date": d,
                "temp_max_c": _idx(daily.get("temperature_2m_max"), i),
                "temp_min_c": _idx(daily.get("temperature_2m_min"), i),
                "precipitation_mm": _idx(daily.get("precipitation_sum"), i),
                "precip_probability_pct": _idx(daily.get("precipitation_probability_max"), i),
                "weather_code": _idx(daily.get("weather_code"), i),
            }
        )
    return jsonify(
        {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "daily": days_out,
            "source": "Open-Meteo (no API key required)",
        }
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "farmer-advisory-python"})


@app.errorhandler(HTTPException)
def _http_errors(err: HTTPException):
    return jsonify({"error": err.description or str(err)}), err.code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=False)
