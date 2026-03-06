import json
import re

SHOWS_FILE    = "cosmichawg/shows.json"
SETLISTS_FILE = "cosmichawg/setlists.json"
LINEUPS_FILE  = "cosmichawg/lineups.json"

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

def valid_date_input(prompt="Date (YYYY-MM-DD): "):
    while True:
        value = input(prompt).strip()
        if not value:
            print("  ⚠️  Date is required!")
            continue
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            print("  ⚠️  Date must be in YYYY-MM-DD format (e.g. 2026-03-15)")
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

# --- EDIT SHOW ---
def edit_show():
    with open(SHOWS_FILE, "r") as f:
        shows = json.load(f)

    print("\nAvailable shows:")
    idx = pick_entry(shows, lambda s: f"{s['date']} - {s['venue']} - {s['city']}")
    show = shows[idx]

    while True:
        print(f"\nEditing: {show['date']} - {show['venue']} - {show['city']}")
        print(f"  1. Date:  {show['date']}")
        print(f"  2. Venue: {show['venue']}")
        print(f"  3. City:  {show['city']}")

        field = input("\nWhich field to edit (1-3, or Enter to finish): ").strip()
        if not field:
            break
        if field == "1":
            show['date'] = valid_date_input("New Date (YYYY-MM-DD): ")
        elif field == "2":
            show['venue'] = required_input("New Venue name: ")
        elif field == "3":
            show['city'] = required_input("New City, ST: ")
        else:
            print("  ⚠️  Please enter 1, 2, or 3")
            continue

        # update IDs
        show['lineupId'] = make_id(show['venue'], show['date'])
        show['setlistId'] = make_id(show['venue'], show['date'])

    shows[idx] = show
    with open(SHOWS_FILE, "w") as f:
        json.dump(shows, f, indent=2)
    print(f"\n✅ Show updated!")

# --- EDIT SETLIST ---
def edit_setlist():
    with open(SETLISTS_FILE, "r") as f:
        data = json.load(f)

    shows = data["shows"]
    print("\nAvailable setlists:")
    idx = pick_entry(shows, lambda s: f"{s['date']['month']} {s['date']['day']} {s['date']['year']} - {s['venue']} - {s['city']}")
    show = shows[idx]

    while True:
        print(f"\nEditing setlist: {show['venue']} - {show['date']['month']} {show['date']['day']} {show['date']['year']}")
        print("  1. Edit date/venue/city")
        print("  2. Edit songs")
        field = input("\nWhat to edit (1-2, or Enter to finish): ").strip()
        if not field:
            break
        if field == "1":
            date  = valid_date_input("New Date (YYYY-MM-DD): ")
            venue = required_input("New Venue name: ")
            city  = required_input("New City, ST: ")
            show['date']  = parse_date(date)
            show['venue'] = venue
            show['city']  = city
            show['id']    = make_id(venue, date)
        elif field == "2":
            while True:
                print("\nCurrent songs:")
                for i, s in enumerate(show['setlist']):
                    print(f"  {i+1}. {s['title']}")
                print(f"  {len(show['setlist'])+1}. Add new song")
                choice = input("\nSelect song to edit, or pick last option to add (Enter to finish): ").strip()
                if not choice:
                    break
                if not choice.isdigit():
                    print("  ⚠️  Please enter a number")
                    continue
                choice = int(choice)
                if choice == len(show['setlist']) + 1:
                    title = required_input("New song title: ")
                    show['setlist'].append({"title": title})
                elif 1 <= choice <= len(show['setlist']):
                    print(f"  1. Edit title")
                    print(f"  2. Remove song")
                    action = input("  Action (1-2): ").strip()
                    if action == "1":
                        show['setlist'][choice-1]['title'] = required_input("New title: ")
                    elif action == "2":
                        if len(show['setlist']) == 1:
                            print("  ⚠️  At least one song is required!")
                        else:
                            show['setlist'].pop(choice-1)
                            print("  Song removed.")
                else:
                    print(f"  ⚠️  Please enter a number between 1 and {len(show['setlist'])+1}")
        else:
            print("  ⚠️  Please enter 1 or 2")

    shows[idx] = show
    data["shows"] = shows
    with open(SETLISTS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ Setlist updated!")

# --- EDIT LINEUP ---
def edit_lineup():
    with open(LINEUPS_FILE, "r") as f:
        data = json.load(f)

    shows = data["shows"]
    print("\nAvailable lineups:")
    idx = pick_entry(shows, lambda s: f"{s['date']['month']} {s['date']['day']} {s['date']['year']} - {s['venue']} - {s['city']}")
    show = shows[idx]

    while True:
        print(f"\nEditing lineup: {show['venue']} - {show['date']['month']} {show['date']['day']} {show['date']['year']}")
        print("  1. Edit date/venue/city")
        print("  2. Edit members")
        field = input("\nWhat to edit (1-2, or Enter to finish): ").strip()
        if not field:
            break
        if field == "1":
            date  = valid_date_input("New Date (YYYY-MM-DD): ")
            venue = required_input("New Venue name: ")
            city  = required_input("New City, ST: ")
            show['date']  = parse_date(date)
            show['venue'] = venue
            show['city']  = city
            show['id']    = make_id(venue, date)
        elif field == "2":
            while True:
                print("\nCurrent members:")
                for i, m in enumerate(show['lineup']):
                    print(f"  {i+1}. {m['name']} - {m['role']}")
                print(f"  {len(show['lineup'])+1}. Add new member")
                choice = input("\nSelect member to edit, or pick last option to add (Enter to finish): ").strip()
                if not choice:
                    break
                if not choice.isdigit():
                    print("  ⚠️  Please enter a number")
                    continue
                choice = int(choice)
                if choice == len(show['lineup']) + 1:
                    name = required_input("New member name: ")
                    role = required_input(f"  {name}'s role: ")
                    show['lineup'].append({"name": name, "role": role})
                elif 1 <= choice <= len(show['lineup']):
                    print(f"  1. Edit name")
                    print(f"  2. Edit role")
                    print(f"  3. Remove member")
                    action = input("  Action (1-3): ").strip()
                    if action == "1":
                        show['lineup'][choice-1]['name'] = required_input("New name: ")
                    elif action == "2":
                        show['lineup'][choice-1]['role'] = required_input("New role: ")
                    elif action == "3":
                        if len(show['lineup']) == 1:
                            print("  ⚠️  At least one member is required!")
                        else:
                            show['lineup'].pop(choice-1)
                            print("  Member removed.")
                else:
                    print(f"  ⚠️  Please enter a number between 1 and {len(show['lineup'])+1}")
        else:
            print("  ⚠️  Please enter 1 or 2")

    shows[idx] = show
    data["shows"] = shows
    with open(LINEUPS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ Lineup updated!")

# --- MAIN ---
while True:
    print("\n--- Edit Entry ---")
    while True:
        which = input("Which file? (show/setlist/lineup): ").strip().lower()
        if which not in ("show", "setlist", "lineup"):
            print("  ⚠️  Please enter show, setlist, or lineup")
            continue
        break

    if which == "show":
        edit_show()
    elif which == "setlist":
        edit_setlist()
    elif which == "lineup":
        edit_lineup()

    while True:
        again = input("\nEdit another entry? (yes/no): ").strip().lower()
        if again not in ("yes", "no"):
            print("  ⚠️  Please enter yes or no")
            continue
        break
    if again == "no":
        print("\nGoodbye!")
        break
