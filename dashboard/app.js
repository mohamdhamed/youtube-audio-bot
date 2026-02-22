/**
 * YouTube Audio Bot — Dashboard Frontend Logic
 */

const API = '';

// ==================== State ====================
let currentSection = 'overview';
let configData = null;

// ==================== DOM Helpers ====================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ==================== Toast ====================
function showToast(message, type = 'success') {
    const toast = $('#toast');
    const msg = $('#toast-message');
    msg.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => { toast.className = 'toast hidden'; }, 3000);
}

// ==================== API Calls ====================
async function api(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        ...options,
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || 'خطأ غير متوقع');
    }
    return data;
}

// ==================== Auth ====================
async function handleLogin(e) {
    e.preventDefault();
    const password = $('#login-password').value;
    const errorEl = $('#login-error');
    errorEl.classList.add('hidden');

    try {
        await api('/api/login', {
            method: 'POST',
            body: JSON.stringify({ password }),
        });
        $('#login-screen').classList.add('hidden');
        $('#dashboard').classList.remove('hidden');
        loadDashboard();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.remove('hidden');
    }
}

async function handleLogout() {
    try { await api('/api/logout', { method: 'POST' }); } catch (_) { }
    $('#dashboard').classList.add('hidden');
    $('#login-screen').classList.remove('hidden');
    $('#login-password').value = '';
}

// ==================== Navigation ====================
function switchSection(section) {
    currentSection = section;
    $$('.nav-item').forEach(btn => btn.classList.remove('active'));
    $(`.nav-item[data-section="${section}"]`).classList.add('active');
    $$('.section').forEach(s => s.classList.remove('active'));
    $(`#section-${section}`).classList.add('active');

    // Load section data
    if (section === 'overview') loadOverview();
    if (section === 'folders') loadFolders();
    if (section === 'users') loadUsers();
    if (section === 'drive') loadDriveTabs();
    if (section === 'logs') loadLogs();
}

// ==================== Dashboard Init ====================
async function loadDashboard() {
    loadOverview();
}

