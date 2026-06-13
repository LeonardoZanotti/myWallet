let portfolioChartInstance = null;
let evolutionChartInstance = null;
let walletGroups = {};
let currentExchangeRate = 5.0;
let globalAssets = [];
let globalTransactions = [];
let globalInvestmentSummary = null;
let currentSort = { column: 'pctInGroup', direction: 'desc' };

function setSort(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'desc';
    }
    if (globalAssets.length > 0) {
        renderWallet(globalAssets, currentExchangeRate);
    }
}

function sortIcon(column) {
    if (currentSort.column !== column) return '<i class="fa-solid fa-sort ml-1 opacity-40"></i>';
    return currentSort.direction === 'asc' 
        ? '<i class="fa-solid fa-sort-up ml-1 text-brand-blue"></i>' 
        : '<i class="fa-solid fa-sort-down ml-1 text-brand-blue"></i>';
}

function showFeedback(message, type = 'error') {
    const feedback = document.getElementById('app-feedback');
    feedback.innerText = message;
    feedback.classList.remove('hidden', 'feedback-error', 'feedback-success');
    feedback.classList.add(type === 'success' ? 'feedback-success' : 'feedback-error');
}

function clearFeedback() {
    const feedback = document.getElementById('app-feedback');
    feedback.innerText = '';
    feedback.classList.add('hidden');
    feedback.classList.remove('feedback-error', 'feedback-success');
}

function parseLocalizedNumber(value) {
    if (value === null || value === undefined) return null;
    const normalized = String(value).trim();
    if (!normalized) return null;
    return parseFloat(normalized.replace(',', '.'));
}

document.addEventListener('DOMContentLoaded', () => {
    fetchWallet();
    
    document.getElementById('add-asset-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearFeedback();
        const data = {
            ticker: document.getElementById('add-ticker').value.toUpperCase(),
            weight: parseInt(document.getElementById('add-weight').value),
            tag: document.getElementById('add-tag').value
        };
        
        showLoader();
        try {
            const response = await fetch('/api/wallet/asset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || 'Could not save asset.');
                return;
            }
            e.target.reset();
            showFeedback('Asset saved.', 'success');
            await fetchWallet();
        } finally {
            hideLoader();
        }
    });

    document.getElementById('edit-asset-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearFeedback();
        const ticker = document.getElementById('edit-ticker').value;
        const data = {
            weight: parseInt(document.getElementById('edit-weight').value),
            tag: document.getElementById('edit-tag').value
        };
        
        showLoader();
        try {
            const response = await fetch(`/api/wallet/asset/${ticker}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || 'Could not update asset.');
                return;
            }
            closeEditModal();
            showFeedback('Asset updated.', 'success');
            await fetchWallet();
        } finally {
            hideLoader();
        }
    });

    document.getElementById('group-edit-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearFeedback();
        const tag = document.getElementById('group-edit-tag').value;
        const targetVal = document.getElementById('group-edit-target').value;
        
        const data = {};
        if (targetVal.trim() !== '') {
            data.target_percent = parseLocalizedNumber(targetVal);
        } else {
            data.target_percent = null;
        }
        
        showLoader();
        try {
            const response = await fetch(`/api/wallet/group/${encodeURIComponent(tag)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || 'Could not update group target.');
                return;
            }
            closeGroupEditModal();
            showFeedback('Group target updated.', 'success');
            await fetchWallet();
        } finally {
            hideLoader();
        }
    });

    document.getElementById('tx-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearFeedback();
        const data = {
            ticker: document.getElementById('tx-ticker').value.toUpperCase(),
            date: document.getElementById('tx-date').value,
            type: document.getElementById('tx-type').value,
            quantity: parseLocalizedNumber(document.getElementById('tx-qty').value),
            price: parseLocalizedNumber(document.getElementById('tx-price').value),
            amount: parseLocalizedNumber(document.getElementById('tx-amount').value),
            currency: document.getElementById('tx-currency').value,
            tag: document.getElementById('tx-tag').value,
            weight: parseInt(document.getElementById('tx-weight').value || '0')
        };
        
        showLoader();
        try {
            const response = await fetch('/api/wallet/transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || 'Could not save transaction.');
                return;
            }
            e.target.reset();
            closeTxModal();
            showFeedback('Transaction saved.', 'success');
            await fetchWallet();
        } finally {
            hideLoader();
        }
    });

    document.getElementById('release-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('add-release-line').addEventListener('click', () => addReleaseLine());
    document.getElementById('release-form').addEventListener('submit', submitRelease);
    addReleaseLine();
});

