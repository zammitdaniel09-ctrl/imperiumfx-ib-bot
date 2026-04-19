import asyncio
import re
import sqlite3
import time
import html
import traceback
import logging
from datetime import datetime, timezone, timedelta
from functools import wraps

# Python 3.14 workaround
asyncio.set_event_loop(asyncio.new_event_loop())

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===================================================================
# CONFIG (kept hardcoded as requested)
# ===================================================================
BOT_TOKEN = "8085633137:AAEM6MOSPirix26Bs4Ye9wqryX063L-FO60"
ADMIN_CHAT_ID = -1003919089074  # supergroup format with -100 prefix

IB_LINK = "https://www.puprime.partners/forex-trading-account/?affid=MjMyMTMwODY="
IB_CODE = "pOenf2oC"
IB_ACCOUNT_NUMBER = "23213086"
TUTORIAL_PDF = "IB_E_BOOK.pdf"
TRANSFER_EMAIL_1 = "aleksandra.stojkovic@puprime.com"
TRANSFER_EMAIL_2 = "info@puprime.com"
SOLANA_ADDRESS = "GrSbxLK1Z6ZgEhEtViY4ibLEq7xYuXiuGCxVFYjzwazt"
ETHEREUM_ADDRESS = "0x2474F60027Fda971aaA773031f07Fd58F3e14627"
BTC_ADDRESS = "bc1pzzz24czpr9yem4st5p727gcm30fw6c6yfnt07pypr6esxu56092smassch"

DB_PATH = "bot.db"

# Admin team roster
ADMINS = {
    "apollo": {
        "username": "ApolloFX9",
        "label": "Apollo (Right-Hand Admin)",
        "role": "general",
    },
    "plato": {
        "username": "PlatoFX9",
        "label": "Plato (Signal Provider / Admin)",
        "role": "signals",
    },
    "hd": {
        "username": "HD_lFX",
        "label": "HD (Socials / Agent)",
        "role": "socials",
    },
}

SOCIALS = [
    ("📸 Instagram — @imperiumxaufx", "https://www.instagram.com/imperiumxaufx"),
    ("🎵 TikTok — @kratosxaufx", "https://www.tiktok.com/@kratosxaufx"),
]

FAQ = [
    (
        "faq_1",
        "What is VIP access?",
        "<b>VIP access</b> gives you our private signals, setups and trade calls. "
        "Free VIP requires you to come under our IB and deposit. "
        "Paid VIP (funded) is direct access for funded account traders.",
    ),
    (
        "faq_2",
        "What is an IB?",
        "An <b>IB (Introducing Broker)</b> means your trading account is registered or "
        "transferred under our partner code. We earn a small commission from your "
        "spread — at <b>no extra cost to you</b> — and in return you get free VIP access.",
    ),
    (
        "faq_3",
        "How long does review take?",
        "Reviews are <b>usually within 24 hours</b>. If it's been longer, press "
        "<b>Contact Support</b> and an admin will follow up.",
    ),
    (
        "faq_4",
        "Why didn't my UID get accepted?",
        "Common reasons: account is not under our IB code, no deposit yet, "
        "or wrong UID format. Make sure you used code <code>" + IB_CODE + "</code>, "
        "deposited, and submitted in this exact format: <code>UID: 12345678</code>",
    ),
    (
        "faq_5",
        "How much does Funded VIP cost?",
        "<b>€50</b> for the first month, then <b>€80</b>/month. "
        "Payable in BTC, ETH or SOL. After payment, send proof with caption "
        "<code>PAYMENT: FUNDED</code>.",
    ),
    (
        "faq_6",
        "Is there a minimum deposit?",
        "PU Prime sets the minimum deposit. We recommend at least <b>$200</b> "
        "for a meaningful position size and to qualify smoothly for VIP.",
    ),
]

# Simple in-memory rate limit (per-user)
_LAST_ACTION = {}
RATE_LIMIT_SECONDS = 0.6

# ===================================================================
# LOGGING
# ===================================================================
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("imperiumfx-bot")


