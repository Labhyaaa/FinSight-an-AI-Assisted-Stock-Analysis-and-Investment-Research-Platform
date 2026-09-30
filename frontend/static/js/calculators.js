/**
 * FinSight – Calculators JS
 * SIP, Lumpsum, SWP, PF, Brokerage, Margin – pure client-side.
 */

let sipChart, lsChart, swpChart, pfChart;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSIP();
    initLumpsum();
    initSWP();
    initPF();
    initMarginSlider();
});

// ── Tab Switching ───────────────────────────────────────────
function initTabs() {
    document.querySelectorAll('#calc-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#calc-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.calc-panel').forEach(p => p.style.display = 'none');
            document.getElementById('panel-' + tab.dataset.tab).style.display = 'block';
        });
    });
}

// ── Currency Formatter ──────────────────────────────────────
function fc(n) { return '₹' + Math.round(n).toLocaleString('en-IN'); }

// ── SIP Calculator ──────────────────────────────────────────
function initSIP() {
    const invest = document.getElementById('sip-invest');
    const rate = document.getElementById('sip-rate');
    const years = document.getElementById('sip-years');
    [invest, rate, years].forEach(el => el.addEventListener('input', calcSIP));
    calcSIP();
}

function calcSIP() {
    const P = parseInt(document.getElementById('sip-invest').value);
    const r = parseFloat(document.getElementById('sip-rate').value) / 100 / 12;
    const n = parseInt(document.getElementById('sip-years').value) * 12;

    document.getElementById('sip-invest-val').textContent = fc(P);
    document.getElementById('sip-rate-val').textContent = document.getElementById('sip-rate').value + '%';
    document.getElementById('sip-years-val').textContent = document.getElementById('sip-years').value;

    const maturity = P * ((Math.pow(1 + r, n) - 1) / r) * (1 + r);
    const invested = P * n;
    const returns = maturity - invested;

    document.getElementById('sip-invested').textContent = fc(invested);
    document.getElementById('sip-returns').textContent = fc(returns);
    document.getElementById('sip-total').textContent = fc(maturity);

    // Chart: growth over years
    const labels = [], investedData = [], totalData = [];
    for (let y = 1; y <= parseInt(document.getElementById('sip-years').value); y++) {
        const m = y * 12;
        labels.push('Year ' + y);
        investedData.push(P * m);
        totalData.push(P * ((Math.pow(1 + r, m) - 1) / r) * (1 + r));
    }
    renderDualChart('sip-chart', sipChart, labels, investedData, totalData, 'Invested', 'Value');
}

// ── Lumpsum Calculator ──────────────────────────────────────
function initLumpsum() {
    const invest = document.getElementById('ls-invest');
    const rate = document.getElementById('ls-rate');
    const years = document.getElementById('ls-years');
    [invest, rate, years].forEach(el => el.addEventListener('input', calcLumpsum));
    calcLumpsum();
}

function calcLumpsum() {
    const P = parseInt(document.getElementById('ls-invest').value);
    const r = parseFloat(document.getElementById('ls-rate').value) / 100;
    const n = parseInt(document.getElementById('ls-years').value);

    document.getElementById('ls-invest-val').textContent = fc(P);
    document.getElementById('ls-rate-val').textContent = document.getElementById('ls-rate').value + '%';
    document.getElementById('ls-years-val').textContent = n;

    const maturity = P * Math.pow(1 + r, n);
    const returns = maturity - P;

    document.getElementById('ls-invested').textContent = fc(P);
    document.getElementById('ls-returns').textContent = fc(returns);
    document.getElementById('ls-total').textContent = fc(maturity);

    const labels = [], investedData = [], totalData = [];
    for (let y = 1; y <= n; y++) {
        labels.push('Year ' + y);
        investedData.push(P);
        totalData.push(P * Math.pow(1 + r, y));
    }
    renderDualChart('ls-chart', lsChart, labels, investedData, totalData, 'Invested', 'Value');
}

