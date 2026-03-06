import json
import re
from datetime import date

SHOWS_FILE   = "/Users/john/Downloads/cosmichawg/shows.json"
LINEUPS_FILE = "/Users/john/Downloads/cosmichawg/lineups.json"

MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
}

def make_id(venue, date_str):
    slug = re.sub(r'[^a-z0-9]+', '-', venue.lower()).strip('-')
    return f"{slug}-{date_str}"

def parse_date(date_str):
    year, month, day = date_str.split("-")
    return {
        "month": MONTH_MAP[month],
        "day": str(int(day)),
        "year": year
    }

def required_input(prompt):
    while True:
        value = input(prompt).strip()
        if not value:
            print("  ⚠️  This field is required!")
            continue
        return value

def pick_entry(entries, label_fn):
    for i, e in enumerate(entries):
        print(f"  {i+1}. {label_fn(e)}")
    while True:
        choice = input(f"\nSelect entry (1-{len(entries)}): ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(entries)):
            print(f"  ⚠️  Please enter a number between 1 and {len(entries)}")
            continue
        return int(choice) - 1

def add_lineup():
    with open(SHOWS_FILE, "r") as f:
        shows = json.load(f)

    with open(LINEUPS_FILE, "r") as f:
        lineups = json.load(f)

    today = date.today().isoformat()
    existing_ids = {s["id"] for s in lineups["shows"]}

    eligible = [
        s for s in shows
        if s["date"] < today and make_id(s["venue"], s["date"]) not in existing_ids
    ]

    if not eligible:
        print("\n✅ No shows missing a lineup.")
        return

    print("\n--- Add Lineup ---")
    print("Shows missing a lineup:\n")
    idx = pick_entry(eligible, lambda s: f"{s['date']} - {s['venue']} - {s['city']}")
    show = eligible[idx]

    show_id    = make_id(show["venue"], show["date"])
    date_parts = parse_date(show["date"])

    print(f"\nAdding lineup for: {show['venue']} — {show['date']} — {show['city']}")

    members = []
    print("\nEnter lineup members one by one. Press Enter with no name when done (minimum 1 required).")
    while True:
        while True:
            name = input(f"  Member {len(members)+1}: ").strip()
            if not name and len(members) == 0:
                print("  ⚠️  At least one member is required!")
                continue
            break
        if not name:
            break
        while True:
            role = input(f"  {name}'s role: ").strip()
            if not role:
                print("  ⚠️  Role is required!")
                continue
            break
        members.append({"name": name, "role": role})

    lineups["shows"].insert(0, {
        "id": show_id,
        "venue": show["venue"],
        "city": show["city"],
        "date": date_parts,
        "lineup": members
    })

    with open(LINEUPS_FILE, "w") as f:
        json.dump(lineups, f, indent=2)

    print(f"\n✅ Lineup saved! Show ID: {show_id}")

add_lineup()