# ===================================================================
# DATABASE
# ===================================================================
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    conn = db()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            full_name      TEXT,
            first_seen     TEXT,
            last_seen      TEXT,
            referrer       TEXT,
            main_path      TEXT,
            vip_mode       TEXT,
            flow           TEXT,
            vip_submitted  INTEGER DEFAULT 0,
            vip_uid        TEXT,
            vip_status     TEXT DEFAULT 'pending',
            vip_decision_at TEXT,
            aff_submitted  INTEGER DEFAULT 0,
            aff_uid        TEXT,
            aff_status     TEXT DEFAULT 'pending',
            aff_decision_at TEXT,
            funded_paid_at TEXT,
            funded_status  TEXT DEFAULT 'none',
            funded_renew_at TEXT,
            blocked        INTEGER DEFAULT 0,
            started_at     TEXT,
            deposited_at   TEXT
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            event     TEXT,
            data      TEXT,
            ts        TEXT
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS uid_registry (
            uid        TEXT PRIMARY KEY,
            user_id    INTEGER,
            kind       TEXT,
            ts         TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def upsert_user(user, referrer=None):
    conn = db()
    c = conn.cursor()
    username = user.username or ""
    full_name = user.full_name or ""
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    row = c.fetchone()
    if row is None:
        c.execute(
            """INSERT INTO users (user_id, username, full_name, first_seen, last_seen, referrer, started_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user.id, username, full_name, now_iso(), now_iso(), referrer, now_iso()),
        )
    else:
        c.execute(
            "UPDATE users SET username=?, full_name=?, last_seen=? WHERE user_id=?",
            (username, full_name, now_iso(), user.id),
        )
    conn.commit()
    conn.close()


def update_user(user_id, **fields):
    if not fields:
        return
    keys = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [user_id]
    conn = db()
    conn.execute(f"UPDATE users SET {keys} WHERE user_id=?", vals)
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row


def is_blocked(user_id):
    row = get_user(user_id)
    return bool(row and row["blocked"])


def log_event(user_id, event, data=""):
    conn = db()
    conn.execute(
        "INSERT INTO events (user_id, event, data, ts) VALUES (?, ?, ?, ?)",
        (user_id, event, data, now_iso()),
    )
    conn.commit()
    conn.close()


def register_uid(uid, user_id, kind):
    """Returns (ok, existing_user_id_or_None)."""
    conn = db()
    row = conn.execute("SELECT user_id FROM uid_registry WHERE uid=?", (uid,)).fetchone()
    if row and row["user_id"] != user_id:
        conn.close()
        return False, row["user_id"]
    if row is None:
        conn.execute(
            "INSERT INTO uid_registry (uid, user_id, kind, ts) VALUES (?, ?, ?, ?)",
            (uid, user_id, kind, now_iso()),
        )
        conn.commit()
    conn.close()
    return True, None


def stats_snapshot():
    conn = db()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    started = c.execute("SELECT COUNT(*) AS n FROM users WHERE started_at IS NOT NULL").fetchone()["n"]
    vip_pending = c.execute("SELECT COUNT(*) AS n FROM users WHERE vip_submitted=1 AND vip_status='pending'").fetchone()["n"]
    vip_approved = c.execute("SELECT COUNT(*) AS n FROM users WHERE vip_status='approved'").fetchone()["n"]
    vip_rejected = c.execute("SELECT COUNT(*) AS n FROM users WHERE vip_status='rejected'").fetchone()["n"]
    aff_pending = c.execute("SELECT COUNT(*) AS n FROM users WHERE aff_submitted=1 AND aff_status='pending'").fetchone()["n"]
    aff_approved = c.execute("SELECT COUNT(*) AS n FROM users WHERE aff_status='approved'").fetchone()["n"]
    funded_active = c.execute("SELECT COUNT(*) AS n FROM users WHERE funded_status='active'").fetchone()["n"]
    blocked = c.execute("SELECT COUNT(*) AS n FROM users WHERE blocked=1").fetchone()["n"]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    new_24h = c.execute("SELECT COUNT(*) AS n FROM users WHERE first_seen>=?", (cutoff,)).fetchone()["n"]
    conn.close()
    return {
        "total": total,
        "started": started,
        "new_24h": new_24h,
        "vip_pending": vip_pending,
        "vip_approved": vip_approved,
        "vip_rejected": vip_rejected,
        "aff_pending": aff_pending,
        "aff_approved": aff_approved,
        "funded_active": funded_active,
        "blocked": blocked,
    }


# ===================================================================
# HELPERS
# ===================================================================
def is_admin_chat(update: Update) -> bool:
    """Return True if the update originates from the admin chat.
    The admin chat is used for logs and admin commands only — the regular
    bot flow must not run there."""
    chat = update.effective_chat
    if chat is None:
        return False
    return chat.id == ADMIN_CHAT_ID


def admin_only(func):
    """Decorator: command only works in the admin chat. Silently ignore otherwise."""
    @wraps(func)
    async def wrapper(update, context, *a, **kw):
        if not is_admin_chat(update):
            return
        return await func(update, context, *a, **kw)
    return wrapper


def rate_limited(user_id) -> bool:
    now = time.time()
    last = _LAST_ACTION.get(user_id, 0)
    _LAST_ACTION[user_id] = now
    return (now - last) < RATE_LIMIT_SECONDS


async def try_react(update, context, emoji="👍"):
    """Best-effort emoji reaction. Silently no-op on older PTB versions."""
    try:
        msg = update.effective_message
        if msg is None:
            return
        await context.bot.set_message_reaction(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            reaction=emoji,
        )
    except Exception:
        pass


def parse_uid_submission(text: str):
    if not text:
        return None
    text = text.strip()
    match = re.fullmatch(r"UID:\s*(\d{5,20})", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def parse_payment_submission(text: str):
    if not text:
        return None
    text = text.strip()
    match = re.fullmatch(r"PAYMENT:\s*FUNDED", text, flags=re.IGNORECASE)
    if not match:
        return None
    return "FUNDED"


def uid_format_guide():
    return (
        "<b>Invalid UID format.</b>\n\n"
        "Send your UID in this exact format:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Rules:</b>\n"
        "• must start with <code>UID:</code>\n"
        "• numbers only after that\n"
        "• no extra words\n"
        "• no spaces before UID\n\n"
        "<i>Example:</i> <code>UID: 123517235</code>"
    )


def payment_format_guide():
    return (
        "<b>Invalid payment proof format.</b>\n\n"
        "If you send payment proof, the caption must be exactly:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    )


# ===================================================================
# MENUS
# ===================================================================
def start_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join VIP Access", callback_data="vip_access")],
        [InlineKeyboardButton("💼 Become an IB Affiliate", callback_data="ib_affiliate")],
        [InlineKeyboardButton("👥 Meet the Team", callback_data="team"),
         InlineKeyboardButton("📲 Follow Us", callback_data="socials")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq"),
         InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
    ])


def confirm_restart_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, restart", callback_data="restart_yes"),
         InlineKeyboardButton("❌ No, keep progress", callback_data="restart_no")],
    ])


def vip_entry_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆓 Free VIP", callback_data="vip_free")],
        [InlineKeyboardButton("💳 Paid VIP", callback_data="vip_paid")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_start")],
    ])


def vip_free_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 New to PU Prime", callback_data="vip_new")],
        [InlineKeyboardButton("🔁 Already with PU Prime", callback_data="vip_existing")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="vip_access")],
    ])


def vip_paid_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Live Account", callback_data="vip_paid_live")],
        [InlineKeyboardButton("🏦 Funded Account", callback_data="vip_paid_funded")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="vip_access")],
    ])


def affiliate_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 I don't know what IB is", callback_data="what_is_ib")],
        [InlineKeyboardButton("✅ I already know, continue", callback_data="affiliate_main")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_start")],
    ])


def ib_pdf_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Continue", callback_data="affiliate_main")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="ib_affiliate")],
    ])


def affiliate_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 New to PU Prime", callback_data="flow_new")],
        [InlineKeyboardButton("🔁 Already with PU Prime", callback_data="flow_existing")],
        [InlineKeyboardButton("💼 IB Benefits", callback_data="benefits")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_start")],
    ])


def vip_new_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Step 1: Register with PU Prime", url=IB_LINK)],
        [InlineKeyboardButton("✅ Step 2: I Completed Registration", callback_data="vip_registered")],
        [InlineKeyboardButton("💰 Step 3: I Deposited", callback_data="vip_deposit_done")],
        [InlineKeyboardButton("📩 Step 4: Submit UID", callback_data="submit_uid_vip")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="vip_free")],
    ])


def vip_existing_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Step 1: View Transfer Email", callback_data="vip_transfer_email")],
        [InlineKeyboardButton("📨 Step 2: I Sent the Email", callback_data="vip_sent_transfer")],
        [InlineKeyboardButton("💰 Step 3: I Deposited", callback_data="vip_existing_deposit_done")],
        [InlineKeyboardButton("📩 Step 4: Submit UID", callback_data="submit_uid_vip")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="vip_free")],
    ])


def funded_payment_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("₿ View BTC Address", callback_data="show_btc")],
        [InlineKeyboardButton("Ξ View ETH Address", callback_data="show_eth")],
        [InlineKeyboardButton("◎ View SOL Address", callback_data="show_sol")],
        [InlineKeyboardButton("📤 I Sent Payment", callback_data="funded_payment_sent")],
        [InlineKeyboardButton("📎 Submit Payment Proof", callback_data="submit_payment_proof")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="vip_paid")],
    ])


def funded_review_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Waiting for Payment Review", callback_data="funded_waiting_review")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")],
    ])


def new_user_step_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Step 1: Start Registration", url=IB_LINK)],
        [InlineKeyboardButton("✅ Step 2: I Completed Registration", callback_data="completed_registration")],
        [InlineKeyboardButton("📩 Step 3: Submit UID", callback_data="submit_uid_affiliate")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="affiliate_main")],
    ])


def existing_user_step_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Step 1: View Transfer Email", callback_data="transfer_email_template")],
        [InlineKeyboardButton("📨 Step 2: I Sent the Email", callback_data="sent_transfer_email")],
        [InlineKeyboardButton("📩 Step 3: Submit UID", callback_data="submit_uid_affiliate")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back", callback_data="affiliate_main")],
    ])


def back_to_start():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")]
    ])


def back_to_affiliate_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back to Affiliate Menu", callback_data="affiliate_main")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
    ])


def back_to_vip_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back to VIP Menu", callback_data="vip_access")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
    ])


def vip_submitted_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Waiting for Review", callback_data="vip_waiting_review")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")],
    ])


def affiliate_submitted_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Waiting for Review", callback_data="affiliate_waiting_review")],
        [InlineKeyboardButton("🛠 Contact Support", callback_data="support")],
        [InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")],
    ])


def team_menu():
    rows = []
    for info in ADMINS.values():
        rows.append([InlineKeyboardButton(
            f"💬 Message {info['label']}",
            url=f"https://t.me/{info['username']}",
        )])
    rows.append([InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")])
    return InlineKeyboardMarkup(rows)


def socials_menu():
    rows = [[InlineKeyboardButton(label, url=url)] for label, url in SOCIALS]
    rows.append([InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")])
    return InlineKeyboardMarkup(rows)


def faq_menu():
    rows = [[InlineKeyboardButton(f"❓ {q[1]}", callback_data=q[0])] for q in FAQ]
    rows.append([InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")])
    return InlineKeyboardMarkup(rows)


def support_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Onboarding / General — Apollo",
                              url=f"https://t.me/{ADMINS['apollo']['username']}")],
        [InlineKeyboardButton("📊 Signals — Plato",
                              url=f"https://t.me/{ADMINS['plato']['username']}")],
        [InlineKeyboardButton("📲 Socials — HD",
                              url=f"https://t.me/{ADMINS['hd']['username']}")],
        [InlineKeyboardButton("⬅ Back to Start", callback_data="back_start")],
    ])


def admin_review_menu(user_id, kind):
    """Inline buttons for the admin chat to action a submission."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"adm:app:{kind}:{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"adm:rej:{kind}:{user_id}"),
        ],
        [InlineKeyboardButton("⛔ Block User", callback_data=f"adm:blk:{user_id}")],
    ])