// ── SWP Calculator ──────────────────────────────────────────
function initSWP() {
    const invest = document.getElementById('swp-invest');
    const withdraw = document.getElementById('swp-withdraw');
    const rate = document.getElementById('swp-rate');
    const years = document.getElementById('swp-years');
    [invest, withdraw, rate, years].forEach(el => el.addEventListener('input', calcSWP));
    calcSWP();
}

function calcSWP() {
    const P = parseInt(document.getElementById('swp-invest').value);
    const W = parseInt(document.getElementById('swp-withdraw').value);
    const r = parseFloat(document.getElementById('swp-rate').value) / 100 / 12;
    const n = parseInt(document.getElementById('swp-years').value) * 12;

    document.getElementById('swp-invest-val').textContent = fc(P);
    document.getElementById('swp-withdraw-val').textContent = fc(W);
    document.getElementById('swp-rate-val').textContent = document.getElementById('swp-rate').value + '%';
    document.getElementById('swp-years-val').textContent = document.getElementById('swp-years').value;

    let balance = P;
    const balances = [], labels = [];
    for (let m = 1; m <= n; m++) {
        balance = balance * (1 + r) - W;
        if (balance < 0) balance = 0;
        if (m % 12 === 0) {
            labels.push('Year ' + (m/12));
            balances.push(Math.round(balance));
        }
    }

    const totalWithdrawals = W * n;
    document.getElementById('swp-total-withdraw').textContent = fc(totalWithdrawals);
    document.getElementById('swp-remaining').textContent = fc(Math.max(balance, 0));

    // Chart
    if (swpChart) swpChart.destroy();
    const ctx = document.getElementById('swp-chart').getContext('2d');
    swpChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels, datasets: [{
                label: 'Remaining Corpus',
                data: balances, borderColor: '#2EC4B6',
                backgroundColor: 'rgba(46,196,182,0.15)', fill: true,
                tension: 0.3, pointRadius: 3,
            }]
        },
        options: chartOptions()
    });
}

// ── PF Calculator ───────────────────────────────────────────
function initPF() {
    ['pf-salary','pf-emp','pf-employer','pf-interest','pf-years'].forEach(id => {
        document.getElementById(id).addEventListener('input', calcPF);
    });
    calcPF();
}

function calcPF() {
    const salary = parseInt(document.getElementById('pf-salary').value);
    const empPct = parseInt(document.getElementById('pf-emp').value) / 100;
    const employerPct = parseInt(document.getElementById('pf-employer').value) / 100;
    const interest = parseFloat(document.getElementById('pf-interest').value) / 100 / 12;
    const years = parseInt(document.getElementById('pf-years').value);

    document.getElementById('pf-salary-val').textContent = fc(salary);
    document.getElementById('pf-emp-val').textContent = document.getElementById('pf-emp').value + '%';
    document.getElementById('pf-employer-val').textContent = document.getElementById('pf-employer').value + '%';
    document.getElementById('pf-interest-val').textContent = document.getElementById('pf-interest').value + '%';
    document.getElementById('pf-years-val').textContent = years;

    const monthlyContrib = salary * (empPct + employerPct);
    let balance = 0;
    const labels = [], contribs = [], totals = [];

    for (let y = 1; y <= years; y++) {
        for (let m = 0; m < 12; m++) {
            balance = (balance + monthlyContrib) * (1 + interest);
        }
        labels.push('Year ' + y);
        contribs.push(Math.round(monthlyContrib * 12 * y));
        totals.push(Math.round(balance));
    }

    const totalContrib = monthlyContrib * 12 * years;
    document.getElementById('pf-contribution').textContent = fc(totalContrib);
    document.getElementById('pf-interest-earned').textContent = fc(balance - totalContrib);
    document.getElementById('pf-maturity').textContent = fc(balance);

    renderDualChart('pf-chart', pfChart, labels, contribs, totals, 'Contributions', 'Corpus');
}

