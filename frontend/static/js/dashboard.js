/**
 * FinSight – Dashboard JS
 * Loads profile, watchlists, portfolio positions.
 */
document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    loadProfile();
    loadWatchlists();
    loadPositions();
});

async function loadProfile() {
    try {
        const user = await api.get('/user/profile');
        document.getElementById('user-name').textContent = user.name || 'User';
        document.getElementById('user-email').textContent = user.email;
        const meta = document.getElementById('profile-meta');
        meta.innerHTML = `
            <span><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 1em; height: 1em; vertical-align: middle;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg> ${user.risk_profile || 'Moderate'}</span>
            <span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg> ${user.experience_level || 'Beginner'}</span>
            <span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="10"></circle><path d="M2 12h20"></path><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg> ${user.country || 'India'}</span>
        `;
    } catch (e) {
        console.error('Profile load error:', e);
    }
}

async function loadWatchlists() {
    const container = document.getElementById('watchlists-container');
    try {
        const watchlists = await api.get('/watchlists/');
        if (watchlists.length === 0) {
            container.innerHTML = '<p style="color:var(--text-light);padding:20px 0">No watchlists yet. Click <strong>+ New Watchlist</strong> to create one!</p>';
            return;
        }
        container.innerHTML = watchlists.map(wl => `
            <div class="watchlist-card card" style="margin-bottom:16px; padding:20px;">
                <div class="flex-between mb-2">
                    <h4 style="margin:0">${wl.name}</h4>
                    <div style="display:flex;gap:8px;align-items:center;">
                        <span class="badge badge-info">${wl.items.length} stocks</span>
                        <button class="btn btn-sm btn-outline" onclick="openWatchlistModal(${wl.id})">+ Add Stock</button>
                    </div>
                </div>
                ${wl.items.length === 0
                    ? '<p style="color:var(--text-light);font-size:0.85rem;margin-top:12px">Empty — click Add Stock to start tracking.</p>'
                    : wl.items.map(item => `
                        <div class="watchlist-item" style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--gray-100)">
                            <div>
                                <a href="/pages/instrument_detail.html?id=${item.instrument_id}" style="font-weight:600;color:var(--text);text-decoration:none">${item.symbol}</a>
                                <span style="color:var(--text-light);font-size:0.75rem;margin-left:8px">${item.name}</span>
                            </div>
                            <div style="display:flex;align-items:center;gap:16px">
                                <div style="text-align:right">
                                    <div style="font-weight:600">${formatCurrency(item.current_price)}</div>
                                    <div style="font-size:0.75rem" class="${item.day_change_pct >= 0 ? 'text-positive' : 'text-negative'}">
                                        ${item.day_change_pct >= 0 ? '+' : ''}${item.day_change_pct}%
                                    </div>
                                </div>
                                <button onclick="removeFromWatchlist(${wl.id}, ${item.item_id})"
                                    style="background:none;border:none;cursor:pointer;color:var(--text-light);font-size:18px;padding:0 4px;line-height:1"
                                    title="Remove">&times;</button>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color:var(--danger)">Failed to load watchlists</p>';
    }
}

async function createWatchlist() {
    const name = prompt('Watchlist name:');
    if (!name) return;
    try {
        await api.post('/watchlists/', { name });
        showToast('Watchlist created!', 'success');
        loadWatchlists();
    } catch (e) {
        showToast(e.error || 'Failed to create watchlist', 'error');
    }
}

// ── Watchlist Item Management ─────────────────────────────────
let _wlSearchTimer = null;

function openWatchlistModal(watchlistId) {
    document.getElementById('wl-target-id').value = watchlistId;
    document.getElementById('wl-search-input').value = '';
    document.getElementById('wl-search-results').innerHTML = '<p style="color:var(--text-light);font-size:0.85rem;padding:8px 0">Start typing to search stocks...</p>';
    document.getElementById('watchlist-add-modal').classList.add('active');
    setTimeout(() => document.getElementById('wl-search-input').focus(), 100);
}

function closeWatchlistModal() {
    document.getElementById('watchlist-add-modal').classList.remove('active');
}