# ===================================================================
# ADMIN NOTIFY
# ===================================================================
async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception as e:
        log.warning("notify_admin failed: %s", e)


# ===================================================================
# /start, /help, /status
# ===================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    user = update.effective_user
    if is_blocked(user.id):
        return

    # Pull referral payload (e.g. /start ref_apollo)
    referrer = None
    if context.args:
        ref = " ".join(context.args).strip()
        if re.match(r"^[A-Za-z0-9_\-]{1,32}$", ref):
            referrer = ref

    upsert_user(user, referrer=referrer)
    log_event(user.id, "start", referrer or "")

    # Restart protection — ask before wiping mid-flow progress
    if context.user_data and any(context.user_data.values()):
        await update.message.reply_text(
            "<b>You already have progress in the bot.</b>\n\n"
            "Do you want to <b>restart</b> from the beginning, or keep your current progress?",
            reply_markup=confirm_restart_menu(),
            parse_mode="HTML",
        )
        return

    context.user_data.clear()
    text = (
        "<b>Welcome to ImperiumFX Setup</b>\n\n"
        "Choose your path below.\n\n"
        "• <b>VIP Access</b> — join our VIP signal access\n"
        "• <b>IB Affiliate</b> — become an affiliate and follow the IB onboarding process\n"
        "• <b>Meet the Team</b> — see who runs ImperiumFX\n"
        "• <b>Follow Us</b> — Instagram & TikTok\n"
        "• <b>FAQ</b> — quick answers to common questions\n\n"
        "<i>Please choose the option that matches what you want.</i>"
    )
    await update.message.reply_text(text, reply_markup=start_menu(), parse_mode="HTML")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    await update.message.reply_text(
        "<b>ImperiumFX Bot — Help</b>\n\n"
        "• /start — open the main menu\n"
        "• /status — see where you are in the process\n"
        "• /help — show this message\n\n"
        "If you get stuck, press <b>Contact Support</b> from any menu.",
        parse_mode="HTML",
        reply_markup=back_to_start(),
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    user = update.effective_user
    row = get_user(user.id)
    if not row:
        await update.message.reply_text(
            "No record found yet. Press /start to begin.",
            parse_mode="HTML",
        )
        return
    parts = [
        "<b>Your status</b>",
        f"Path: <b>{row['main_path'] or '—'}</b>",
        f"Flow: <b>{row['flow'] or '—'}</b>",
        f"VIP submitted: <b>{'yes' if row['vip_submitted'] else 'no'}</b>"
        + (f" (status: {row['vip_status']})" if row['vip_submitted'] else ""),
        f"Affiliate submitted: <b>{'yes' if row['aff_submitted'] else 'no'}</b>"
        + (f" (status: {row['aff_status']})" if row['aff_submitted'] else ""),
    ]
    if row["funded_status"] and row["funded_status"] != "none":
        parts.append(f"Funded VIP: <b>{row['funded_status']}</b>")
    await update.message.reply_text(
        "\n".join(parts),
        parse_mode="HTML",
        reply_markup=back_to_start(),
    )


# ===================================================================
# BUTTON HANDLER (user flow + admin review buttons)
# ===================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    data = query.data or ""

    # ---------- Admin chat: ONLY admin review actions allowed ----------
    if is_admin_chat(update):
        if data.startswith("adm:"):
            await admin_action(update, context)
            return
        try:
            await query.answer()
        except Exception:
            pass
        return

    # ---------- Normal user flow ----------
    user = query.from_user
    if is_blocked(user.id):
        try:
            await query.answer("Access disabled. Contact support.", show_alert=True)
        except Exception:
            pass
        return

    if rate_limited(user.id):
        try:
            await query.answer("Slow down 🙂")
        except Exception:
            pass
        return

    await query.answer()
    upsert_user(user)
    username = f"@{user.username}" if user.username else "No username"

    # Restart confirmation
    if data == "restart_yes":
        context.user_data.clear()
        await query.message.reply_text(
            "<b>Welcome to ImperiumFX Setup</b>\n\n"
            "Choose your path below.",
            reply_markup=start_menu(),
            parse_mode="HTML",
        )
        return
    if data == "restart_no":
        await query.message.reply_text(
            "Progress kept. Press a button below to continue.",
            reply_markup=start_menu(),
            parse_mode="HTML",
        )
        return

    if data == "back_start":
        context.user_data.clear()
        await query.message.reply_text(
            "<b>Welcome to ImperiumFX Setup</b>\n\n"
            "Choose your path below.\n\n"
            "• <b>VIP Access</b> — join our VIP signal access\n"
            "• <b>IB Affiliate</b> — become an affiliate and follow the IB onboarding process\n\n"
            "<i>Please choose the option that matches what you want.</i>",
            reply_markup=start_menu(),
            parse_mode="HTML",
        )
        return

    # ---------- Team / Socials / FAQ ----------
    if data == "team":
        text = "<b>Meet the Team</b>\n\n"
        for info in ADMINS.values():
            text += f"• <b>{info['label']}</b> — @{info['username']}\n"
        text += "\n<i>Tap a button below to message them directly.</i>"
        await query.message.reply_text(text, reply_markup=team_menu(), parse_mode="HTML")
        return

    if data == "socials":
        await query.message.reply_text(
            "<b>Follow ImperiumFX</b>\n\n"
            "Stay up to date with our latest content, signal previews and giveaways.",
            reply_markup=socials_menu(),
            parse_mode="HTML",
        )
        return

    if data == "faq":
        await query.message.reply_text(
            "<b>Frequently Asked Questions</b>\n\nPick a question below.",
            reply_markup=faq_menu(),
            parse_mode="HTML",
        )
        return

    for fid, fq, fa in FAQ:
        if data == fid:
            await query.message.reply_text(
                f"<b>{html.escape(fq)}</b>\n\n{fa}",
                reply_markup=faq_menu(),
                parse_mode="HTML",
            )
            return

    if data == "vip_access":
        context.user_data["main_path"] = "vip"
        update_user(user.id, main_path="vip")
        await query.message.reply_text(
            "<b>VIP Access</b>\n\n"
            "Choose your VIP route below.\n\n"
            "<b>Free VIP</b>\n"
            "• for users who come under our IB\n"
            "• requires registration/transfer under us and deposit\n\n"
            "<b>Paid VIP</b>\n"
            "• for users who want direct access\n"
            "• funded accounts pay monthly\n\n"
            "<i>Select the option that matches your situation.</i>",
            reply_markup=vip_entry_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_free":
        context.user_data["vip_mode"] = "free"
        update_user(user.id, vip_mode="free")
        await query.message.reply_text(
            "<b>Free VIP</b>\n\n"
            "To qualify, you must do <b>one</b> of the following:\n\n"
            "1. <b>Register with PU Prime under us</b>\n"
            "2. <b>Transfer your existing PU Prime account under us</b>\n\n"
            "<b>Important rules:</b>\n"
            "• You must come under our IB\n"
            "• You must <b>deposit</b>\n"
            "• Without this, <b>free VIP access will not be granted</b>\n\n"
            "<i>Select the option that matches your situation below.</i>",
            reply_markup=vip_free_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_paid":
        context.user_data["vip_mode"] = "paid"
        update_user(user.id, vip_mode="paid")
        await query.message.reply_text(
            "<b>Paid VIP</b>\n\n"
            "Choose the type of account you use.\n\n"
            "<b>Live Account</b>\n"
            "• same structure as free VIP\n"
            "• you must come under our IB and deposit\n\n"
            "<b>Funded Account</b>\n"
            "• <b>€50</b> first month\n"
            "• <b>€80</b> from the next month onward\n\n"
            "<i>Select your account type below.</i>",
            reply_markup=vip_paid_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_paid_live":
        context.user_data["vip_mode"] = "paid_live"
        update_user(user.id, vip_mode="paid_live")
        await query.message.reply_text(
            "<b>Paid VIP — Live Account</b>\n\n"
            "For live accounts, your access is handled through our IB structure.\n\n"
            "That means you must:\n"
            "1. register under us or transfer under us\n"
            "2. deposit\n"
            "3. submit your UID\n\n"
            "<i>Select your route below.</i>",
            reply_markup=vip_free_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_paid_funded":
        context.user_data["vip_mode"] = "paid_funded"
        context.user_data["flow"] = "vip_paid_funded"
        update_user(user.id, vip_mode="paid_funded", flow="vip_paid_funded")
        await query.message.reply_text(
            "<b>Paid VIP — Funded Account</b>\n\n"
            "<b>Pricing:</b>\n"
            "• <b>€50</b> first month\n"
            "• <b>€80</b> from the next month onward\n\n"
            "<b>Payment methods:</b>\n"
            "• BTC\n"
            "• ETH\n"
            "• SOL\n\n"
            "<b>Next step:</b>\n"
            "1. view the wallet address\n"
            "2. send the payment\n"
            "3. submit payment proof\n\n"
            "<i>Use the buttons below.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML",
        )
    elif data == "show_btc":
        await query.message.reply_text(
            "<b>BTC Address</b>\n\n"
            f"<code>{BTC_ADDRESS}</code>\n\n"
            "<i>Tap the address to copy. After sending payment, press I Sent Payment and then submit your proof.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML",
        )
    elif data == "show_eth":
        await query.message.reply_text(
            "<b>ETH Address</b>\n\n"
            f"<code>{ETHEREUM_ADDRESS}</code>\n\n"
            "<i>Tap the address to copy. After sending payment, press I Sent Payment and then submit your proof.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML",
        )
    elif data == "show_sol":
        await query.message.reply_text(
            "<b>SOL Address</b>\n\n"
            f"<code>{SOLANA_ADDRESS}</code>\n\n"
            "<i>Tap the address to copy. After sending payment, press I Sent Payment and then submit your proof.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML",
        )
    elif data == "funded_payment_sent":
        context.user_data["funded_payment_sent"] = True
        log_event(user.id, "funded_payment_sent")
        await query.message.reply_text(
            "<b>Payment marked as sent.</b>\n\n"
            "Now submit your payment proof.\n\n"
            "<b>Important:</b> if you send a screenshot or document, the caption must be:\n\n"
            "<code>PAYMENT: FUNDED</code>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>Funded VIP user says they sent payment</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>VIP Paid Funded</b>"
            ),
        )
    elif data == "submit_payment_proof":
        if context.user_data.get("funded_submitted"):
            await query.message.reply_text(
                "<b>Your payment proof has already been received.</b>\n\n"
                "Please wait for review or contact support if needed.",
                reply_markup=funded_review_menu(),
                parse_mode="HTML",
            )
            return
        if not context.user_data.get("funded_payment_sent"):
            await query.message.reply_text(
                "<b>You must mark payment as sent first.</b>\n\n"
                "Please follow the funded VIP steps in order.",
                reply_markup=funded_payment_menu(),
                parse_mode="HTML",
            )
            return
        context.user_data["awaiting_payment_proof"] = True
        await query.message.reply_text(
            "Send your <b>payment proof</b> now.\n\n"
            "<b>Required caption format:</b>\n"
            "<code>PAYMENT: FUNDED</code>\n\n"
            "<i>Screenshot or document only.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML",
        )
    elif data == "funded_waiting_review":
        await query.message.reply_text(
            "<b>Your funded VIP payment proof is already under review.</b>\n\n"
            "There is nothing else you need to submit right now.\n\n"
            "<i>If you need help, press Contact Support.</i>",
            reply_markup=funded_review_menu(),
            parse_mode="HTML",
        )
    elif data == "ib_affiliate":
        context.user_data["main_path"] = "affiliate"
        update_user(user.id, main_path="affiliate")
        await query.message.reply_text(
            "<b>IB Affiliate Setup</b>\n\n"
            "This path is for users who want to understand the IB model and complete the affiliate onboarding process.\n\n"
            "<i>Choose whether you need the beginner guide or want to continue directly.</i>",
            reply_markup=affiliate_menu(),
            parse_mode="HTML",
        )
    elif data == "what_is_ib":
        await query.message.reply_text(
            "Start with the <b>tutorial PDF</b> below.\n\n"
            "<b>Next step:</b> once you've read it, press <b>Continue</b>.",
            reply_markup=ib_pdf_menu(),
            parse_mode="HTML",
        )
        try:
            with open(TUTORIAL_PDF, "rb") as pdf:
                await query.message.reply_document(document=pdf, caption="IB Tutorial Guide")
        except FileNotFoundError:
            await query.message.reply_text(
                f"Tutorial PDF not found.\n\n"
                f"Put <b>{TUTORIAL_PDF}</b> in the same folder as <b>ib_bot.py</b>.",
                reply_markup=ib_pdf_menu(),
                parse_mode="HTML",
            )
    elif data == "affiliate_main":
        await query.message.reply_text(
            "<b>IB Affiliate Menu</b>\n\nChoose the path that matches your situation.",
            reply_markup=affiliate_main_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_new":
        context.user_data["flow"] = "vip_new"
        update_user(user.id, flow="vip_new")
        await query.message.reply_text(
            "<b>VIP Access — New to PU Prime</b>\n\n"
            "Follow these steps in order:\n\n"
            "1. <b>Register using our link</b>\n"
            f"2. Make sure the code is <b>{IB_CODE}</b>\n"
            "3. Complete registration\n"
            "4. <b>Deposit</b>\n"
            "5. Submit your <b>MT5 UID / account number</b>\n\n"
            "<b>Important:</b>\n"
            "• VIP is only for users who come under us\n"
            "• Registration alone is <b>not enough</b>\n"
            "• You must <b>deposit</b> before access is reviewed\n\n"
            "<i>Complete the steps below carefully.</i>",
            reply_markup=vip_new_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_existing":
        context.user_data["flow"] = "vip_existing"
        update_user(user.id, flow="vip_existing")
        await query.message.reply_text(
            "<b>VIP Access — Existing PU Prime User</b>\n\n"
            "Follow these steps in order:\n\n"
            "1. Send the <b>IB transfer email</b>\n"
            "2. Wait for transfer confirmation\n"
            "3. <b>Deposit</b>\n"
            "4. Submit your <b>MT5 UID / account number</b>\n\n"
            "<b>Important:</b>\n"
            "• Your account must be moved under our IB\n"
            "• You must <b>deposit</b>\n"
            "• Without this, <b>VIP access will not be granted</b>\n\n"
            "<i>Complete the steps below carefully.</i>",
            reply_markup=vip_existing_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_registered":
        context.user_data["vip_registered"] = True
        log_event(user.id, "vip_registered")
        await query.message.reply_text(
            "<b>Registration marked as completed.</b>\n\n"
            "<b>Next requirement:</b> you must now <b>deposit</b> before submitting your UID for VIP review.\n\n"
            "<i>Do not skip this step.</i>",
            reply_markup=vip_new_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>VIP user completed registration</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP New User</b>"
            ),
        )
    elif data == "vip_deposit_done":
        if not context.user_data.get("vip_registered"):
            await query.message.reply_text(
                "<b>You must complete registration first.</b>\n\n"
                "Please follow the steps in order.\n\n"
                "<i>Step 1 must be completed before Step 3.</i>",
                reply_markup=vip_new_menu(),
                parse_mode="HTML",
            )
            return
        context.user_data["vip_deposit_done"] = True
        update_user(user.id, deposited_at=now_iso())
        log_event(user.id, "vip_deposit_done")
        await query.message.reply_text(
            "<b>Deposit marked as completed.</b>\n\n"
            "You can now submit your <b>MT5 UID / account number</b> for VIP review.",
            reply_markup=vip_new_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>VIP user says they deposited</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP New User</b>"
            ),
        )
    elif data == "vip_transfer_email":
        await query.message.reply_text(
            "<b>VIP Transfer Email Template</b>\n\n"
            f"<b>To:</b>\n<code>{TRANSFER_EMAIL_1}</code>\n<code>{TRANSFER_EMAIL_2}</code>\n\n"
            f"<b>Subject:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
            "<b>Body:</b>\n"
            "<code>Hello,\n\n"
            f"Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
            "Full Name: [Your Name and Surname]\n"
            "Account Email: [Your PU Prime account email]\n\n"
            "Please confirm once this has been completed.\n\n"
            "Thank you.</code>\n\n"
            "<b>Important:</b> after transfer confirmation, you must also <b>deposit</b> to qualify for VIP.",
            reply_markup=vip_existing_menu(),
            parse_mode="HTML",
        )
    elif data == "vip_sent_transfer":
        context.user_data["vip_transfer_sent"] = True
        log_event(user.id, "vip_transfer_sent")
        await query.message.reply_text(
            "<b>Transfer email marked as sent.</b>\n\n"
            "Wait for PU Prime to confirm the IB transfer.\n\n"
            "<b>After that:</b>\n"
            "• deposit\n"
            "• then submit your UID\n\n"
            "<i>This is required for VIP review.</i>",
            reply_markup=vip_existing_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>VIP user says they sent the transfer email</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP Existing User</b>"
            ),
        )
    elif data == "vip_existing_deposit_done":
        if not context.user_data.get("vip_transfer_sent"):
            await query.message.reply_text(
                "<b>You must send the transfer email first.</b>\n\n"
                "Please follow the VIP transfer steps in order.",
                reply_markup=vip_existing_menu(),
                parse_mode="HTML",
            )
            return
        context.user_data["vip_existing_deposit_done"] = True
        update_user(user.id, deposited_at=now_iso())
        log_event(user.id, "vip_existing_deposit_done")
        await query.message.reply_text(
            "<b>Deposit marked as completed.</b>\n\n"
            "You can now submit your <b>MT5 UID / account number</b> for VIP review.",
            reply_markup=vip_existing_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>VIP existing user says they deposited</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP Existing User</b>"
            ),
        )
    elif data == "flow_new":
        context.user_data["flow"] = "affiliate_new"
        update_user(user.id, flow="affiliate_new")
        await query.message.reply_text(
            "<b>IB Affiliate — New to PU Prime</b>\n\n"
            "Follow these steps in order:\n\n"
            "1. <b>Start Registration</b>\n"
            f"2. Make sure the code is <b>{IB_CODE}</b>\n"
            "3. Complete registration and verification\n"
            "4. Press <b>I Completed Registration</b>\n"
            "5. Submit your <b>MT5 UID / account number</b>\n\n"
            "<b>Important:</b> do not skip steps.\n\n"
            "<i>Press Step 1 below to begin.</i>",
            reply_markup=new_user_step_menu(),
            parse_mode="HTML",
        )
    elif data == "completed_registration":
        context.user_data["affiliate_registered"] = True
        log_event(user.id, "affiliate_registered")
        await query.message.reply_text(
            "<b>Registration marked as completed.</b>\n\n"
            "You can now send your <b>MT5 UID / account number</b> here.\n\n"
            "<i>Please make sure the UID format is correct before sending it.</i>",
            reply_markup=new_user_step_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>Affiliate user completed registration</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>Affiliate New User</b>"
            ),
        )
    elif data == "flow_existing":
        context.user_data["flow"] = "affiliate_existing"
        update_user(user.id, flow="affiliate_existing")
        await query.message.reply_text(
            "<b>IB Affiliate — Existing PU Prime User</b>\n\n"
            "Follow these steps in order:\n\n"
            "1. Open the <b>transfer email template</b>\n"
            "2. Send the email to PU Prime\n"
            "3. Press <b>I Sent the Email</b>\n"
            "4. Wait for PU Prime to confirm the transfer\n"
            "5. Submit your <b>MT5 UID / account number</b>\n\n"
            "<i>Please complete each step in order.</i>",
            reply_markup=existing_user_step_menu(),
            parse_mode="HTML",
        )
    elif data == "transfer_email_template":
        await query.message.reply_text(
            "<b>IB Transfer Email Template</b>\n\n"
            f"<b>To:</b>\n<code>{TRANSFER_EMAIL_1}</code>\n<code>{TRANSFER_EMAIL_2}</code>\n\n"
            f"<b>Subject:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
            "<b>Body:</b>\n"
            "<code>Hello,\n\n"
            f"Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
            "Full Name: [Your Name and Surname]\n"
            "Account Email: [Your PU Prime account email]\n\n"
            "Please confirm once this has been completed.\n\n"
            "Thank you.</code>\n\n"
            "<i>Send this email, then return here and press Step 2.</i>",
            reply_markup=existing_user_step_menu(),
            parse_mode="HTML",
        )
    elif data == "sent_transfer_email":
        context.user_data["affiliate_transfer_sent"] = True
        log_event(user.id, "affiliate_transfer_sent")
        await query.message.reply_text(
            "<b>Email marked as sent.</b>\n\n"
            "Wait for PU Prime to confirm the IB transfer.\n\n"
            "Once confirmed, submit your <b>MT5 UID / account number</b> here.",
            reply_markup=existing_user_step_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>Affiliate user says they sent the IB transfer email</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>Affiliate Existing User</b>"
            ),
        )
    elif data == "benefits":
        await query.message.reply_text(
            "<b>IB Benefits</b>\n\n"
            "• Structured onboarding\n"
            "• Direct admin support\n"
            "• Clear setup process\n"
            "• Access to the next stage after validation\n\n"
            "<i>Go back and continue the correct path.</i>",
            reply_markup=back_to_affiliate_main(),
            parse_mode="HTML",
        )
    elif data == "submit_uid_vip":
        flow = context.user_data.get("flow")
        if context.user_data.get("vip_submitted"):
            await query.message.reply_text(
                "<b>Your VIP submission has already been received.</b>\n\n"
                "Please wait for review or contact support if needed.",
                reply_markup=vip_submitted_menu(),
                parse_mode="HTML",
            )
            return
        if flow == "vip_new" and not context.user_data.get("vip_deposit_done"):
            await query.message.reply_text(
                "<b>You are not ready to submit UID yet.</b>\n\n"
                "For VIP access as a <b>new user</b>, you must:\n"
                "1. register under us\n"
                "2. deposit\n"
                "3. then submit your UID\n\n"
                "<i>Please complete the required steps first.</i>",
                reply_markup=vip_new_menu(),
                parse_mode="HTML",
            )
            return
        if flow == "vip_existing" and not context.user_data.get("vip_existing_deposit_done"):
            await query.message.reply_text(
                "<b>You are not ready to submit UID yet.</b>\n\n"
                "For VIP access as an <b>existing user</b>, you must:\n"
                "1. send the transfer email\n"
                "2. wait for confirmation\n"
                "3. deposit\n"
                "4. then submit your UID\n\n"
                "<i>Please complete the required steps first.</i>",
                reply_markup=vip_existing_menu(),
                parse_mode="HTML",
            )
            return
        context.user_data["awaiting_uid"] = True
        context.user_data["uid_type"] = "vip"
        await query.message.reply_text(
            "Send your <b>MT5 UID / account number</b> now in this exact format:\n\n"
            "<code>UID: 12345678</code>\n\n"
            "<b>Important:</b>\n"
            "• write <code>UID:</code> first\n"
            "• then your number\n"
            "• digits only\n"
            "• no extra text\n\n"
            "If you send a screenshot or document, the <b>caption</b> must use the same format.",
            reply_markup=back_to_vip_menu(),
            parse_mode="HTML",
        )
    elif data == "submit_uid_affiliate":
        flow = context.user_data.get("flow")
        if context.user_data.get("affiliate_submitted"):
            await query.message.reply_text(
                "<b>Your affiliate submission has already been received.</b>\n\n"
                "Please wait for review or contact support if needed.",
                reply_markup=affiliate_submitted_menu(),
                parse_mode="HTML",
            )
            return
        if flow == "affiliate_new" and not context.user_data.get("affiliate_registered"):
            await query.message.reply_text(
                "<b>You must complete registration first.</b>\n\n"
                "Please follow the affiliate steps in order.",
                reply_markup=new_user_step_menu(),
                parse_mode="HTML",
            )
            return
        if flow == "affiliate_existing" and not context.user_data.get("affiliate_transfer_sent"):
            await query.message.reply_text(
                "<b>You must send the transfer email first.</b>\n\n"
                "Please follow the affiliate steps in order.",
                reply_markup=existing_user_step_menu(),
                parse_mode="HTML",
            )
            return
        context.user_data["awaiting_uid"] = True
        context.user_data["uid_type"] = "affiliate"
        await query.message.reply_text(
            "Send your <b>MT5 UID / account number</b> now in this exact format:\n\n"
            "<code>UID: 12345678</code>\n\n"
            "<b>Important:</b>\n"
            "• write <code>UID:</code> first\n"
            "• then your number\n"
            "• digits only\n"
            "• no extra text\n\n"
            "If you send a screenshot or document, the <b>caption</b> must use the same format.",
            reply_markup=back_to_affiliate_main(),
            parse_mode="HTML",
        )
    elif data == "vip_waiting_review":
        await query.message.reply_text(
            "<b>Your VIP submission is already under review.</b>\n\n"
            "There is nothing else you need to submit right now.\n\n"
            "<i>If you need help, press Contact Support.</i>",
            reply_markup=vip_submitted_menu(),
            parse_mode="HTML",
        )
    elif data == "affiliate_waiting_review":
        await query.message.reply_text(
            "<b>Your affiliate submission is already under review.</b>\n\n"
            "There is nothing else you need to submit right now.\n\n"
            "<i>If you need help, press Contact Support.</i>",
            reply_markup=affiliate_submitted_menu(),
            parse_mode="HTML",
        )
    elif data == "support":
        await query.message.reply_text(
            "<b>Contact Support</b>\n\n"
            "Pick the admin best suited for your question:",
            reply_markup=support_admin_menu(),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>Support request received</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Main Path: <b>{context.user_data.get('main_path', 'unknown')}</b>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                f"Flow: <b>{context.user_data.get('flow', 'unknown')}</b>"
            ),
        )


