function switchTab(tab, btn) {
  document.querySelectorAll('.shows-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + tab).classList.add('active');
  btn.classList.add('active');
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const SHOWS_PER_PAGE = 4;
const paginationState = {};

function buildShowItem(show, isPast) {
  const [year, month, day] = show.date.split('-');
  const item = document.createElement('div');
  item.className = 'tour-item' + (isPast ? ' past' : '');

  const dateBox = `<div class="tour-date-box">
    <p class="tour-month">${MONTHS[parseInt(month)-1]}</p>
    <p class="tour-day">${day}</p>
    <span class="tour-year">${year}</span>
  </div>`;

  const info = `<div>
    <p class="tour-venue">${show.venue}</p>
    <p class="tour-city">${show.city}</p>
  </div>`;

  const action = isPast
    ? (() => {
        const lineupBtn = show.lineupId
          ? `<button class="lineup-btn" onclick="showLineup('${show.lineupId}')">Lineup</button>`
          : '';
        const setlistBtn = show.setlistId
          ? `<button class="setlist-btn" onclick="showSetlist('${show.setlistId}')">Setlist</button>`
          : '';
        return (lineupBtn || setlistBtn)
          ? `<div class="show-btns">${lineupBtn}${setlistBtn}</div>`
          : '';
      })()
    : '';

  item.innerHTML = dateBox + info + action;
  return item;
}

function renderShows(ALL_SHOWS) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const upcoming = ALL_SHOWS
    .filter(s => new Date(s.date + 'T00:00:00') >= today)
    .sort((a, b) => a.date.localeCompare(b.date));

  const previous = ALL_SHOWS
    .filter(s => new Date(s.date + 'T00:00:00') < today)
    .sort((a, b) => b.date.localeCompare(a.date));

  const upcomingList = document.getElementById('list-upcoming');
  const previousList = document.getElementById('list-previous');
  upcomingList.innerHTML = '';
  previousList.innerHTML = '';

  if (upcoming.length === 0) {
    document.getElementById('no-upcoming').style.display = '';
  } else {
    upcoming.forEach(s => upcomingList.appendChild(buildShowItem(s, false)));
  }

  if (previous.length === 0) {
    document.getElementById('no-previous').style.display = '';
  } else {
    previous.forEach(s => previousList.appendChild(buildShowItem(s, true)));
  }

  initPagination('upcoming');
  initPagination('previous');
}

function initPagination(panelId) {
  const list = document.getElementById('list-' + panelId);
  if (!list) return;
  const items = Array.from(list.querySelectorAll('.tour-item'));
  if (items.length === 0) return;
  paginationState[panelId] = 1;
  renderPage(panelId, items);
}

function renderPage(panelId, items) {
  const page = paginationState[panelId];
  const totalPages = Math.ceil(items.length / SHOWS_PER_PAGE);
  const start = (page - 1) * SHOWS_PER_PAGE;
  const end = start + SHOWS_PER_PAGE;

  items.forEach((item, i) => {
    item.style.display = (i >= start && i < end) ? '' : 'none';
  });

  const paginationEl = document.getElementById('pagination-' + panelId);
  if (!paginationEl) return;
  paginationEl.innerHTML = '';
  if (totalPages <= 1) return;

  // ── Sliding window pagination: max 3 page numbers + arrows ──
  const WINDOW = 3;

  // Calculate the window start so the current page is centered when possible
  let winStart = Math.max(1, page - Math.floor(WINDOW / 2));
  let winEnd = winStart + WINDOW - 1;
  if (winEnd > totalPages) {
    winEnd = totalPages;
    winStart = Math.max(1, winEnd - WINDOW + 1);
  }

  function makeBtn(label, targetPage, isActive) {
    const btn = document.createElement('button');
    btn.className = 'page-btn' + (isActive ? ' active' : '');
    btn.textContent = label;
    btn.addEventListener('click', () => {
      paginationState[panelId] = targetPage;
      renderPage(panelId, items);
      const tabsEl = document.getElementById('shows-tabs-anchor');
      const offset = tabsEl.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: offset, behavior: 'smooth' });
    });
    return btn;
  }

  // Left arrow
  if (page > 1) {
    paginationEl.appendChild(makeBtn('‹', page - 1, false));
  }

  // Page number buttons (sliding window)
  for (let i = winStart; i <= winEnd; i++) {
    paginationEl.appendChild(makeBtn(i, i, i === page));
  }

  // Right arrow
  if (page < totalPages) {
    paginationEl.appendChild(makeBtn('›', page + 1, false));
  }
}

// ── Reveal on scroll ──
const reveals = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(el => { if (el.isIntersecting) el.target.classList.add('visible'); });
}, { threshold: 0.1 });
reveals.forEach(el => observer.observe(el));

// ── YouTube facade ──
function loadVideo() {
  var facade = document.getElementById('yt-facade');
  var iframe = document.getElementById('yt-iframe');
  facade.style.display = 'none';
  iframe.src = 'https://www.youtube.com/embed/AJsZSgBB1mw?autoplay=1&rel=0';
  document.getElementById('yt-iframe-wrap').style.display = 'block';
  iframe.style.display = 'block';
}

