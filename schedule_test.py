"""
schedule_test.py
==================
Selenium test suite for Cosmic Hawg — cosmichawg.com

Runs inside Docker via GitHub Actions on every push to main.
Generates dummy test data, runs all tests, then the container disappears.
Your real shows.json / lineups.json / setlists.json are never modified.
"""

import http.server
import json
import math
import os
import random
import re
import socketserver
import threading
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ── Config ────────────────────────────────────────────────────────────────────

SITE_DIR          = Path(os.environ.get("SITE_DIR", "/app"))
BASE_URL          = "http://localhost:8000"
PORT              = 8000
HEADLESS          = True
SHOWS_PER_PAGE    = 4
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
CHROME_BINARY     = "/usr/bin/google-chrome"

# ── Generate test data ───────────────────────────────────────────────────────
# Runs before the server starts and Chrome opens.

_MONTH_MAP = {
    "01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
    "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"
}

_ALL_MEMBERS = [
    {"name":"Dan B.",    "role":"Guitar / Vocals"},
    {"name":"Jeff F.",   "role":"Guitar"},
    {"name":"Chris K.",  "role":"Bass"},
    {"name":"Ryan T.",   "role":"Drums"},
    {"name":"Robbie B.", "role":"Keyboard / Vocals"},
    {"name":"Eddie S.",  "role":"Vocals"},
    {"name":"Nelson R.", "role":"Saxophone"},
    {"name":"Roman",     "role":"Saxophone"},
    {"name":"Skip",      "role":"Percussion"},
]
_CORE     = _ALL_MEMBERS[:4]
_OPTIONAL = _ALL_MEMBERS[4:]

_ALL_SONGS = [
    "Graziatto","All My Days","Stay","Down By The River","Greetings",
    "Nightrider","G13","One More Time (Try Me)","It Ain't No Use",
    "Rollo","Right Place Wrong Time","Sabrosa","Red Moon",
    "Soul Shine","Funkify","Easy Wind","Rollin' On",
    "Blue Canoe","The Messenger","Loose Change","High Desert",
    "Carolina Moon","River Road","Back Porch","Slow Burn",
    "Magnolia","Cottonwood","Sunday Driver","Ol' Faithful",
]

_VENUES_UPCOMING = [
    ("The Radio Room","Greenville, SC"),("Fluor Field at the West End","Greenville, SC"),
    ("Poe Mill Music Hall","Greenville, SC"),("The Handlebar","Greenville, SC"),
    ("Portman Shoals Park","Belton, SC"),("TD Saturday Market","Greenville, SC"),
    ("Hub City Brewing Co.","Spartanburg, SC"),("The Skullcandy Stage","Spartanburg, SC"),
    ("The Spinning Jenny","Greer, SC"),("Falls Park Amphitheater","Greenville, SC"),
    ("Warehouse Theatre","Greenville, SC"),("The Bohemian","Greenville, SC"),
    ("Larkins on the River","Greenville, SC"),("The Rusty Rudder","Anderson, SC"),
    ("Carolina Ale House","Greenville, SC"),("Wild Wing Cafe","Greenville, SC"),
    ("Roost Chicken + Beer","Greenville, SC"),("The Southern Craft Creamery","Greer, SC"),
    ("Trailblazer Park","Greer, SC"),("Thomas Street Tavern","Charlotte, NC"),
    ("Asheville Music Hall","Asheville, NC"),("The Grey Eagle","Asheville, NC"),
    ("Isis Music Hall","Asheville, NC"),("Drayton Mills Marketplace","Spartanburg, SC"),
    ("Greenville County Museum","Greenville, SC"),
]

_VENUES_PAST = [
    ("Smileys on the Roxx","Greenville, SC"),("Artistry Workshops & Gallery","Greenville, SC"),
    ("Poe Mill Music Hall","Greenville, SC"),("The Radio Room","Greenville, SC"),
    ("The Handlebar","Greenville, SC"),("Hub City Brewing Co.","Spartanburg, SC"),
    ("The Spinning Jenny","Greer, SC"),("Trailblazer Park","Greer, SC"),
    ("Carolina Ale House","Greenville, SC"),("Wild Wing Cafe","Greenville, SC"),
    ("Falls Park Amphitheater","Greenville, SC"),("The Rusty Rudder","Anderson, SC"),
    ("TD Saturday Market","Greenville, SC"),("The Bohemian","Greenville, SC"),
    ("Drayton Mills Marketplace","Spartanburg, SC"),("Portman Shoals Park","Belton, SC"),
    ("Warehouse Theatre","Greenville, SC"),("The Grey Eagle","Asheville, NC"),
    ("Isis Music Hall","Asheville, NC"),("Asheville Music Hall","Asheville, NC"),
    ("Thomas Street Tavern","Charlotte, NC"),("The Skullcandy Stage","Spartanburg, SC"),
    ("Roost Chicken + Beer","Greenville, SC"),("Larkins on the River","Greenville, SC"),
    ("The Southern Craft Creamery","Greer, SC"),
]

