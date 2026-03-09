from flask import Flask, request, jsonify, send_from_directory, session, redirect
import json
import re
import os
import base64
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'cosmichawg')

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO  = 'DB1111d/cosmichawg'
GITHUB_BRANCH = 'main'

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

# ── GitHub API helpers ──
def gh_headers():
    return {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

def gh_get(path):
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}'
    r = requests.get(url, headers=gh_headers())
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    return json.loads(content), data['sha']

def gh_put(path, content_obj, sha, message):
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'
    body = {
        'message': message,
        'content': base64.b64encode(json.dumps(content_obj, indent=2).encode()).decode(),
        'sha': sha,
        'branch': GITHUB_BRANCH
    }
    r = requests.put(url, headers=gh_headers(), json=body)
    r.raise_for_status()

# ── Auth ──
def logged_in():
    return session.get('admin') is True

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if data.get('user') == ADMIN_USER and data.get('password') == ADMIN_PASS:
        session['admin'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Wrong username or password'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/auth-check')
def auth_check():
    return jsonify({'ok': logged_in()})

# ── Serve admin page from GitHub ──
@app.route('/admin')
def admin():
    content, _ = gh_get('admin.html')
    # gh_get parses as JSON, so we need raw for HTML
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/admin.html?ref={GITHUB_BRANCH}'
    r = requests.get(url, headers=gh_headers())
    raw = base64.b64decode(r.json()['content']).decode('utf-8')
    return raw, 200, {'Content-Type': 'text/html'}

# ── SHOWS ──
@app.route('/api/shows', methods=['GET'])
def get_shows():
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    data, _ = gh_get('shows.json')
    return jsonify(data)

@app.route('/api/shows', methods=['POST'])
def add_show():
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    body = request.json
    date  = body['date']
    venue = body['venue']
    city  = body['city']
    show_id = make_id(venue, date)
    shows, sha = gh_get('shows.json')
    shows.insert(0, {
        "date": date,
        "venue": venue,
        "city": city,
        "lineupId": show_id,
        "setlistId": show_id
    })
    gh_put('shows.json', shows, sha, f'Add show: {venue} ({date})')
    return jsonify({"ok": True, "id": show_id})

@app.route('/api/shows/<int:idx>', methods=['PUT'])
def edit_show(idx):
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    body  = request.json
    shows, sha = gh_get('shows.json')
    if idx < 0 or idx >= len(shows):
        return jsonify({"error": "Not found"}), 404
    show = shows[idx]
    show['date']  = body.get('date', show['date'])
    show['venue'] = body.get('venue', show['venue'])
    show['city']  = body.get('city', show['city'])
    show['lineupId']  = make_id(show['venue'], show['date'])
    show['setlistId'] = make_id(show['venue'], show['date'])
    shows[idx] = show
    gh_put('shows.json', shows, sha, f'Edit show: {show["venue"]} ({show["date"]})')
    return jsonify({"ok": True})

@app.route('/api/shows/<int:idx>', methods=['DELETE'])
def delete_show(idx):
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    shows, sha = gh_get('shows.json')
    if idx < 0 or idx >= len(shows):
        return jsonify({"error": "Not found"}), 404
    shows.pop(idx)
    gh_put('shows.json', shows, sha, f'Delete show at index {idx}')
    return jsonify({"ok": True})

# ── SETLISTS ──
@app.route('/api/setlists', methods=['GET'])
def get_setlists():
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    data, _ = gh_get('setlists.json')
    return jsonify(data)

@app.route('/api/setlists', methods=['POST'])
def add_setlist():
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    body  = request.json
    date  = body['date']
    venue = body['venue']
    city  = body['city']
    songs = [{"title": t} for t in body['songs']]
    show_id = make_id(venue, date)
    data, sha = gh_get('setlists.json')
    data['shows'].insert(0, {
        "id": show_id,
        "venue": venue,
        "city": city,
        "date": parse_date(date),
        "setlist": songs
    })
    gh_put('setlists.json', data, sha, f'Add setlist: {venue} ({date})')
    return jsonify({"ok": True, "id": show_id})

@app.route('/api/setlists/<int:idx>', methods=['PUT'])
def edit_setlist(idx):
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    body  = request.json
    data, sha = gh_get('setlists.json')
    shows = data['shows']
    if idx < 0 or idx >= len(shows):
        return jsonify({"error": "Not found"}), 404
    show = shows[idx]
    if 'date' in body and 'venue' in body and 'city' in body:
        show['date']  = parse_date(body['date'])
        show['venue'] = body['venue']
        show['city']  = body['city']
        show['id']    = make_id(body['venue'], body['date'])
    if 'songs' in body:
        show['setlist'] = [{"title": t} for t in body['songs']]
    shows[idx] = show
    data['shows'] = shows
    gh_put('setlists.json', data, sha, f'Edit setlist: {show["venue"]}')
    return jsonify({"ok": True})

@app.route('/api/setlists/<int:idx>', methods=['DELETE'])
def delete_setlist(idx):
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    data, sha = gh_get('setlists.json')
    shows = data['shows']
    if idx < 0 or idx >= len(shows):
        return jsonify({"error": "Not found"}), 404
    shows.pop(idx)
    data['shows'] = shows
    gh_put('setlists.json', data, sha, f'Delete setlist at index {idx}')
    return jsonify({"ok": True})

# ── LINEUPS ──
@app.route('/api/lineups', methods=['GET'])
def get_lineups():
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    data, _ = gh_get('lineups.json')
    return jsonify(data)

@app.route('/api/lineups', methods=['POST'])
def add_lineup():
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    body    = request.json
    date    = body['date']
    venue   = body['venue']
    city    = body['city']
    members = body['members']
    show_id = make_id(venue, date)
    data, sha = gh_get('lineups.json')
    data['shows'].insert(0, {
        "id": show_id,
        "venue": venue,
        "city": city,
        "date": parse_date(date),
        "lineup": members
    })
    gh_put('lineups.json', data, sha, f'Add lineup: {venue} ({date})')
    return jsonify({"ok": True, "id": show_id})

@app.route('/api/lineups/<int:idx>', methods=['PUT'])
def edit_lineup(idx):
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    body  = request.json
    data, sha = gh_get('lineups.json')
    shows = data['shows']
    if idx < 0 or idx >= len(shows):
        return jsonify({"error": "Not found"}), 404
    show = shows[idx]
    if 'date' in body and 'venue' in body and 'city' in body:
        show['date']  = parse_date(body['date'])
        show['venue'] = body['venue']
        show['city']  = body['city']
        show['id']    = make_id(body['venue'], body['date'])
    if 'members' in body:
        show['lineup'] = body['members']
    shows[idx] = show
    data['shows'] = shows
    gh_put('lineups.json', data, sha, f'Edit lineup: {show["venue"]}')
    return jsonify({"ok": True})

@app.route('/api/lineups/<int:idx>', methods=['DELETE'])
def delete_lineup(idx):
    if not logged_in(): return jsonify({'error': 'Unauthorized'}), 401
    data, sha = gh_get('lineups.json')
    shows = data['shows']
    if idx < 0 or idx >= len(shows):
        return jsonify({"error": "Not found"}), 404
    shows.pop(idx)
    data['shows'] = shows
    gh_put('lineups.json', data, sha, f'Delete lineup at index {idx}')
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
