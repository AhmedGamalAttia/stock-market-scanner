# EGX Data Proxy — Cloudflare Worker

Forwards EGX OHLCV requests to investing.com **from Cloudflare's own network**,
bypassing the bot blocks Cloudflare puts on cloud IPs (Azure / GitHub Actions / etc).

**Cost:** $0 — Cloudflare Workers free tier = 100,000 requests/day. Scanner uses 43.

## نشر الـ Worker (مرة واحدة، 5 دقايق)

### 1) سجّل على Cloudflare (مجاناً)
- روح [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
- اعمل حساب — مفيش بطاقة ائتمان مطلوبة

### 2) ثبّت Wrangler (CLI بتاع Cloudflare)
من PowerShell، فى أى مكان:
```powershell
npm install -g wrangler
```

### 3) سجّل دخول Wrangler
```powershell
cd "D:\General Projects\stock-market\cloudflare-worker"
wrangler login
```
هيفتحلك المتصفح للموافقة → اضغط Allow → ارجع للـ terminal.

### 4) عيّن أول subdomain (لو دى أول مرة)
أول deploy هيسألك تختار subdomain شخصى لك (زى `ahmedgamal.workers.dev`). اختار اسم وخلاص.

### 5) عيّن PROXY_TOKEN كـ secret
ده الـ shared secret اللى بيحمى الـ Worker من إن أى حد يستخدمه. اختار أى string عشوائى طويل (مثال: `egx-secret-x8k2q9vm3p1n`):

```powershell
wrangler secret put PROXY_TOKEN
```
Wrangler هيطلب منك القيمة → ألصقها → Enter.

> **خد copy للقيمة دى** — هتستخدمها فى GitHub Secrets كمان.

### 6) Deploy
```powershell
wrangler deploy
```

هيطلعلك URL للـ Worker، شكله:
```
https://egx-data-proxy.YOUR-SUBDOMAIN.workers.dev
```
**خد copy للـ URL ده.**

### 7) جرّبه
افتح فى المتصفح:
```
https://egx-data-proxy.YOUR-SUBDOMAIN.workers.dev/health
```
لازم يرجع: `{"ok":true,"worker":"egx-data-proxy"}`

---

## استخدام الـ Worker من الـ Scanner

ضِف الاتنين دول كـ **GitHub Repository Secrets**:

| Name | Value |
|------|-------|
| `CLOUDFLARE_PROXY_URL` | الـ URL من خطوة 6 (مثال: `https://egx-data-proxy.YOUR-SUBDOMAIN.workers.dev`) |
| `CLOUDFLARE_PROXY_TOKEN` | نفس قيمة الـ PROXY_TOKEN من خطوة 5 |

والـ scanner هيستخدمه أوتوماتيك. الـ workflow بيمرّر القيمتين كـ env vars.

---

## كيف يشتغل؟

```
GitHub Actions (Azure IP — محجوب من investing.com)
        ↓ (طلب مع X-Proxy-Token)
Cloudflare Worker (IP بتاع Cloudflare نفسها)
        ↓ (طلب مع نفس headers المتصفح)
investing.com (Cloudflare-protected — بيقبل لأن الـ Worker على نفس الشبكة)
        ↓ (JSON OHLCV)
Cloudflare Worker → GitHub Actions → Supabase
```

## مشاكل شائعة

- **`unauthorized`** → الـ token اللى بتبعته من scanner مش مطابق للـ secret على الـ Worker. تأكد إنهم نفس القيمة بالظبط.
- **`PROXY_TOKEN not configured on worker`** → نسيت تشغل `wrangler secret put PROXY_TOKEN`.
- **`ENOENT wrangler`** → ما ثبّتش wrangler. شغل `npm install -g wrangler`.

## تعديل + إعادة نشر
عدّل `worker.js` ثم:
```powershell
wrangler deploy
```
خلاص. التغييرات live خلال ثوانى.

## مراقبة (live tail)
```powershell
wrangler tail
```
هيعرضلك كل request بتيجى للـ Worker فى الوقت الفعلى.