// ── Lineup popup ──
let lineupData = null;
(async () => {
  try {
    const res = await fetch('/lineups.json');
    lineupData = await res.json();
  } catch(e) { console.warn('Could not load lineups.json', e); }
})();

function showLineup(id) {
  const noData = !lineupData || !lineupData.shows.find(s => s.id === id);
  if (noData) {
    document.getElementById('lineup-title').textContent = 'Lineup coming soon.';
    document.getElementById('lineup-date').textContent = '';
    document.getElementById('lineup-list').innerHTML = '';
    document.getElementById('lineup-modal').classList.add('open');
    return;
  }
  const show = lineupData.shows.find(s => s.id === id);
  document.getElementById('lineup-title').textContent = show.venue;
  document.getElementById('lineup-date').textContent =
    show.date.month + ' ' + show.date.day + ', ' + show.date.year + ' - ' + show.city;
  document.getElementById('lineup-list').innerHTML = show.lineup
    .map(m => '<div class="lineup-row"><span class="lineup-name">' + m.name + '</span><span class="lineup-role">' + m.role + '</span></div>')
    .join('');
  document.getElementById('lineup-modal').classList.add('open');
}

document.addEventListener('click', function(e) {
  const lineupModal = document.getElementById('lineup-modal');
  if (lineupModal && e.target === lineupModal) lineupModal.classList.remove('open');
  const setlistModal = document.getElementById('setlist-modal');
  if (setlistModal && e.target === setlistModal) setlistModal.classList.remove('open');
  const songHistoryModal = document.getElementById('song-history-modal');
  if (songHistoryModal && e.target === songHistoryModal) songHistoryModal.classList.remove('open');
});

// ── Setlist popup ──
let setlistData = null;
(async () => {
  try {
    const res = await fetch('/setlists.json');
    setlistData = await res.json();
  } catch(e) { console.warn('Could not load setlists.json', e); }
})();

function buildSongHistory() {
  if (!setlistData) return {};
  const map = {};
  setlistData.shows.forEach(show => {
    (show.setlist || []).forEach(song => {
      const key = song.title.toLowerCase().trim();
      if (!map[key]) map[key] = { title: song.title, plays: [] };
      map[key].plays.push({
        month: show.date.month,
        day: show.date.day,
        year: show.date.year,
        venue: show.venue,
        city: show.city
      });
    });
  });
  return map;
}

function showSetlist(id) {
  const noData = !setlistData || !setlistData.shows.find(s => s.id === id);
  if (noData) {
    document.getElementById('setlist-title').textContent = 'Setlist coming soon.';
    document.getElementById('setlist-date').textContent = '';
    document.getElementById('setlist-list').innerHTML = '';
    document.getElementById('setlist-modal').classList.add('open');
    return;
  }
  const show = setlistData.shows.find(s => s.id === id);
  const songHistory = buildSongHistory();
  document.getElementById('setlist-title').textContent = show.venue;
  document.getElementById('setlist-date').textContent =
    show.date.month + ' ' + show.date.day + ', ' + show.date.year + ' — ' + show.city;
  document.getElementById('setlist-list').innerHTML = show.setlist
    .map((song, i) => {
      const key = song.title.toLowerCase().trim();
      const count = songHistory[key] ? songHistory[key].plays.length : 1;
      return `<div class="setlist-row">
        <span class="setlist-num">${i + 1}.</span>
        <span class="setlist-song">
          <a class="song-link" href="#" onclick="showSongHistory('${song.title.replace(/'/g,"\\'")}');return false;">${song.title}</a>
        </span>
      </div>`;
    })
    .join('');
  document.getElementById('setlist-modal').classList.add('open');
}

function showSongHistory(title) {
  const songHistory = buildSongHistory();
  const key = title.toLowerCase().trim();
  const entry = songHistory[key];
  const count = entry ? entry.plays.length : 0;
  document.getElementById('song-history-title').textContent = title;
  document.getElementById('song-history-count').textContent = 'Times Played: ' + count;
  document.getElementById('song-history-list').innerHTML = entry
    ? entry.plays.map(p => `
        <div class="history-row">
          <span class="history-date">${p.month} ${p.day}, ${p.year}</span>
          <span class="history-venue">${p.venue} — ${p.city}</span>
        </div>`).join('')
    : '<p style="text-align:center;opacity:0.5;font-family:Special Elite,cursive;letter-spacing:2px;font-size:0.8rem;margin-top:1rem;">No history found.</p>';
  document.getElementById('setlist-modal').classList.remove('open');
  document.getElementById('song-history-modal').classList.add('open');
}

// ── Init: fetch shows.json then render ──
document.addEventListener('DOMContentLoaded', () => {
  fetch('/shows.json')
    .then(res => res.json())
    .then(data => renderShows(data))
    .catch(e => console.error('Could not load shows.json', e));
});