function openEditModal(ticker, weight, tag) {
    const decodedTicker = decodeURIComponent(ticker);
    const decodedTag = decodeURIComponent(tag);
    document.getElementById('edit-ticker').value = decodedTicker;
    document.getElementById('edit-ticker-display').innerText = decodedTicker;
    document.getElementById('edit-weight').value = weight;
    document.getElementById('edit-tag').value = decodedTag;
    
    const modal = document.getElementById('edit-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

function openGroupEditModal(tag) {
    const decodedTag = decodeURIComponent(tag);
    document.getElementById('group-edit-tag').value = decodedTag;
    document.getElementById('group-edit-tag-display').innerText = decodedTag;
    
    const currentGroup = walletGroups[decodedTag];
    const currentTarget = currentGroup ? currentGroup.target_percent : undefined;
    document.getElementById('group-edit-target').value = currentTarget !== undefined && currentTarget !== null ? currentTarget : '';
    
    const modal = document.getElementById('group-edit-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

function closeGroupEditModal() {
    const modal = document.getElementById('group-edit-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

function openTxModal() {
    document.getElementById('tx-date').value = new Date().toISOString().split('T')[0];
    const modal = document.getElementById('tx-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

function closeTxModal() {
    const modal = document.getElementById('tx-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

function categoryOptions(selected = 'BR ETFs') {
    const categories = ['BR ETFs', 'US ETFs', 'FII', 'Ações', 'BDR', 'Stocks', 'Crypto'];
    return categories.map(category => `<option value="${category}" ${category === selected ? 'selected' : ''}>${category}</option>`).join('');
}

function addReleaseLine(defaults = {}) {
    const container = document.getElementById('release-lines');
    const line = document.createElement('div');
    line.className = 'release-line grid grid-cols-1 xl:grid-cols-[1.1fr_1fr_.8fr_1fr_1fr_1fr_.7fr_auto] gap-3 items-end p-4 border border-dark-border rounded-xl bg-dark-bg/35';
    line.innerHTML = `
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Ticker</label>
            <input type="text" data-field="ticker" value="${defaults.ticker || ''}" required placeholder="IVVB11, VOO" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
        </div>
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Category</label>
            <select data-field="tag" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
                ${categoryOptions(defaults.tag || 'BR ETFs')}
            </select>
        </div>
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Currency</label>
            <select data-field="currency" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
                <option value="BRL" ${(defaults.currency || 'BRL') === 'BRL' ? 'selected' : ''}>BRL</option>
                <option value="USD" ${defaults.currency === 'USD' ? 'selected' : ''}>USD</option>
            </select>
        </div>
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Invested</label>
            <input type="text" inputmode="decimal" data-field="amount" value="${defaults.amount || ''}" required placeholder="1000,00" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
        </div>
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Unit Price</label>
            <input type="text" inputmode="decimal" data-field="price" value="${defaults.price || ''}" required placeholder="100,00" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
        </div>
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Quantity</label>
            <input type="text" inputmode="decimal" data-field="quantity" value="${defaults.quantity || ''}" placeholder="auto" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
        </div>
        <div>
            <label class="text-dark-muted text-xs font-medium mb-1 block">Weight</label>
            <input type="number" min="0" max="100" data-field="weight" value="${defaults.weight || 10}" class="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:border-brand-blue outline-none transition-colors">
        </div>
        <button type="button" onclick="removeReleaseLine(this)" class="h-10 w-10 inline-flex items-center justify-center rounded-lg text-dark-muted hover:text-brand-red hover:bg-brand-red/10 transition-colors" title="Remove line">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;
    container.appendChild(line);
}

function removeReleaseLine(button) {
    const container = document.getElementById('release-lines');
    if (container.children.length === 1) {
        button.closest('.release-line').querySelectorAll('input').forEach(input => {
            if (input.dataset.field !== 'weight') input.value = '';
        });
        return;
    }
    button.closest('.release-line').remove();
}

function readReleaseLine(line, date) {
    const field = name => line.querySelector(`[data-field="${name}"]`);
    const amount = parseLocalizedNumber(field('amount').value);
    const price = parseLocalizedNumber(field('price').value);
    const quantity = parseLocalizedNumber(field('quantity').value);
    return {
        ticker: field('ticker').value.toUpperCase(),
        date,
        type: 'BUY',
        amount,
        price,
        quantity,
        currency: field('currency').value,
        tag: field('tag').value,
        weight: parseInt(field('weight').value || '0')
    };
}

async function submitRelease(event) {
    event.preventDefault();
    clearFeedback();
    const date = document.getElementById('release-date').value;
    const lines = [...document.querySelectorAll('.release-line')].map(line => readReleaseLine(line, date));
    const validLines = lines.filter(line => line.ticker && line.amount > 0 && line.price >= 0);

    if (!date || validLines.length === 0) {
        showFeedback('Add at least one investment line with date, ticker, amount, and price.');
        return;
    }

    showLoader();
    try {
        for (const line of validLines) {
            const response = await fetch('/api/wallet/transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(line)
            });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || `Could not save ${line.ticker}.`);
                return;
            }
        }
        document.getElementById('release-form').reset();
        document.getElementById('release-date').value = new Date().toISOString().split('T')[0];
        document.getElementById('release-lines').innerHTML = '';
        addReleaseLine();
        showFeedback('Monthly contribution saved.', 'success');
        await fetchWallet();
    } finally {
        hideLoader();
    }
}

function switchTab(tabId) {
    const tabs = ['portfolio', 'proventos', 'transactions'];
    tabs.forEach(t => {
        const view = document.getElementById(`${t}-view`);
        const btn = document.getElementById(`tab-${t}`);
        if (!view || !btn) return;
        
        if (t === tabId) {
            view.classList.remove('hidden');
            btn.classList.add('text-brand-blue', 'border-brand-blue');
            btn.classList.remove('text-dark-muted', 'hover:text-white', 'border-transparent');
        } else {
            view.classList.add('hidden');
            btn.classList.remove('text-brand-blue', 'border-brand-blue');
            btn.classList.add('text-dark-muted', 'hover:text-white', 'border-transparent');
        }
    });
}

function focusInvestmentForm() {
    const card = document.getElementById('investment-form-card');
    if (!card) return;
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const firstTicker = card.querySelector('[data-field="ticker"]');
    if (firstTicker) {
        setTimeout(() => firstTicker.focus(), 350);
    }
}

function showLoader() {
    const l = document.getElementById('global-loader');
    l.classList.remove('hidden');
    l.classList.add('flex');
}
function hideLoader() {
    const l = document.getElementById('global-loader');
    l.classList.add('hidden');
    l.classList.remove('flex');
}

async function fetchWallet() {
    showLoader();
    try {
        const response = await fetch('/api/wallet');
        const data = await response.json();
        if (!response.ok) {
            showFeedback(data.error || 'Error fetching wallet');
            return;
        }
        clearFeedback();
        walletGroups = data.groups || {};
        currentExchangeRate = data.exchange_rate || 5.0;
        globalAssets = data.assets || [];
        globalTransactions = data.transactions || [];
        globalInvestmentSummary = data.investment_summary || null;
        renderWallet(globalAssets, currentExchangeRate);
        renderTransactions(globalTransactions);
        renderInvestmentSummary(globalInvestmentSummary);
        if (!proventosLoaded) {
            fetchProventos();
        } else {
            renderProventos(globalProventosSummary);
        }
    } catch (error) {
        console.error("Error fetching wallet", error);
        showFeedback('Error fetching wallet');
    } finally {
        hideLoader();
    }
}

let globalProventosSummary = null;
let proventosLoaded = false;

async function fetchProventos() {
    try {
        document.getElementById('prov-total-all').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-sm"></i>';
        const response = await fetch('/api/wallet/proventos');
        const data = await response.json();
        if (response.ok) {
            globalProventosSummary = data;
            proventosLoaded = true;
            renderProventos(globalProventosSummary);
        }
    } catch (e) {
        console.error('Failed to load proventos', e);
    }
}

function renderTransactions(transactions) {
    const tbody = document.getElementById('transactions-body');
    tbody.innerHTML = '';

    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="py-4 px-6 text-center text-dark-muted">No transactions found.</td></tr>';
        renderEvolutionChart([]);
        return;
    }

    const sortedTxs = [...transactions].sort((a, b) => new Date(b.date) - new Date(a.date));

    sortedTxs.forEach(tx => {
        const typeClass = tx.type === 'BUY' ? 'text-brand-green' : 'text-brand-red';
        const currency = tx.currency || assetCurrency(tx.ticker);
        const total = tx.amount !== undefined ? tx.amount : tx.quantity * tx.price;
        const asset = globalAssets.find(a => a.ticker === tx.ticker);
        tbody.innerHTML += `
            <tr class="hover:bg-dark-border/10 transition-colors">
                <td class="py-3 px-6 whitespace-nowrap">${tx.date}</td>
                <td class="py-3 px-6 font-medium ${typeClass}">${tx.type}</td>
                <td class="py-3 px-6 font-medium">${tx.ticker}</td>
                <td class="py-3 px-6 text-dark-muted">${asset ? asset.tag : (tx.tag || '-')}</td>
                <td class="py-3 px-6">${currency}</td>
                <td class="py-3 px-6 text-right">${formatQuantity(tx.quantity)}</td>
                <td class="py-3 px-6 text-right">${formatCurrency(tx.price, currency)}</td>
                <td class="py-3 px-6 text-right">${formatCurrency(total, currency)}</td>
                <td class="py-3 px-6 text-right">
                    <button onclick="deleteTransaction('${tx.id}')" class="text-dark-muted hover:text-brand-red transition-colors"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>
        `;
    });

    renderEvolutionChart(transactions);
}

function renderEvolutionChart(transactions) {
    const monthly = globalInvestmentSummary && globalInvestmentSummary.monthly
        ? globalInvestmentSummary.monthly
        : buildMonthlySummaryFromTransactions(transactions);
    const labels = monthly.map(item => item.month);
    const brlBuys = monthly.map(item => item.buy_brl || 0);
    const usdBuysInBrl = monthly.map(item => (item.buy_usd || 0) * currentExchangeRate);
    let accumulated = 0;
    const accumulatedData = monthly.map(item => {
        accumulated += item.net_brl_equivalent || 0;
        return accumulated;
    });
    window.__lastEvolutionChartData = { labels, brlBuys, usdBuysInBrl, accumulatedData };

    if (typeof Chart === 'undefined') return;
    const ctx = document.getElementById('evolutionChart').getContext('2d');

    if (evolutionChartInstance) {
        evolutionChartInstance.destroy();
    }

    evolutionChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(l => {
                const parts = l.split('-');
                return `${parts[1]}/${parts[0]}`;
            }),
            datasets: [
                {
                    label: 'BRL contributions',
                    data: brlBuys,
                    backgroundColor: '#10b981',
                    borderRadius: 4,
                    stack: 'contributions'
                },
                {
                    label: 'USD contributions in BRL',
                    data: usdBuysInBrl,
                    backgroundColor: '#3b82f6',
                    borderRadius: 4,
                    stack: 'contributions'
                },
                {
                    label: 'Accumulated net invested',
                    type: 'line',
                    data: accumulatedData,
                    borderColor: '#f59e0b',
                    backgroundColor: '#f59e0b',
                    tension: 0.25,
                    pointRadius: 3,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#f8fafc', font: { family: 'Inter' } }
                }
            },
            scales: {
                y: {
                    stacked: false,
                    ticks: {
                        color: '#94a3b8',
                        callback: value => formatCurrency(value, 'BRL')
                    },
                    grid: { color: '#334155' }
                },
                x: {
                    stacked: true,
                    ticks: { color: '#94a3b8' },
                    grid: { display: false }
                }
            }
        }
    });
}

function buildMonthlySummaryFromTransactions(transactions) {
    const monthly = {};
    transactions.forEach(tx => {
        const d = new Date(tx.date);
        const month = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        const currency = tx.currency || assetCurrency(tx.ticker);
        const amount = tx.amount !== undefined ? tx.amount : tx.quantity * tx.price;
        const sign = tx.type === 'BUY' ? 1 : -1;
        const bucket = monthly[month] || {
            month,
            buy_brl: 0,
            buy_usd: 0,
            sell_brl: 0,
            sell_usd: 0,
            net_brl_equivalent: 0
        };
        const key = `${tx.type === 'BUY' ? 'buy' : 'sell'}_${currency.toLowerCase()}`;
        bucket[key] += amount;
        bucket.net_brl_equivalent += sign * (currency === 'USD' ? amount * currentExchangeRate : amount);
        monthly[month] = bucket;
    });
    return Object.keys(monthly).sort().map(key => monthly[key]);
}

function renderInvestmentSummary(summary) {
    if (!summary) return;
    const currentValue = globalAssets.reduce((sum, asset) => {
        const rate = asset.currency === 'USD' ? currentExchangeRate : 1;
        return sum + (asset.total_value * rate);
    }, 0);
    const netInvested = summary.net_invested_brl_equivalent || 0;
    const delta = currentValue - netInvested;
    const deltaPct = netInvested > 0 ? (delta / netInvested) * 100 : 0;
    const lastMonth = summary.monthly && summary.monthly.length > 0 ? summary.monthly[summary.monthly.length - 1] : null;

    setText('history-total-invested', formatCurrency(summary.gross_invested_brl_equivalent || 0, 'BRL'));
    setText('history-total-usd', formatCurrency(summary.total_buy_usd || 0, 'USD'));
    setText('history-current-delta', `${delta >= 0 ? '+' : ''}${formatCurrency(delta, 'BRL')} (${deltaPct.toFixed(1)}%)`);
    setText('history-last-month', lastMonth ? formatCurrency(lastMonth.gross_brl_equivalent || 0, 'BRL') : formatCurrency(0, 'BRL'));

    const deltaEl = document.getElementById('history-current-delta');
    if (deltaEl) {
        deltaEl.classList.toggle('text-brand-green', delta >= 0);
        deltaEl.classList.toggle('text-brand-red', delta < 0);
    }

    const tbody = document.getElementById('monthly-history-body');
    if (!tbody) return;
    if (!summary.monthly || summary.monthly.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="py-4 px-6 text-center text-dark-muted">No monthly contributions yet.</td></tr>';
        return;
    }
    tbody.innerHTML = [...summary.monthly].reverse().map(month => `
        <tr class="hover:bg-dark-border/10 transition-colors">
            <td class="py-3 px-6 whitespace-nowrap">${formatMonth(month.month)}</td>
            <td class="py-3 px-6 text-right">${formatCurrency(month.buy_brl || 0, 'BRL')}</td>
            <td class="py-3 px-6 text-right">${formatCurrency(month.buy_usd || 0, 'USD')}</td>
            <td class="py-3 px-6 text-right">${formatCurrency(month.gross_brl_equivalent || 0, 'BRL')}</td>
            <td class="py-3 px-6 text-right">${formatCurrency(month.net_brl_equivalent || 0, 'BRL')}</td>
        </tr>
    `).join('');
}

let proventosChartInstance = null;

function renderProventos(summary) {
    if (!summary) return;
    
    // Summary Cards
    let totalAllTime = 0;
    if (summary.by_asset) {
        summary.by_asset.forEach(a => {
            const divUsd = (a.dividend_amount && a.currency === 'USD') ? a.dividend_amount : 0;
            const divBrl = (a.dividend_amount && a.currency === 'BRL') ? a.dividend_amount : 0;
            totalAllTime += divBrl + (divUsd * currentExchangeRate);
        });
    }
    
    setText('prov-total-all', formatCurrency(totalAllTime, 'BRL'));
    
    const monthly = summary.monthly || [];
    const last12 = monthly.slice(-12);
    let total12m = 0;
    last12.forEach(m => {
        total12m += (m.dividend_brl || 0) + ((m.dividend_usd || 0) * currentExchangeRate);
    });
    
    const avg12m = last12.length > 0 ? total12m / last12.length : 0;
    setText('prov-monthly-avg', formatCurrency(avg12m, 'BRL'));
    
    const lastMonth = last12.length > 0 ? last12[last12.length - 1] : null;
    const lastMonthTotal = lastMonth ? (lastMonth.dividend_brl || 0) + ((lastMonth.dividend_usd || 0) * currentExchangeRate) : 0;
    setText('prov-last-month', formatCurrency(lastMonthTotal, 'BRL'));
    
    // Chart
    const labels = last12.map(item => formatMonth(item.month));
    const data = last12.map(item => (item.dividend_brl || 0) + ((item.dividend_usd || 0) * currentExchangeRate));
    
    if (typeof Chart !== 'undefined') {
        const ctx = document.getElementById('proventosChart');
        if (ctx) {
            if (proventosChartInstance) {
                proventosChartInstance.destroy();
            }
            const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)'); // blue-500
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.2)');

            proventosChartInstance = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Proventos Recebidos (BRL)',
                        data: data,
                        backgroundColor: gradient,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1,
                        borderRadius: 6,
                        hoverBackgroundColor: 'rgba(59, 130, 246, 1)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { color: '#f8fafc', font: { family: 'Inter', size: 13, weight: '500' } } },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleFont: { size: 14, family: 'Inter' },
                            bodyFont: { size: 14, family: 'Inter' },
                            padding: 12,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    return 'R$ ' + context.parsed.y.toFixed(2).replace('.', ',');
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { color: '#94a3b8', font: { family: 'Inter' }, callback: value => formatCurrency(value, 'BRL') },
                            grid: { color: 'rgba(51, 65, 85, 0.5)', borderDash: [5, 5] },
                            border: { display: false }
                        },
                        x: {
                            ticks: { color: '#94a3b8', font: { family: 'Inter' } },
                            grid: { display: false },
                            border: { display: false }
                        }
                    }
                }
            });
        }
    }
    
    // Table
    const tbody = document.getElementById('proventos-assets-body');
    if (!tbody) return;
    
    if (!summary.by_asset || summary.by_asset.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="py-4 px-6 text-center text-dark-muted">No dividend data available.</td></tr>';
        return;
    }
    
    const dividendAssets = summary.by_asset.filter(a => a.dividend_amount && a.dividend_amount > 0);
    dividendAssets.sort((a, b) => {
        const valA = a.currency === 'USD' ? a.dividend_amount * currentExchangeRate : a.dividend_amount;
        const valB = b.currency === 'USD' ? b.dividend_amount * currentExchangeRate : b.dividend_amount;
        return valB - valA;
    });
    
    if (dividendAssets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="py-4 px-6 text-center text-dark-muted">No dividend data available.</td></tr>';
    } else {
        tbody.innerHTML = dividendAssets.map(a => `
            <tr class="hover:bg-dark-border/10 transition-colors">
                <td class="py-3 px-6 font-medium">${a.ticker}</td>
                <td class="py-3 px-6 text-dark-muted">${a.tag || '-'}</td>
                <td class="py-3 px-6 text-right font-medium text-brand-green">${formatCurrency(a.dividend_amount, a.currency)}</td>
            </tr>
        `).join('');
    }

    // History Table
    const histBody = document.getElementById('proventos-history-body');
    if (!histBody) return;
    
    if (!summary.events || summary.events.length === 0) {
        histBody.innerHTML = '<tr><td colspan="7" class="py-4 px-6 text-center text-dark-muted">No historical dividend events found.</td></tr>';
        return;
    }
    
    histBody.innerHTML = summary.events.map(ev => {
        // Date formatting: Ex-Date (Data Com)
        const dateParts = ev.date.split('-');
        const dateStr = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
        
        const isPaid = ev.status === 'Pago';
        const statusBadge = isPaid 
            ? '<span class="bg-brand-green/20 text-brand-green px-2 py-1 rounded text-xs font-semibold flex items-center w-max"><i class="fa-solid fa-check-circle mr-1"></i> Pago</span>'
            : '<span class="bg-brand-blue/20 text-brand-blue px-2 py-1 rounded text-xs font-semibold flex items-center w-max"><i class="fa-solid fa-calendar-day mr-1"></i> A Receber</span>';
            
        return `
            <tr class="hover:bg-dark-border/10 transition-colors">
                <td class="py-3 px-6 font-medium flex items-center">
                    <span class="w-6 h-6 rounded-full bg-dark-bg border border-dark-border flex items-center justify-center mr-2 text-[10px]"><i class="fa-solid fa-building"></i></span>
                    ${ev.ticker}
                </td>
                <td class="py-3 px-6 text-dark-muted"><span class="bg-dark-bg border border-dark-border px-2 py-1 rounded text-xs">${ev.tag || '-'}</span></td>
                <td class="py-3 px-6">${statusBadge}</td>
                <td class="py-3 px-6">${dateStr}</td>
                <td class="py-3 px-6 text-right">${formatQuantity(ev.quantity)}</td>
                <td class="py-3 px-6 text-right text-dark-muted">${formatCurrency(ev.amount_per_share, ev.currency)}</td>
                <td class="py-3 px-6 text-right font-medium">${formatCurrency(ev.amount, ev.currency)}</td>
            </tr>
        `;
    }).join('');
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.innerText = value;
}

function formatMonth(month) {
    const [year, monthNumber] = month.split('-');
    return `${monthNumber}/${year}`;
}

async function deleteTransaction(id) {
    if (confirm(`Remove transaction?`)) {
        clearFeedback();
        showLoader();
        try {
            const response = await fetch(`/api/wallet/transaction/${id}`, { method: 'DELETE' });
            if (!response.ok) {
                const payload = await response.json();
                showFeedback(payload.error || 'Could not remove transaction.');
                return;
            }
            showFeedback('Transaction removed.', 'success');
            await fetchWallet();
        } finally {
            hideLoader();
        }
    }
}

function renderWallet(assets, exchangeRate = 5.0) {
    let totalPatrimonyUnified = 0;
    let totalCostUnified = 0;
    let totalBrl = 0;
    let totalUsd = 0;
    
    // Group by tag
    const groups = {};
    assets.forEach(a => {
        if (!groups[a.tag]) groups[a.tag] = [];
        groups[a.tag].push(a);
        
        const rate = a.currency === 'USD' ? exchangeRate : 1.0;
        
        totalPatrimonyUnified += (a.total_value * rate);
        totalCostUnified += (a.quantity * a.average_price * rate);
        
        if (a.currency === 'USD') {
            totalUsd += a.total_value;
        } else {
            totalBrl += a.total_value;
        }
    });
    
    // Update Summaries
    document.getElementById('total-patrimony').innerText = formatCurrency(totalPatrimonyUnified, 'BRL');
    document.getElementById('total-brl').innerText = formatCurrency(totalBrl, 'BRL');
    document.getElementById('total-usd').innerText = formatCurrency(totalUsd, 'USD');
    
    const variation = totalCostUnified > 0 ? ((totalPatrimonyUnified - totalCostUnified) / totalCostUnified) * 100 : 0;
    const variationEl = document.getElementById('total-variation');
    variationEl.innerHTML = `<span class="${variation >= 0 ? 'text-brand-green' : 'text-brand-red'} font-medium flex items-center"><i class="fa-solid fa-arrow-trend-${variation >= 0 ? 'up' : 'down'} mr-1"></i> ${variation.toFixed(2)}%</span>`;

    let totalGroupTargets = 0;
    for (const [tag, groupAssets] of Object.entries(groups)) {
        let gTarget = walletGroups[tag] ? walletGroups[tag].target_percent : undefined;
        if (gTarget === undefined || gTarget === null) gTarget = 50.0;
        totalGroupTargets += parseFloat(gTarget);
    }

    if (totalGroupTargets === 0) {
        totalGroupTargets = Object.keys(groups).length * 50.0;
    }

    // Render Tables
    const container = document.getElementById('asset-groups-container');
    container.innerHTML = '';

    if (assets.length === 0) {
        container.innerHTML = `
        <div class="bg-dark-card rounded-2xl border border-dark-border shadow-lg p-10 text-center text-dark-muted">
            <div class="text-4xl mb-3"><i class="fa-solid fa-wallet"></i></div>
            <p class="font-medium text-white mb-1">No assets yet</p>
            <p>Add your first asset to start tracking the wallet.</p>
        </div>`;
        renderChart({}, exchangeRate);
        return;
    }
    
    for (const [tag, groupAssets] of Object.entries(groups)) {
        const cur = groupAssets[0] ? groupAssets[0].currency : 'BRL';
        let groupTotal = groupAssets.reduce((sum, a) => sum + a.total_value, 0);
        let groupCost = groupAssets.reduce((sum, a) => sum + (a.quantity * a.average_price), 0);
        let groupVar = groupCost > 0 ? ((groupTotal - groupCost) / groupCost) * 100 : 0;
        
        let pctInWallet = totalPatrimonyUnified > 0 ? (groupTotal * (cur === 'USD' ? exchangeRate : 1.0) / totalPatrimonyUnified) * 100 : 0;
        let groupTargetStr = walletGroups[tag] && walletGroups[tag].target_percent !== undefined && walletGroups[tag].target_percent !== null
            ? `Target: ${walletGroups[tag].target_percent}%`
            : `No target set`;
        
        let html = `
        <div class="bg-dark-card rounded-2xl border border-dark-border shadow-lg overflow-hidden">
            <div class="px-6 py-4 border-b border-dark-border flex justify-between items-center bg-dark-bg/30">
                <div>
                    <h3 class="font-bold flex items-center">
                        <i class="fa-solid fa-layer-group text-dark-muted mr-2"></i> ${tag}
                        <button onclick="openGroupEditModal('${encodeURIComponent(tag)}')" class="ml-3 text-xs text-brand-blue hover:text-blue-400"><i class="fa-solid fa-pen"></i></button>
                    </h3>
                    <p class="text-xs text-dark-muted mt-1">${pctInWallet.toFixed(1)}% of Wallet • ${groupTargetStr}</p>
                </div>
                <div class="text-sm text-right">
                    <div class="text-dark-muted">Value: <span class="text-white font-medium">${formatCurrency(groupTotal, cur)}</span></div>
                    <div class="${groupVar >= 0 ? 'text-brand-green' : 'text-brand-red'} font-medium">${groupVar >= 0 ? '+' : ''}${groupVar.toFixed(2)}%</div>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="text-dark-muted text-xs uppercase tracking-wider border-b border-dark-border bg-dark-bg/10">
                            <th class="py-3 px-3 cursor-pointer hover:text-white transition-colors whitespace-nowrap" onclick="setSort('ticker')">Asset ${sortIcon('ticker')}</th>
                            <th class="py-3 px-3">Qty</th>
                            <th class="py-3 px-3">Avg Price</th>
                            <th class="py-3 px-3">Current</th>
                            <th class="py-3 px-3">Variation</th>
                            <th class="py-3 px-3">Value</th>
                            <th class="py-3 px-3 text-center cursor-pointer hover:text-white transition-colors whitespace-nowrap" onclick="setSort('weight')">Weight ${sortIcon('weight')}</th>
                            <th class="py-3 px-3 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap" onclick="setSort('pctInGroup')">% Group ${sortIcon('pctInGroup')}</th>
                            <th class="py-3 px-3 text-right whitespace-nowrap">% Wallet</th>
                            <th class="py-3 px-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="text-sm divide-y divide-dark-border">
        `;
        
        let totalGroupWeight = groupAssets.reduce((sum, a) => sum + a.weight, 0);
        
        groupAssets.forEach(a => {
            a.pctInGroup = groupTotal > 0 ? (a.total_value / groupTotal) * 100 : 0;
        });

        groupAssets.sort((a, b) => {
            let valA = a[currentSort.column];
            let valB = b[currentSort.column];
            
            if (currentSort.column === 'ticker') {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }
            
            if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
            if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });
        
        groupAssets.forEach(a => {
            const isPositive = a.variation >= 0;
            const priceText = a.current_price !== null && a.current_price !== undefined ? formatCurrency(a.current_price, a.currency) : '<span class="text-dark-muted">N/A</span>';
            
            const pctInGroup = groupTotal > 0 ? (a.total_value / groupTotal) * 100 : 0;
            const targetPctInGroup = totalGroupWeight > 0 ? (a.weight / totalGroupWeight) * 100 : 0;
            const aUnifiedValue = a.total_value * (a.currency === 'USD' ? exchangeRate : 1.0);
            const aPctInWallet = totalPatrimonyUnified > 0 ? (aUnifiedValue / totalPatrimonyUnified) * 100 : 0;
            
            let gTarget = walletGroups[tag] ? walletGroups[tag].target_percent : undefined;
            if (gTarget === undefined || gTarget === null) gTarget = 50.0;
            const normalizedGroupTarget = totalGroupTargets > 0 ? (parseFloat(gTarget) / totalGroupTargets) * 100 : 0;
            
            const targetPctInWallet = normalizedGroupTarget * (targetPctInGroup / 100);
            
            html += `
            <tr class="asset-row">
                <td class="py-3 px-3 font-medium">${a.ticker}</td>
                <td class="py-3 px-3">${formatQuantity(a.quantity)}</td>
                <td class="py-3 px-3">${formatCurrency(a.average_price, a.currency)}</td>
                <td class="py-3 px-3">${priceText}</td>
                <td class="py-3 px-3">
                    <span class="${isPositive ? 'variation-positive' : 'variation-negative'} inline-flex items-center text-xs font-semibold">
                        ${isPositive ? '+' : ''}${a.variation.toFixed(2)}%
                    </span>
                </td>
                <td class="py-3 px-3 font-medium">${formatCurrency(a.total_value, a.currency)}</td>
                <td class="py-3 px-3 text-center"><span class="bg-dark-border px-2 py-1 rounded text-xs">${a.weight}</span></td>
                <td class="py-3 px-3 text-right font-medium text-white">${a.pctInGroup.toFixed(1)}% <span class="text-dark-muted font-normal text-[11px] ml-1">/ ${targetPctInGroup.toFixed(1)}%</span></td>
                <td class="py-3 px-3 text-right font-medium text-purple-400">${aPctInWallet.toFixed(1)}% <span class="text-dark-muted font-normal text-[11px] ml-1">/ ${targetPctInWallet.toFixed(1)}%</span></td>
                <td class="py-3 px-3 text-right">
                    <button onclick="openEditModal('${encodeURIComponent(a.ticker)}', ${a.weight}, '${encodeURIComponent(a.tag)}')" class="text-brand-blue hover:text-blue-400 transition-colors mr-3"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button onclick="deleteAsset('${encodeURIComponent(a.ticker)}')" class="text-dark-muted hover:text-brand-red transition-colors"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>
            `;
        });
        
        html += `</tbody></table></div></div>`;
        container.innerHTML += html;
    }
    
    renderChart(groups, exchangeRate);
}

async function deleteAsset(ticker) {
    const decodedTicker = decodeURIComponent(ticker);
    if (confirm(`Remove ${decodedTicker}? All associated transactions will also be permanently deleted.`)) {
        clearFeedback();
        showLoader();
        try {
            const response = await fetch(`/api/wallet/asset/${decodedTicker}`, { method: 'DELETE' });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || 'Could not remove asset.');
                return;
            }
            showFeedback('Asset and related transactions removed.', 'success');
            await fetchWallet();
        } finally {
            hideLoader();
        }
    }
}

async function calculateSmartBuy() {
    clearFeedback();
    const brl = parseLocalizedNumber(document.getElementById('invest-brl').value) || 0;
    const usd = parseLocalizedNumber(document.getElementById('invest-usd').value) || 0;
    
    if (brl === 0 && usd === 0) {
        showFeedback("Please enter an amount to invest.");
        return;
    }
    
    const btn = document.querySelector('button[onclick="calculateSmartBuy()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Calculating...`;
    
    try {
        const response = await fetch('/api/smart-buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invest_brl: brl, invest_usd: usd })
        });
        const data = await response.json();
        if (!response.ok) {
            showFeedback(data.error || 'Error calculating');
            return;
        }
        
        // Populate modal
        const tbody = document.getElementById('recommendation-body');
        tbody.innerHTML = '';
        
        let total_brl_current = 0;
        data.recommendations.forEach(r => {
            let rate = r.currency === 'USD' ? currentExchangeRate : 1.0;
            total_brl_current += (r.current_value * rate);
        });
        
        let new_total_brl = total_brl_current + brl + (usd * currentExchangeRate);

        let sortedRecs = data.recommendations.sort((a, b) => {
            if (a.value_to_buy > 0 && b.value_to_buy === 0) return -1;
            if (a.value_to_buy === 0 && b.value_to_buy > 0) return 1;
            return b.ideal_percent - a.ideal_percent;
        });

        sortedRecs.forEach(r => {
            let rate = r.currency === 'USD' ? currentExchangeRate : 1.0;
            let current_unified = r.current_value * rate;
            let current_pct = total_brl_current > 0 ? (current_unified / total_brl_current) * 100 : 0;
            
            let post_inv_native = r.current_value + r.value_to_buy;
            let post_inv_unified = post_inv_native * rate;
            let post_inv_pct = new_total_brl > 0 ? (post_inv_unified / new_total_brl) * 100 : 0;
            
            let isSkip = r.value_to_buy === 0;
            let rowClass = isSkip ? 'opacity-40 hover:opacity-80 transition-opacity grayscale' : 'hover:bg-dark-border/20 transition-colors';
            
            let shares = r.currency === 'BRL' ? Math.floor(r.shares_to_buy) : r.shares_to_buy.toFixed(2);
            let sharesText = isSkip ? '-' : `${shares} shs`;
            let buyText = isSkip ? '-' : `+${formatCurrency(r.value_to_buy, r.currency)}`;
            
            tbody.innerHTML += `
            <tr class="${rowClass} border-b border-dark-border/50 last:border-0">
                <td class="py-3 px-2 font-medium">${r.ticker}</td>
                <td class="py-3 px-2 text-dark-muted text-[11px] uppercase tracking-wider">${r.tag}</td>
                <td class="py-3 px-2 text-right">
                    <div class="font-medium">${current_pct.toFixed(1)}%</div>
                    <div class="text-[10px] text-dark-muted">${formatCurrency(r.current_value, r.currency)}</div>
                </td>
                <td class="py-3 px-2 text-center font-medium">${(r.ideal_percent * 100).toFixed(1)}%</td>
                <td class="py-3 px-2 text-right">
                    <div class="font-bold ${isSkip ? 'text-dark-muted' : 'text-brand-green'}">${buyText}</div>
                    <div class="text-[10px] ${isSkip ? 'text-dark-muted' : 'text-brand-blue'} font-medium">${sharesText}</div>
                </td>
                <td class="py-3 px-2 text-right">
                    <div class="font-medium ${isSkip ? 'text-dark-muted' : 'text-purple-400'}">${post_inv_pct.toFixed(1)}%</div>
                    <div class="text-[10px] ${isSkip ? 'text-dark-muted' : 'text-purple-400/70'}">${formatCurrency(post_inv_native, r.currency)}</div>
                </td>
            </tr>
            `;
        });

        const leftoverContainer = document.getElementById('leftover-container');
        if (data.leftover_brl > 0 || data.leftover_usd > 0) {
            let leftoverText = [];
            if (data.leftover_brl > 0) leftoverText.push(`${formatCurrency(data.leftover_brl, 'BRL')}`);
            if (data.leftover_usd > 0) leftoverText.push(`${formatCurrency(data.leftover_usd, 'USD')}`);
            document.getElementById('leftover-amount').innerHTML = leftoverText.join(' + ');
            leftoverContainer.classList.remove('hidden');
        } else if (leftoverContainer) {
            leftoverContainer.classList.add('hidden');
        }
        
        const modal = document.getElementById('recommendation-modal');
        modal.classList.remove('hidden');
        setTimeout(() => modal.classList.add('show'), 10);
        
    } catch (e) {
        showFeedback("Error calculating");
    } finally {
        btn.innerHTML = originalText;
    }
}

function closeModal() {
    const modal = document.getElementById('recommendation-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

function formatCurrency(val, currency = 'BRL') {
    if (currency === 'USD') {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
    }
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
}

function formatQuantity(value) {
    const number = Number(value || 0);
    if (Number.isInteger(number)) {
        return String(number);
    }
    return number.toFixed(8).replace(/0+$/, '').replace(/\.$/, '');
}

function assetCurrency(ticker) {
    const asset = globalAssets.find(item => item.ticker === ticker);
    if (asset) return asset.currency;
    return ticker && ticker.endsWith('.SA') ? 'BRL' : 'USD';
}

function renderChart(groups, exchangeRate = 5.0) {
    const labels = [];
    const data = [];
    const bgColors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#14b8a6'];
    
    for (const [tag, groupAssets] of Object.entries(groups)) {
        labels.push(tag);
        data.push(groupAssets.reduce((sum, a) => {
            const rate = a.currency === 'USD' ? exchangeRate : 1.0;
            return sum + (a.total_value * rate);
        }, 0));
    }
    window.__lastPortfolioChartData = { labels, data };
    
    if (typeof Chart === 'undefined') {
        return;
    }
    const ctx = document.getElementById('portfolioChart').getContext('2d');
    
    if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
    }
    
    portfolioChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors.slice(0, labels.length),
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f8fafc', padding: 20, font: { family: 'Inter' } }
                }
            },
            cutout: '75%'
        }
    });
}
