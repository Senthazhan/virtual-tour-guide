import csv, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
json_path = ROOT / "data" / "places.json"
csv_path = ROOT / "data" / "sri_lanka_places.csv"

# Load existing JSON (tolerate BOM)
data = {}
if json_path.exists():
    txt = json_path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(txt)
    except Exception as e:
        raise SystemExit(f"Failed to parse {json_path}: {e}")

def row_to_entry(r):
    def as_int(x, default=0):
        try: return int(str(x).strip())
        except: return default
    def as_float(x):
        try:
            return float(str(x).strip())
        except:
            return None
    def split_list(x):
        vals = [v.strip() for v in str(x or "").split(";") if v and v.strip()]
        return vals
    # Collect stops up to 5
    stops = []
    for i in range(1, 6):
        key = f"stop{i}"
        if r.get(key):
            stops.append({
                "name": r[key].strip(),
                "minutes": as_int(r.get(f"stop{i}_minutes"), 45)
            })
    # Collect facts up to 8
    facts = []
    for i in range(1, 9):
        fx = (r.get(f"fact{i}") or "").strip()
        if fx:
            facts.append(fx)
    # Optional extras
    lat = as_float(r.get("lat"))
    lng = as_float(r.get("lng"))
    coords = {"lat": lat, "lng": lng} if (lat is not None and lng is not None) else None

    entry = {
        "facts": facts[:8],
        "ticket": (r.get("ticket") or "Ticket info varies by site.").strip(),
        "stops": stops
    }
    aliases = split_list(r.get("aliases"))
    if aliases:
        entry["aliases"] = aliases
    city = (r.get("city") or "").strip()
    if city:
        entry["city"] = city
    best_time = (r.get("best_time") or "").strip()
    if best_time:
        entry["best_time"] = best_time
    highlights = split_list(r.get("highlights"))
    if highlights:
        entry["highlights"] = highlights
    if coords:
        entry["coords"] = coords
    opening = (r.get("opening_hours") or "").strip()
    if opening:
        entry["opening_hours"] = opening
    website = (r.get("website") or "").strip()
    if website:
        entry["website"] = website
    tags = split_list(r.get("tags"))
    if tags:
        entry["tags"] = tags
    safety = (r.get("safety_notes") or "").strip()
    if safety:
        entry["safety_notes"] = safety
    return entry

# Merge CSV rows
with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        place = (r.get("place") or "").strip()
        if not place: 
            continue
        data[place] = row_to_entry(r)

# Save pretty JSON (no BOM)
json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {json_path} with {len(data)} places")
