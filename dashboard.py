"""
Web Dashboard for YouTube Audio Bot
Flask-based admin panel for managing bot settings, users, and Drive folders.
"""

import os
import json
import logging
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dashboard', static_url_path='/dashboard')
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(hours=24)

# ==============  In-memory activity log  ==============
activity_log = []
MAX_LOG_ENTRIES = 200


def log_activity(action: str, details: str = ""):
    """Add an entry to the in-memory activity log."""
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
    }
    activity_log.insert(0, entry)
    if len(activity_log) > MAX_LOG_ENTRIES:
        activity_log.pop()


# ==============  Auth helpers  ==============
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "غير مصرح"}), 401
        return f(*args, **kwargs)
    return decorated


# ==============  .env helpers  ==============
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')


def read_env() -> dict:
    """Read .env file into a dict."""
    env_vars = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip()
    return env_vars


def write_env(env_vars: dict):
    """Write env vars back to .env preserving comments and structure."""
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in env_vars:
                new_lines.append(f"{key}={env_vars[key]}\n")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Append any new keys
    for key, value in env_vars.items():
        if key not in updated_keys:
            new_lines.append(f"\n{key}={value}\n")

    with open(ENV_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


# ==============  Routes  ==============

@app.route('/')
def index():
    return send_from_directory('dashboard', 'index.html')


@app.route('/api/login', methods=['POST'])
def login():
    from config import DASHBOARD_PASSWORD
    data = request.get_json()
    password = data.get('password', '')
    if password == DASHBOARD_PASSWORD:
        session.permanent = True
        session['authenticated'] = True
        log_activity("تسجيل دخول", "تم تسجيل الدخول بنجاح")
        return jsonify({"success": True})
    return jsonify({"error": "كلمة السر غلط"}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route('/api/status')
@login_required
def get_status():
    from config import FOLDERS, ALLOWED_USERS
    active_folders = sum(1 for f in FOLDERS.values() if f['id'])
    return jsonify({
        "bot_running": True,
        "active_folders": active_folders,
        "total_folders": len(FOLDERS),
        "allowed_users_count": len(ALLOWED_USERS),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route('/api/config')
@login_required
def get_config():
    from config import FOLDERS, ALLOWED_USERS, GOOGLE_DRIVE_FOLDER_ID
    folders_data = {}
    for key, folder in FOLDERS.items():
        folders_data[key] = {
            "id": folder['id'],
            "name": folder['name'],
            "emoji": folder['emoji'],
            "active": bool(folder['id']),
        }
    return jsonify({
        "folders": folders_data,
        "allowed_users": list(ALLOWED_USERS),
        "default_folder_id": GOOGLE_DRIVE_FOLDER_ID or "",
    })


@app.route('/api/config/folders', methods=['POST'])
@login_required
def update_folders():
    from config import reload_config
    data = request.get_json()
    env_vars = read_env()

    folder_map = {
        'audio': 'FOLDER_AUDIO',
        'video': 'FOLDER_VIDEO',
        'books': 'FOLDER_BOOKS',
        'other': 'FOLDER_OTHER',
    }

    changes = []
    for key, env_key in folder_map.items():
        if key in data:
            new_val = data[key].strip()
            old_val = env_vars.get(env_key, '')
            if new_val != old_val:
                env_vars[env_key] = new_val
                from config import FOLDERS
                label = FOLDERS[key]['name']
                changes.append(f"{label}: {old_val or '(فارغ)'} → {new_val or '(فارغ)'}")

    if changes:
        write_env(env_vars)
        reload_config()
        log_activity("تحديث الفولدرات", " | ".join(changes))

    return jsonify({"success": True, "changes": changes})


@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    from config import ALLOWED_USERS
    return jsonify({"users": list(ALLOWED_USERS)})


@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    from config import reload_config
    data = request.get_json()
    user_id = data.get('user_id', '')

    try:
        user_id = int(str(user_id).strip())
    except (ValueError, TypeError):
        return jsonify({"error": "ID المستخدم لازم يكون رقم"}), 400

    env_vars = read_env()
    current = env_vars.get('ALLOWED_USERS', '')
    current_ids = [uid.strip() for uid in current.split(',') if uid.strip()]

    if str(user_id) in current_ids:
        return jsonify({"error": "المستخدم موجود بالفعل"}), 400

    current_ids.append(str(user_id))
    env_vars['ALLOWED_USERS'] = ','.join(current_ids)
    write_env(env_vars)
    reload_config()
    log_activity("إضافة مستخدم", f"ID: {user_id}")
    return jsonify({"success": True, "user_id": user_id})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def remove_user(user_id):
    from config import reload_config
    env_vars = read_env()
    current = env_vars.get('ALLOWED_USERS', '')
    current_ids = [uid.strip() for uid in current.split(',') if uid.strip()]

    if str(user_id) not in current_ids:
        return jsonify({"error": "المستخدم مش موجود"}), 404

    current_ids.remove(str(user_id))
    env_vars['ALLOWED_USERS'] = ','.join(current_ids)
    write_env(env_vars)
    reload_config()
    log_activity("حذف مستخدم", f"ID: {user_id}")
    return jsonify({"success": True})


@app.route('/api/drive/files/<folder_key>')
@login_required
def get_drive_files(folder_key):
    from config import FOLDERS, CREDENTIALS_PATH
    folder = FOLDERS.get(folder_key)
    if not folder or not folder['id']:
        return jsonify({"error": "الفولدر مش موجود أو مش مفعّل"}), 404

    try:
        from services.drive_service import get_drive_service
        service = get_drive_service(CREDENTIALS_PATH)
        if not service:
            return jsonify({"error": "فشل الاتصال بـ Google Drive"}), 500

        results = service.files().list(
            q=f"'{folder['id']}' in parents and trashed = false",
            pageSize=50,
            fields="files(id, name, mimeType, size, createdTime, webViewLink)",
            orderBy="createdTime desc"
        ).execute()

        files = results.get('files', [])
        file_list = []
        for f in files:
            size_bytes = int(f.get('size', 0))
            size_mb = size_bytes / (1024 * 1024)
            file_list.append({
                "id": f['id'],
                "name": f['name'],
                "type": f.get('mimeType', ''),
                "size": f"{size_mb:.1f} MB" if size_bytes else "—",
                "date": f.get('createdTime', '')[:10],
                "link": f.get('webViewLink', f"https://drive.google.com/file/d/{f['id']}/view"),
            })

        return jsonify({"files": file_list, "folder_name": folder['name']})

    except Exception as e:
        logger.error(f"Drive API error: {e}")
        return jsonify({"error": f"خطأ: {str(e)}"}), 500


@app.route('/api/logs')
@login_required
def get_logs():
    limit = request.args.get('limit', 50, type=int)
    return jsonify({"logs": activity_log[:limit]})


@app.route('/api/password', methods=['POST'])
@login_required
def change_password():
    from config import reload_config
    data = request.get_json()
    new_password = data.get('new_password', '').strip()

    if len(new_password) < 4:
        return jsonify({"error": "كلمة السر لازم تكون 4 حروف على الأقل"}), 400

    env_vars = read_env()
    env_vars['DASHBOARD_PASSWORD'] = new_password
    write_env(env_vars)
    reload_config()
    log_activity("تغيير كلمة السر", "تم تغيير كلمة سر الداشبورد")
    return jsonify({"success": True})


# ==============  Google Token Management  ==============

@app.route('/api/token/status')
@login_required
def token_status():
    """Check Google OAuth token status."""
    import pickle
    from services.drive_service import TOKEN_PATH

    if not os.path.exists(TOKEN_PATH):
        return jsonify({"status": "missing", "message": "التوكن غير موجود"})

    try:
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)

        if creds.valid:
            expiry = creds.expiry.strftime("%Y-%m-%d %H:%M") if creds.expiry else "غير معروف"
            return jsonify({"status": "valid", "message": f"التوكن شغال — ينتهي: {expiry}"})
        elif creds.expired and creds.refresh_token:
            return jsonify({"status": "expired", "message": "التوكن منتهي — يمكن تجديده"})
        else:
            return jsonify({"status": "invalid", "message": "التوكن تالف — لازم تعمل مصادقة جديدة"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"خطأ في قراءة التوكن: {str(e)}"})


@app.route('/api/token/refresh', methods=['POST'])
@login_required
def token_refresh():
    """Try to refresh the existing token."""
    import pickle
    from services.drive_service import TOKEN_PATH
    from google.auth.transport.requests import Request

    if not os.path.exists(TOKEN_PATH):
        return jsonify({"error": "التوكن غير موجود — لازم تعمل مصادقة جديدة"}), 400

    try:
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'wb') as f:
                pickle.dump(creds, f)
            log_activity("تجديد التوكن", "تم تجديد توكن Google بنجاح")
            return jsonify({"success": True, "message": "تم تجديد التوكن بنجاح ✅"})
        elif creds.valid:
            return jsonify({"success": True, "message": "التوكن لسه شغال ومش محتاج تجديد"})
        else:
            return jsonify({"error": "التوكن تالف — لازم تعمل مصادقة جديدة"}), 400
    except Exception as e:
        log_activity("فشل تجديد التوكن", str(e))
        return jsonify({"error": f"فشل التجديد: {str(e)}. لازم تعمل مصادقة جديدة."}), 500


@app.route('/api/token/start-auth', methods=['POST'])
@login_required
def token_start_auth():
    """Generate OAuth URL for new authentication."""
    from config import CREDENTIALS_PATH
    from services.drive_service import SCOPES

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        auth_url, _ = flow.authorization_url(prompt='consent')

        # Store flow in app config temporarily
        app.config['_oauth_flow'] = flow

        log_activity("بدء مصادقة جديدة", "تم إنشاء رابط المصادقة")
        return jsonify({"auth_url": auth_url})
    except Exception as e:
        return jsonify({"error": f"خطأ: {str(e)}"}), 500


@app.route('/api/token/complete-auth', methods=['POST'])
@login_required
def token_complete_auth():
    """Complete OAuth flow with the authorization code."""
    import pickle
    from services.drive_service import TOKEN_PATH

    data = request.get_json()
    code = data.get('code', '').strip()

    if not code:
        return jsonify({"error": "لازم تدخل الكود"}), 400

    flow = app.config.get('_oauth_flow')
    if not flow:
        return jsonify({"error": "لازم تبدأ المصادقة الأول (اضغط 'بدء المصادقة')"}), 400

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials

        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)

        app.config.pop('_oauth_flow', None)
        log_activity("مصادقة جديدة", "تم حفظ توكن Google جديد بنجاح ✅")
        return jsonify({"success": True, "message": "تم المصادقة بنجاح وحفظ التوكن الجديد! ✅"})
    except Exception as e:
        log_activity("فشل المصادقة", str(e))
        return jsonify({"error": f"فشل المصادقة: {str(e)}"}), 500


def start_dashboard():
    """Start the dashboard server in a thread."""
    from config import DASHBOARD_PORT
    log_activity("بدء التشغيل", f"الداشبورد شغال على بورت {DASHBOARD_PORT}")
    app.run(
        host='0.0.0.0',
        port=DASHBOARD_PORT,
        debug=False,
        use_reloader=False,
    )