// ── Brokerage Calculator ────────────────────────────────────
function calcBrokerage() {
    const buy = parseFloat(document.getElementById('brk-buy').value);
    const sell = parseFloat(document.getElementById('brk-sell').value);
    const qty = parseInt(document.getElementById('brk-qty').value);
    const fee = parseFloat(document.getElementById('brk-fee').value);

    const totalBrokerage = fee * 2; // buy + sell
    const turnover = (buy + sell) * qty;
    const stt = turnover * 0.001; // 0.1% STT approximation
    const grossPL = (sell - buy) * qty;
    const netPL = grossPL - totalBrokerage - stt;

    document.getElementById('brk-total-cost').textContent = fc(totalBrokerage + stt);
    const plEl = document.getElementById('brk-net-pl');
    plEl.textContent = fc(netPL);
    plEl.className = `calc-stat-value ${netPL >= 0 ? 'text-positive' : 'text-negative'}`;

    document.getElementById('brk-breakdown').innerHTML = `
        <table style="width:100%">
            <tr><td>Turnover</td><td style="text-align:right">${fc(turnover)}</td></tr>
            <tr><td>Brokerage (×2)</td><td style="text-align:right">${fc(totalBrokerage)}</td></tr>
            <tr><td>STT (approx)</td><td style="text-align:right">${fc(stt)}</td></tr>
            <tr><td>Gross P/L</td><td style="text-align:right" class="${grossPL>=0?'text-positive':'text-negative'}">${fc(grossPL)}</td></tr>
            <tr style="font-weight:700"><td>Net P/L</td><td style="text-align:right" class="${netPL>=0?'text-positive':'text-negative'}">${fc(netPL)}</td></tr>
        </table>
    `;
}

// ── Margin Calculator ───────────────────────────────────────
function initMarginSlider() {
    document.getElementById('mrg-pct').addEventListener('input', () => {
        document.getElementById('mrg-pct-val').textContent = document.getElementById('mrg-pct').value + '%';
    });
}

function calcMargin() {
    const price = parseFloat(document.getElementById('mrg-price').value);
    const qty = parseInt(document.getElementById('mrg-qty').value);
    const pct = parseInt(document.getElementById('mrg-pct').value) / 100;

    const totalValue = price * qty;
    const margin = totalValue * pct;

    document.getElementById('mrg-total-value').textContent = fc(totalValue);
    document.getElementById('mrg-required').textContent = fc(margin);
}

// ── Chart Helpers ───────────────────────────────────────────
function renderDualChart(canvasId, chartInstance, labels, data1, data2, label1, label2) {
    if (chartInstance) chartInstance.destroy();
    const ctx = document.getElementById(canvasId).getContext('2d');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: label1, data: data1, backgroundColor: '#CBF3F0', borderRadius: 4 },
                { label: label2, data: data2, backgroundColor: '#2EC4B6', borderRadius: 4 },
            ]
        },
        options: chartOptions()
    });
    // Store reference
    if (canvasId === 'sip-chart') sipChart = chart;
    else if (canvasId === 'ls-chart') lsChart = chart;
    else if (canvasId === 'pf-chart') pfChart = chart;
}

function chartOptions() {
    return {
        responsive: true, maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom', labels: { font: { size: 11 } } },
            tooltip: { backgroundColor: '#1F2937', cornerRadius: 8, padding: 10 }
        },
        scales: {
            x: { grid: { display: false }, ticks: { font: { size: 10 } } },
            y: { 
                grid: { color: 'rgba(0,0,0,0.05)' }, 
                ticks: { 
                    font: { size: 10 },
                    callback: function(value) {
                        if (value >= 10000000) return '₹' + (value / 10000000).toFixed(1).replace(/\.0$/, '') + 'Cr';
                        if (value >= 100000) return '₹' + (value / 100000).toFixed(1).replace(/\.0$/, '') + 'L';
                        if (value >= 1000) return '₹' + (value / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
                        return '₹' + value;
                    }
                } 
            }
        }
    };
}