def _make_id(venue, date_str):
    return re.sub(r"[^a-z0-9]+", "-", venue.lower()).strip("-") + "-" + date_str

def _parse_date(date_str):
    y, m, d = date_str.split("-")
    return {"month": _MONTH_MAP[m], "day": str(int(d)), "year": y}

def _spread_dates(anchor, count, direction, min_gap=5, max_gap=18):
    dates, current = [], anchor
    for _ in range(count):
        gap = random.randint(min_gap, max_gap)
        current = current + timedelta(days=gap) if direction == "future" else current - timedelta(days=gap)
        dates.append(current.isoformat())
    return dates

def _random_lineup(large=False):
    if large:
        guest_names = ["Marcus D.","Tanya R.","Leo V.","Priya S.","Walt H.",
                       "Keisha M.","André T.","Fiona C.","Dez W.","Bart L.",
                       "Simone K.","Gus P.","Rhonda J.","Cal N.","Vera O.",
                       "Theo B.","Iris F."]
        guest_roles = ["Percussion","Backing Vocals","Trumpet","Saxophone","Trombone",
                       "Violin","Harmonica","Keyboard","Congas","Tambourine",
                       "Acoustic Guitar","Flute","Steel Guitar","Lap Steel",
                       "Mandolin","Upright Bass","Baritone Guitar"]
        base = _CORE + _OPTIONAL
        needed = random.randint(20, 24) - len(base)
        names = random.sample(guest_names, k=min(needed, len(guest_names)))
        roles = random.sample(guest_roles, k=len(names))
        return base + [{"name": n, "role": r} for n, r in zip(names, roles)]
    return _CORE + random.sample(_OPTIONAL, k=random.randint(0, 3))

def _random_setlist(large=False):
    if large:
        pool = _ALL_SONGS + ["Encore: Down By The River","Encore: G13","Encore: Graziatto",
                             "Jam — Free Form","Crowd Favorite Medley","Blues Shuffle #1",
                             "Blues Shuffle #2","Improv Outro"]
        return [{"title": t} for t in random.sample(pool, k=min(random.randint(20,25), len(pool)))]
    return [{"title": t} for t in random.sample(_ALL_SONGS, k=random.randint(7, 11))]

def _generate_data():
    today = date.today()
    venues_up   = list(_VENUES_UPCOMING);  random.shuffle(venues_up)
    venues_past = list(_VENUES_PAST);      random.shuffle(venues_past)

    upcoming_dates = _spread_dates(today, 25, "future")
    past_dates     = _spread_dates(today, 25, "past")

    shows, lineups_list, setlists_list = [], [], []

    for i, ds in enumerate(upcoming_dates):
        venue, city = venues_up[i % len(venues_up)]
        shows.append({"date": ds, "venue": venue, "city": city,
                      "lineupId": None, "setlistId": None})

    for i, ds in enumerate(past_dates):
        venue, city = venues_past[i % len(venues_past)]
        sid = _make_id(venue, ds)
        shows.append({"date": ds, "venue": venue, "city": city,
                      "lineupId": sid, "setlistId": sid})
        is_large = random.random() < 0.20
        dp = _parse_date(ds)
        lineups_list.append({"id": sid, "venue": venue, "city": city,
                              "date": dp, "lineup": _random_lineup(is_large)})
        setlists_list.append({"id": sid, "venue": venue, "city": city,
                               "date": dp, "setlist": _random_setlist(is_large)})

    # ── Inject one fixed empty show (no entry in lineups/setlists → coming soon) ─
    empty_date  = (today - timedelta(days=2)).isoformat()
    empty_venue = "Empty Show Test Venue"
    empty_city  = "Greenville, SC"
    empty_sid   = _make_id(empty_venue, empty_date)
    # Only add to shows.json — NOT to lineups/setlists so JS shows "coming soon"
    shows.append({"date": empty_date, "venue": empty_venue, "city": empty_city,
                  "lineupId": empty_sid, "setlistId": empty_sid})

    shows.sort(key=lambda s: s["date"], reverse=True)

    with open(SITE_DIR / "shows.json", "w") as f:
        json.dump(shows, f, indent=2)
    with open(SITE_DIR / "lineups.json", "w") as f:
        json.dump({"shows": lineups_list}, f, indent=2)
    with open(SITE_DIR / "setlists.json", "w") as f:
        json.dump({"shows": setlists_list}, f, indent=2)

    print(f"✅ Generated {len(shows)} shows "
          f"({len(upcoming_dates)} upcoming, {len(past_dates)} past) → {SITE_DIR}")

