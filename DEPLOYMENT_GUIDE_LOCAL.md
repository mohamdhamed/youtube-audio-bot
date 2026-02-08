# دليل النشر على السيرفر الشخصي (Local Server)

بما أن لديك سيرفر محلي (`192.168.1.10`) ومستودع GitHub، فهذه هي أسرع طريقة للنشر:

## 1. تحديث الكود على GitHub
أولاً، ارفع التعديلات التي قمنا بها إلى GitHub:
```bash
git add .
git commit -m "Update bot features and deployment files"
git push origin main
```

## 2. الدخول للسيرفر وتجهيز المجلد
ادخل على السيرفر عن طريق SSH (من جهازك):
```bash
ssh user@192.168.1.10
# (استبدل user باسم المستخدم الخاص بك)
```

ثم انسخ المشروع (إذا لم يكن موجوداً):
```bash
git clone https://github.com/mohamdhamed/youtube-audio-bot.git
cd youtube-audio-bot
```
أو حدثه إذا كان موجوداً:
```bash
cd youtube-audio-bot
git pull origin main
```

## 3. نقل الملفات السرية (المهمة جداً!)
الملفات التالية **لا** يتم رفعها على GitHub للحفاظ على سريتها، لذا يجب نقلها يدوياً من جهازك للسيرفر.
افتح نافذة Terminal جديدة (على جهازك أنت وليس السيرفر) ونفذ هذا الأمر:

```bash
scp .env user@192.168.1.10:~/youtube-audio-bot/
scp oauth_credentials.json user@192.168.1.10:~/youtube-audio-bot/
scp credentials.json user@192.168.1.10:~/youtube-audio-bot/
scp token.pickle user@192.168.1.10:~/youtube-audio-bot/
```
*(تأكد من تعديل المسار `~/youtube-audio-bot/` إذا كنت وضعت المشروع في مكان آخر)*

## 4. التشغيل
الآن ارجع لشاشة السيرفر (SSH) وشغل البوت باستخدام Docker:

```bash
docker compose up -d --build
```

## 5. التحديث مستقبلاً
إذا عدلت أي كود، فقط:
1. `git push` من جهازك.
2. `git pull` في السيرفر.
3. `docker compose up -d --build` في السيرفر.