# ===================================================================
# ADMIN ACTIONS (callback buttons inside admin chat)
# ===================================================================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    parts = data.split(":")
    try:
        await query.answer()
    except Exception:
        pass
    if len(parts) < 3:
        return
    op = parts[1]
    if op == "blk" and len(parts) >= 3:
        target = int(parts[2])
        update_user(target, blocked=1)
        log_event(target, "blocked", f"by:{query.from_user.id}")
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await notify_admin(
            context,
            f"⛔ User <code>{target}</code> blocked by @{query.from_user.username or query.from_user.id}.",
        )
        return
    if op in ("app", "rej") and len(parts) >= 4:
        kind = parts[2]
        target = int(parts[3])
        status = "approved" if op == "app" else "rejected"
        if kind == "vip":
            update_user(target, vip_status=status, vip_decision_at=now_iso())
        elif kind == "aff":
            update_user(target, aff_status=status, aff_decision_at=now_iso())
        elif kind == "funded":
            update_user(
                target,
                funded_status="active" if op == "app" else "rejected",
                funded_paid_at=now_iso() if op == "app" else None,
                funded_renew_at=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat() if op == "app" else None,
            )
        log_event(target, f"{kind}_{status}", f"by:{query.from_user.id}")

        # DM the user
        try:
            if status == "approved":
                msg = (
                    "<b>✅ Your submission has been approved.</b>\n\n"
                    "An admin will follow up shortly with the next step."
                )
            else:
                msg = (
                    "<b>❌ Your submission was not approved at this stage.</b>\n\n"
                    "Please contact support to resolve the issue."
                )
            await context.bot.send_message(
                chat_id=target, text=msg, parse_mode="HTML", reply_markup=back_to_start()
            )
        except Exception as e:
            log.warning("DM to user %s failed: %s", target, e)

        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await notify_admin(
            context,
            f"📝 <b>{kind.upper()}</b> submission for <code>{target}</code> "
            f"marked <b>{status}</b> by @{query.from_user.username or query.from_user.id}.",
        )


