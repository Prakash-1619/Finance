const state = {
  transactions: [
    { date: '2026-07-18', type: 'Income', domain: 'Salary', category: 'Salary', amount: 86000, description: 'Monthly salary' },
    { date: '2026-07-19', type: 'Expenditure', domain: 'Home', category: 'Rent', amount: 15800, description: 'House rent' },
    { date: '2026-07-17', type: 'Expenditure', domain: 'Car', category: 'Fuel', amount: 3200, description: 'Petrol refill' },
    { date: '2026-07-16', type: 'Income', domain: 'Agri Land', category: 'Produce', amount: 22500, description: 'Vegetable sale' },
    { date: '2026-07-15', type: 'Expenditure', domain: 'Loans', category: 'EMI', amount: 7800, description: 'Loan EMI payment' }
  ],
  filterType: 'All',
  filterDomain: 'All'
};

const pages = Array.from(document.querySelectorAll('.page'));
const navButtons = document.querySelectorAll('.nav-btn');
const filterType = document.getElementById('filterType');
const filterDomain = document.getElementById('filterDomain');
const recentTable = document.getElementById('recentTable');
const allTransactions = document.getElementById('allTransactions');
const balanceValue = document.getElementById('balanceValue');
const incomeValue = document.getElementById('incomeValue');
const expenseValue = document.getElementById('expenseValue');
const transactionCount = document.getElementById('transactionCount');
const distributionChart = document.getElementById('distributionChart');
const topDomains = document.getElementById('topDomains');
const newEntryBtn = document.getElementById('newEntryBtn');
const transactionForm = document.getElementById('transactionForm');
const toast = document.getElementById('toast');

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('visible');
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.remove('visible'), 2400);
}

function updateNavigation(target) {
  pages.forEach((page) => page.classList.toggle('active', page.id === target));
  navButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.target === target));
}

function getFilteredTransactions() {
  return state.transactions.filter((transaction) => {
    if (state.filterType !== 'All' && transaction.type !== state.filterType) {
      return false;
    }
    if (state.filterDomain !== 'All' && transaction.domain !== state.filterDomain) {
      return false;
    }
    return true;
  });
}

function formatCurrency(value) {
  return `₹${value.toLocaleString('en-IN')}`;
}

function renderSummary() {
  const filtered = getFilteredTransactions();
  const income = filtered.filter((item) => item.type === 'Income').reduce((sum, item) => sum + item.amount, 0);
  const expense = filtered.filter((item) => item.type === 'Expenditure').reduce((sum, item) => sum + item.amount, 0);
  const balance = income - expense;

  incomeValue.textContent = formatCurrency(income);
  expenseValue.textContent = formatCurrency(expense);
  balanceValue.textContent = formatCurrency(balance);
  transactionCount.textContent = filtered.length;
}

function createRow(transaction) {
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>${transaction.date}</td>
    <td class="${transaction.type === 'Income' ? 'income' : 'expense'}">${transaction.type}</td>
    <td>${transaction.domain}</td>
    <td>${transaction.category}</td>
    <td>${formatCurrency(transaction.amount)}</td>
    <td>${transaction.description}</td>
  `;
  return tr;
}

function renderRecentTransactions() {
  recentTable.innerHTML = '';
  const filtered = getFilteredTransactions().slice(0, 6);
  if (filtered.length === 0) {
    recentTable.innerHTML = '<tr><td colspan="6" class="empty-row">No transactions available.</td></tr>';
    return;
  }
  filtered.forEach((transaction) => recentTable.appendChild(createRow(transaction)));
}

function renderAllTransactions() {
  allTransactions.innerHTML = '';
  const filtered = getFilteredTransactions();
  if (filtered.length === 0) {
    allTransactions.innerHTML = '<tr><td colspan="4" class="empty-row">No transactions available.</td></tr>';
    return;
  }
  filtered.forEach((transaction) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${transaction.date}</td>
      <td>${transaction.type}</td>
      <td>${transaction.domain}</td>
      <td>${formatCurrency(transaction.amount)}</td>
    `;
    allTransactions.appendChild(tr);
  });
}

function renderDomainFilters() {
  const domainSet = new Set(state.transactions.map((item) => item.domain));
  const domains = ['All', ...Array.from(domainSet).sort()];
  filterDomain.innerHTML = domains.map((domain) => `<option value="${domain}">${domain}</option>`).join('');
}

function renderAnalytics() {
  const filtered = getFilteredTransactions();
  const domainTotals = filtered.reduce((acc, item) => {
    acc[item.domain] = (acc[item.domain] || 0) + item.amount;
    return acc;
  }, {});

  const sortedDomains = Object.entries(domainTotals).sort((a, b) => b[1] - a[1]);
  const maxValue = sortedDomains.length ? sortedDomains[0][1] : 1;

  distributionChart.innerHTML = sortedDomains.map(([domain, amount]) => {
    const width = Math.max(6, Math.round((amount / maxValue) * 100));
    return `
      <div class="bar-item">
        <div class="bar-label"><span>${domain}</span><span>${formatCurrency(amount)}</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${width}%; background:#${Math.floor(Math.random()*16777215).toString(16).padStart(6,'0')}"></div></div>
      </div>
    `;
  }).join('');

  topDomains.innerHTML = sortedDomains.slice(0, 5).map(([domain, amount]) => `
    <li><span>${domain}</span><strong>${formatCurrency(amount)}</strong></li>
  `).join('');

  if (sortedDomains.length === 0) {
    distributionChart.innerHTML = '<p class="empty-row">No domain analytics available.</p>';
    topDomains.innerHTML = '<li class="empty-row">No data to display.</li>';
  }
}

function renderUI() {
  renderDomainFilters();
  renderSummary();
  renderRecentTransactions();
  renderAllTransactions();
  renderAnalytics();
}

navButtons.forEach((button) => {
  button.addEventListener('click', () => updateNavigation(button.dataset.target));
});

filterType.addEventListener('change', (event) => {
  state.filterType = event.target.value;
  renderUI();
});

filterDomain.addEventListener('change', (event) => {
  state.filterDomain = event.target.value;
  renderUI();
});

newEntryBtn.addEventListener('click', () => updateNavigation('transactions'));

transactionForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const date = document.getElementById('entryDate').value;
  const type = document.getElementById('entryType').value;
  const domain = document.getElementById('entryDomain').value;
  const category = document.getElementById('entryCategory').value || 'General';
  const amount = Number(document.getElementById('entryAmount').value);
  const description = document.getElementById('entryDescription').value || '-';

  if (!date || !type || !domain || !amount) {
    showToast('Please fill in all required fields.');
    return;
  }

  state.transactions.unshift({ date, type, domain, category, amount, description });
  transactionForm.reset();
  showToast('Transaction added successfully!');
  renderUI();
});

window.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('entryDate').value = today;
  renderUI();
});
