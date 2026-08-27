# EGX Scanner — قرارات يومية للبورصة المصرية (Swing Trading)

أداة بتقولك كل يوم بعد الإقفال: **ادخل إيه، استمر فى إيه، واخرج من إيه** — بسعر دخول ووقف
وأهداف وحجم صفقة لرأس مال 20 ألف جنيه، وتبعتلك رسالة تليجرام. الاستراتيجية المُفعّلة هى
اللى كسبت فى **backtest على 5 سنين بعد عمولة ثاندر**، والأرقام كلها معروضة فى صفحة الأداء.

> **تنبيه:** الأداة تعليمية وليست نصيحة استثمارية. الأداء السابق لا يضمن المستقبل. أى
> استراتيجية بتخسر صفقات — الفكرة إن المتوسط موجب بعد العمولة **مع التزام صارم بالوقف**.

الموقع: https://stock-market-scanner-teal.vercel.app

## إزاى شغالة (من غير أى قاعدة بيانات)

```
Yahoo Finance (COMI.CA …) ──► scanner/main.py ──► web/public/data/*.json ──► git commit ──► Vercel
       5 سنين شموع يومية        الاستراتيجية + المحفظة الورقية      (GitHub Actions)        الموقع
                                        │
                                        └──► Telegram (دخول / استمر / اخرج)
```

- **البيانات:** Yahoo Finance بيخدم البورصة المصرية بلاحقة `.CA` (42 سهم، 5 سنين). الأسهم اللى
  عملت تجزئة/منحة بيتم تصحيحها تلقائياً (`scanner/series.py`).
- **التخزين:** ملفات JSON فى `web/public/data/` بيكتبها الـ Actions ويعمل commit — مستحيل
  "تتوقف" زى قواعد البيانات المجانية.
- **الاستراتيجيات** (`scanner/strategies/`):
  | الاسم | الفكرة |
  |---|---|
  | `kalman_supertrend` | سكريبت "Hytham Sherif Pro Scalper" متحول من Pine Script: فلتر كالمان + سوبرترند، دخول عند انقلاب الاتجاه، وقف = خط السوبرترند، 3 أهداف عند 0.5/1.0/1.5 R |
  | `kalman_ma200` | نفس الإشارات لكن فوق متوسط 200 يوم فقط |
  | `kalman_ride` | نفس الإشارات بدون أهداف — خروج عند انقلاب الاتجاه |
  | `current_scoring` | النظام القديم: اختراق 20 جلسة + MACD + تقاطع ذهبى + ارتداد RSI |
- **الـ Backtest** (`scanner/backtest/`): دخول على افتتاح اليوم التالى، الوقف قبل الأهداف،
  عمولة 0.4% لكل طرف، انزلاق 0.1%، حساب 20 ألف بحد أقصى 4 مراكز. النتائج مقسومة
  داخل/خارج العينة، والاستراتيجية المُفعّلة بتتحدد أوتوماتيك = أعلى عائد/تراجع **خارج
  العينة** (`web/public/data/backtest/index.json → recommended`).
- **المحفظة الورقية** (`scanner/positions.py`): كل إشارة بتتحول لمركز بيتدار بنفس قواعد
  الـ backtest بالظبط، وده اللى بيطلّع قسم "استمر" و"اخرج".

## التشغيل المحلى

```powershell
cd scanner
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

.\.venv\Scripts\python main.py --dry-run          # يجيب البيانات ويطبع من غير كتابة
.\.venv\Scripts\python main.py                    # يكتب web/public/data/*.json
.\.venv\Scripts\python main.py --no-fetch --notify  # من الكاش + معاينة رسالة تليجرام
.\.venv\Scripts\python -m backtest.run            # يعيد تقييم كل الاستراتيجيات
.\.venv\Scripts\python -m tests.test_kalman       # اختبارات
.\.venv\Scripts\python -m tests.test_positions

cd ../web
npm install
npm run dev     # http://localhost:3000
```

## الإعداد على GitHub (مرة واحدة)

1. **Settings → Actions → General → Workflow permissions → Read and write** (عشان الـ Actions
   يقدر يعمل commit للبيانات).
2. **Settings → Secrets and variables → Actions:**
   | Secret | القيمة |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | من @BotFather → `/newbot` |
   | `TELEGRAM_CHAT_ID` | ابعت رسالة للبوت ثم افتح `https://api.telegram.org/bot<TOKEN>/getUpdates` وخد `chat.id` |
3. Vercel: Root Directory = `web`، من غير أى Environment Variables.

الـ workflows:
- `scanner.yml` — 3 مرات يومياً (Yahoo بينشر شمعة اليوم مساءً): 19:00 و22:30 القاهرة +
  08:30 صباحاً كاحتياط. بيعمل commit لو البيانات اتغيرت بس، وبيبعت تليجرام لما تاريخ
  البيانات يتقدم.
- `backtest.yml` — كل جمعة: اختبارات + إعادة تقييم الاستراتيجيات + commit.

## بنية المشروع

```
scanner/
  main.py            ← التشغيل اليومى: بيانات → إشارات → مراكز → JSON → تليجرام
  fetch.py           ← Yahoo Finance + كاش JSON
  series.py          ← تصحيح التجزئة/المنح غير المعدّلة
  indicators.py      ← RSI/MACD/ATR/MA (pandas خام)
  signals.py         ← الطبقة "الخبيرة": تصنيف المخاطرة، الثقة، حجم الصفقة، الشرح بالعربى
  strategies/        ← base.py + current_scoring.py + kalman_supertrend.py
  backtest/          ← engine.py (المحاكاة) + metrics.py + run.py
  positions.py       ← المحفظة الورقية (ادخل/استمر/اخرج)
  notify.py          ← تليجرام
  store_json.py / paths.py
  tests/
web/
  public/data/       ← "قاعدة البيانات": stocks, prices/{SYM}, latest, positions, trades_live, backtest/
  src/app/           ← اليوم / المراكز / الأداء / الأسهم / متابعتى / دفتر الصفقات / الحاسبة / stock/[symbol]
  src/lib/data.ts    ← قراءة JSON (build-time)
  src/lib/kalman.ts  ← نسخة TypeScript من السوبرترند لرسم الشارت
  src/components/    ← candles-chart (lightweight-charts), position-card, exit-card, ...
recommended-scripts.txt ← سكريبت Pine الأصلى (المرجع)
```

## قواعد الاستخدام

1. افتح الموقع (أو اقرأ رسالة تليجرام) مرة واحدة بعد الإقفال ونفّذ القرارات على افتتاح الجلسة
   التالية.
2. الوقف مش اختيارى — كل أرقام الأداء محسوبة بافتراض الخروج عليه.
3. حد أقصى 4 مراكز مفتوحة برأس مال 20 ألف، و2% مخاطرة لكل صفقة.
4. سجّل صفقاتك الحقيقية فى دفتر الصفقات وقارنها بالمحفظة الورقية.