# ===================================================================
# TEXT HANDLER
# ===================================================================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    user = update.message.from_user
    if is_blocked(user.id):
        return
    if rate_limited(user.id):
        return
    upsert_user(user)
    username = f"@{user.username}" if user.username else "No username"

    if context.user_data.get("awaiting_uid"):
        submitted_text = update.message.text.strip() if update.message.text else ""
        parsed_uid = parse_uid_submission(submitted_text)
        if not parsed_uid:
            await update.message.reply_text(uid_format_guide(), parse_mode="HTML")
            return

        uid_type = context.user_data.get("uid_type", "unknown")
        flow = context.user_data.get("flow", "unknown")

        # Duplicate UID guard
        ok, existing_owner = register_uid(parsed_uid, user.id, uid_type)
        if not ok:
            await update.message.reply_text(
                "<b>This UID is already registered to another user.</b>\n\n"
                "If you believe this is an error, please contact support.",
                reply_markup=back_to_start(),
                parse_mode="HTML",
            )
            await notify_admin(
                context,
                (
                    "<b>⚠ Duplicate UID attempt</b>\n"
                    f"UID: <code>{parsed_uid}</code>\n"
                    f"Tried by: {html.escape(user.full_name)} ({username}, <code>{user.id}</code>)\n"
                    f"Already owned by user_id: <code>{existing_owner}</code>"
                ),
            )
            return

        if uid_type == "vip":
            reply_markup = vip_submitted_menu()
            context.user_data["vip_submitted"] = True
            update_user(user.id, vip_submitted=1, vip_uid=parsed_uid, vip_status="pending")
        else:
            reply_markup = affiliate_submitted_menu()
            context.user_data["affiliate_submitted"] = True
            update_user(user.id, aff_submitted=1, aff_uid=parsed_uid, aff_status="pending")

        await try_react(update, context, "👌")
        await update.message.reply_text(
            "<b>Submission received.</b>\n\n"
            "Your details have been forwarded for review.\n\n"
            "<i>Please wait for confirmation or further instructions.</i>",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )
        except Exception:
            pass
        await notify_admin(
            context,
            (
                "<b>New UID submission received</b>\n"
                f"Type: <b>{uid_type.upper()}</b>\n"
                f"Flow: <b>{flow}</b>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"UID: <code>{parsed_uid}</code>"
            ),
            reply_markup=admin_review_menu(user.id, "vip" if uid_type == "vip" else "aff"),
        )
        context.user_data["awaiting_uid"] = False
    else:
        await update.message.reply_text(
            "I didn't catch that — here's the menu.\n"
            "Press /start to begin, /status to check your progress, or /help for help.",
            parse_mode="HTML",
            reply_markup=back_to_start(),
        )