_generate_data()

# ── Start local server (inside container) ─────────────────────────────────────

def _start_server():
    os.chdir(SITE_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

_server_thread = threading.Thread(target=_start_server, daemon=True)
_server_thread.start()
time.sleep(1.5)
print(f"✅ Server started at {BASE_URL} — serving {SITE_DIR}")

# ── Dynamic fixture builder ───────────────────────────────────────────────────

def _load(filename):
    path = SITE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"\nCould not find {filename} at {path}\n"
            "Data generation failed — check SITE_DIR is correct."
        )
    with open(path) as f:
        return json.load(f)


def _build_fixtures():
    shows_raw    = _load("shows.json")
    lineups_raw  = _load("lineups.json")
    setlists_raw = _load("setlists.json")

    today = date.today().isoformat()

    upcoming = sorted(
        [s for s in shows_raw if s["date"] >= today],
        key=lambda s: s["date"]
    )
    past = sorted(
        [s for s in shows_raw if s["date"] < today],
        key=lambda s: s["date"], reverse=True
    )

    lineups  = lineups_raw["shows"]
    setlists = setlists_raw["shows"]

    # Pick large/normal by member/song count
    non_empty_lineups = [l for l in lineups if len(l["lineup"]) > 0]
    large_lineup  = max(non_empty_lineups, key=lambda l: len(l["lineup"]))
    normal_lineup = min(non_empty_lineups, key=lambda l: len(l["lineup"]))
    non_empty_setlists = [s for s in setlists if len(s["setlist"]) > 0]
    large_setlist  = max(non_empty_setlists, key=lambda s: len(s["setlist"]))
    normal_setlist = min(non_empty_setlists, key=lambda s: len(s["setlist"]))

    # Build song play-count map
    song_map = {}
    for show in setlists:
        for song in show["setlist"]:
            key = song["title"].lower().strip()
            song_map.setdefault(key, 0)
            song_map[key] += 1

    # Find which 1-based page a show ID appears on in the past list
    def page_of(show_id):
        for i, s in enumerate(past):
            if s.get("lineupId") == show_id or s.get("setlistId") == show_id:
                return (i // SHOWS_PER_PAGE) + 1
        return None

    large_first_song  = large_setlist["setlist"][0]["title"]
    normal_first_song = normal_setlist["setlist"][0]["title"]

    return {
        "upcoming_total": len(upcoming),
        "upcoming_pages": math.ceil(len(upcoming) / SHOWS_PER_PAGE) if upcoming else 0,
        "past_total":     len(past),
        "past_pages":     math.ceil(len(past) / SHOWS_PER_PAGE) if past else 0,

        "large_lineup_id":    large_lineup["id"],
        "large_lineup_size":  len(large_lineup["lineup"]),
        "large_lineup_page":  page_of(large_lineup["id"]),
        "large_lineup_venue": large_lineup["venue"],

        "normal_lineup_id":    normal_lineup["id"],
        "normal_lineup_size":  len(normal_lineup["lineup"]),
        "normal_lineup_page":  page_of(normal_lineup["id"]),
        "normal_lineup_venue": normal_lineup["venue"],

        "large_setlist_id":         large_setlist["id"],
        "large_setlist_size":       len(large_setlist["setlist"]),
        "large_setlist_page":       page_of(large_setlist["id"]),
        "large_setlist_first_song": large_first_song,
        "large_song_play_count":    song_map[large_first_song.lower().strip()],

        "normal_setlist_id":         normal_setlist["id"],
        "normal_setlist_size":       len(normal_setlist["setlist"]),
        "normal_setlist_page":       page_of(normal_setlist["id"]),
        "normal_setlist_first_song": normal_first_song,
        "normal_song_play_count":    song_map[normal_first_song.lower().strip()],

        # Empty show — fixed injected show with known ID
        "empty_show_id":   _make_id("Empty Show Test Venue",
                                    (date.today() - timedelta(days=2)).isoformat()),
        "empty_show_page": page_of(_make_id("Empty Show Test Venue",
                                    (date.today() - timedelta(days=2)).isoformat())),
    }


FX = _build_fixtures()

print("\n── Fixtures resolved from JSON ─────────────────────────────────────────")
print(f"  Upcoming : {FX['upcoming_total']} shows → {FX['upcoming_pages']} pages")
print(f"  Past     : {FX['past_total']} shows → {FX['past_pages']} pages")
print(f"  Large lineup  : '{FX['large_lineup_venue']}' "
      f"({FX['large_lineup_size']} members, past page {FX['large_lineup_page']})")
print(f"  Normal lineup : '{FX['normal_lineup_venue']}' "
      f"({FX['normal_lineup_size']} members, past page {FX['normal_lineup_page']})")
print(f"  Large setlist  : '{FX['large_setlist_id']}' ({FX['large_setlist_size']} songs, "
      f"past page {FX['large_setlist_page']}) → first song: "
      f"'{FX['large_setlist_first_song']}' ({FX['large_song_play_count']}x)")
print(f"  Normal setlist : '{FX['normal_setlist_id']}' ({FX['normal_setlist_size']} songs, "
      f"past page {FX['normal_setlist_page']}) → first song: "
      f"'{FX['normal_setlist_first_song']}' ({FX['normal_song_play_count']}x)")
print(f"  Empty show     : '{FX['empty_show_id']}' (past page {FX['empty_show_page']})")
print("────────────────────────────────────────────────────────────────────────\n")


# ── Test suite ────────────────────────────────────────────────────────────────

class CosmicHawgTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        opts = Options()
        opts.binary_location = CHROME_BINARY
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1400,900")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        service = Service(executable_path=CHROMEDRIVER_PATH)
        cls.driver = webdriver.Chrome(service=service, options=opts)
        cls.wait   = WebDriverWait(cls.driver, 15)
        cls.driver.get(BASE_URL)
        cls.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#list-previous .tour-item"))
        )
        time.sleep(1)

    def tearDown(self):
        for mid in ("song-history-modal", "setlist-modal", "lineup-modal"):
            try:
                if self._modal_open(mid):
                    self.driver.find_element(By.CSS_SELECTOR, f"#{mid} .close-btn").click()
                    time.sleep(0.3)
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _switch_tab(self, name: str):
        panel_id = "panel-upcoming" if name == "Upcoming" else "panel-previous"
        panel = self.driver.find_element(By.ID, panel_id)
        if "active" not in panel.get_attribute("class"):
            btn = self.driver.find_element(
                By.XPATH,
                f"//button[contains(@class,'tab-btn') and contains(.,'{name}')]"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.4)

    def _visible_items(self, list_id: str):
        return [i for i in self.driver.find_elements(By.CSS_SELECTOR, f"#{list_id} .tour-item")
                if i.is_displayed()]

    def _active_page(self, panel_id: str, top=False) -> int:
        suffix = "-top" if top else ""
        pag = self.driver.find_element(By.ID, f"pagination-{panel_id}{suffix}")
        btns = pag.find_elements(By.CSS_SELECTOR, ".page-btn.active")
        return int(btns[0].text.strip()) if btns else 1

    def _reset_to_page_1(self, panel_id: str, top=False):
        suffix = "-top" if top else ""
        pag = self.driver.find_element(By.ID, f"pagination-{panel_id}{suffix}")
        btns = [b for b in pag.find_elements(By.CLASS_NAME, "page-btn") if b.text.strip() == "1"]
        if btns:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
            self.driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(0.3)

    def _click_next(self, panel_id: str, top=False):
        suffix = "-top" if top else ""
        pag = self.driver.find_element(By.ID, f"pagination-{panel_id}{suffix}")
        btn = pag.find_element(
            By.XPATH,
            ".//button[not(@disabled) and contains(@class,'page-arrow') and text()='>']"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.3)

    def _go_to_page(self, panel_id: str, target: int, top=False):
        if target <= 1:
            return  # single page — no pagination widget rendered, nothing to click
        self._reset_to_page_1(panel_id, top)
        while self._active_page(panel_id, top) < target:
            self._click_next(panel_id, top)

    def _open_btn(self, show_id: str, btn_class: str):
        # Find the button within the active panel only
        active_panel = self.driver.find_element(By.CSS_SELECTOR, ".shows-panel.active")
        btns = active_panel.find_elements(
            By.XPATH,
            f".//button[contains(@class,'{btn_class}') and @onclick[contains(.,'{show_id}')]]"
        )
        self.assertTrue(btns, f"No '{btn_class}' button found for show '{show_id}' on current page")
        btn = btns[0]
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.2)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.4)

    def _modal_open(self, modal_id: str) -> bool:
        return "open" in self.driver.find_element(By.ID, modal_id).get_attribute("class")

    def _close_modal(self, modal_id: str):
        self.driver.find_element(By.CSS_SELECTOR, f"#{modal_id} .close-btn").click()
        time.sleep(0.3)

    def _check_scrollable(self, selector: str):
        el  = self.driver.find_element(By.CSS_SELECTOR, selector)
        sh  = self.driver.execute_script("return arguments[0].scrollHeight;", el)
        ch  = self.driver.execute_script("return arguments[0].clientHeight;", el)
        return sh > ch, sh, ch

    def _scroll_bottom(self, selector: str) -> int:
        el = self.driver.find_element(By.CSS_SELECTOR, selector)
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", el)
        time.sleep(0.3)
        return self.driver.execute_script("return arguments[0].scrollTop;", el)

    def _expected_on_page(self, total: int, page: int, pages: int) -> int:
        remainder = total % SHOWS_PER_PAGE
        return remainder if (page == pages and remainder) else SHOWS_PER_PAGE

    # ── Pagination helper ─────────────────────────────────────────────────────

    def _click_prev(self, panel_id: str, top=False):
        suffix = "-top" if top else ""
        pag = self.driver.find_element(By.ID, f"pagination-{panel_id}{suffix}")
        btn = pag.find_element(
            By.XPATH,
            ".//button[not(@disabled) and contains(@class,'page-arrow') and text()='<']"
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.3)

    def _run_pagination_test(self, panel_id: str, list_id: str, total: int, pages: int):
        """
        Forward up to 3 pages via the TOP counter, then back (one fewer step)
        via the BOTTOM counter, verifying both counters stay in sync throughout.

        Steps forward and back are random each run:
          forward_steps = random 1–3  (capped so we don't overshoot page count)
          back_steps    = forward_steps - 1  (minimum 1)
        """
        if pages < 2:
            self.skipTest(f"{panel_id}: only {pages} page(s) — run generate_shows.py first")

        # Clamp forward steps so we don't go past the last page
        max_fwd = min(3, pages - 1)   # at least 1 page must remain for back
        forward_steps = random.randint(1, max(1, max_fwd))
        back_steps    = max(1, forward_steps - 1)

        print(f"\n    [{panel_id}] forward {forward_steps} page(s) via top, "
              f"back {back_steps} page(s) via bottom")

        # Start at page 1
        self._reset_to_page_1(panel_id, top=True)
        current_page = 1

        # ── Forward via TOP counter ───────────────────────────────────────────
        for step in range(forward_steps):
            self._click_next(panel_id, top=True)
            current_page += 1

            top_page = self._active_page(panel_id, top=True)
            bot_page = self._active_page(panel_id, top=False)

            self.assertEqual(top_page, current_page,
                f"{panel_id} top counter: expected page {current_page}, got {top_page}")
            self.assertEqual(bot_page, current_page,
                f"{panel_id} top→bottom sync: bottom shows {bot_page}, expected {current_page}")

            visible = self._visible_items(list_id)
            expected = self._expected_on_page(total, current_page, pages)
            self.assertEqual(len(visible), expected,
                f"{panel_id} page {current_page}: expected {expected} items, got {len(visible)}")

        # ── Back via BOTTOM counter ───────────────────────────────────────────
        for step in range(back_steps):
            self._click_prev(panel_id, top=False)
            current_page -= 1

            bot_page = self._active_page(panel_id, top=False)
            top_page = self._active_page(panel_id, top=True)

            self.assertEqual(bot_page, current_page,
                f"{panel_id} bottom counter: expected page {current_page}, got {bot_page}")
            self.assertEqual(top_page, current_page,
                f"{panel_id} bottom→top sync: top shows {top_page}, expected {current_page}")

            visible = self._visible_items(list_id)
            expected = self._expected_on_page(total, current_page, pages)
            self.assertEqual(len(visible), expected,
                f"{panel_id} page {current_page}: expected {expected} items, got {len(visible)}")

        return forward_steps, back_steps

    # ── 0. JSON validation ───────────────────────────────────────────────────────

    def test_00_json_validation(self):
        shows    = _load("shows.json")
        lineups  = _load("lineups.json")["shows"]
        setlists = _load("setlists.json")["shows"]

        lineup_ids  = {l["id"] for l in lineups}
        setlist_ids = {s["id"] for s in setlists}
        show_ids    = []

        for i, show in enumerate(shows):
            ref = f"shows.json entry {i+1} ({show.get('venue', '?')})"

            # Required fields
            for field in ("date", "venue", "city"):
                self.assertIn(field, show, f"{ref}: missing '{field}'")
                self.assertTrue(show[field].strip(), f"{ref}: '{field}' is empty")

            # Valid date format
            try:
                from datetime import datetime
                datetime.strptime(show["date"], "%Y-%m-%d")
            except ValueError:
                self.fail(f"{ref}: invalid date format '{show['date']}' — expected YYYY-MM-DD")

            # No duplicate IDs (past shows have lineupId/setlistId as their ID)
            sid = show.get("lineupId") or show.get("setlistId")
            if sid:
                self.assertNotIn(sid, show_ids, f"Duplicate show ID: '{sid}'")
                show_ids.append(sid)

            # If lineupId is set, it must exist in lineups.json
            # (except the intentional empty test show which has no lineup/setlist entry)
            if show.get("lineupId") and show.get("venue") != "Empty Show Test Venue":
                self.assertIn(show["lineupId"], lineup_ids,
                    f"{ref}: lineupId '{show['lineupId']}' not found in lineups.json")

            # If setlistId is set, it must exist in setlists.json
            if show.get("setlistId") and show.get("venue") != "Empty Show Test Venue":
                self.assertIn(show["setlistId"], setlist_ids,
                    f"{ref}: setlistId '{show['setlistId']}' not found in setlists.json")

        print(f"  ✓ JSON valid: {len(shows)} shows, no duplicates, all IDs resolve")

    # ── 9. Empty lineup + setlist — verify "coming soon" verbiage ───────────────

    def test_09_empty_lineup_and_setlist(self):
        self._switch_tab("Previous")
        # Reset to page 1 first, then navigate to the correct page
        self._reset_to_page_1("previous")
        self._go_to_page("previous", FX["empty_show_page"])
        time.sleep(0.5)  # let page render fully

        # ── Empty lineup ──────────────────────────────────────────────────────
        self._open_btn(FX["empty_show_id"], "lineup-btn")
        self.assertTrue(self._modal_open("lineup-modal"), "Empty lineup modal did not open")

        title = self.driver.find_element(By.ID, "lineup-title").text.strip()
        self.assertEqual(title.upper(), "LINEUP COMING SOON.",
            f"Expected 'Lineup coming soon.' but got '{title}'")

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#lineup-list .lineup-row")
        self.assertEqual(len(rows), 0, f"Expected 0 lineup rows, got {len(rows)}")

        self._close_modal("lineup-modal")

        # ── Empty setlist ─────────────────────────────────────────────────────
        self._open_btn(FX["empty_show_id"], "setlist-btn")
        self.assertTrue(self._modal_open("setlist-modal"), "Empty setlist modal did not open")

        title = self.driver.find_element(By.ID, "setlist-title").text.strip()
        self.assertEqual(title.upper(), "SETLIST COMING SOON.",
            f"Expected 'Setlist coming soon.' but got '{title}'")

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#setlist-list .setlist-row")
        self.assertEqual(len(rows), 0, f"Expected 0 setlist rows, got {len(rows)}")

        self._close_modal("setlist-modal")
        print("  ✓ Empty show: 'Lineup coming soon.' and 'Setlist coming soon.' verified")

    # ── 1. Previous pagination — top forward, bottom back, sync checked ───────

    def test_01_previous_pagination(self):
        self._switch_tab("Previous")
        fwd, back = self._run_pagination_test(
            "previous", "list-previous", FX["past_total"], FX["past_pages"]
        )
        print(f"  ✓ Previous: forward {fwd} via top, back {back} via bottom — sync verified")

    # ── 2. Upcoming pagination — top forward, bottom back, sync checked ───────

    def test_02_upcoming_pagination(self):
        self._switch_tab("Upcoming")
        fwd, back = self._run_pagination_test(
            "upcoming", "list-upcoming", FX["upcoming_total"], FX["upcoming_pages"]
        )
        print(f"  ✓ Upcoming: forward {fwd} via top, back {back} via bottom — sync verified")

    # ── 4. Normal lineup modal ────────────────────────────────────────────────

    def test_03_lineup_normal_modal(self):
        self._switch_tab("Previous")
        self._go_to_page("previous", FX["normal_lineup_page"])
        self._open_btn(FX["normal_lineup_id"], "lineup-btn")

        self.assertTrue(self._modal_open("lineup-modal"), "Normal lineup modal did not open")
        self.assertIn(FX["normal_lineup_venue"].upper(),
                      self.driver.find_element(By.ID, "lineup-title").text.upper())

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#lineup-list .lineup-row")
        self.assertEqual(len(rows), FX["normal_lineup_size"])

        self._close_modal("lineup-modal")
        self.assertFalse(self._modal_open("lineup-modal"), "Normal lineup modal did not close")

        print(f"  ✓ Normal lineup: '{FX['normal_lineup_venue']}' — {len(rows)} members")

    # ── 5. Large lineup modal + scrollbar ─────────────────────────────────────

    def test_04_lineup_large_modal_scrollable(self):
        self._switch_tab("Previous")
        self._go_to_page("previous", FX["large_lineup_page"])
        self._open_btn(FX["large_lineup_id"], "lineup-btn")

        self.assertTrue(self._modal_open("lineup-modal"), "Large lineup modal did not open")

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#lineup-list .lineup-row")
        self.assertEqual(len(rows), FX["large_lineup_size"])

        scrollable, sh, ch = self._check_scrollable("#lineup-modal .modal-box")
        self.assertTrue(scrollable,
            f"Large lineup should be scrollable — scrollHeight={sh}, clientHeight={ch}")

        scroll_top = self._scroll_bottom("#lineup-modal .modal-box")
        self.assertGreater(scroll_top, 0, "Scrollbar didn't move after scrolling to bottom")

        self._close_modal("lineup-modal")
        print(f"  ✓ Large lineup: '{FX['large_lineup_venue']}' — {len(rows)} members, "
              f"scrollbar active (sh={sh}, ch={ch})")

    # ── 6. Normal setlist modal ───────────────────────────────────────────────

    def test_05_setlist_normal_modal(self):
        self._switch_tab("Previous")
        self._go_to_page("previous", FX["normal_setlist_page"])
        self._open_btn(FX["normal_setlist_id"], "setlist-btn")

        self.assertTrue(self._modal_open("setlist-modal"), "Normal setlist modal did not open")

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#setlist-list .setlist-row")
        self.assertEqual(len(rows), FX["normal_setlist_size"])

        self._close_modal("setlist-modal")
        self.assertFalse(self._modal_open("setlist-modal"), "Normal setlist modal did not close")

        print(f"  ✓ Normal setlist: {len(rows)} songs")

    # ── 7. Large setlist modal + scrollbar ────────────────────────────────────

    def test_06_setlist_large_modal_scrollable(self):
        self._switch_tab("Previous")
        self._go_to_page("previous", FX["large_setlist_page"])
        self._open_btn(FX["large_setlist_id"], "setlist-btn")

        self.assertTrue(self._modal_open("setlist-modal"), "Large setlist modal did not open")

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#setlist-list .setlist-row")
        self.assertEqual(len(rows), FX["large_setlist_size"])

        scrollable, sh, ch = self._check_scrollable("#setlist-modal .modal-box")
        self.assertTrue(scrollable,
            f"Large setlist should be scrollable — scrollHeight={sh}, clientHeight={ch}")

        scroll_top = self._scroll_bottom("#setlist-modal .modal-box")
        self.assertGreater(scroll_top, 0, "Setlist scrollbar didn't move")

        # Leave open — test 8 uses it
        print(f"  ✓ Large setlist: {len(rows)} songs, scrollbar active (sh={sh}, ch={ch})")

    # ── 8. Song click — large setlist ─────────────────────────────────────────

    def test_07_song_click_large_setlist(self):
        if not self._modal_open("setlist-modal"):
            self._switch_tab("Previous")
            self._go_to_page("previous", FX["large_setlist_page"])
            self._open_btn(FX["large_setlist_id"], "setlist-btn")

        # Scroll to top so first song is visible
        self.driver.execute_script(
            "document.querySelector('#setlist-modal .modal-box').scrollTop = 0;"
        )
        time.sleep(0.2)

        song = FX["large_setlist_first_song"]
        # Find by iterating links to avoid XPath issues with special characters
        song_link = None
        for link in self.driver.find_elements(By.CSS_SELECTOR, "#setlist-list .song-link"):
            if song.lower() in link.text.lower():
                song_link = link
                break
        self.assertIsNotNone(song_link, f"Song link '{song}' not found in large setlist")
        self.driver.execute_script("arguments[0].click();", song_link)
        time.sleep(0.4)

        self.assertFalse(self._modal_open("setlist-modal"), "Setlist modal should close on song click")
        self.assertTrue(self._modal_open("song-history-modal"), "Song history modal did not open")

        self.assertIn(song.upper(), self.driver.find_element(By.ID, "song-history-title").text.upper())
        self.assertIn(str(FX["large_song_play_count"]),
                      self.driver.find_element(By.ID, "song-history-count").text)

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#song-history-list .history-row")
        self.assertEqual(len(rows), FX["large_song_play_count"])
        for i, row in enumerate(rows):
            self.assertTrue(row.find_element(By.CLASS_NAME, "history-date").text.strip(),
                            f"Row {i+1}: date empty")
            self.assertTrue(row.find_element(By.CLASS_NAME, "history-venue").text.strip(),
                            f"Row {i+1}: venue empty")

        self.driver.find_element(By.CSS_SELECTOR, "#song-history-modal .close-btn").click()
        time.sleep(0.3)
        self._close_modal("setlist-modal")

        print(f"  ✓ Large setlist song: '{song}' — "
              f"{FX['large_song_play_count']} plays, {len(rows)} history rows")

    # ── 9. Song click — normal setlist ────────────────────────────────────────

    def test_08_song_click_normal_setlist(self):
        self._switch_tab("Previous")
        self._go_to_page("previous", FX["normal_setlist_page"])
        self._open_btn(FX["normal_setlist_id"], "setlist-btn")

        self.assertTrue(self._modal_open("setlist-modal"), "Normal setlist modal did not open")

        song = FX["normal_setlist_first_song"]
        song_link = None
        for link in self.driver.find_elements(By.CSS_SELECTOR, "#setlist-list .song-link"):
            if song.lower() in link.text.lower():
                song_link = link
                break
        self.assertIsNotNone(song_link, f"Song link '{song}' not found in normal setlist")
        self.driver.execute_script("arguments[0].click();", song_link)
        time.sleep(0.4)

        self.assertFalse(self._modal_open("setlist-modal"), "Setlist modal should close on song click")
        self.assertTrue(self._modal_open("song-history-modal"), "Song history modal did not open")

        self.assertIn(str(FX["normal_song_play_count"]),
                      self.driver.find_element(By.ID, "song-history-count").text)

        rows = self.driver.find_elements(By.CSS_SELECTOR, "#song-history-list .history-row")
        self.assertEqual(len(rows), FX["normal_song_play_count"])
        for i, row in enumerate(rows):
            self.assertTrue(row.find_element(By.CLASS_NAME, "history-date").text.strip(),
                            f"Row {i+1}: date empty")
            self.assertTrue(row.find_element(By.CLASS_NAME, "history-venue").text.strip(),
                            f"Row {i+1}: venue empty")

        self.driver.find_element(By.CSS_SELECTOR, "#song-history-modal .close-btn").click()
        time.sleep(0.3)
        self._close_modal("setlist-modal")

        print(f"  ✓ Normal setlist song: '{song}' — "
              f"{FX['normal_song_play_count']} plays, {len(rows)} history rows")


# ── Entry point ───────────────────────────────────────────────────────────────

class _ResultCollector(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append({"name": test._testMethodName, "status": "passed", "message": ""})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append({"name": test._testMethodName, "status": "failed",
                                   "message": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append({"name": test._testMethodName, "status": "error",
                                   "message": self._exc_info_to_string(err, test)})


if __name__ == "__main__":
    import sys
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(CosmicHawgTests)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=_ResultCollector)
    result = runner.run(suite)

    # Exit 1 on any failure — GitHub Actions marks the commit red
    sys.exit(0 if result.wasSuccessful() else 1)
