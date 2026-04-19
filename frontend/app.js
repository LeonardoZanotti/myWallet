let portfolioChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchWallet();
    
    document.getElementById('add-asset-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            ticker: document.getElementById('add-ticker').value.toUpperCase(),
            quantity: parseFloat(document.getElementById('add-qty').value),
            average_price: parseFloat(document.getElementById('add-price').value),
            nota: parseInt(document.getElementById('add-nota').value),
            tag: document.getElementById('add-tag').value
        };
        
        showLoader();
        await fetch('/api/wallet/asset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        e.target.reset();
        fetchWallet();
    });

    document.getElementById('edit-asset-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const ticker = document.getElementById('edit-ticker').value;
        const data = {
            quantity: parseFloat(document.getElementById('edit-qty').value),
            average_price: parseFloat(document.getElementById('edit-price').value),
            nota: parseInt(document.getElementById('edit-nota').value),
            tag: document.getElementById('edit-tag').value
        };
        
        showLoader();
        await fetch(`/api/wallet/asset/${ticker}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        closeEditModal();
        fetchWallet();
    });
});

function openEditModal(ticker, qty, price, nota, tag) {
    document.getElementById('edit-ticker').value = ticker;
    document.getElementById('edit-ticker-display').innerText = ticker;
    document.getElementById('edit-qty').value = qty;
    document.getElementById('edit-price').value = price;
    document.getElementById('edit-nota').value = nota;
    document.getElementById('edit-tag').value = tag;
    
    const modal = document.getElementById('edit-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
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
        renderWallet(data.assets, data.exchange_rate);
    } catch (error) {
        console.error("Error fetching wallet", error);
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

    // Render Tables
    const container = document.getElementById('asset-groups-container');
    container.innerHTML = '';
    
    for (const [tag, groupAssets] of Object.entries(groups)) {
        const cur = groupAssets[0]?.currency || 'BRL';
        let groupTotal = groupAssets.reduce((sum, a) => sum + a.total_value, 0);
        let groupCost = groupAssets.reduce((sum, a) => sum + (a.quantity * a.average_price), 0);
        let groupVar = groupCost > 0 ? ((groupTotal - groupCost) / groupCost) * 100 : 0;
        
        let html = `
        <div class="bg-dark-card rounded-2xl border border-dark-border shadow-lg overflow-hidden">
            <div class="px-6 py-4 border-b border-dark-border flex justify-between items-center bg-dark-bg/30">
                <h3 class="font-bold flex items-center"><i class="fa-solid fa-layer-group text-dark-muted mr-2"></i> ${tag}</h3>
                <div class="text-sm">
                    <span class="text-dark-muted mr-3">Value: <span class="text-white font-medium">${formatCurrency(groupTotal, cur)}</span></span>
                    <span class="${groupVar >= 0 ? 'text-brand-green' : 'text-brand-red'} font-medium">${groupVar >= 0 ? '+' : ''}${groupVar.toFixed(2)}%</span>
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
                            <th class="py-3 px-6 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="text-sm divide-y divide-dark-border">
        `;
        
        groupAssets.forEach(a => {
            const isPositive = a.variation >= 0;
            const priceText = a.current_price ? formatCurrency(a.current_price, a.currency) : '<span class="text-dark-muted">N/A</span>';
            
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
                <td class="py-3 px-6 text-right">
                    <button onclick="openEditModal('${a.ticker}', ${a.quantity}, ${a.average_price}, ${a.nota}, '${a.tag}')" class="text-brand-blue hover:text-blue-400 transition-colors mr-3"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button onclick="deleteAsset('${a.ticker}')" class="text-dark-muted hover:text-brand-red transition-colors"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>
            `;
        });
        
        html += `</tbody></table></div></div>`;
        container.innerHTML += html;
    }
    
    renderChart(groups);
}

async function deleteAsset(ticker) {
    if (confirm(`Remove ${ticker}?`)) {
        showLoader();
        await fetch(`/api/wallet/asset/${ticker}`, { method: 'DELETE' });
        fetchWallet();
    }
}

async function calculateSmartBuy() {
    const brl = parseFloat(document.getElementById('invest-brl').value) || 0;
    const usd = parseFloat(document.getElementById('invest-usd').value) || 0;
    
    if (brl === 0 && usd === 0) {
        alert("Please enter an amount to invest.");
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
        
        // Populate modal
        const tbody = document.getElementById('recommendation-body');
        tbody.innerHTML = '';
        
        data.recommendations.forEach(r => {
            if (r.value_to_buy > 0) {
                tbody.innerHTML += `
                <tr class="hover:bg-dark-border/20 transition-colors">
                    <td class="py-3 px-2 font-medium">${r.ticker}</td>
                    <td class="py-3 px-2 text-dark-muted text-xs">${r.tag}</td>
                    <td class="py-3 px-2">${formatCurrency(r.current_value, r.currency)}</td>
                    <td class="py-3 px-2">${(r.ideal_percent * 100).toFixed(1)}%</td>
                    <td class="py-3 px-2 font-bold text-brand-green">${formatCurrency(r.value_to_buy, r.currency)}</td>
                    <td class="py-3 px-2 font-bold text-brand-blue">${r.shares_to_buy.toFixed(2)}</td>
                </tr>
                `;
            }
        });
        
        if (tbody.innerHTML === '') {
            tbody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-dark-muted">No purchases recommended.</td></tr>`;
        }
        
        // Show modal
        const modal = document.getElementById('recommendation-modal');
        modal.classList.remove('hidden');
        // Small delay to allow display:flex to apply before adding the 'show' class for transition
        setTimeout(() => modal.classList.add('show'), 10);
        
    } catch (e) {
        alert("Error calculating");
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

function renderChart(groups) {
    const ctx = document.getElementById('portfolioChart').getContext('2d');
    
    const labels = [];
    const data = [];
    const bgColors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#14b8a6'];
    
    let i = 0;
    for (const [tag, groupAssets] of Object.entries(groups)) {
        labels.push(tag);
        data.push(groupAssets.reduce((sum, a) => sum + a.total_value, 0));
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