# ===================================================================
# MEDIA HANDLER
# ===================================================================
async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    user = update.message.from_user
    if is_blocked(user.id):
        return
    if rate_limited(user.id):
        return
    upsert_user(user)
    username = f"@{user.username}" if user.username else "No username"

    if context.user_data.get("awaiting_payment_proof"):
        caption = update.message.caption.strip() if update.message.caption else ""
        payment_type = parse_payment_submission(caption)
        if not payment_type:
            await update.message.reply_text(payment_format_guide(), parse_mode="HTML")
            return
        context.user_data["funded_submitted"] = True
        context.user_data["awaiting_payment_proof"] = False
        update_user(user.id, funded_status="pending", funded_paid_at=now_iso())
        await try_react(update, context, "💰")
        await update.message.reply_text(
            "<b>Payment proof received.</b>\n\n"
            "Your funded VIP payment is now under review.\n\n"
            "<i>Please wait for confirmation or further instructions.</i>",
            reply_markup=funded_review_menu(),
            parse_mode="HTML",
        )
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )
        except Exception:
            pass
        await notify_admin(
            context,
            (
                "<b>Funded VIP payment proof received</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>VIP Paid Funded</b>\n"
                "Payment Type: <b>FUNDED</b>"
            ),
            reply_markup=admin_review_menu(user.id, "funded"),
        )
        return

    if context.user_data.get("awaiting_uid"):
        uid_type = context.user_data.get("uid_type", "unknown")
        flow = context.user_data.get("flow", "unknown")
        caption = update.message.caption.strip() if update.message.caption else ""
        parsed_uid = parse_uid_submission(caption)
        if not parsed_uid:
            await update.message.reply_text(
                "<b>Invalid caption format.</b>\n\n"
                "If you send a screenshot or document, the caption must be:\n\n"
                "<code>UID: 12345678</code>",
                parse_mode="HTML",
            )
            return

        ok, existing_owner = register_uid(parsed_uid, user.id, uid_type)
        if not ok:
            await update.message.reply_text(
                "<b>This UID is already registered to another user.</b>\n\n"
                "If you believe this is an error, please contact support.",
                reply_markup=back_to_start(),
                parse_mode="HTML",
            )
            await notify_admin(
                context,
                (
                    "<b>⚠ Duplicate UID attempt (media)</b>\n"
                    f"UID: <code>{parsed_uid}</code>\n"
                    f"Tried by: {html.escape(user.full_name)} ({username}, <code>{user.id}</code>)\n"
                    f"Already owned by user_id: <code>{existing_owner}</code>"
                ),
            )
            return

        if uid_type == "vip":
            reply_markup = vip_submitted_menu()
            context.user_data["vip_submitted"] = True
            update_user(user.id, vip_submitted=1, vip_uid=parsed_uid, vip_status="pending")
        else:
            reply_markup = affiliate_submitted_menu()
            context.user_data["affiliate_submitted"] = True
            update_user(user.id, aff_submitted=1, aff_uid=parsed_uid, aff_status="pending")

        await try_react(update, context, "👌")
        await update.message.reply_text(
            "<b>Submission received.</b>\n\n"
            "Your file has been forwarded for review.\n\n"
            "<i>Please wait for confirmation or further instructions.</i>",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )
        except Exception:
            pass
        await notify_admin(
            context,
            (
                "<b>New media submission received</b>\n"
                f"Type: <b>{uid_type.upper()}</b>\n"
                f"Flow: <b>{flow}</b>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"UID From Caption: <code>{parsed_uid}</code>"
            ),
            reply_markup=admin_review_menu(user.id, "vip" if uid_type == "vip" else "aff"),
        )
        context.user_data["awaiting_uid"] = False
    else:
        await update.message.reply_text(
            "I didn't catch that — here's the menu. Press /start to begin.",
            parse_mode="HTML",
            reply_markup=back_to_start(),
        )