function searchWatchlistStock(query) {
    clearTimeout(_wlSearchTimer);
    const resultsEl = document.getElementById('wl-search-results');
    if (!query || query.length < 1) {
        resultsEl.innerHTML = '<p style="color:var(--text-light);font-size:0.85rem;padding:8px 0">Start typing to search stocks...</p>';
        return;
    }
    resultsEl.innerHTML = '<p style="color:var(--text-light);font-size:0.85rem;padding:8px 0">Searching...</p>';
    _wlSearchTimer = setTimeout(async () => {
        try {
            const results = await api.get('/instruments/search?q=' + encodeURIComponent(query));
            if (!results || results.length === 0) {
                resultsEl.innerHTML = '<p style="color:var(--text-light);font-size:0.85rem;padding:8px 0">No results found</p>';
                return;
            }
            resultsEl.innerHTML = results.slice(0, 10).map(inst => `
                <div onclick="addToWatchlist(${inst.id})"
                    style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-radius:8px;cursor:pointer;transition:background 0.15s;margin-bottom:4px;border:1px solid var(--gray-100)"
                    onmouseover="this.style.background='var(--gray-50)'" onmouseout="this.style.background=''"
                >
                    <div>
                        <span style="font-weight:700;color:var(--text)">${inst.symbol}</span>
                        <span style="color:var(--text-light);font-size:0.8rem;margin-left:8px">${inst.name}</span>
                    </div>
                    <div style="text-align:right">
                        <div style="font-weight:600">${formatCurrency(inst.current_price)}</div>
                        <div style="font-size:0.75rem" class="${inst.day_change_pct >= 0 ? 'text-positive' : 'text-negative'}">
                            ${inst.day_change_pct >= 0 ? '+' : ''}${inst.day_change_pct}%
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            resultsEl.innerHTML = '<p style="color:var(--danger);font-size:0.85rem">Search failed</p>';
        }
    }, 300);
}

async function addToWatchlist(instrumentId) {
    const watchlistId = parseInt(document.getElementById('wl-target-id').value);
    try {
        await api.post(`/watchlists/${watchlistId}/items`, { instrument_id: instrumentId });
        showToast('Stock added to watchlist!', 'success');
        closeWatchlistModal();
        loadWatchlists();
    } catch (e) {
        showToast(e.error || 'Failed to add stock', 'error');
    }
}

async function removeFromWatchlist(watchlistId, itemId) {
    try {
        await fetch(`/api/watchlists/${watchlistId}/items/${itemId}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + Auth.getToken() }
        });
        showToast('Stock removed from watchlist', 'info');
        loadWatchlists();
    } catch (e) {
        showToast('Failed to remove stock', 'error');
    }
}

async function loadPositions() {
    const tbody = document.getElementById('positions-tbody');
    try {
        const positions = await api.get('/portfolio/');
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-light)">No positions yet</td></tr>';
            updateSummary(0, 0, 0);
            return;
        }
        let totalInvested = 0, totalCurrent = 0, totalPL = 0;
        tbody.innerHTML = positions.map(p => {
            const invested = p.buy_price * p.quantity;
            const current = p.current_price * p.quantity;
            totalInvested += invested;
            totalCurrent += current;
            totalPL += p.unrealized_pl;
            return `<tr>
                <td><a href="/pages/instrument_detail.html?id=${p.instrument_id}">${p.symbol} – ${p.name}</a></td>
                <td>${p.quantity}</td>
                <td>${formatCurrency(p.buy_price)}</td>
                <td>${formatCurrency(p.current_price)}</td>
                <td class="${p.unrealized_pl >= 0 ? 'text-positive' : 'text-negative'}">${formatCurrency(p.unrealized_pl)}</td>
                <td class="${p.return_pct >= 0 ? 'text-positive' : 'text-negative'}">${p.return_pct}%</td>
            </tr>`;
        }).join('');
        updateSummary(totalInvested, totalCurrent, totalPL);
        renderAllocationChart(positions);
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" style="color:var(--danger)">Failed to load</td></tr>';
    }
}

function renderAllocationChart(positions) {
    const card = document.getElementById('allocation-card');
    const canvas = document.getElementById('allocation-chart');
    if (!card || !canvas || typeof Chart === 'undefined' || positions.length === 0) return;

    card.style.display = 'block';

    // Group by sector
    const sectorMap = {};
    positions.forEach(p => {
        const sector = p.sector || 'Other';
        const value = p.current_price * p.quantity;
        sectorMap[sector] = (sectorMap[sector] || 0) + value;
    });

    const labels = Object.keys(sectorMap);
    const data = Object.values(sectorMap);
    const colors = [
        '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
        '#ef4444', '#ec4899', '#6366f1', '#14b8a6', '#f97316',
        '#84cc16', '#a855f7'
    ];

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverBorderWidth: 3,
            }]
        },
        options: {
            responsive: true,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 12, weight: '500' }, padding: 12 }
                }
            }
        }
    });
}

function updateSummary(invested, current, pl) {
    document.getElementById('total-invested').textContent = formatCurrency(invested);
    document.getElementById('current-value').textContent = formatCurrency(current);
    const plEl = document.getElementById('total-pl');
    plEl.textContent = formatCurrency(pl);
    plEl.className = `stat-value ${pl >= 0 ? 'text-positive' : 'text-negative'}`;
}

function showAddPosition() {
    document.getElementById('position-modal').classList.add('active');
}

async function addPosition() {
    const data = {
        instrument_id: parseInt(document.getElementById('pos-instrument').value),
        quantity: parseFloat(document.getElementById('pos-qty').value),
        buy_price: parseFloat(document.getElementById('pos-price').value),
        buy_date: document.getElementById('pos-date').value,
    };
    try {
        await api.post('/portfolio/positions', data);
        showToast('Position added!', 'success');
        document.getElementById('position-modal').classList.remove('active');
        loadPositions();
    } catch (e) {
        showToast(e.error || 'Failed to add position', 'error');
    }
}
