# EGX Scanner — ماسح فرص البورصة المصرية

موقع وأداة بايثون يمسحوا أسهم البورصة المصرية يومياً ويرتبوا أحسن الفرص الفنية بناءً على
**اختراق 20 جلسة + تقاطع MACD + التقاطع الذهبى + ارتداد من تشبع البيع**، مع حساب
سعر الدخول، وقف الخسارة، الأهداف، والمدة المتوقعة بناءً على ATR.

> **تنبيه مهم:** هذه الأداة لا تتنبأ بالمستقبل. هى ترصد توافق إشارات فنية شائعة بين
> المتعاملين وتعرض **نطاقات احتمالية** مبنية على التذبذب التاريخى. نتيجة أى صفقة لا
> تُعرف إلا بعد إغلاقها. تداول على مسؤوليتك ولا تخاطر بأكثر مما تتحمل خسارته.

## ما اللى بتحصل عليه

- **Dashboard أونلاين** على Vercel: أحسن 30 فرصة فى يوم المسح، مع شارت لكل سهم
  وخطة صفقة كاملة (دخول/وقف/هدف 1/هدف 2/مدة متوقعة).
- **حاسبة حجم الصفقة**: تدخل رأس مالك ونسبة المخاطرة، تطلعلك بكام سهم تدخل
  والعمولات الحقيقية لثاندر مأخوذة فى الحسبان.
- **دفتر الصفقات**: تسجل كل صفقة وتعرف نسبة نجاحك الحقيقية (محفوظ محلياً على
  المتصفح).
- **قائمة متابعة** خاصة بيك.
- **Scanner أوتوماتيك** يشتغل كل يوم بعد قفل البورصة عن طريق GitHub Actions
  (مجانى)، يكتب النتايج فى Supabase (مجانى)، والموقع يقرأ منها.

## الـ Stack (كله مجانى)

| الطبقة          | التقنية                                  |
| --------------- | ---------------------------------------- |
| Frontend        | Next.js 15 + Tailwind                    |
| Hosting         | Vercel (Free tier)                       |
| Database        | Supabase Postgres (Free tier)            |
| Scanner         | Python 3.12 (pandas, requests)           |
| Data            | api.investing.com (financialdata public) |
| Cron            | GitHub Actions (Free tier)               |

---

## Quickstart المحلى (5 دقايق)

```powershell
# 1) جرب الـ Scanner من غير ما تنشر حاجة
cd scanner
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python main.py --dry-run --min-score 20

# 2) جرب الموقع محلياً (هيشتغل لكن من غير بيانات لحد ما تربط Supabase)
cd ../web
npm install
npm run dev    # http://localhost:3000
```

---

## الخطوات الكاملة للنشر (~30 دقيقة)

### 1) Supabase — قاعدة البيانات