# ===================================================================
# ADMIN COMMANDS (admin chat only)
# ===================================================================
@admin_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = stats_snapshot()
    await update.message.reply_text(
        "<b>📊 ImperiumFX Bot — Stats</b>\n\n"
        f"Total users: <b>{s['total']}</b>\n"
        f"New (24h): <b>{s['new_24h']}</b>\n"
        f"Started flow: <b>{s['started']}</b>\n\n"
        f"VIP pending: <b>{s['vip_pending']}</b>\n"
        f"VIP approved: <b>{s['vip_approved']}</b>\n"
        f"VIP rejected: <b>{s['vip_rejected']}</b>\n\n"
        f"Affiliate pending: <b>{s['aff_pending']}</b>\n"
        f"Affiliate approved: <b>{s['aff_approved']}</b>\n\n"
        f"Funded VIP active: <b>{s['funded_active']}</b>\n"
        f"Blocked users: <b>{s['blocked']}</b>",
        parse_mode="HTML",
    )


@admin_only
async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: <code>/user &lt;user_id&gt;</code>", parse_mode="HTML"
        )
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id must be an integer.")
        return
    row = get_user(uid)
    if not row:
        await update.message.reply_text("No user found.")
        return
    text = "<b>👤 User Record</b>\n\n"
    for k in row.keys():
        v = row[k]
        if v is None or v == "":
            continue
        text += f"<b>{k}</b>: <code>{html.escape(str(v))}</code>\n"
    await update.message.reply_text(text, parse_mode="HTML")


def _uid_arg(context):
    if not context.args:
        return None
    try:
        return int(context.args[0])
    except ValueError:
        return None


@admin_only
async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = _uid_arg(context)
    if not target:
        await update.message.reply_text(
            "Usage: <code>/approve &lt;user_id&gt; [vip|aff|funded]</code>",
            parse_mode="HTML",
        )
        return
    kind = (context.args[1] if len(context.args) > 1 else "vip").lower()
    if kind == "vip":
        update_user(target, vip_status="approved", vip_decision_at=now_iso())
    elif kind == "aff":
        update_user(target, aff_status="approved", aff_decision_at=now_iso())
    elif kind == "funded":
        update_user(
            target,
            funded_status="active",
            funded_paid_at=now_iso(),
            funded_renew_at=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        )
    log_event(target, f"{kind}_approved", f"by:{update.effective_user.id}")
    try:
        await context.bot.send_message(
            chat_id=target,
            text="<b>✅ Your submission has been approved.</b>\n\nAn admin will follow up shortly.",
            parse_mode="HTML",
            reply_markup=back_to_start(),
        )
    except Exception:
        pass
    await update.message.reply_text(
        f"Approved <code>{target}</code> ({kind}).", parse_mode="HTML"
    )


