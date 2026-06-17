"""Build trajectory animation data from travel CSV + map coordinates."""
import csv
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
MAP_W, MAP_H = 1514, 1570

X_MIN, X_MAX = -5000, 3000
Y_MIN, Y_MAX = -400, 8200

MARGIN_LEFT = 0.095
MARGIN_RIGHT = 0.965
MARGIN_BOTTOM = 0.075
MARGIN_TOP = 0.915

TRAVEL_FILES = {
    "35": BASE / "travel_35.csv",
    "195": BASE / "travel_195.csv",
}


def load_locations():
    locs = {}
    with open(BASE / "city_function_points.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            locs[int(float(row["id"]))] = {
                "x": float(row["x"]),
                "y": float(row["y"]),
                "category": row["category"],
            }
    return locs


def world_to_pixel(x, y, img_w, img_h):
    plot_w = img_w * (MARGIN_RIGHT - MARGIN_LEFT)
    plot_h = img_h * (MARGIN_TOP - MARGIN_BOTTOM)
    px = MARGIN_LEFT * img_w + (x - X_MIN) / (X_MAX - X_MIN) * plot_w
    py = MARGIN_TOP * img_h - (y - Y_MIN) / (Y_MAX - Y_MIN) * plot_h
    return px, py


def parse_travel(path, locs):
    trips = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            start_id = int(float(row["travelStartLocationId"]))
            end_id = int(float(row["travelEndLocationId"]))
            if start_id not in locs or end_id not in locs:
                continue
            start = locs[start_id]
            end = locs[end_id]
            t0 = datetime.fromisoformat(row["travelStartTime"].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(row["travelEndTime"].replace("Z", "+00:00"))
            duration_ms = max(int((t1 - t0).total_seconds() * 1000), 500)
            trip = {
                "startX": start["x"], "startY": start["y"],
                "endX": end["x"], "endY": end["y"],
                "startType": start["category"], "endType": end["category"],
                "purpose": row["purpose"],
                "startTime": row["travelStartTime"],
                "endTime": row["travelEndTime"],
                "durationMs": duration_ms,
                "hour": t0.hour,
                "date": t0.strftime("%Y-%m-%d"),
            }
            trip["startPx"], trip["startPy"] = world_to_pixel(trip["startX"], trip["startY"], MAP_W, MAP_H)
            trip["endPx"], trip["endPy"] = world_to_pixel(trip["endX"], trip["endY"], MAP_W, MAP_H)
            trips.append(trip)
    return trips


def main():
    locs = load_locations()
    participants = {}
    for pid, path in TRAVEL_FILES.items():
        trips = parse_travel(path, locs)
        participants[pid] = {
            "name": f"居民 {pid}",
            "trips": trips,
            "dates": sorted({t["date"] for t in trips}),
            "tripCount": len(trips),
        }
        print(f"Participant {pid}: {len(trips)} trips")

    out = BASE / "animation_data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"mapSize": {"width": MAP_W, "height": MAP_H},
                   "bounds": {"xMin": X_MIN, "xMax": X_MAX, "yMin": Y_MIN, "yMax": Y_MAX},
                   "participants": participants}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
