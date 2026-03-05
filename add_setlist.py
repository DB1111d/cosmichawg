import json
import re

SETLISTS_FILE = "setlistpath"

MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "apr",
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

def add_setlist():
    print("\n--- Add Setlist ---")
    date  = valid_date_input()
    venue = required_input("Venue name: ")
    city  = required_input("City, ST: ")

    show_id    = make_id(venue, date)
    date_parts = parse_date(date)

    songs = []
    print("\nEnter song titles one by one. Press Enter with no input when done (minimum 1 required).")
    while True:
        while True:
            title = input(f"  Song {len(songs)+1}: ").strip()
            if not title and len(songs) == 0:
                print("  ⚠️  At least one song is required!")
                continue
            break
        if not title:
            break
        songs.append({"title": title})

    with open(SETLISTS_FILE, "r") as f:
        setlists = json.load(f)

    setlists["shows"].insert(0, {
        "id": show_id,
        "venue": venue,
        "city": city,
        "date": date_parts,
        "setlist": songs
    })

    with open(SETLISTS_FILE, "w") as f:
        json.dump(setlists, f, indent=2)

    print(f"\n✅ Setlist saved! Show ID: {show_id}")

add_setlist()
