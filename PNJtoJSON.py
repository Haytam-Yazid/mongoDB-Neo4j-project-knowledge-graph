import os
import json
from pathlib import Path
from PIL import Image
from google import genai
from pymongo import MongoClient

# ----------------- CONFIGURATION -----------------
IMAGES_ROOT = Path(r"C:\Users\wwwie\Documents\Big_Data\project1\CSC3331_Project1_Files")

MONGODB_URI = (
    "mongodb+srv://ykikilolo726_db_user:local4444@cluster0.lpewrs5.mongodb.net/"
    "?appName=Cluster0&tls=true&tlsInsecure=true"
)
MONGODB_DB = "CSC_CourseCatalog"

GEMINI_API_KEY = "AIzaSyCJsHFqGKl8ID4MRvkukH_RfdtCmhoC8qc"
DEFAULT_MODEL = "gemini-2.5-flash"

# ----------------- FOLDER MAPPING -----------------
FOLDER_MAPPING = {
    ("Computer Science Core and Computing Elective", "Computer Science Core"),
    ("Computer Science Core and Computing Elective", "Computing Elective"),
    ("Computing Specialization Courses", "Advanced Computer Science", "Required Courses"),
    ("Computing Specialization Courses", "Advanced Computer Science", "Elective Courses"),
    ("Computing Specialization Courses", "Artificial Intelligence", "Required Courses"),
    ("Computing Specialization Courses", "Artificial Intelligence", "Elective Courses"),
    ("Computing Specialization Courses", "Big Data Analytics", "Required Courses"),
    ("Computing Specialization Courses", "Big Data Analytics", "Elective Courses"),
    ("Computing Specialization Courses", "Computer Systems", "Required Courses"),
    ("Computing Specialization Courses", "Computer Systems", "Elective Courses"),
    ("Computing Specialization Courses", "Software Engineering", "Required Courses"),
    ("Computing Specialization Courses", "Software Engineering", "Elective Courses"),
    ("Free Electives", "Free Elective"),
    ("Free Electives", "Not Counted Elective"),
    ("General Education", "Arabic"),
    ("General Education", "Art Appreciation & Creation"),
    ("General Education", "Civic Engagement"),
    ("General Education", "Communication"),
    ("General Education", "English"),
    ("General Education", "First Year Experience"),
    ("General Education", "Foundations for Academic Success"),
    ("General Education", "French"),
    ("General Education", "History or Political Science"),
    ("General Education", "Humanities"),
    ("General Education", "Social Sciences"),
    ("Mathematics Sciences and Engineering", "Engineering"),
    ("Mathematics Sciences and Engineering", "Mathematics"),
    ("Mathematics Sciences and Engineering", "Sciences"),
    ("Minor", "Business Administration", "Required Courses"),
    ("Minor", "Business Administration", "Other"),
    ("Minor", "Communication", "Required Courses"),
    ("Minor", "Communication", "Other"),
    ("Minor", "International Studies", "Required Courses"),
    ("Minor", "International Studies", "Other"),
    ("Minor", "Psychology", "Required Courses"),
    ("Minor", "Psychology", "Other"),
}


# ----------------- HELPERS -----------------

def get_image_parts(image_path: Path) -> list:
    """Loads the image for Gemini input."""
    img = Image.open(image_path)
    return [img]


def extract_collection_info(image_path: Path, root_path: Path) -> dict:
    
    try:
        parts = image_path.relative_to(root_path).parts
    except ValueError:
        return {"collection_name": None, "category": None, "status": None}

    collection_name = parts[0] if len(parts) > 0 else None
    category = parts[1] if len(parts) > 1 else parts[0] if len(parts) > 0 else None
    status = None

    # Check for status (3rd level)
    if len(parts) > 2:
        third = parts[2].lower()
        if "required" in third:
            status = "required"
        elif "elective" in third or "other" in third:
            status = "elective"

    return {
        "collection_name": collection_name,
        "category": category,
        "status": status,
    }


def build_prompt(category: str = None, status: str = None) -> str:
    """Creates the Gemini prompt including metadata."""
    category_text = f'Category: "{category}"' if category else "Category: collection_name"
    status_text = f'Status: "{status}"' if status in ("required", "elective") else "Status: null"

    return (
        "You are a JSON extraction assistant. Analyze the image, extract the course information "
        "from the text in the image, and return ONLY a JSON object.\n"
        "Required fields (exact keys):\n"
        "- Course Code (string)\n"
        "- Course Title (string)\n"
        "- Number of Credits (string)\n"
        "- Course Description (string)\n"
        "- Course Discipline (string)\n"
        "- PreOrCoRequisites (array of strings; if none return [])\n"
        f"- {category_text}\n"
        f"- {status_text}\n"
        "Return JSON only, no explanations."
    )


def call_gemini_for_json(image_path: Path, category: str = None, status: str = None) -> dict:
    """Calls Gemini API to extract course JSON from the image."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    image_parts = get_image_parts(image_path)
    prompt_text = build_prompt(category, status)

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[prompt_text] + image_parts,
            config={"temperature": 0.0, "max_output_tokens": 4000},
        )
    except Exception as e:
        print(f"API call failed for {image_path.name}: {e}")
        return {}

    text = response.text or ""
    start, end = text.find("{"), text.rfind("}") + 1
    if start == -1 or end <= start:
        print(f"Warning: Invalid JSON from API for {image_path.name}")
        return {}

    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {image_path.name}: {e}")
        return {}


# ----------------- MAIN PROCESSING -----------------

def process_images():
    """Processes all .png files and saves/insert JSONs."""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    stats = {"total_images": 0, "json_saved": 0, "inserted": 0, "failed": 0}
    tracking_number = 0

    for image_file in IMAGES_ROOT.rglob("*.png"):
        stats["total_images"] += 1
        tracking_number += 1
        print(f"\nPNG No: {tracking_number}")
        print(f"Processing: {image_file.name}")

        try:
            info = extract_collection_info(image_file, IMAGES_ROOT)
            course_json = call_gemini_for_json(image_file, info["category"], info["status"])

            if not course_json:
                raise ValueError("Empty or invalid JSON from Gemini API.")

            # Always include Category and Status in JSON
            course_json["Category"] = info["category"]
            course_json["Status"] = info["status"]

            # Save JSON to disk
            json_path = image_file.with_suffix(".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(course_json, f, ensure_ascii=False, indent=2)
            stats["json_saved"] += 1

            # Insert into MongoDB
            collection_name = info["collection_name"] or "root"
            db[collection_name].insert_one(course_json)
            stats["inserted"] += 1

            print(
                f"SUCCESS: Saved and inserted into '{collection_name}' "
                f"(Category: {info['category']}, Status: {info['status']})"
            )

        except Exception as e:
            stats["failed"] += 1
            print(f"FAILED: {image_file.name}: {e}")

    client.close()
    print("\n==== SUMMARY ====")
    for k, v in stats.items():
        print(f"{k}: {v}")


# ----------------- RUN -----------------
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set.")
    process_images()