@admin_only
async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = _uid_arg(context)
    if not target:
        await update.message.reply_text(
            "Usage: <code>/reject &lt;user_id&gt; [vip|aff|funded]</code>",
            parse_mode="HTML",
        )
        return
    kind = (context.args[1] if len(context.args) > 1 else "vip").lower()
    if kind == "vip":
        update_user(target, vip_status="rejected", vip_decision_at=now_iso())
    elif kind == "aff":
        update_user(target, aff_status="rejected", aff_decision_at=now_iso())
    elif kind == "funded":
        update_user(target, funded_status="rejected")
    log_event(target, f"{kind}_rejected", f"by:{update.effective_user.id}")
    try:
        await context.bot.send_message(
            chat_id=target,
            text="<b>❌ Your submission was not approved.</b>\n\nPlease contact support to resolve this.",
            parse_mode="HTML",
            reply_markup=back_to_start(),
        )
    except Exception:
        pass
    await update.message.reply_text(
        f"Rejected <code>{target}</code> ({kind}).", parse_mode="HTML"
    )


@admin_only
async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = _uid_arg(context)
    if not target:
        await update.message.reply_text(
            "Usage: <code>/block &lt;user_id&gt;</code>", parse_mode="HTML"
        )
        return
    update_user(target, blocked=1)
    log_event(target, "blocked", f"by:{update.effective_user.id}")
    await update.message.reply_text(f"⛔ Blocked <code>{target}</code>.", parse_mode="HTML")


@admin_only
async def cmd_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = _uid_arg(context)
    if not target:
        await update.message.reply_text(
            "Usage: <code>/unblock &lt;user_id&gt;</code>", parse_mode="HTML"
        )
        return
    update_user(target, blocked=0)
    log_event(target, "unblocked", f"by:{update.effective_user.id}")
    await update.message.reply_text(f"✅ Unblocked <code>{target}</code>.", parse_mode="HTML")


@admin_only
async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.partition(" ")[2].strip()
    if not msg:
        await update.message.reply_text(
            "Usage: <code>/broadcast &lt;message&gt;</code>", parse_mode="HTML"
        )
        return
    conn = db()
    rows = conn.execute("SELECT user_id FROM users WHERE blocked=0").fetchall()
    conn.close()
    sent = 0
    failed = 0
    for r in rows:
        try:
            await context.bot.send_message(chat_id=r["user_id"], text=msg, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"📣 Broadcast done. Sent: <b>{sent}</b>, Failed: <b>{failed}</b>",
        parse_mode="HTML",
    )


@admin_only
async def cmd_adminhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>🛡 Admin Commands</b> (admin chat only)\n\n"
        "/stats — bot stats snapshot\n"
        "/user &lt;id&gt; — show full user record\n"
        "/approve &lt;id&gt; [vip|aff|funded]\n"
        "/reject &lt;id&gt; [vip|aff|funded]\n"
        "/block &lt;id&gt; — block a user\n"
        "/unblock &lt;id&gt; — unblock a user\n"
        "/broadcast &lt;text&gt; — message all users (HTML allowed)\n"
        "/adminhelp — show this list\n\n"
        "<i>Inline buttons on each new submission also work for Approve / Reject / Block.</i>",
        parse_mode="HTML",
    )


# ===================================================================
# SCHEDULED JOBS
# ===================================================================
async def job_nudges(context: ContextTypes.DEFAULT_TYPE):
    """Gentle reminders for users who started but didn't finish."""
    conn = db()
    now = datetime.now(timezone.utc)
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    cutoff_72h = (now - timedelta(hours=72)).isoformat()
    rows = conn.execute(
        "SELECT user_id, started_at, deposited_at, vip_submitted, aff_submitted, blocked FROM users"
    ).fetchall()
    conn.close()
    for r in rows:
        if r["blocked"]:
            continue
        try:
            # 24h after /start, no submission yet
            if (
                r["started_at"]
                and r["started_at"] <= cutoff_24h
                and not r["vip_submitted"]
                and not r["aff_submitted"]
            ):
                await context.bot.send_message(
                    chat_id=r["user_id"],
                    text=(
                        "👋 Just checking in.\n\n"
                        "If you got stuck during ImperiumFX setup, press /start "
                        "to resume — or hit Contact Support and we'll help."
                    ),
                )
                continue
            # 72h after deposit but no UID submitted
            if (
                r["deposited_at"]
                and r["deposited_at"] <= cutoff_72h
                and not r["vip_submitted"]
            ):
                await context.bot.send_message(
                    chat_id=r["user_id"],
                    text=(
                        "📩 You marked your deposit as done — don't forget to submit your "
                        "<b>MT5 UID</b> so we can finalize VIP access."
                    ),
                    parse_mode="HTML",
                )
        except Exception:
            pass
        await asyncio.sleep(0.05)


async def job_renewals(context: ContextTypes.DEFAULT_TYPE):
    """Funded VIP renewal reminders at 3d / 1d / 0d before renew_at."""
    conn = db()
    rows = conn.execute(
        "SELECT user_id, funded_renew_at FROM users WHERE funded_status='active' AND funded_renew_at IS NOT NULL"
    ).fetchall()
    conn.close()
    now = datetime.now(timezone.utc)
    for r in rows:
        try:
            renew = datetime.fromisoformat(r["funded_renew_at"])
            delta_days = (renew - now).days
            if delta_days in (3, 1, 0):
                await context.bot.send_message(
                    chat_id=r["user_id"],
                    text=(
                        "<b>🔔 Funded VIP renewal reminder</b>\n\n"
                        f"Your renewal is due in <b>{delta_days} day(s)</b>.\n"
                        "Renewal is <b>€80</b>. Press /start → Paid VIP → Funded to pay.\n\n"
                        "<b>Wallets:</b>\n"
                        f"BTC: <code>{BTC_ADDRESS}</code>\n"
                        f"ETH: <code>{ETHEREUM_ADDRESS}</code>\n"
                        f"SOL: <code>{SOLANA_ADDRESS}</code>"
                    ),
                    parse_mode="HTML",
                )
        except Exception:
            pass
        await asyncio.sleep(0.05)


# ===================================================================
# ERROR HANDLER
# ===================================================================
async def on_error(update, context):
    err = context.error
    log.exception("Unhandled error: %s", err)
    try:
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        tb_short = tb[-3500:]
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"<b>🚨 Bot error</b>\n<pre>{html.escape(tb_short)}</pre>",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ===================================================================
# MAIN
# ===================================================================
def main():
    db_init()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))

    # Admin commands (silently no-op outside admin chat via @admin_only)
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("user", cmd_user))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("reject", cmd_reject))
    app.add_handler(CommandHandler("block", cmd_block))
    app.add_handler(CommandHandler("unblock", cmd_unblock))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("adminhelp", cmd_adminhelp))

    # Callbacks + messages
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, media_handler))

    # Error handler
    app.add_error_handler(on_error)

    # Scheduled jobs (graceful fallback if job-queue extra not installed)
    if app.job_queue is not None:
        app.job_queue.run_repeating(job_nudges, interval=3600, first=120)
        app.job_queue.run_repeating(job_renewals, interval=21600, first=300)
        log.info("Job queue enabled.")
    else:
        log.warning(
            "Job queue not available. Install with: "
            "pip install \"python-telegram-bot[job-queue]>=20.0\""
        )

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()