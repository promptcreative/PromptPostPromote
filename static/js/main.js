document.addEventListener('DOMContentLoaded', function() {
    loadCalendars();
    loadSettings();

    document.getElementById('fetchCalBtn').addEventListener('click', async function() {
        const btn = this;
        const url = document.getElementById('fetchCalUrl').value.trim();
        const calType = document.getElementById('fetchCalType').value;
        const calName = document.getElementById('fetchCalName').value.trim() || calType;

        if (!url) { alert('Please enter a calendar URL'); return; }

        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Fetching...';

        try {
            const resp = await fetch('/api/calendars/fetch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ics_url: url, calendar_type: calType, calendar_name: calName})
            });
            const data = await resp.json();
            if (data.success) {
                alert('Imported ' + data.event_count + ' events!');
                loadCalendars();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch(e) {
            alert('Error: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-cloud-download"></i> Fetch & Import';
        }
    });

    document.getElementById('importCalForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('importCalFile');
        const calType = document.getElementById('importCalType').value;

        if (!fileInput.files.length) { alert('Select a file'); return; }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('calendar_type', calType);
        formData.append('calendar_name', fileInput.files[0].name);

        try {
            const resp = await fetch('/api/calendars/import', {method: 'POST', body: formData});
            const data = await resp.json();
            if (data.success) {
                alert('Imported ' + data.event_count + ' events!');
                loadCalendars();
                fileInput.value = '';
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch(e) {
            alert('Error: ' + e.message);
        }
    });

    document.getElementById('loadEventsBtn').addEventListener('click', loadEvents);

    document.getElementById('selectAllEvents').addEventListener('change', function() {
        var isChecked = this.checked;
        document.querySelectorAll('.event-checkbox').forEach(function(cb) { cb.checked = isChecked; });
        updatePushButton();
    });

    document.getElementById('pushToPublerBtn').addEventListener('click', pushToPubler);

    document.getElementById('testPublerBtn').addEventListener('click', async function() {
        const statusDiv = document.getElementById('publerStatus');
        statusDiv.innerHTML = '<span class="text-muted">Testing...</span>';
        try {
            const resp = await fetch('/api/publer/test');
            const data = await resp.json();
            if (data.success) {
                statusDiv.innerHTML = '<div class="alert alert-success">Connected successfully!</div>';
            } else {
                statusDiv.innerHTML = '<div class="alert alert-danger">Connection failed: ' + (data.error || 'Unknown') + '</div>';
            }
        } catch(e) {
            statusDiv.innerHTML = '<div class="alert alert-danger">Error: ' + e.message + '</div>';
        }
    });

    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
});

async function loadCalendars() {
    try {
        const resp = await fetch('/api/calendars');
        const calendars = await resp.json();
        const container = document.getElementById('calendarList');

        if (!calendars.length) {
            container.innerHTML = '<p class="text-muted">No calendars loaded</p>';
            return;
        }

        container.innerHTML = calendars.map(function(cal) {
            return '<div class="d-flex justify-content-between align-items-center border-bottom py-2">' +
                '<div>' +
                    '<strong>' + cal.calendar_name + '</strong> ' +
                    '<span class="badge bg-secondary ms-1">' + cal.calendar_type + '</span>' +
                    '<br><small class="text-muted">' + cal.event_count + ' events</small>' +
                    (cal.ics_url ? '<br><small class="text-muted text-truncate d-inline-block" style="max-width:300px">' + cal.ics_url + '</small>' : '') +
                '</div>' +
                '<button class="btn btn-sm btn-outline-danger" onclick="deleteCalendar(' + cal.id + ')">' +
                    '<i class="bi bi-trash"></i>' +
                '</button>' +
            '</div>';
        }).join('');
    } catch(e) {
        console.error('Error loading calendars:', e);
    }
}

async function deleteCalendar(id) {
    if (!confirm('Delete this calendar and all its events?')) return;
    try {
        await fetch('/api/calendars/' + id, {method: 'DELETE'});
        loadCalendars();
    } catch(e) {
        alert('Error: ' + e.message);
    }
}

async function loadEvents() {
    const calFilter = document.getElementById('eventCalFilter').value;
    const statusFilter = document.getElementById('eventStatusFilter').value;

    var url = '/api/events';
    if (calFilter) url += '?calendar_type=' + calFilter;

    try {
        const resp = await fetch(url);
        var events = await resp.json();

        if (statusFilter) {
            events = events.filter(function(e) { return e.publer_status === statusFilter; });
        }

        const tbody = document.getElementById('eventsTableBody');
        const noMsg = document.getElementById('noEventsMsg');

        if (!events.length) {
            tbody.innerHTML = '';
            noMsg.style.display = 'block';
            noMsg.textContent = 'No events found';
            return;
        }

        noMsg.style.display = 'none';
        tbody.innerHTML = events.map(function(ev) {
            const date = new Date(ev.midpoint_time);
            const statusClasses = {
                'pending': 'bg-warning text-dark',
                'ready': 'bg-info',
                'pushed': 'bg-success'
            };
            const statusBadge = statusClasses[ev.publer_status] || 'bg-secondary';

            return '<tr>' +
                '<td><input type="checkbox" class="event-checkbox" value="' + ev.id + '" onchange="updatePushButton()"></td>' +
                '<td>' + date.toLocaleDateString() + '</td>' +
                '<td>' + date.toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"}) + '</td>' +
                '<td><small>' + ev.summary + '</small></td>' +
                '<td>' +
                    '<textarea class="form-control form-control-sm social-copy" data-event-id="' + ev.id + '" rows="2" placeholder="Write social media copy...">' + (ev.social_copy || '') + '</textarea>' +
                '</td>' +
                '<td><span class="badge ' + statusBadge + '">' + ev.publer_status + '</span></td>' +
                '<td>' +
                    '<button class="btn btn-sm btn-outline-primary" onclick="saveCopy(' + ev.id + ')">' +
                        '<i class="bi bi-save"></i>' +
                    '</button>' +
                '</td>' +
            '</tr>';
        }).join('');
    } catch(e) {
        alert('Error loading events: ' + e.message);
    }
}

async function saveCopy(eventId) {
    const textarea = document.querySelector('textarea[data-event-id="' + eventId + '"]');
    const copy = textarea.value.trim();

    try {
        const resp = await fetch('/api/events/' + eventId + '/copy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({social_copy: copy})
        });
        const data = await resp.json();
        if (data.id) {
            loadEvents();
        }
    } catch(e) {
        alert('Error: ' + e.message);
    }
}

function updatePushButton() {
    const checked = document.querySelectorAll('.event-checkbox:checked');
    const btn = document.getElementById('pushToPublerBtn');
    btn.disabled = checked.length === 0;
    if (checked.length > 0) {
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Push ' + checked.length + ' to Publer';
    } else {
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Push to Publer';
    }
}

async function pushToPubler() {
    const checked = document.querySelectorAll('.event-checkbox:checked');
    const eventIds = Array.from(checked).map(function(cb) { return parseInt(cb.value); });

    if (!eventIds.length) return;
    if (!confirm('Push ' + eventIds.length + ' events to Publer?')) return;

    const btn = document.getElementById('pushToPublerBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Pushing...';

    try {
        const resp = await fetch('/api/publer/push', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({event_ids: eventIds})
        });
        const data = await resp.json();
        const success = data.results.filter(function(r) { return r.success; }).length;
        const failed = data.results.filter(function(r) { return !r.success; }).length;
        alert('Pushed: ' + success + ' success, ' + failed + ' failed');
        loadEvents();
    } catch(e) {
        alert('Error: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Push to Publer';
    }
}

async function loadSettings() {
    try {
        const resp = await fetch('/api/settings');
        const settings = await resp.json();
        document.getElementById('settingsCompanyName').value = settings.company_name || '';
        document.getElementById('settingsBrandedHashtag').value = settings.branded_hashtag || '';
        document.getElementById('settingsShopUrl').value = settings.shop_url || '';
    } catch(e) {
        console.error('Error loading settings:', e);
    }
}

async function saveSettings() {
    try {
        const resp = await fetch('/api/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                company_name: document.getElementById('settingsCompanyName').value,
                branded_hashtag: document.getElementById('settingsBrandedHashtag').value,
                shop_url: document.getElementById('settingsShopUrl').value
            })
        });
        const data = await resp.json();
        if (data.id) alert('Settings saved!');
    } catch(e) {
        alert('Error: ' + e.message);
    }
}
