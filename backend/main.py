import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from ibm_watsonx_ai.foundation_models import ModelInference

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/save", methods=["POST"])
def save_schedule():
    data = request.get_json()  # Grab JSON from request body
    major = data.get("major")
    gen_ed = data.get("genEd")
    wake_time = data.get("wakeTime")

    print("Received data from frontend:")
    print(f"Major: {major}")
    print(f"Gen-Ed: {gen_ed}")
    print(f"Wake-Up Time: {wake_time}")

    # Here you could save it to a database

    return jsonify({"message": "Data received successfully!"})


# --- Paths (prevents FileNotFoundError when running from different folders) ---
def load_json(filename: str):
    path = os.path.join(BASE_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Load config + data ---
config = load_json("credentials.json")
classes_data = load_json("combined_curriculum.json")   # can be list or dict depending on your file
times = load_json("full_course_schedule.json")

# Normalize classes into a set of allowed class names
# Supports either:
#  - classes.json = ["CSE 2221", "MATH 2568", ...]
#  - classes.json = {"classes": ["CSE 2221", ...]}
if isinstance(classes_data, dict) and "classes" in classes_data:
    allowed_classes = set(classes_data["classes"])
elif isinstance(classes_data, list):
    allowed_classes = set(classes_data)
else:
    allowed_classes = set()

# --- Watsonx.ai Model client ---
# credentials.json should include: api_key, url, project_id, model_id
model = ModelInference(
    model_id=config["model_id"],
    credentials={"apikey": config["api_key"], "url": config["url"]},
    project_id=config["project_id"],
)

@app.route("/", methods=["GET"])
def index():
    return "Welcome to the watsonx.ai Course Planner API!"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/message", methods=["POST"])
def send_message():
    try:
        body = request.get_json(silent=True) or {}
        message = (body.get("message") or "").strip()

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Ask watsonx.ai to output *ONLY* JSON array of class names
        prompt = build_prompt(message, allowed_classes)

        # Generate
        generated = model.generate_text(prompt=prompt)

        # Parse JSON list from model output
        recommended_classes = parse_recommended_classes(generated)

        # Optional: filter to only classes we recognize
        if allowed_classes:
            recommended_classes = [c for c in recommended_classes if c in allowed_classes]

        schedule = generate_schedule(recommended_classes, times)

        return jsonify({
            "input": message,
            "recommended_classes": recommended_classes,
            "schedule": schedule,
            "raw_model_output": generated  # remove this in production if you want
        })

    except KeyError as e:
        return jsonify({"error": f"Missing config key: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def build_prompt(user_message: str, allowed: set[str]) -> str:
    # If you have a known list of classes, it helps the model stay constrained.
    # Keep it short if your list is huge.
    allowed_hint = ""
    if allowed:
        # limit to avoid giant prompts
        sample = list(sorted(allowed))[:200]
        allowed_hint = (
            "You must choose ONLY from this allowed list:\n"
            + json.dumps(sample)
            + "\n"
        )

    return f"""
You are a college course-planning assistant.
Given the student's request, return ONLY a JSON array of recommended class names (strings).
No extra text, no markdown, no explanations.

Rules:
- Output must be valid JSON.
- Return 3 to 6 class names.
- Prefer classes that match the student's goals and constraints.

{allowed_hint}
Student request: {user_message}
""".strip()


def parse_recommended_classes(model_output: str) -> list[str]:
    """
    Try to parse model output as JSON array. If the model adds extra text,
    attempt to extract the first JSON array substring.
    """
    text = (model_output or "").strip()

    # 1) direct JSON parse
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass

    # 2) extract first JSON array block
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end + 1]
        try:
            data = json.loads(snippet)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except Exception:
            pass

    # 3) fallback: split lines/commas (last resort)
    # e.g. "CSE 2221, MATH 2568"
    cleaned = text.replace("\n", ",")
    parts = [p.strip(" -•\t\r") for p in cleaned.split(",")]
    return [p for p in parts if p]


def generate_schedule(recommended_classes: list[str], times: dict) -> dict:
    """
    times.json expected shapes:
      A) {"Monday": {"CSE 2221": ["10:00"], "MATH 2568": ["14:00"]}, ...}
      B) {"Monday": ["CSE 2221", "MATH 2568"], ...}
    We'll support both.
    """
    schedule = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}

    for day, day_data in times.items():
        if day not in schedule:
            continue

        # Case A: dict of class -> timeslots
        if isinstance(day_data, dict):
            for cls in recommended_classes:
                if cls in day_data:
                    schedule[day].append({"class": cls, "times": day_data[cls]})
        # Case B: list of class names offered that day
        elif isinstance(day_data, list):
            for cls in recommended_classes:
                if cls in day_data:
                    schedule[day].append({"class": cls})

    return schedule


if __name__ == "__main__":
    app.run(debug=True)