1. اعمل حساب على [supabase.com](https://supabase.com) → **New Project**.
2. اختار region قريب (Frankfurt مثلاً)، اختار password قوى للـ DB.
3. لما المشروع يجهز، روح **SQL Editor** → **New query** → الصق محتوى ملف
   `supabase/schema.sql` → **Run**.
4. روح **Settings → API** وانسخ:
   - `Project URL` (هتستخدمه فى الـ env)
   - `anon public key` (للموقع)
   - `service_role key` (للـ Scanner — سرى، خليه فى GitHub Secrets فقط)

### 2) GitHub — رفع الكود

```powershell
cd "D:\General Projects\stock-market"
git init
git add .
git commit -m "Initial: EGX scanner + Next.js dashboard"
# اعمل repo فاضى على GitHub.com باسم egx-scanner
git remote add origin https://github.com/YOUR_USER/egx-scanner.git
git branch -M main
git push -u origin main
```

ضِف الـ Secrets فى GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

| Name                        | Value                                |
| --------------------------- | ------------------------------------ |
| `SUPABASE_URL`              | الـ Project URL من Supabase          |
| `SUPABASE_SERVICE_ROLE_KEY` | الـ service_role key (مش anon!)      |

### 3) شغّل الـ Scanner مرة يدوياً (ملو بيانات أولى)

روح GitHub → tab **Actions** → اختار workflow **EGX Scanner** →
**Run workflow** → main → Run.

هياخد دقيقة-دقيقتين، وبعدها هتلاقى البيانات فى جداول Supabase.

> الـ workflow هيشتغل أوتوماتيك كل يوم عمل (الأحد→الخميس) الساعة 3 بتوقيت
> القاهرة. لو عايز تغير التوقيت عدّل الـ cron فى `.github/workflows/scanner.yml`.

### 4) Vercel — نشر الموقع

1. اعمل حساب على [vercel.com](https://vercel.com) واربطه بـ GitHub.
2. **Add New → Project** → اختار repo بتاعك.
3. **Root Directory** = `web` (مهم!).
4. Framework Preset = Next.js (هيتعرف لوحده).
5. تحت **Environment Variables** ضِف:

| Name                              | Value                              |
| --------------------------------- | ---------------------------------- |
| `NEXT_PUBLIC_SUPABASE_URL`        | نفس الـ Project URL                |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`   | الـ anon public key (مش service!)  |

6. **Deploy** → بعد دقيقة هتلاقى لينك زى `egx-scanner.vercel.app`.

---

## بنية المشروع

```
stock-market/
├── README.md
├── .gitignore
├── supabase/
│   └── schema.sql                 ← شغله مرة فى Supabase SQL Editor
├── scanner/                       ← يشتغل على GitHub Actions يومياً
│   ├── requirements.txt
│   ├── main.py                    ← entry point
│   ├── tickers.py                 ← قائمة 43 سهم EGX + IDs
│   ├── fetch.py                   ← investing.com API
│   ├── indicators.py              ← RSI, MACD, MA, ATR
│   ├── signals.py                 ← منطق رصد الفرص + scoring
│   ├── store.py                   ← كتابة Supabase
│   └── .env.example
├── web/                           ← Next.js — يتنشر على Vercel
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           ← فرص اليوم
│   │   │   ├── stock/[symbol]/    ← صفحة تفاصيل سهم + شارت
│   │   │   ├── stocks/            ← كل الأسهم
│   │   │   ├── watchlist/         ← قائمة متابعتى (localStorage)
│   │   │   ├── journal/           ← دفتر الصفقات (localStorage)
│   │   │   └── calculator/        ← حاسبة المخاطرة
│   │   ├── components/
│   │   └── lib/
│   └── .env.example
└── .github/workflows/
    └── scanner.yml                ← cron يومى
```

---

## كيف يشتغل الـ Scoring؟

كل سهم بياخد score من 0 لـ 100 بناءً على عدد الإشارات اللى فعّلت فى نفس اليوم:

| Setup                          | Points | الشرط                                                          |
| ------------------------------ | ------ | -------------------------------------------------------------- |
| `breakout_20d`                 | +30    | إغلاق فوق أعلى 20 جلسة + حجم > +1σ                             |
| `macd_cross_up`                | +20    | MACD histogram انتقل من سالب لموجب                             |
| `golden_cross_20_50`           | +15    | MA20 قطعت MA50 لفوق فى آخر 5 جلسات                             |
| `pullback_bounce`              | +15    | RSI ارتد من <40 → >45 والسهم فوق MA50                          |
| Trend bonus                    | +10    | السعر > MA20 > MA50                                            |
| Volume bonus                   | +10    | حجم تداول > +1.5σ                                              |

الإشارات بتتعرض لما score ≥ 30.

### حساب الدخول/الوقف/الأهداف

كله مبنى على **ATR(14)** — مقياس التذبذب الفعلى للسهم:

- **دخول** = آخر إغلاق
- **وقف خسارة** = الدخول − 1.5 × ATR
- **هدف 1** = الدخول + 2.0 × ATR (نسبة عائد/مخاطرة 1.33:1)
- **هدف 2** = الدخول + 3.5 × ATR (نسبة 2.33:1)
- **مدة متوقعة** = 5/8/12/18 جلسة حسب نسبة ATR للسعر

ده **مش تنبؤ**. ده نطاق منطقى مبنى على إن السهم بيتحرك تاريخياً ضِعف ATR فى أيام،
ومرة ونصف ATR فى الاتجاه المعاكس قبل ما الـ stop يصرف.

---

## القواعد العشرة قبل ما تستخدم الأداة فى صفقات حقيقية

1. **مفيش أداة بتتنبأ بالأسعار.** الإشارات احتمالية، ممكن تخسر فى 40-50% من الصفقات.
2. **ابدأ صغير** — أول شهر-شهرين خاطر بـ 25-50% من رأس مالك بس عشان تختبر.
3. **التزم بوقف الخسارة دايماً**. لو متجوش، النظام مش هيشتغل.
4. **متفتحش أكتر من 3-4 صفقات فى نفس الوقت** برأس مال 20 ألف.
5. **عمولة ثاندر ~0.8% رايح جاى** — السهم لازم يطلع 1% قبل أى ربح.
6. **لو R:R أقل من 1.5:1**، اتجاهل الصفقة حتى لو الـ score عالى.
7. **سجل كل صفقة** فى الـ Journal مع السبب — هتكتشف نقاط ضعفك بنفسك.
8. **إشارة قوية ≠ صفقة مضمونة**. ADIB بـ score 70 ممكن تخسر، COMI بـ score 0 ممكن
   تطلع 10% — السوق متحركش بالمنطق الفنى وحده.
9. **متاجرش بناءً على score من سهم واحد**. شوف ≥ 3 إشارات من setups مختلفة.
10. **الأخبار والإفصاحات بتفوق المؤشرات الفنية** — قبل ما تدخل صفقة شوف صفحة السهم
    على [moe.gov.eg](https://www.moe.gov.eg) و [egx.com.eg](https://www.egx.com.eg).

---

## تطوير الأداة

- **إضافة سهم**: عدّل `scanner/tickers.py`. لقطة الـ ID من
  `https://api.investing.com/api/search/v2/search?q=SYMBOL`.
- **تعديل المؤشرات**: `scanner/indicators.py` (كله pandas نقى، مفيش lib تانى).
- **تعديل منطق الإشارات**: `scanner/signals.py` — `_detect()` و scoring weights.
- **تغيير توقيت التشغيل**: `.github/workflows/scanner.yml` (السطر `cron`).

## مشاكل شائعة

- **الـ Scanner مش بيرجع بيانات**: investing.com عمل rate-limit. زوّد الـ sleep
  فى `main.py` من `0.25` لـ `0.5`.
- **خطأ Supabase RLS**: الـ writes لازم تتم بـ service_role key (مش anon). تأكد من
  GitHub Secret.
- **الموقع شغال لكن فاضى**: متأكد إنك ضفت `NEXT_PUBLIC_SUPABASE_*` فى Vercel
  وعملت Re-deploy؟

---

## الترخيص

استخدم وعدّل بحرية. ممنوع تبيع كاشتراك من غير ما تطورها بشكل ملحوظ.

اللهم بارك. وفقك الله.
#   s t o c k - m a r k e t - s c a n n e r  
 