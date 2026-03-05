import json
import re

JSON_FILE = "showpath"

def make_id(venue, date):
    slug = re.sub(r'[^a-z0-9]+', '-', venue.lower()).strip('-')
    return f"{slug}-{date}"

def add_show():
    with open(JSON_FILE, "r") as f:
        shows = json.load(f)

    print("\n--- Add New Show ---")
    date   = input("Date (YYYY-MM-DD): ").strip()
    venue  = input("Venue name: ").strip()
    city   = input("City, ST: ").strip()

    show_id = make_id(venue, date)

    new_show = {
        "date": date,
        "venue": venue,
        "city": city,
        "lineupId": show_id,
        "setlistId": show_id
    }

    shows.insert(0, new_show)  # adds to top (most recent first)

    with open(JSON_FILE, "w") as f:
        json.dump(shows, f, indent=2)

    print(f"\n✅ Show added! ID: {show_id}")

add_show()
