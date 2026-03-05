import json
import re

LINEUPS_FILE = "lineuppath"

MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
}

def make_id(venue, date):
    slug = re.sub(r'[^a-z0-9]+', '-', venue.lower()).strip('-')
    return f"{slug}-{date}"

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

def valid_date_input():
    while True:
        value = input("Date (YYYY-MM-DD): ").strip()
        if not value:
            print("  ⚠️  Date is required!")
            continue
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            print("  ⚠️  Date must be in YYYY-MM-DD format (e.g. 2026-03-15)")
            continue
        return value

def add_lineup():
    print("\n--- Add Lineup ---")
    date  = valid_date_input()
    venue = required_input("Venue name: ")
    city  = required_input("City, ST: ")

    show_id    = make_id(venue, date)
    date_parts = parse_date(date)

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

    with open(LINEUPS_FILE, "r") as f:
        lineups = json.load(f)

    lineups["shows"].insert(0, {
        "id": show_id,
        "venue": venue,
        "city": city,
        "date": date_parts,
        "lineup": members
    })

    with open(LINEUPS_FILE, "w") as f:
        json.dump(lineups, f, indent=2)

    print(f"\n✅ Lineup saved! Show ID: {show_id}")

add_lineup()
