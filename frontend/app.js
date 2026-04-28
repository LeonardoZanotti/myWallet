let portfolioChartInstance = null;
let walletGroups = {};
let currentExchangeRate = 5.0;

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
            quantity: parseLocalizedNumber(document.getElementById('add-qty').value),
            average_price: parseLocalizedNumber(document.getElementById('add-price').value),
            nota: parseInt(document.getElementById('add-nota').value),
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
            quantity: parseLocalizedNumber(document.getElementById('edit-qty').value),
            average_price: parseLocalizedNumber(document.getElementById('edit-price').value),
            nota: parseInt(document.getElementById('edit-nota').value),
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
            data.target_percent = null; // Removing target
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
});

function openEditModal(ticker, qty, price, nota, tag) {
    const decodedTicker = decodeURIComponent(ticker);
    const decodedTag = decodeURIComponent(tag);
    document.getElementById('edit-ticker').value = decodedTicker;
    document.getElementById('edit-ticker-display').innerText = decodedTicker;
    document.getElementById('edit-qty').value = qty;
    document.getElementById('edit-price').value = price;
    document.getElementById('edit-nota').value = nota;
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
    
    // Set current target if it exists
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
        renderWallet(data.assets, data.exchange_rate);
    } catch (error) {
        console.error("Error fetching wallet", error);
        showFeedback('Error fetching wallet');
    } finally {
        hideLoader();
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
                            <th class="py-3 px-6">Asset</th>
                            <th class="py-3 px-6">Qty</th>
                            <th class="py-3 px-6">Avg Price</th>
                            <th class="py-3 px-6">Current</th>
                            <th class="py-3 px-6">Variation</th>
                            <th class="py-3 px-6">Value</th>
                            <th class="py-3 px-6 text-center">Weight</th>
                            <th class="py-3 px-6 text-right">% Group</th>
                            <th class="py-3 px-6 text-right">% Wallet</th>
                            <th class="py-3 px-6 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="text-sm divide-y divide-dark-border">
        `;
        
        let totalGroupNota = groupAssets.reduce((sum, a) => sum + a.nota, 0);
        
        groupAssets.forEach(a => {
            const isPositive = a.variation >= 0;
            const priceText = a.current_price !== null && a.current_price !== undefined ? formatCurrency(a.current_price, a.currency) : '<span class="text-dark-muted">N/A</span>';
            
            const pctInGroup = groupTotal > 0 ? (a.total_value / groupTotal) * 100 : 0;
            const targetPctInGroup = totalGroupNota > 0 ? (a.nota / totalGroupNota) * 100 : 0;
            const aUnifiedValue = a.total_value * (a.currency === 'USD' ? exchangeRate : 1.0);
            const aPctInWallet = totalPatrimonyUnified > 0 ? (aUnifiedValue / totalPatrimonyUnified) * 100 : 0;
            
            let gTarget = walletGroups[tag] ? walletGroups[tag].target_percent : undefined;
            if (gTarget === undefined || gTarget === null) gTarget = 50.0;
            const normalizedGroupTarget = totalGroupTargets > 0 ? (parseFloat(gTarget) / totalGroupTargets) * 100 : 0;
            
            const targetPctInWallet = normalizedGroupTarget * (targetPctInGroup / 100);
            
            html += `
            <tr class="asset-row">
                <td class="py-3 px-6 font-medium">${a.ticker}</td>
                <td class="py-3 px-6">${a.quantity}</td>
                <td class="py-3 px-6">${formatCurrency(a.average_price, a.currency)}</td>
                <td class="py-3 px-6">${priceText}</td>
                <td class="py-3 px-6">
                    <span class="${isPositive ? 'variation-positive' : 'variation-negative'} inline-flex items-center text-xs font-semibold">
                        ${isPositive ? '+' : ''}${a.variation.toFixed(2)}%
                    </span>
                </td>
                <td class="py-3 px-6 font-medium">${formatCurrency(a.total_value, a.currency)}</td>
                <td class="py-3 px-6 text-center"><span class="bg-dark-border px-2 py-1 rounded text-xs">${a.nota}</span></td>
                <td class="py-3 px-6 text-right font-medium text-white">${pctInGroup.toFixed(1)}% <span class="text-dark-muted font-normal text-[11px] ml-1">/ ${targetPctInGroup.toFixed(1)}%</span></td>
                <td class="py-3 px-6 text-right font-medium text-purple-400">${aPctInWallet.toFixed(1)}% <span class="text-dark-muted font-normal text-[11px] ml-1">/ ${targetPctInWallet.toFixed(1)}%</span></td>
                <td class="py-3 px-6 text-right">
                    <button onclick="openEditModal('${encodeURIComponent(a.ticker)}', ${a.quantity}, ${a.average_price}, ${a.nota}, '${encodeURIComponent(a.tag)}')" class="text-brand-blue hover:text-blue-400 transition-colors mr-3"><i class="fa-solid fa-pen-to-square"></i></button>
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
    if (confirm(`Remove ${decodedTicker}?`)) {
        clearFeedback();
        showLoader();
        try {
            const response = await fetch(`/api/wallet/asset/${decodedTicker}`, { method: 'DELETE' });
            const payload = await response.json();
            if (!response.ok) {
                showFeedback(payload.error || 'Could not remove asset.');
                return;
            }
            showFeedback('Asset removed.', 'success');
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

        // Handle leftover
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
        
        // Show modal
        const modal = document.getElementById('recommendation-modal');
        modal.classList.remove('hidden');
        // Small delay to allow display:flex to apply before adding the 'show' class for transition
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

function renderChart(groups, exchangeRate = 5.0) {
    if (typeof Chart === 'undefined') {
        return;
    }
    const ctx = document.getElementById('portfolioChart').getContext('2d');
    
    const labels = [];
    const data = [];
    const bgColors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#14b8a6'];
    
    let i = 0;
    for (const [tag, groupAssets] of Object.entries(groups)) {
        labels.push(tag);
        data.push(groupAssets.reduce((sum, a) => {
            const rate = a.currency === 'USD' ? exchangeRate : 1.0;
            return sum + (a.total_value * rate);
        }, 0));
        i++;
    }
    
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