// ==================== Overview ====================
async function loadOverview() {
    try {
        const status = await api('/api/status');
        $('#stat-status').textContent = status.bot_running ? 'شغال ✅' : 'واقف ❌';
        $('#stat-folders').textContent = `${status.active_folders} / ${status.total_folders}`;
        $('#stat-users').textContent = status.allowed_users_count || 'مفتوح للكل';
        $('#stat-time').textContent = status.timestamp.split(' ')[1];

        const logs = await api('/api/logs?limit=5');
        renderLogsList(logs.logs, '#overview-logs');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== Folders ====================
async function loadFolders() {
    try {
        const data = await api('/api/config');
        configData = data;
        const grid = $('#folders-grid');
        grid.innerHTML = '';

        for (const [key, folder] of Object.entries(data.folders)) {
            const card = document.createElement('div');
            card.className = 'folder-card';
            card.innerHTML = `
                <div class="folder-header">
                    <span class="folder-emoji">${folder.emoji}</span>
                    <span class="folder-name">${folder.name}</span>
                    <span class="folder-status ${folder.active ? 'active' : 'inactive'}">
                        ${folder.active ? 'مفعّل' : 'معطّل'}
                    </span>
                </div>
                <label>Folder ID</label>
                <input type="text" class="input folder-input" data-key="${key}"
                       value="${folder.id}" placeholder="اتركه فارغ للتعطيل">
            `;
            grid.appendChild(card);
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function saveFolders() {
    const inputs = $$('.folder-input');
    const data = {};
    inputs.forEach(input => {
        data[input.dataset.key] = input.value.trim();
    });

    try {
        const result = await api('/api/config/folders', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        if (result.changes && result.changes.length > 0) {
            showToast(`✅ تم حفظ ${result.changes.length} تغيير`, 'success');
        } else {
            showToast('لا يوجد تغييرات', 'success');
        }
        loadFolders();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== Users ====================
async function loadUsers() {
    try {
        const data = await api('/api/users');
        const list = $('#users-list');

        if (data.users.length === 0) {
            list.innerHTML = '<p class="empty-state">🔓 لا يوجد قيود — أي حد يقدر يستخدم البوت</p>';
            return;
        }

        list.innerHTML = data.users.map(uid => `
            <div class="user-card">
                <div class="user-info">
                    <div class="user-avatar">👤</div>
                    <span class="user-id">${uid}</span>
                </div>
                <button class="btn btn-danger btn-sm" onclick="removeUser(${uid})">🗑️ حذف</button>
            </div>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function addUser() {
    const input = $('#new-user-id');
    const userId = input.value.trim();
    if (!userId) return;

    try {
        await api('/api/users', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId }),
        });
        showToast('✅ تم إضافة المستخدم', 'success');
        input.value = '';
        loadUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function removeUser(userId) {
    if (!confirm(`حذف المستخدم ${userId}؟`)) return;

    try {
        await api(`/api/users/${userId}`, { method: 'DELETE' });
        showToast('✅ تم حذف المستخدم', 'success');
        loadUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== Drive Browser ====================
async function loadDriveTabs() {
    try {
        const data = await api('/api/config');
        const tabs = $('#drive-tabs');
        tabs.innerHTML = '';

        for (const [key, folder] of Object.entries(data.folders)) {
            const btn = document.createElement('button');
            btn.className = 'drive-tab';
            btn.textContent = `${folder.emoji} ${folder.name}`;
            btn.disabled = !folder.active;
            if (folder.active) {
                btn.onclick = () => loadDriveFiles(key, btn);
            }
            tabs.appendChild(btn);
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadDriveFiles(folderKey, tabBtn) {
    $$('.drive-tab').forEach(t => t.classList.remove('active'));
    if (tabBtn) tabBtn.classList.add('active');

    const container = $('#drive-files');
    container.innerHTML = '<p class="empty-state"><span class="spinner"></span> جاري التحميل...</p>';

    try {
        const data = await api(`/api/drive/files/${folderKey}`);

        if (data.files.length === 0) {
            container.innerHTML = '<p class="empty-state">📭 الفولدر فاضي</p>';
            return;
        }

        container.innerHTML = `
            <table class="drive-files-table">
                <thead>
                    <tr>
                        <th>📄 اسم الملف</th>
                        <th>📦 الحجم</th>
                        <th>📅 التاريخ</th>
                        <th>🔗 رابط</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.files.map(f => `
                        <tr>
                            <td>${f.name}</td>
                            <td>${f.size}</td>
                            <td style="direction:ltr; text-align:center;">${f.date}</td>
                            <td><a href="${f.link}" target="_blank">فتح ↗</a></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        container.innerHTML = `<p class="empty-state" style="color: var(--red);">❌ ${err.message}</p>`;
    }
}

// ==================== Logs ====================
async function loadLogs() {
    try {
        const data = await api('/api/logs?limit=50');
        renderLogsList(data.logs, '#logs-list');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderLogsList(logs, selector) {
    const container = $(selector);
    if (!logs || logs.length === 0) {
        container.innerHTML = '<p class="empty-state">لا توجد سجلات بعد</p>';
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="log-entry">
            <span class="log-time">${log.time}</span>
            <span class="log-action">${log.action}</span>
            <span class="log-details">${log.details}</span>
        </div>
    `).join('');
}

// ==================== Settings ====================
async function changePassword() {
    const newPass = $('#new-password').value;
    const confirmPass = $('#confirm-password').value;

    if (!newPass) {
        showToast('أدخل كلمة السر الجديدة', 'error');
        return;
    }
    if (newPass !== confirmPass) {
        showToast('كلمة السر مش متطابقة', 'error');
        return;
    }

    try {
        await api('/api/password', {
            method: 'POST',
            body: JSON.stringify({ new_password: newPass }),
        });
        showToast('✅ تم تغيير كلمة السر', 'success');
        $('#new-password').value = '';
        $('#confirm-password').value = '';
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== Event Listeners ====================
document.addEventListener('DOMContentLoaded', () => {
    // Login
    $('#login-form').addEventListener('submit', handleLogin);
    $('#logout-btn').addEventListener('click', handleLogout);

    // Navigation
    $$('.nav-item').forEach(btn => {
        btn.addEventListener('click', () => switchSection(btn.dataset.section));
    });

    // Folders
    $('#save-folders-btn').addEventListener('click', saveFolders);

    // Users
    $('#add-user-btn').addEventListener('click', addUser);
    $('#new-user-id').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addUser();
    });

    // Logs
    $('#refresh-logs-btn').addEventListener('click', loadLogs);

    // Settings
    $('#change-password-btn').addEventListener('click', changePassword);

    // Check if already authenticated by trying to load status
    api('/api/status').then(() => {
        $('#login-screen').classList.add('hidden');
        $('#dashboard').classList.remove('hidden');
        loadDashboard();
    }).catch(() => {
        // Not authenticated, show login
    });
});
