"""Telegram notifications for the daily action list.

Secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (GitHub Actions secrets / .env).
Never raises — a Telegram hiccup must not fail the data run.
"""

from __future__ import annotations

import html
import os

import requests

SITE_URL = os.environ.get("SITE_URL", "https://stock-market-scanner-teal.vercel.app")
MAX_LEN = 4000  # Telegram hard limit is 4096


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _n(x, nd=2) -> str:
    if x is None:
        return "—"
    return f"{x:,.{nd}f}"


def format_daily_message(latest: dict) -> str:
    date = latest.get("date") or "—"
    label = latest.get("strategy_label_ar") or latest.get("strategy") or ""
    buys = latest.get("buys") or []
    holds = latest.get("holds") or []
    exits = latest.get("exits") or []

    lines = [f"📊 <b>EGX Scanner — جلسة {_esc(date)}</b>", f"<i>{_esc(label)}</i>", ""]

    lines.append(f"🟢 <b>دخول جديد ({len(buys)})</b>")
    if not buys:
        lines.append("لا يوجد — مفيش سهم حقق شروط الدخول النهاردة.")
    for s in buys:
        name = (s.get("stock") or {}).get("name_ar") or s["symbol"]
        tps = " / ".join(_n(t) for t in (s.get("target_1"), s.get("target_2"), s.get("target_3")) if t)
        lines.append(
            f"• <b>{_esc(s['symbol'])}</b> {_esc(name)} — ادخل ≤ <b>{_n(s['entry'])}</b> "
            f"| وقف {_n(s['stop_loss'])} | أهداف {tps} "
            f"| {s.get('suggested_shares_20k') or 0} سهم (~{_n(s.get('suggested_value_20k'), 0)} ج) "
            f"| ثقة {s.get('confidence')}%"
        )
    lines.append("")

    lines.append(f"🔵 <b>استمر ({len(holds)})</b>")
    if not holds:
        lines.append("مفيش مراكز مفتوحة.")
    for h in holds:
        name = h.get("name_ar") or h["symbol"]
        if h["status"] == "pending":
            lines.append(f"• <b>{_esc(h['symbol'])}</b> {_esc(name)} — ينفذ الدخول عند افتتاح الجلسة القادمة")
            continue
        chg = h.get("change_pct")
        chg_s = f"{chg:+.1f}%" if chg is not None else "—"
        hits = "".join("✓" if x else "·" for x in (h.get("tp_hit") or []))
        lines.append(
            f"• <b>{_esc(h['symbol'])}</b> {_esc(name)} — دخلت {_n(h['entry'])} | الآن {_n(h['last_close'])} ({chg_s}) "
            f"| وقف {_n(h['stop'])} (−{_n(h.get('stop_distance_pct'), 1)}%) | أهداف {hits} | {h['bars_held']} جلسة"
        )
        if h.get("pending_exit"):
            lines.append(f"   {_esc(h.get('note_ar'))}")
    lines.append("")

    lines.append(f"🔴 <b>اخرج ({len(exits)})</b>")
    if not exits:
        lines.append("لا يوجد.")
    for e in exits:
        name = e.get("name_ar") or e["symbol"]
        r = e.get("realized_r")
        pnl = e.get("realized_pnl")
        lines.append(
            f"• <b>{_esc(e['symbol'])}</b> {_esc(name)} — خرج {_n(e.get('exit_price'))} | {_esc(e.get('reason_ar'))} "
            f"| {r:+.2f}R ({pnl:+,.0f} ج)" if r is not None and pnl is not None else
            f"• <b>{_esc(e['symbol'])}</b> {_esc(name)} — {_esc(e.get('reason_ar'))}"
        )
    lines.append("")
    lines.append(f"🔗 {SITE_URL}")
    lines.append("⚠️ للأغراض التعليمية فقط — مش نصيحة استثمارية. التزم بالوقف.")
    return "\n".join(lines)


def _chunks(text: str, limit: int = MAX_LEN) -> list[str]:
    if len(text) <= limit:
        return [text]
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur:
        out.append(cur)
    return out


def send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("(telegram: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — skipping)")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    ok = True
    for part in _chunks(text):
        try:
            r = requests.post(
                url,
                json={"chat_id": chat_id, "text": part, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=15,
            )
            if r.status_code != 200:
                print(f"  ⚠ telegram {r.status_code}: {r.text[:160]}")
                ok = False
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ telegram error: {str(e)[:120]}")
            ok = False
    if ok:
        print("telegram: sent")
    return ok
