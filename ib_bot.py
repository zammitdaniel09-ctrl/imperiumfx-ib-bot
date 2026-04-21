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
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===================================================================
# CONFIG
# ===================================================================
BOT_TOKEN = "8085633137:AAFmd8l4i1JHj_5SccWUqdIft7SgGDcwzpE"
ADMIN_CHAT_ID = -5102939745
MAIN_GROUP_CHAT_ID = -1003752395437
BOT_USERNAME = "imperiumfx_onboarding_bot"

IB_LINK = "https://www.puprime.partners/forex-trading-account/?affid=MjMyMTMwODY="
IB_CODE = "pOenf2oC"
IB_ACCOUNT_NUMBER = "23213086"
TUTORIAL_PDF = "IB_E_BOOK.pdf"
TUTORIAL_PDF_2 = "IB_E_BOOK_1.pdf"
TRANSFER_EMAIL_1 = "tommaso.ticconi@puprime.com"
TRANSFER_EMAIL_2 = "info@puprime.com"
SOLANA_ADDRESS = "GrSbxLK1Z6ZgEhEtViY4ibLEq7xYuXiuGCxVFYjzwazt"
ETHEREUM_ADDRESS = "0x2474F60027Fda971aaA773031f07Fd58F3e14627"
BTC_ADDRESS = "bc1pzzz24czpr9yem4st5p727gcm30fw6c6yfnt07pypr6esxu56092smassch"

DB_PATH = "bot.db"

# Admin team roster
ADMINS = {
    "kratos": {
        "username": "ImperiumXAUUSD",
        "user_id": 7121821750,
        "label": "Kratos (Founder & Head Admin)",
        "role": "owner",
    },
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
    ("Instagram - @imperiumxaufx", "https://www.instagram.com/imperiumxaufx"),
    ("TikTok - @kratosxaufx", "https://www.tiktok.com/@kratosxaufx"),
]

# ===================================================================
# LANGUAGES
# ===================================================================
LANGS = ["en", "es", "hi", "ar", "ru"]
DEFAULT_LANG = "en"

LANG_LABELS = {
    "en": "English",
    "es": "Espanol (Spanish)",
    "hi": "हिन्दी (Hindi)",
    "ar": "العربية (Arabic)",
    "ru": "Русский (Russian)",
}

LANG_FLAG = {
    "en": "EN",
    "es": "ES",
    "hi": "HI",
    "ar": "AR",
    "ru": "RU",
}

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
# TEXTS - all user-facing strings, 5 languages
# Admin-facing messages stay English elsewhere in this file.
# ===================================================================
TEXTS = {}

TEXTS["en"] = {
    # ---------- language picker ----------
    "lang_picker_title": "✨ <b>Welcome to ImperiumFX</b> ✨\n\nYour gateway to premium trading — curated VIP signals, IB partnerships, and a team that actually trades.\n\n🌐 <b>Please choose your language to continue.</b>\n<i>You can change it later anytime with /language.</i>",
    "lang_set_ok": "✅ <b>Language set.</b> Loading your main menu…",

    # ---------- welcome / start ----------
    "welcome_title": "💎 <b>Welcome to ImperiumFX</b> 💎",
    "welcome_body": "💎 <b>Welcome to ImperiumFX</b> 💎\n\nThe home of premium VIP signals and IB partnerships for PU Prime traders.\n\n<b>What brings you here today?</b>\n\n💎 <b>VIP Access</b> — private signals, setups and live calls\n🤝 <b>IB Affiliate</b> — become a partner and earn commissions\n👥 <b>Meet the Team</b> — see who runs ImperiumFX\n🌐 <b>Follow Us</b> — Instagram and TikTok\n❓ <b>FAQ</b> — quick answers to common questions\n\n<i>Tap an option below to continue.</i>",
    "resume_prompt": (
        "<b>You already have progress in the bot.</b>\n\n"
        "Do you want to <b>restart</b> from the beginning, or keep your current progress?"
    ),
    "restart_yes_msg": "💎 <b>Welcome to ImperiumFX</b> 💎\n\nChoose your path below.",
    "restart_no_msg": "Progress kept. Press a button below to continue.",
    "back_short_welcome": "💎 <b>Welcome to ImperiumFX</b> 💎\n\nChoose your path below.\n\n💎 <b>VIP Access</b> — join our VIP signal access\n🤝 <b>IB Affiliate</b> — become an affiliate and follow the IB onboarding process\n\n<i>Please choose the option that matches what you want.</i>",

    # ---------- help / status ----------
    "help_text": (
        "<b>ImperiumFX Bot - Help</b>\n\n"
        "- /start - open the main menu\n"
        "- /status - see where you are in the process\n"
        "- /language - change your language\n"
        "- /help - show this message\n\n"
        "If you get stuck, press <b>Contact Support</b> from any menu."
    ),
    "status_title": "<b>Your status</b>",
    "status_no_record": "No record found yet. Press /start to begin.",
    "status_path": "Path",
    "status_flow": "Flow",
    "status_vip_submitted": "VIP submitted",
    "status_aff_submitted": "Affiliate submitted",
    "status_funded": "Funded VIP",
    "yes": "yes",
    "no": "no",
    "status_field_status": "status",
    "dash": "-",

    # ---------- common ----------
    "access_disabled": "Access disabled. Contact support.",
    "slow_down": "Slow down",
    "fallback_unknown": (
        "I didn't catch that - here's the menu.\n"
        "Press /start to begin, /status to check your progress, or /help for help."
    ),
    "fallback_media": "I didn't catch that - here's the menu. Press /start to begin.",

    # ---------- team / socials / faq ----------
    "team_title": "<b>Meet the Team</b>",
    "team_footer": "<i>Tap a button below to message them directly.</i>",
    "socials_body": (
        "<b>Follow ImperiumFX</b>\n\n"
        "Stay up to date with our latest content, signal previews and giveaways."
    ),
    "faq_intro": "<b>Frequently Asked Questions</b>\n\nPick a question below.",

    # ---------- vip entry ----------
    "vip_access_body": (
        "<b>VIP Access</b>\n\n"
        "Choose your VIP route below.\n\n"
        "<b>Free VIP</b>\n"
        "- for users who come under our IB\n"
        "- requires registration/transfer under us and deposit\n\n"
        "<b>Paid VIP</b>\n"
        "- for users who want direct access\n"
        "- funded accounts pay monthly\n\n"
        "<i>Select the option that matches your situation.</i>"
    ),
    "vip_free_body": (
        "<b>Free VIP</b>\n\n"
        "To qualify, you must do <b>one</b> of the following:\n\n"
        "1. <b>Register with PU Prime under us</b>\n"
        "2. <b>Transfer your existing PU Prime account under us</b>\n\n"
        "<b>Important rules:</b>\n"
        "- You must come under our IB\n"
        "- You must <b>deposit</b>\n"
        "- Without this, <b>free VIP access will not be granted</b>\n\n"
        "<i>Select the option that matches your situation below.</i>"
    ),
    "vip_paid_body": (
        "<b>Paid VIP</b>\n\n"
        "Choose the type of account you use.\n\n"
        "<b>Live Account</b>\n"
        "- same structure as free VIP\n"
        "- you must come under our IB and deposit\n\n"
        "<b>Funded Account</b>\n"
        "- <b>EUR 50</b> first month\n"
        "- <b>EUR 80</b> from the next month onward\n\n"
        "<i>Select your account type below.</i>"
    ),
    "vip_paid_live_body": (
        "<b>Paid VIP - Live Account</b>\n\n"
        "For live accounts, your access is handled through our IB structure.\n\n"
        "That means you must:\n"
        "1. register under us or transfer under us\n"
        "2. deposit\n"
        "3. submit your UID\n\n"
        "<i>Select your route below.</i>"
    ),
    "vip_paid_funded_body": (
        "<b>Paid VIP - Funded Account</b>\n\n"
        "<b>Pricing:</b>\n"
        "- <b>EUR 50</b> first month\n"
        "- <b>EUR 80</b> from the next month onward\n\n"
        "<b>Payment methods:</b>\n"
        "- BTC\n"
        "- ETH\n"
        "- SOL\n\n"
        "<b>Next step:</b>\n"
        "1. view the wallet address\n"
        "2. send the payment\n"
        "3. submit payment proof\n\n"
        "<i>Use the buttons below.</i>"
    ),
    "vip_new_body": (
        "<b>VIP Access - New to PU Prime</b>\n\n"
        "Follow these steps in order:\n\n"
        "1. <b>Register using our link</b>\n"
        "2. Make sure the code is <b>{IB_CODE}</b>\n"
        "3. Complete registration\n"
        "4. <b>Deposit</b>\n"
        "5. Submit your <b>MT5 UID / account number</b>\n\n"
        "<b>Important:</b>\n"
        "- VIP is only for users who come under us\n"
        "- Registration alone is <b>not enough</b>\n"
        "- You must <b>deposit</b> before access is reviewed\n\n"
        "<i>Complete the steps below carefully.</i>"
    ),
    "vip_existing_body": (
        "<b>VIP Access - Existing PU Prime User</b>\n\n"
        "Follow these steps in order:\n\n"
        "1. Send the <b>IB transfer email</b>\n"
        "2. Wait for transfer confirmation\n"
        "3. <b>Deposit</b>\n"
        "4. Submit your <b>MT5 UID / account number</b>\n\n"
        "<b>Important:</b>\n"
        "- Your account must be moved under our IB\n"
        "- You must <b>deposit</b>\n"
        "- Without this, <b>VIP access will not be granted</b>\n\n"
        "<i>Complete the steps below carefully.</i>"
    ),
    "vip_registered_msg": (
        "<b>Registration marked as completed.</b>\n\n"
        "<b>Next requirement:</b> you must now <b>deposit</b> before submitting your UID for VIP review.\n\n"
        "<i>Do not skip this step.</i>"
    ),
    "vip_must_register_first": (
        "<b>You must complete registration first.</b>\n\n"
        "Please follow the steps in order.\n\n"
        "<i>Step 1 must be completed before Step 3.</i>"
    ),
    "vip_deposit_done_msg": (
        "<b>Deposit marked as completed.</b>\n\n"
        "You can now submit your <b>MT5 UID / account number</b> for VIP review."
    ),
    "vip_existing_deposit_done_msg": (
        "<b>Deposit marked as completed.</b>\n\n"
        "You can now submit your <b>MT5 UID / account number</b> for VIP review."
    ),
    "vip_transfer_email_body": (
        "<b>VIP Transfer Email Template</b>\n\n"
        "<b>To:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>Subject:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>Body:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<b>Important:</b> after transfer confirmation, you must also <b>deposit</b> to qualify for VIP."
    ),
    "vip_transfer_sent_msg": (
        "<b>Transfer email marked as sent.</b>\n\n"
        "Wait for PU Prime to confirm the IB transfer.\n\n"
        "<b>After that:</b>\n"
        "- deposit\n"
        "- then submit your UID\n\n"
        "<i>This is required for VIP review.</i>"
    ),
    "vip_must_send_transfer_first": (
        "<b>You must send the transfer email first.</b>\n\n"
        "Please follow the VIP transfer steps in order."
    ),

    # ---------- affiliate entry ----------
    "ib_affiliate_body": (
        "<b>IB Affiliate Setup</b>\n\n"
        "This path is for users who want to understand the IB model and complete the affiliate onboarding process.\n\n"
        "<i>Choose whether you need the beginner guide or want to continue directly.</i>"
    ),
    "what_is_ib_msg": (
        "Start with the <b>tutorial PDF</b> below.\n\n"
        "<b>Next step:</b> once you've read it, press <b>Continue</b>."
    ),
    "pdf_missing": "Tutorial PDF not found.\n\nPut <b>{PDF}</b> in the same folder as <b>ib_bot.py</b>.",
    "pdf_caption": "IB Tutorial Guide",
    "affiliate_main_body": "<b>IB Affiliate Menu</b>\n\nChoose the path that matches your situation.",
    "flow_new_body": (
        "<b>IB Affiliate - New to PU Prime</b>\n\n"
        "Follow these steps in order:\n\n"
        "1. <b>Start Registration</b>\n"
        "2. Make sure the code is <b>{IB_CODE}</b>\n"
        "3. Complete registration and verification\n"
        "4. Press <b>I Completed Registration</b>\n"
        "5. Submit your <b>MT5 UID / account number</b>\n\n"
        "<b>Important:</b> do not skip steps.\n\n"
        "<i>Press Step 1 below to begin.</i>"
    ),
    "flow_existing_body": (
        "<b>IB Affiliate - Existing PU Prime User</b>\n\n"
        "Follow these steps in order:\n\n"
        "1. Open the <b>transfer email template</b>\n"
        "2. Send the email to PU Prime\n"
        "3. Press <b>I Sent the Email</b>\n"
        "4. Wait for PU Prime to confirm the transfer\n"
        "5. Submit your <b>MT5 UID / account number</b>\n\n"
        "<i>Please complete each step in order.</i>"
    ),
    "affiliate_registered_msg": (
        "<b>Registration marked as completed.</b>\n\n"
        "You can now send your <b>MT5 UID / account number</b> here.\n\n"
        "<i>Please make sure the UID format is correct before sending it.</i>"
    ),
    "affiliate_transfer_email_body": (
        "<b>IB Transfer Email Template</b>\n\n"
        "<b>To:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>Subject:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>Body:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<i>Send this email, then return here and press Step 2.</i>"
    ),
    "affiliate_transfer_sent_msg": (
        "<b>Email marked as sent.</b>\n\n"
        "Wait for PU Prime to confirm the IB transfer.\n\n"
        "Once confirmed, submit your <b>MT5 UID / account number</b> here."
    ),
    "affiliate_must_register": (
        "<b>You must complete registration first.</b>\n\n"
        "Please follow the affiliate steps in order."
    ),
    "affiliate_must_send_transfer": (
        "<b>You must send the transfer email first.</b>\n\n"
        "Please follow the affiliate steps in order."
    ),
    "benefits_body": (
        "<b>IB Benefits</b>\n\n"
        "- Structured onboarding\n"
        "- Direct admin support\n"
        "- Clear setup process\n"
        "- Access to the next stage after validation\n\n"
        "<i>Go back and continue the correct path.</i>"
    ),

    # ---------- funded payment ----------
    "show_btc_body": (
        "<b>BTC Address</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Tap the address to copy. After sending payment, press I Sent Payment and then submit your proof.</i>"
    ),
    "show_eth_body": (
        "<b>ETH Address</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Tap the address to copy. After sending payment, press I Sent Payment and then submit your proof.</i>"
    ),
    "show_sol_body": (
        "<b>SOL Address</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Tap the address to copy. After sending payment, press I Sent Payment and then submit your proof.</i>"
    ),
    "funded_payment_sent_msg": (
        "<b>Payment marked as sent.</b>\n\n"
        "Now submit your payment proof.\n\n"
        "<b>Important:</b> if you send a screenshot or document, the caption must be:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "funded_already_submitted": (
        "<b>Your payment proof has already been received.</b>\n\n"
        "Please wait for review or contact support if needed."
    ),
    "funded_must_send_first": (
        "<b>You must mark payment as sent first.</b>\n\n"
        "Please follow the funded VIP steps in order."
    ),
    "funded_proof_prompt": (
        "Send your <b>payment proof</b> now.\n\n"
        "<b>Required caption format:</b>\n"
        "<code>PAYMENT: FUNDED</code>\n\n"
        "<i>Screenshot or document only.</i>"
    ),
    "funded_waiting_review_msg": (
        "<b>Your funded VIP payment proof is already under review.</b>\n\n"
        "There is nothing else you need to submit right now.\n\n"
        "<i>If you need help, press Contact Support.</i>"
    ),
    "funded_proof_received": (
        "<b>Payment proof received.</b>\n\n"
        "Your funded VIP payment is now under review.\n\n"
        "<i>Please wait for confirmation or further instructions.</i>"
    ),

    # ---------- uid submission ----------
    "submit_uid_prompt": (
        "Send your <b>MT5 UID / account number</b> now.\n\n"
        "Just type the number — for example:\n\n"
        "<code>12345678</code>\n\n"
        "<i>If you send a screenshot or document, include your UID in the caption.</i>"
    ),
    "uid_format_guide": (
        "<b>UID not recognized.</b>\n\n"
        "Please send just your MT5 UID — for example:\n\n"
        "<code>12345678</code>"
    ),
    "payment_format_guide": (
        "<b>Invalid payment proof format.</b>\n\n"
        "If you send payment proof, the caption must be exactly:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>Caption missing UID.</b>\n\n"
        "If you send a screenshot or document, the caption must contain your UID — for example:\n\n"
        "<code>12345678</code>"
    ),
    "uid_already_registered": (
        "<b>This UID is already registered to another user.</b>\n\n"
        "If you believe this is an error, please contact support."
    ),
    "uid_not_ready_new_vip": (
        "<b>You are not ready to submit UID yet.</b>\n\n"
        "For VIP access as a <b>new user</b>, you must:\n"
        "1. register under us\n"
        "2. deposit\n"
        "3. then submit your UID\n\n"
        "<i>Please complete the required steps first.</i>"
    ),
    "uid_not_ready_existing_vip": (
        "<b>You are not ready to submit UID yet.</b>\n\n"
        "For VIP access as an <b>existing user</b>, you must:\n"
        "1. send the transfer email\n"
        "2. wait for confirmation\n"
        "3. deposit\n"
        "4. then submit your UID\n\n"
        "<i>Please complete the required steps first.</i>"
    ),
    "vip_already_submitted": (
        "<b>Your VIP submission has already been received.</b>\n\n"
        "Please wait for review or contact support if needed."
    ),
    "aff_already_submitted": (
        "<b>Your affiliate submission has already been received.</b>\n\n"
        "Please wait for review or contact support if needed."
    ),
    "submission_received_text": (
        "<b>Submission received.</b>\n\n"
        "Your details have been forwarded for review.\n\n"
        "<i>Please wait for confirmation or further instructions.</i>"
    ),
    "submission_received_media": (
        "<b>Submission received.</b>\n\n"
        "Your file has been forwarded for review.\n\n"
        "<i>Please wait for confirmation or further instructions.</i>"
    ),
    "vip_waiting_review_msg": (
        "<b>Your VIP submission is already under review.</b>\n\n"
        "There is nothing else you need to submit right now.\n\n"
        "<i>If you need help, press Contact Support.</i>"
    ),
    "aff_waiting_review_msg": (
        "<b>Your affiliate submission is already under review.</b>\n\n"
        "There is nothing else you need to submit right now.\n\n"
        "<i>If you need help, press Contact Support.</i>"
    ),

    # ---------- support ----------
    "support_body": "<b>Contact Support</b>\n\nPick the admin best suited for your question:",

    # ---------- approval DMs ----------
    "approved_dm": (
        "<b>Your submission has been approved.</b>\n\n"
        "An admin will follow up shortly with the next step."
    ),
    "rejected_dm": (
        "<b>Your submission was not approved at this stage.</b>\n\n"
        "Please contact support to resolve the issue."
    ),

    # ---------- nudges / renewals ----------
    "nudge_24h": (
        "Just checking in.\n\n"
        "If you got stuck during ImperiumFX setup, press /start to resume - "
        "or hit Contact Support and we'll help."
    ),
    "nudge_72h_deposit": (
        "You marked your deposit as done - don't forget to submit your "
        "<b>MT5 UID</b> so we can finalize VIP access."
    ),
    "renewal_reminder": (
        "<b>Funded VIP renewal reminder</b>\n\n"
        "Your renewal is due in <b>{DAYS} day(s)</b>.\n"
        "Renewal is <b>EUR 80</b>. Press /start -> Paid VIP -> Funded to pay.\n\n"
        "<b>Wallets:</b>\n"
        "BTC: <code>{BTC}</code>\n"
        "ETH: <code>{ETH}</code>\n"
        "SOL: <code>{SOL}</code>"
    ),

    "fallback_msg": "I didn't catch that — please use the buttons below.",
    "uid_bad_format": (
        "<b>UID not recognized.</b>\n"
        "Please send just your MT5 UID — for example:\n"
        "<code>12345678</code>"
    ),
    "vip_uid_received": (
        "<b>VIP submission received.</b>\n"
        "Our team will review it shortly and DM you when you're approved. ✅"
    ),
    "aff_uid_received": (
        "<b>Affiliate submission received.</b>\n"
        "Our team will confirm your IB sub-affiliate status and DM you. ✅"
    ),
    "funded_submit_bad_format": (
        "<b>Format not recognized.</b>\n"
        "Please send:\n"
        "<code>Amount: 80 EUR\nTX/Ref: &lt;hash or reference&gt;\nMethod: BTC|ETH|SOL</code>\n"
        "Or send the proof image with the same caption."
    ),
    "funded_submit_received": (
        "<b>Funded VIP payment received.</b>\n"
        "We're verifying it now — you'll be DM'd once access is granted. 🔒"
    ),
    "nudge_incomplete": (
        "<b>Still interested in VIP?</b>\n"
        "You started but didn't finish — tap /start to pick up where you left off."
    ),

    # ---------- faq body (questions+answers) ----------
    "faq_q1": "What is VIP access?",
    "faq_a1": (
        "<b>VIP access</b> gives you our private signals, setups and trade calls. "
        "Free VIP requires you to come under our IB and deposit. "
        "Paid VIP (funded) is direct access for funded account traders."
    ),
    "faq_q2": "What is an IB?",
    "faq_a2": (
        "An <b>IB (Introducing Broker)</b> means your trading account is registered or "
        "transferred under our partner code. We earn a small commission from your "
        "spread - at <b>no extra cost to you</b> - and in return you get free VIP access."
    ),
    "faq_q3": "How long does review take?",
    "faq_a3": (
        "Reviews are <b>usually within 24 hours</b>. If it's been longer, press "
        "<b>Contact Support</b> and an admin will follow up."
    ),
    "faq_q4": "Why didn't my UID get accepted?",
    "faq_a4": (
        "Common reasons: account is not under our IB code, no deposit yet, "
        "or we couldn't read your UID. Make sure you used code <code>{IB_CODE}</code>, "
        "deposited, and sent just the digits, e.g. <code>12345678</code>"
    ),
    "faq_q5": "How much does Funded VIP cost?",
    "faq_a5": (
        "<b>EUR 50</b> for the first month, then <b>EUR 80</b>/month. "
        "Payable in BTC, ETH or SOL. After payment, send proof with caption "
        "<code>PAYMENT: FUNDED</code>."
    ),
    "faq_q6": "Is there a minimum deposit?",
    "faq_a6": (
        "PU Prime sets the minimum deposit. We recommend at least <b>USD 200</b> "
        "for a meaningful position size and to qualify smoothly for VIP."
    ),

    # ---------- buttons ----------
    "btn_vip_access": "💎 Join VIP Access",
    "btn_ib_affiliate": "🤝 Become an IB Affiliate",
    "btn_team": "👥 Meet the Team",
    "btn_socials": "🌐 Follow Us",
    "btn_faq": "❓ FAQ",
    "btn_support": "💬 Contact Support",
    "btn_back": "◀️ Back",
    "btn_back_to_start": "🏠 Back to Start",
    "btn_back_to_vip": "◀️ Back to VIP Menu",
    "btn_back_to_affiliate": "◀️ Back to Affiliate Menu",
    "btn_yes_restart": "🔄 Yes, restart",
    "btn_no_keep": "✅ No, keep progress",
    "btn_free_vip": "🎁 Free VIP",
    "btn_paid_vip": "👑 Paid VIP",
    "btn_new_to_pu": "🆕 New to PU Prime",
    "btn_existing_pu": "📂 Already with PU Prime",
    "btn_live_account": "📊 Live Account",
    "btn_funded_account": "🏦 Funded Account",
    "btn_dont_know_ib": "🤔 I don't know what IB is",
    "btn_already_know": "✅ I already know, continue",
    "btn_continue": "➡️ Continue",
    "btn_step1_register": "1️⃣ Step 1: Register with PU Prime",
    "btn_step1_start_reg": "1️⃣ Step 1: Start Registration",
    "btn_step2_completed": "2️⃣ Step 2: I Completed Registration",
    "btn_step3_deposited": "3️⃣ Step 3: I Deposited",
    "btn_step4_submit_uid": "4️⃣ Step 4: Submit UID",
    "btn_step3_submit_uid": "3️⃣ Step 3: Submit UID",
    "btn_step1_view_email": "1️⃣ Step 1: View Transfer Email",
    "btn_step2_sent_email": "2️⃣ Step 2: I Sent the Email",
    "btn_view_btc": "₿ View BTC Address",
    "btn_view_eth": "Ξ View ETH Address",
    "btn_view_sol": "◎ View SOL Address",
    "btn_sent_payment": "💸 I Sent Payment",
    "btn_submit_proof": "📤 Submit Payment Proof",
    "btn_waiting_payment_review": "⏳ Waiting for Payment Review",
    "btn_waiting_review": "⏳ Waiting for Review",
    "btn_benefits": "🎯 IB Benefits",
    "btn_message": "💬 Message",
    "btn_founder": "👑 Founder - Kratos",
    "btn_onboarding": "🚀 Onboarding / General - Apollo",
    "btn_signals": "📈 Signals - Plato",
    "btn_socials_admin": "📱 Socials - HD",
    "btn_change_language": "🌐 Change Language",
    "btn_approve": "✅ Approve",
    "btn_reject": "❌ Reject",
    "btn_block_user": "🚫 Block User",
}

TEXTS["hi"] = {
    "lang_picker_title": "✨ <b>ImperiumFX में आपका स्वागत है</b> ✨\n\nप्रीमियम ट्रेडिंग का आपका द्वार — चुने हुए VIP सिग्नल, IB पार्टनरशिप, और एक असली ट्रेडिंग टीम।\n\n🌐 <b>जारी रखने के लिए कृपया अपनी भाषा चुनें।</b>\n<i>आप बाद में /language से कभी भी बदल सकते हैं।</i>",
    "lang_set_ok": "✅ <b>भाषा सेट हो गई।</b> मुख्य मेनू लोड हो रहा है…",
    "welcome_title": "💎 <b>ImperiumFX में आपका स्वागत है</b> 💎",
    "welcome_body": "💎 <b>ImperiumFX में आपका स्वागत है</b> 💎\n\nPU Prime ट्रेडर्स के लिए प्रीमियम VIP सिग्नल और IB पार्टनरशिप का घर।\n\n<b>आज आप यहाँ क्यों आए हैं?</b>\n\n💎 <b>VIP Access</b> — प्राइवेट सिग्नल, सेटअप और लाइव कॉल्स\n🤝 <b>IB Affiliate</b> — पार्टनर बनें और कमीशन कमाएं\n👥 <b>टीम से मिलें</b> — देखिए ImperiumFX को कौन चलाता है\n🌐 <b>हमें फॉलो करें</b> — Instagram और TikTok\n❓ <b>FAQ</b> — सामान्य सवालों के तुरंत जवाब\n\n<i>जारी रखने के लिए नीचे कोई विकल्प दबाएं।</i>",
    "resume_prompt": "<b>आपकी प्रगति पहले से बॉट में मौजूद है।</b>\n\nक्या आप <b>फिर से शुरू</b> करना चाहते हैं, या अपनी मौजूदा प्रगति रखना चाहते हैं?",
    "restart_yes_msg": "💎 <b>ImperiumFX में आपका स्वागत है</b> 💎\n\nनीचे अपना रास्ता चुनें।",
    "restart_no_msg": "प्रगति सुरक्षित है। जारी रखने के लिए नीचे कोई बटन दबाएं।",
    "back_short_welcome": "💎 <b>ImperiumFX में आपका स्वागत है</b> 💎\n\nनीचे अपना रास्ता चुनें।\n\n💎 <b>VIP Access</b> — हमारे VIP सिग्नल में शामिल हों\n🤝 <b>IB Affiliate</b> — एफिलिएट बनें और IB प्रक्रिया का पालन करें\n\n<i>कृपया वह विकल्प चुनें जो आपके लिए सही है।</i>",
    "help_text": "<b>ImperiumFX Bot - सहायता</b>\n\n- /start - मुख्य मेनू खोलें\n- /status - अपनी प्रगति देखें\n- /language - भाषा बदलें\n- /help - यह संदेश दिखाएं\n\nअगर आप अटक जाएं, तो किसी भी मेनू से <b>Contact Support</b> दबाएं।",
    "status_title": "<b>आपकी स्थिति</b>",
    "status_no_record": "अभी तक कोई रिकॉर्ड नहीं मिला। शुरू करने के लिए /start दबाएं।",
    "status_path": "रास्ता",
    "status_flow": "प्रक्रिया",
    "status_vip_submitted": "VIP जमा किया",
    "status_aff_submitted": "Affiliate जमा किया",
    "status_funded": "Funded VIP",
    "yes": "हाँ",
    "no": "नहीं",
    "status_field_status": "स्थिति",
    "dash": "-",
    "access_disabled": "एक्सेस बंद है। सपोर्ट से संपर्क करें।",
    "slow_down": "थोड़ा धीमे",
    "fallback_unknown": "मुझे समझ नहीं आया — यह मेनू है।\nशुरू करने के लिए /start दबाएं।",
    "fallback_media": "मुझे समझ नहीं आया — यह मेनू है। शुरू करने के लिए /start दबाएं।",
    "team_title": "<b>टीम से मिलें</b>",
    "team_footer": "<i>उनसे सीधे बात करने के लिए नीचे कोई बटन दबाएं।</i>",
    "socials_body": "<b>ImperiumFX को फॉलो करें</b>\n\nहमारे नवीनतम कंटेंट, ट्रेड्स और टीम अपडेट्स के साथ जुड़े रहें।\n\nनीचे दिए बटन से हमारे चैनलों पर जाएं।",
    "faq_intro": "<b>अक्सर पूछे जाने वाले सवाल</b>\n\nनीचे कोई सवाल चुनें।",
    "vip_access_body": "<b>VIP Access</b>\n\nनीचे अपना VIP रास्ता चुनें।\n\n<b>Free VIP</b> — हमारे IB के तहत रजिस्टर करें और पात्रता के लिए डिपॉज़िट करें।\n<b>Paid VIP</b> — सीधी एक्सेस (Live या Funded खाता)।",
    "vip_free_body": "<b>Free VIP</b>\n\nपात्र होने के लिए, आपको <b>इनमें से एक</b> करना होगा:\n\n1. हमारे IB कोड <code>{IB_CODE}</code> के तहत नया PU Prime खाता खोलें।\n2. यदि आप पहले से PU Prime उपयोगकर्ता हैं, तो हमारे IB के तहत ट्रांसफर करें।\n\nपूरी प्रक्रिया के लिए नीचे अपना मार्ग चुनें।",
    "vip_paid_body": "<b>Paid VIP</b>\n\nजो खाता आप उपयोग करते हैं वह चुनें।\n\n<b>Live Account</b> — आपकी PU Prime डिपॉज़िट के ज़रिए सीधी एक्सेस।\n<b>Funded Account</b> — Funded ट्रेडर्स के लिए क्रिप्टो में भुगतान।",
    "vip_paid_live_body": "<b>Paid VIP - Live Account</b>\n\nलाइव खातों के लिए आपकी एक्सेस PU Prime डिपॉज़िट के ज़रिए है।\n\n<b>आवश्यक:</b>\n- हमारे IB कोड <code>{IB_CODE}</code> के तहत खाता\n- न्यूनतम डिपॉज़िट पूरा हुआ\n- आपका MT5 UID / खाता नंबर जमा करें\n\nजारी रखने के लिए नीचे <b>Submit UID</b> दबाएं।",
    "vip_paid_funded_body": "<b>Paid VIP - Funded Account</b>\n\n<b>मूल्य:</b>\n- पहले महीने <b>EUR 50</b>\n- इसके बाद <b>EUR 80</b>/माह\n\n<b>भुगतान के तरीके:</b>\nBTC / ETH / SOL — नीचे पता देखें।\n\nभुगतान के बाद, अपने ट्रांज़ैक्शन का सबूत भेजें।",
    "vip_new_body": "<b>VIP Access - PU Prime में नए</b>\n\nइन चरणों का क्रम से पालन करें:\n\n1️⃣ हमारे IB कोड <code>{IB_CODE}</code> के तहत रजिस्टर करें\n2️⃣ रजिस्ट्रेशन पूरा होने की पुष्टि करें\n3️⃣ अपने खाते में डिपॉज़िट करें\n4️⃣ अपना MT5 UID जमा करें",
    "vip_existing_body": "<b>VIP Access - मौजूदा PU Prime उपयोगकर्ता</b>\n\nइन चरणों का क्रम से पालन करें:\n\n1️⃣ हमारे ट्रांसफर ईमेल टेम्पलेट को देखें\n2️⃣ ईमेल PU Prime को भेजें\n3️⃣ अपना MT5 UID जमा करें",
    "vip_registered_msg": "<b>रजिस्ट्रेशन पूरा के रूप में चिह्नित।</b>\n\n<b>अगली आवश्यकता:</b> Free VIP के लिए एक डिपॉज़िट करें।\nतैयार होने पर <b>Step 3: I Deposited</b> दबाएं।",
    "vip_must_register_first": "<b>आपको पहले रजिस्ट्रेशन पूरा करना होगा।</b>\n\nकृपया मेनू के अनुसार चरणों का पालन करें।",
    "vip_deposit_done_msg": "<b>डिपॉज़िट पूरा के रूप में चिह्नित।</b>\n\nअब आप अपना MT5 UID जमा कर सकते हैं।",
    "vip_existing_deposit_done_msg": "<b>डिपॉज़िट पूरा के रूप में चिह्नित।</b>\n\nअब आप अपना MT5 UID जमा कर सकते हैं।",
    "vip_transfer_email_body": "<b>VIP ट्रांसफर ईमेल टेम्पलेट</b>\n\n<b>प्रति:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n<b>विषय:</b>\n<code>IB transfer request</code>\n\n<b>मुख्य भाग:</b>\n<code>Hello,\nPlease transfer my PU Prime account to IB account {IB_ACCOUNT_NUMBER} (code {IB_CODE}).\nMT5 UID: &lt;your UID&gt;\nThanks.</code>\n\nईमेल भेजने के बाद <b>I Sent the Email</b> दबाएं।",
    "vip_transfer_sent_msg": "<b>ट्रांसफर ईमेल भेजा गया के रूप में चिह्नित।</b>\n\nपुष्टि के लिए PU Prime की प्रतीक्षा करें, फिर आप अपना UID जमा कर सकते हैं।",
    "vip_must_send_transfer_first": "<b>पहले ट्रांसफर ईमेल भेजना होगा।</b>\n\nकृपया मेनू के अनुसार चरणों का पालन करें।",
    "ib_affiliate_body": "<b>IB Affiliate सेटअप</b>\n\nयह उन उपयोगकर्ताओं के लिए है जो PU Prime के तहत हमारे उप-सहयोगी बनना चाहते हैं।\n\nअगर आप IB नहीं समझते, तो पहले ट्यूटोरियल देखें।",
    "what_is_ib_msg": "नीचे <b>ट्यूटोरियल PDF</b> से शुरू करें।\n\n<b>अगला चरण:</b> तैयार होने पर मुख्य Affiliate मेनू पर लौटें।",
    "pdf_missing": "ट्यूटोरियल PDF नहीं मिली।\n\nबॉट के साथ <b>{PDF}</b> उसी फोल्डर में रखें।",
    "pdf_caption": "IB ट्यूटोरियल गाइड",
    "affiliate_main_body": "<b>IB Affiliate मेनू</b>\n\nअपनी स्थिति से मेल खाने वाला रास्ता चुनें।",
    "flow_new_body": "<b>IB Affiliate - PU Prime में नए</b>\n\nइन चरणों का क्रम से पालन करें:\n\n1️⃣ हमारे IB कोड <code>{IB_CODE}</code> के तहत रजिस्टर करें\n2️⃣ रजिस्ट्रेशन पूरा होने की पुष्टि करें\n3️⃣ अपना MT5 UID जमा करें",
    "flow_existing_body": "<b>IB Affiliate - मौजूदा PU Prime उपयोगकर्ता</b>\n\nइन चरणों का क्रम से पालन करें:\n\n1️⃣ हमारे ट्रांसफर ईमेल टेम्पलेट को देखें\n2️⃣ ईमेल PU Prime को भेजें\n3️⃣ अपना MT5 UID जमा करें",
    "affiliate_registered_msg": "<b>रजिस्ट्रेशन पूरा के रूप में चिह्नित।</b>\n\nअब आप अपना MT5 UID जमा कर सकते हैं।",
    "affiliate_transfer_email_body": "<b>IB ट्रांसफर ईमेल टेम्पलेट</b>\n\n<b>प्रति:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n<b>विषय:</b>\n<code>IB transfer request</code>\n\n<b>मुख्य भाग:</b>\n<code>Hello,\nPlease transfer my PU Prime account to IB account {IB_ACCOUNT_NUMBER} (code {IB_CODE}).\nMT5 UID: &lt;your UID&gt;\nThanks.</code>\n\nईमेल भेजने के बाद <b>I Sent the Email</b> दबाएं।",
    "affiliate_transfer_sent_msg": "<b>ईमेल भेजा गया के रूप में चिह्नित।</b>\n\nपुष्टि के लिए PU Prime की प्रतीक्षा करें, फिर आप अपना UID जमा कर सकते हैं।",
    "affiliate_must_register": "<b>आपको पहले रजिस्ट्रेशन पूरा करना होगा।</b>\n\nकृपया मेनू के अनुसार चरणों का पालन करें।",
    "affiliate_must_send_transfer": "<b>पहले ट्रांसफर ईमेल भेजना होगा।</b>\n\nकृपया मेनू के अनुसार चरणों का पालन करें।",
    "benefits_body": "<b>IB लाभ</b>\n\n- व्यवस्थित ऑनबोर्डिंग\n- सीधा एडमिन समर्थन\n- मुफ्त VIP सिग्नल एक्सेस\n- उप-सहयोगी आयोग संरचना\n- विशेष टीम चैनल",
    "show_btc_body": "<b>BTC पता</b>\n\n<code>{ADDR}</code>\n\n<i>कॉपी करने के लिए पते पर टैप करें। भेजने के बाद <b>I Sent Payment</b> दबाएं।</i>",
    "show_eth_body": "<b>ETH पता</b>\n\n<code>{ADDR}</code>\n\n<i>कॉपी करने के लिए पते पर टैप करें। भेजने के बाद <b>I Sent Payment</b> दबाएं।</i>",
    "show_sol_body": "<b>SOL पता</b>\n\n<code>{ADDR}</code>\n\n<i>कॉपी करने के लिए पते पर टैप करें। भेजने के बाद <b>I Sent Payment</b> दबाएं।</i>",
    "funded_payment_sent_msg": "<b>भुगतान भेजा गया के रूप में चिह्नित।</b>\n\nअब अपना भुगतान प्रमाण जमा करें।",
    "funded_already_submitted": "<b>आपका भुगतान प्रमाण पहले ही प्राप्त हो चुका है।</b>\n\nकृपया हमारी समीक्षा की प्रतीक्षा करें।",
    "funded_must_send_first": "<b>पहले भुगतान को भेजा गया के रूप में चिह्नित करें।</b>\n\nकृपया चरणों का पालन करें।",
    "funded_proof_prompt": "अपना <b>भुगतान प्रमाण</b> अभी भेजें।\n\n<b>आवश्यक कैप्शन प्रारूप:</b>\n<code>Amount: 80 EUR\nTX/Ref: &lt;hash या reference&gt;\nMethod: BTC|ETH|SOL</code>\n\nआप स्क्रीनशॉट के साथ कैप्शन भी भेज सकते हैं।",
    "funded_waiting_review_msg": "<b>आपका Funded VIP भुगतान प्रमाण पहले से समीक्षाधीन है।</b>\n\nकुछ और करने की ज़रूरत नहीं है।",
    "funded_proof_received": "<b>भुगतान प्रमाण प्राप्त हुआ।</b>\n\nआपका Funded VIP भुगतान अब समीक्षा के अधीन है। स्वीकृत होने पर आपको DM मिलेगी।",
    "submit_uid_prompt": "अभी अपना <b>MT5 UID / खाता नंबर</b> भेजें।\n\nबस नंबर टाइप करें — उदाहरण:\n\n<code>12345678</code>\n\n<i>अगर स्क्रीनशॉट या डॉक्युमेंट भेज रहे हैं, तो कैप्शन में अपना UID शामिल करें।</i>",
    "uid_format_guide": "<b>UID पहचाना नहीं गया।</b>\n\nकृपया बस अपना MT5 UID भेजें — उदाहरण:\n\n<code>12345678</code>",
    "payment_format_guide": "<b>अमान्य भुगतान प्रमाण प्रारूप।</b>\n\nयदि आप स्क्रीनशॉट के साथ भुगतान भेज रहे हैं, तो कैप्शन में शामिल करें:\n<code>Amount: 80 EUR\nTX/Ref: &lt;hash या reference&gt;\nMethod: BTC|ETH|SOL</code>",
    "uid_caption_invalid": "<b>कैप्शन में UID नहीं मिला।</b>\n\nअगर स्क्रीनशॉट या फ़ाइल भेज रहे हैं, तो कैप्शन में अपना UID शामिल करें — उदाहरण:\n\n<code>12345678</code>",
    "uid_already_registered": "<b>यह UID पहले से किसी अन्य उपयोगकर्ता के लिए पंजीकृत है।</b>\n\nयदि यह एक त्रुटि है, तो सपोर्ट से संपर्क करें।",
    "uid_not_ready_new_vip": "<b>आप अभी UID जमा करने के लिए तैयार नहीं हैं।</b>\n\nVIP एक्सेस के लिए पहले रजिस्टर और डिपॉज़िट करें।",
    "uid_not_ready_existing_vip": "<b>आप अभी UID जमा करने के लिए तैयार नहीं हैं।</b>\n\nVIP एक्सेस के लिए पहले ट्रांसफर ईमेल भेजें।",
    "vip_already_submitted": "<b>आपकी VIP सबमिशन पहले ही प्राप्त हो चुकी है।</b>\n\nकृपया समीक्षा की प्रतीक्षा करें।",
    "aff_already_submitted": "<b>आपकी एफिलिएट सबमिशन पहले ही प्राप्त हो चुकी है।</b>\n\nकृपया समीक्षा की प्रतीक्षा करें।",
    "submission_received_text": "<b>सबमिशन प्राप्त हुआ।</b>\n\nआपका विवरण समीक्षा के लिए भेज दिया गया है। स्वीकृत होने पर आपको DM मिलेगी।",
    "submission_received_media": "<b>सबमिशन प्राप्त हुआ।</b>\n\nआपकी फ़ाइल समीक्षा के लिए भेज दी गई है। स्वीकृत होने पर आपको DM मिलेगी।",
    "vip_waiting_review_msg": "<b>आपकी VIP सबमिशन पहले से समीक्षाधीन है।</b>\n\nकुछ और करने की ज़रूरत नहीं है।",
    "aff_waiting_review_msg": "<b>आपकी एफिलिएट सबमिशन पहले से समीक्षाधीन है।</b>\n\nकुछ और करने की ज़रूरत नहीं है।",
    "support_body": "<b>Contact Support</b>\n\nअपने प्रश्न के लिए सबसे उपयुक्त एडमिन चुनें।",
    "approved_dm": "<b>आपकी सबमिशन स्वीकृत कर दी गई है।</b>\n\nएक एडमिन जल्द ही अगले चरणों के साथ आपसे संपर्क करेगा। 🎉",
    "rejected_dm": "<b>इस चरण पर आपकी सबमिशन स्वीकृत नहीं हुई।</b>\n\nविस्तार के लिए कृपया सपोर्ट से संपर्क करें।",
    "nudge_24h": "बस जांच कर रहे हैं।\n\nअगर आप ImperiumFX सेटअप में अटक गए हैं, तो सपोर्ट से संपर्क करें या /start दबाएं।",
    "nudge_72h_deposit": "आपने अपना डिपॉज़िट पूरा बताया था — अपना UID जमा करना न भूलें।\nजारी रखने के लिए /start दबाएं।",
    "renewal_reminder": "<b>Funded VIP नवीकरण अनुस्मारक</b>\n\nआपका नवीकरण <b>{DAYS} दिन</b> में देय है।\nनवीकरण <b>EUR 80</b> है। भुगतान के लिए /start -> Paid VIP -> Funded दबाएं।\n\n<b>वॉलेट:</b>\nBTC: <code>{BTC}</code>\nETH: <code>{ETH}</code>\nSOL: <code>{SOL}</code>",
    "fallback_msg": "मुझे समझ नहीं आया — कृपया नीचे दिए बटनों का उपयोग करें।",
    "uid_bad_format": "<b>UID पहचाना नहीं गया।</b>\nकृपया बस अपना MT5 UID भेजें — उदाहरण:\n<code>12345678</code>",
    "vip_uid_received": "<b>VIP सबमिशन प्राप्त हुआ।</b>\nहमारी टीम जल्द ही इसकी समीक्षा करेगी और स्वीकृत होने पर आपको DM करेगी। ✅",
    "aff_uid_received": "<b>एफिलिएट सबमिशन प्राप्त हुआ।</b>\nहमारी टीम आपकी IB उप-सहयोगी स्थिति की पुष्टि करेगी और आपको DM करेगी। ✅",
    "funded_submit_bad_format": "<b>प्रारूप समझ नहीं आया।</b>\nकृपया भेजें:\n<code>Amount: 80 EUR\nTX/Ref: &lt;hash या reference&gt;\nMethod: BTC|ETH|SOL</code>\nया उसी कैप्शन के साथ प्रमाण की छवि भेजें।",
    "funded_submit_received": "<b>Funded VIP भुगतान प्राप्त हुआ।</b>\nहम अभी सत्यापित कर रहे हैं — एक्सेस मिलते ही आपको DM करेंगे। 🔒",
    "nudge_incomplete": "<b>क्या आप अभी भी VIP में रुचि रखते हैं?</b>\nआपने शुरू किया लेकिन पूरा नहीं किया — जहां रुके थे वहीं से जारी रखने के लिए /start दबाएं।",
    "faq_q1": "VIP एक्सेस क्या है?",
    "faq_a1": "<b>VIP एक्सेस</b> आपको हमारे प्राइवेट सिग्नल, सेटअप और ट्रेड कॉल देता है। Free VIP के लिए हमारे IB के तहत आना और डिपॉज़िट करना आवश्यक है। Paid VIP (funded) funded खाता ट्रेडर्स के लिए सीधी एक्सेस है।",
    "faq_q2": "IB क्या है?",
    "faq_a2": "<b>IB (Introducing Broker)</b> का मतलब है कि आपका ट्रेडिंग खाता हमारे पार्टनर कोड के तहत रजिस्टर या ट्रांसफर है। हम आपके स्प्रेड से छोटा कमीशन कमाते हैं — <b>आप पर कोई अतिरिक्त शुल्क नहीं</b> — और बदले में आपको मुफ्त VIP एक्सेस मिलता है।",
    "faq_q3": "समीक्षा में कितना समय लगता है?",
    "faq_a3": "समीक्षा <b>आमतौर पर 24 घंटे के भीतर</b> होती है। अगर उससे ज़्यादा हो गया है, तो सपोर्ट से संपर्क करें।",
    "faq_q4": "मेरा UID क्यों स्वीकार नहीं हुआ?",
    "faq_a4": "सामान्य कारण: खाता हमारे IB कोड <code>{IB_CODE}</code> के तहत नहीं है, कोई डिपॉज़िट नहीं हुआ, या गलत प्रारूप। सुनिश्चित करें कि आप सही UID और ईमेल भेज रहे हैं।",
    "faq_q5": "Funded VIP की कीमत क्या है?",
    "faq_a5": "पहले महीने <b>EUR 50</b>, फिर <b>EUR 80</b>/माह। भुगतान BTC, ETH या SOL में स्वीकार किया जाता है।",
    "faq_q6": "न्यूनतम डिपॉज़िट क्या है?",
    "faq_a6": "PU Prime न्यूनतम डिपॉज़िट निर्धारित करता है। हम VIP पात्रता के लिए कम से कम <b>USD 100</b> की सलाह देते हैं।",
    "btn_vip_access": "💎 VIP एक्सेस में शामिल हों",
    "btn_ib_affiliate": "🤝 IB एफिलिएट बनें",
    "btn_team": "👥 टीम से मिलें",
    "btn_socials": "🌐 हमें फॉलो करें",
    "btn_faq": "❓ FAQ",
    "btn_support": "💬 सपोर्ट से संपर्क करें",
    "btn_back": "◀️ वापस",
    "btn_back_to_start": "🏠 शुरुआत पर वापस",
    "btn_back_to_vip": "◀️ VIP मेनू पर वापस",
    "btn_back_to_affiliate": "◀️ एफिलिएट मेनू पर वापस",
    "btn_yes_restart": "🔄 हाँ, फिर से शुरू करें",
    "btn_no_keep": "✅ नहीं, प्रगति रखें",
    "btn_free_vip": "🎁 Free VIP",
    "btn_paid_vip": "👑 Paid VIP",
    "btn_new_to_pu": "🆕 PU Prime में नए",
    "btn_existing_pu": "📂 पहले से PU Prime के साथ",
    "btn_live_account": "📊 Live खाता",
    "btn_funded_account": "🏦 Funded खाता",
    "btn_dont_know_ib": "🤔 मुझे IB नहीं पता",
    "btn_already_know": "✅ मुझे पता है, जारी रखें",
    "btn_continue": "➡️ जारी रखें",
    "btn_step1_register": "1️⃣ चरण 1: PU Prime के साथ रजिस्टर करें",
    "btn_step1_start_reg": "1️⃣ चरण 1: रजिस्ट्रेशन शुरू करें",
    "btn_step2_completed": "2️⃣ चरण 2: मैंने रजिस्ट्रेशन पूरा किया",
    "btn_step3_deposited": "3️⃣ चरण 3: मैंने डिपॉज़िट किया",
    "btn_step4_submit_uid": "4️⃣ चरण 4: UID जमा करें",
    "btn_step3_submit_uid": "3️⃣ चरण 3: UID जमा करें",
    "btn_step1_view_email": "1️⃣ चरण 1: ट्रांसफर ईमेल देखें",
    "btn_step2_sent_email": "2️⃣ चरण 2: मैंने ईमेल भेज दिया",
    "btn_view_btc": "₿ BTC पता देखें",
    "btn_view_eth": "Ξ ETH पता देखें",
    "btn_view_sol": "◎ SOL पता देखें",
    "btn_sent_payment": "💸 मैंने भुगतान भेज दिया",
    "btn_submit_proof": "📤 भुगतान प्रमाण जमा करें",
    "btn_waiting_payment_review": "⏳ भुगतान समीक्षा की प्रतीक्षा",
    "btn_waiting_review": "⏳ समीक्षा की प्रतीक्षा",
    "btn_benefits": "🎯 IB लाभ",
    "btn_message": "💬 संदेश",
    "btn_founder": "👑 संस्थापक - Kratos",
    "btn_onboarding": "🚀 ऑनबोर्डिंग / जनरल - Apollo",
    "btn_signals": "📈 सिग्नल - Plato",
    "btn_socials_admin": "📱 सोशल - HD",
    "btn_change_language": "🌐 भाषा बदलें",
    "btn_approve": "✅ स्वीकृत करें",
    "btn_reject": "❌ अस्वीकार करें",
    "btn_block_user": "🚫 उपयोगकर्ता ब्लॉक करें",
}

TEXTS["ar"] = {
    "lang_picker_title": "✨ <b>أهلاً بك في ImperiumFX</b> ✨\n\nبوابتك للتداول المميّز — إشارات VIP مختارة، شراكات IB، وفريق يتداول فعلاً.\n\n🌐 <b>يرجى اختيار لغتك للمتابعة.</b>\n<i>يمكنك تغييرها لاحقاً عبر /language.</i>",
    "lang_set_ok": "✅ <b>تم ضبط اللغة.</b> جارٍ تحميل القائمة الرئيسية…",

    "welcome_title": "💎 <b>أهلاً بك في ImperiumFX</b> 💎",
    "welcome_body": "💎 <b>أهلاً بك في ImperiumFX</b> 💎\n\nموطن إشارات VIP المميّزة وشراكات IB لمتداولي PU Prime.\n\n<b>ما الذي جاء بك اليوم؟</b>\n\n💎 <b>وصول VIP</b> — إشارات خاصة وإعدادات ومكالمات مباشرة\n🤝 <b>شراكة IB</b> — كن شريكًا واكسب العمولات\n👥 <b>تعرّف على الفريق</b> — تعرّف على من يدير ImperiumFX\n🌐 <b>تابعنا</b> — إنستغرام وتيك توك\n❓ <b>الأسئلة الشائعة</b> — إجابات سريعة لأكثر الأسئلة شيوعًا\n\n<i>اضغط على أحد الخيارات أدناه للمتابعة.</i>",
    "resume_prompt": (
        "<b>لديك تقدم حالي في البوت.</b>\n\n"
        "هل تريد <b>إعادة البدء</b> من البداية، أم الاحتفاظ بتقدمك الحالي؟"
    ),
    "restart_yes_msg": "💎 <b>أهلاً بك في ImperiumFX</b> 💎\n\nاختر مسارك من الأسفل.",
    "restart_no_msg": "تم الاحتفاظ بالتقدم. اضغط على زر من الأسفل للمتابعة.",
    "back_short_welcome": "💎 <b>أهلاً بك في ImperiumFX</b> 💎\n\nاختر مسارك من الأسفل.\n\n💎 <b>وصول VIP</b> — انضم إلى قناة إشاراتنا الحصرية\n🤝 <b>شراكة IB</b> — كن شريكًا واتبع خطوات تسجيل IB\n\n<i>يرجى اختيار الخيار الذي يناسبك.</i>",

    "help_text": (
        "<b>بوت ImperiumFX - المساعدة</b>\n\n"
        "- /start - فتح القائمة الرئيسية\n"
        "- /status - مشاهدة تقدمك\n"
        "- /language - تغيير اللغة\n"
        "- /help - عرض هذه الرسالة\n\n"
        "إذا واجهت مشكلة، اضغط <b>تواصل مع الدعم</b> من أي قائمة."
    ),
    "status_title": "<b>حالتك</b>",
    "status_no_record": "لم يتم العثور على سجل بعد. اضغط /start للبدء.",
    "status_path": "المسار",
    "status_flow": "الخطوة",
    "status_vip_submitted": "VIP تم التقديم",
    "status_aff_submitted": "الشراكة تم التقديم",
    "status_funded": "VIP ممول",
    "yes": "نعم",
    "no": "لا",
    "status_field_status": "الحالة",
    "dash": "-",

    "access_disabled": "تم تعطيل الوصول. تواصل مع الدعم.",
    "slow_down": "تمهل قليلاً",
    "fallback_unknown": (
        "لم أفهم ذلك - هذه هي القائمة.\n"
        "اضغط /start للبدء، /status لرؤية تقدمك، أو /help للمساعدة."
    ),
    "fallback_media": "لم أفهم ذلك - هذه هي القائمة. اضغط /start للبدء.",

    "team_title": "<b>تعرف على الفريق</b>",
    "team_footer": "<i>اضغط على زر من الأسفل لمراسلتهم مباشرة.</i>",
    "socials_body": (
        "<b>تابع ImperiumFX</b>\n\n"
        "ابق على اطلاع بأحدث محتوياتنا ومعاينات الإشارات والجوائز."
    ),
    "faq_intro": "<b>الأسئلة الشائعة</b>\n\nاختر سؤالاً من الأسفل.",

    "vip_access_body": (
        "<b>وصول VIP</b>\n\n"
        "اختر مسار VIP الخاص بك من الأسفل.\n\n"
        "<b>VIP مجاني</b>\n"
        "- للمستخدمين الذين يأتون تحت شراكة IB الخاصة بنا\n"
        "- يتطلب التسجيل/النقل تحتنا وإيداع\n\n"
        "<b>VIP مدفوع</b>\n"
        "- للمستخدمين الذين يريدون وصولاً مباشرًا\n"
        "- الحسابات الممولة تدفع شهريًا\n\n"
        "<i>اختر الخيار الذي يناسب وضعك.</i>"
    ),
    "vip_free_body": (
        "<b>VIP مجاني</b>\n\n"
        "للتأهل، يجب عليك القيام <b>بأحد</b> الآتي:\n\n"
        "1. <b>التسجيل في PU Prime تحتنا</b>\n"
        "2. <b>نقل حساب PU Prime الحالي تحتنا</b>\n\n"
        "<b>قواعد مهمة:</b>\n"
        "- يجب أن تكون تحت شراكة IB الخاصة بنا\n"
        "- يجب <b>الإيداع</b>\n"
        "- بدون ذلك، <b>لن يتم منح وصول VIP المجاني</b>\n\n"
        "<i>اختر الخيار المناسب من الأسفل.</i>"
    ),
    "vip_paid_body": (
        "<b>VIP مدفوع</b>\n\n"
        "اختر نوع الحساب الذي تستخدمه.\n\n"
        "<b>حساب حقيقي</b>\n"
        "- نفس هيكل VIP المجاني\n"
        "- يجب أن تكون تحت IB الخاص بنا مع إيداع\n\n"
        "<b>حساب ممول</b>\n"
        "- <b>50 يورو</b> الشهر الأول\n"
        "- <b>80 يورو</b> من الشهر الثاني فصاعدًا\n\n"
        "<i>اختر نوع حسابك من الأسفل.</i>"
    ),
    "vip_paid_live_body": (
        "<b>VIP مدفوع - حساب حقيقي</b>\n\n"
        "للحسابات الحقيقية، يتم التعامل مع وصولك من خلال هيكل IB الخاص بنا.\n\n"
        "هذا يعني أنه يجب عليك:\n"
        "1. التسجيل تحتنا أو النقل تحتنا\n"
        "2. الإيداع\n"
        "3. تقديم الـ UID الخاص بك\n\n"
        "<i>اختر مسارك من الأسفل.</i>"
    ),
    "vip_paid_funded_body": (
        "<b>VIP مدفوع - حساب ممول</b>\n\n"
        "<b>السعر:</b>\n"
        "- <b>50 يورو</b> الشهر الأول\n"
        "- <b>80 يورو</b> من الشهر الثاني فصاعدًا\n\n"
        "<b>طرق الدفع:</b>\n"
        "- BTC\n"
        "- ETH\n"
        "- SOL\n\n"
        "<b>الخطوة التالية:</b>\n"
        "1. عرض عنوان المحفظة\n"
        "2. إرسال الدفعة\n"
        "3. تقديم إثبات الدفع\n\n"
        "<i>استخدم الأزرار أدناه.</i>"
    ),
    "vip_new_body": (
        "<b>وصول VIP - مستخدم جديد في PU Prime</b>\n\n"
        "اتبع هذه الخطوات بالترتيب:\n\n"
        "1. <b>التسجيل باستخدام رابطنا</b>\n"
        "2. تأكد من أن الرمز هو <b>{IB_CODE}</b>\n"
        "3. إكمال التسجيل\n"
        "4. <b>الإيداع</b>\n"
        "5. تقديم <b>MT5 UID / رقم الحساب</b>\n\n"
        "<b>مهم:</b>\n"
        "- VIP فقط للمستخدمين تحتنا\n"
        "- التسجيل وحده <b>غير كافٍ</b>\n"
        "- يجب <b>الإيداع</b> قبل مراجعة الوصول\n\n"
        "<i>أكمل الخطوات أدناه بعناية.</i>"
    ),
    "vip_existing_body": (
        "<b>وصول VIP - مستخدم PU Prime حالي</b>\n\n"
        "اتبع هذه الخطوات بالترتيب:\n\n"
        "1. إرسال <b>بريد نقل IB</b>\n"
        "2. انتظار تأكيد النقل\n"
        "3. <b>الإيداع</b>\n"
        "4. تقديم <b>MT5 UID / رقم الحساب</b>\n\n"
        "<b>مهم:</b>\n"
        "- يجب نقل حسابك تحت IB الخاص بنا\n"
        "- يجب <b>الإيداع</b>\n"
        "- بدون ذلك، <b>لن يتم منح وصول VIP</b>\n\n"
        "<i>أكمل الخطوات أدناه بعناية.</i>"
    ),
    "vip_registered_msg": (
        "<b>تم تحديد التسجيل كمكتمل.</b>\n\n"
        "<b>المتطلب التالي:</b> يجب <b>الإيداع</b> قبل تقديم UID لمراجعة VIP.\n\n"
        "<i>لا تتخطى هذه الخطوة.</i>"
    ),
    "vip_must_register_first": (
        "<b>يجب إكمال التسجيل أولاً.</b>\n\n"
        "يرجى اتباع الخطوات بالترتيب.\n\n"
        "<i>يجب إكمال الخطوة 1 قبل الخطوة 3.</i>"
    ),
    "vip_deposit_done_msg": (
        "<b>تم تحديد الإيداع كمكتمل.</b>\n\n"
        "يمكنك الآن تقديم <b>MT5 UID / رقم الحساب</b> لمراجعة VIP."
    ),
    "vip_existing_deposit_done_msg": (
        "<b>تم تحديد الإيداع كمكتمل.</b>\n\n"
        "يمكنك الآن تقديم <b>MT5 UID / رقم الحساب</b> لمراجعة VIP."
    ),
    "vip_transfer_email_body": (
        "<b>قالب بريد نقل VIP</b>\n\n"
        "<b>إلى:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>الموضوع:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>المحتوى:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<b>مهم:</b> بعد تأكيد النقل، يجب <b>الإيداع</b> للتأهل لـ VIP."
    ),
    "vip_transfer_sent_msg": (
        "<b>تم تحديد بريد النقل كمرسل.</b>\n\n"
        "انتظر PU Prime لتأكيد نقل IB.\n\n"
        "<b>بعد ذلك:</b>\n"
        "- الإيداع\n"
        "- ثم تقديم UID\n\n"
        "<i>هذا مطلوب لمراجعة VIP.</i>"
    ),
    "vip_must_send_transfer_first": (
        "<b>يجب إرسال بريد النقل أولاً.</b>\n\n"
        "اتبع خطوات نقل VIP بالترتيب."
    ),

    "ib_affiliate_body": (
        "<b>إعداد شراكة IB</b>\n\n"
        "هذا المسار للمستخدمين الذين يرغبون في فهم نموذج IB وإكمال عملية تسجيل الشراكة.\n\n"
        "<i>اختر ما إذا كنت تحتاج دليل المبتدئين أو تريد المتابعة مباشرة.</i>"
    ),
    "what_is_ib_msg": (
        "ابدأ بـ <b>دليل PDF</b> أدناه.\n\n"
        "<b>الخطوة التالية:</b> بعد قراءته، اضغط <b>متابعة</b>."
    ),
    "pdf_missing": "لم يتم العثور على دليل PDF.\n\nضع <b>{PDF}</b> في نفس مجلد <b>ib_bot.py</b>.",
    "pdf_caption": "دليل IB التعليمي",
    "affiliate_main_body": "<b>قائمة شراكة IB</b>\n\nاختر المسار الذي يناسب وضعك.",
    "flow_new_body": (
        "<b>شراكة IB - مستخدم PU Prime جديد</b>\n\n"
        "اتبع هذه الخطوات بالترتيب:\n\n"
        "1. <b>بدء التسجيل</b>\n"
        "2. تأكد من أن الرمز هو <b>{IB_CODE}</b>\n"
        "3. إكمال التسجيل والتحقق\n"
        "4. اضغط <b>لقد أكملت التسجيل</b>\n"
        "5. تقديم <b>MT5 UID / رقم الحساب</b>\n\n"
        "<b>مهم:</b> لا تتخطى الخطوات.\n\n"
        "<i>اضغط الخطوة 1 أدناه للبدء.</i>"
    ),
    "flow_existing_body": (
        "<b>شراكة IB - مستخدم PU Prime حالي</b>\n\n"
        "اتبع هذه الخطوات بالترتيب:\n\n"
        "1. افتح <b>قالب بريد النقل</b>\n"
        "2. أرسل البريد إلى PU Prime\n"
        "3. اضغط <b>لقد أرسلت البريد</b>\n"
        "4. انتظر PU Prime لتأكيد النقل\n"
        "5. تقديم <b>MT5 UID / رقم الحساب</b>\n\n"
        "<i>يرجى إكمال كل خطوة بالترتيب.</i>"
    ),
    "affiliate_registered_msg": (
        "<b>تم تحديد التسجيل كمكتمل.</b>\n\n"
        "يمكنك الآن إرسال <b>MT5 UID / رقم الحساب</b> هنا.\n\n"
        "<i>يرجى التأكد من أن تنسيق UID صحيح قبل الإرسال.</i>"
    ),
    "affiliate_transfer_email_body": (
        "<b>قالب بريد نقل IB</b>\n\n"
        "<b>إلى:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>الموضوع:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>المحتوى:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<i>أرسل هذا البريد، ثم عد هنا واضغط الخطوة 2.</i>"
    ),
    "affiliate_transfer_sent_msg": (
        "<b>تم تحديد البريد كمرسل.</b>\n\n"
        "انتظر PU Prime لتأكيد نقل IB.\n\n"
        "بمجرد التأكيد، قدم <b>MT5 UID / رقم الحساب</b> هنا."
    ),
    "affiliate_must_register": (
        "<b>يجب إكمال التسجيل أولاً.</b>\n\n"
        "اتبع خطوات الشراكة بالترتيب."
    ),
    "affiliate_must_send_transfer": (
        "<b>يجب إرسال بريد النقل أولاً.</b>\n\n"
        "اتبع خطوات الشراكة بالترتيب."
    ),
    "benefits_body": (
        "<b>فوائد IB</b>\n\n"
        "- عملية تسجيل منظمة\n"
        "- دعم مباشر من المشرف\n"
        "- عملية إعداد واضحة\n"
        "- الوصول إلى المرحلة التالية بعد التحقق\n\n"
        "<i>عد وتابع المسار الصحيح.</i>"
    ),

    "show_btc_body": (
        "<b>عنوان BTC</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>اضغط على العنوان للنسخ. بعد إرسال الدفعة، اضغط لقد دفعت ثم قدم الإثبات.</i>"
    ),
    "show_eth_body": (
        "<b>عنوان ETH</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>اضغط على العنوان للنسخ. بعد إرسال الدفعة، اضغط لقد دفعت ثم قدم الإثبات.</i>"
    ),
    "show_sol_body": (
        "<b>عنوان SOL</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>اضغط على العنوان للنسخ. بعد إرسال الدفعة، اضغط لقد دفعت ثم قدم الإثبات.</i>"
    ),
    "funded_payment_sent_msg": (
        "<b>تم تحديد الدفعة كمرسلة.</b>\n\n"
        "الآن قدم إثبات الدفع.\n\n"
        "<b>مهم:</b> إذا أرسلت لقطة شاشة أو مستندًا، يجب أن يكون التعليق:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "funded_already_submitted": (
        "<b>تم استلام إثبات الدفع الخاص بك.</b>\n\n"
        "يرجى انتظار المراجعة أو تواصل مع الدعم إذا لزم الأمر."
    ),
    "funded_must_send_first": (
        "<b>يجب تحديد الدفعة كمرسلة أولاً.</b>\n\n"
        "اتبع خطوات VIP الممولة بالترتيب."
    ),
    "funded_proof_prompt": (
        "أرسل <b>إثبات الدفع</b> الآن.\n\n"
        "<b>تنسيق التعليق المطلوب:</b>\n"
        "<code>PAYMENT: FUNDED</code>\n\n"
        "<i>لقطة شاشة أو مستند فقط.</i>"
    ),
    "funded_waiting_review_msg": (
        "<b>إثبات دفع VIP الممول الخاص بك قيد المراجعة.</b>\n\n"
        "لا يوجد شيء آخر عليك تقديمه الآن.\n\n"
        "<i>إذا احتجت المساعدة، اضغط تواصل مع الدعم.</i>"
    ),
    "funded_proof_received": (
        "<b>تم استلام إثبات الدفع.</b>\n\n"
        "دفعة VIP الممولة قيد المراجعة الآن.\n\n"
        "<i>انتظر التأكيد أو التعليمات الإضافية.</i>"
    ),

    "submit_uid_prompt": (
        "أرسل <b>MT5 UID / رقم الحساب</b> الآن.\n\n"
        "فقط اكتب الرقم — مثال:\n\n"
        "<code>12345678</code>\n\n"
        "<i>إذا أرسلت لقطة شاشة أو مستندًا، ضمّن الـ UID في التعليق.</i>"
    ),
    "uid_format_guide": (
        "<b>لم يتم التعرف على UID.</b>\n\n"
        "فضلاً أرسل فقط رقم MT5 UID الخاص بك — مثال:\n\n"
        "<code>12345678</code>"
    ),
    "payment_format_guide": (
        "<b>تنسيق إثبات الدفع غير صالح.</b>\n\n"
        "إذا أرسلت إثبات الدفع، يجب أن يكون التعليق بالضبط:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>التعليق لا يحتوي على UID.</b>\n\n"
        "إذا أرسلت لقطة شاشة أو مستندًا، يجب أن يحتوي التعليق على UID — مثال:\n\n"
        "<code>12345678</code>"
    ),
    "uid_already_registered": (
        "<b>هذا UID مسجل بالفعل لمستخدم آخر.</b>\n\n"
        "إذا كنت تعتقد أن هذا خطأ، تواصل مع الدعم."
    ),
    "uid_not_ready_new_vip": (
        "<b>لست جاهزًا لتقديم UID بعد.</b>\n\n"
        "للحصول على VIP كمستخدم <b>جديد</b>، يجب عليك:\n"
        "1. التسجيل تحتنا\n"
        "2. الإيداع\n"
        "3. ثم تقديم UID\n\n"
        "<i>أكمل الخطوات المطلوبة أولاً.</i>"
    ),
    "uid_not_ready_existing_vip": (
        "<b>لست جاهزًا لتقديم UID بعد.</b>\n\n"
        "للحصول على VIP كمستخدم <b>حالي</b>، يجب عليك:\n"
        "1. إرسال بريد النقل\n"
        "2. انتظار التأكيد\n"
        "3. الإيداع\n"
        "4. ثم تقديم UID\n\n"
        "<i>أكمل الخطوات المطلوبة أولاً.</i>"
    ),
    "vip_already_submitted": (
        "<b>تم استلام تقديم VIP الخاص بك.</b>\n\n"
        "انتظر المراجعة أو تواصل مع الدعم إذا لزم الأمر."
    ),
    "aff_already_submitted": (
        "<b>تم استلام تقديم الشراكة الخاص بك.</b>\n\n"
        "انتظر المراجعة أو تواصل مع الدعم إذا لزم الأمر."
    ),
    "submission_received_text": (
        "<b>تم استلام التقديم.</b>\n\n"
        "تم توجيه تفاصيلك للمراجعة.\n\n"
        "<i>انتظر التأكيد أو التعليمات الإضافية.</i>"
    ),
    "submission_received_media": (
        "<b>تم استلام التقديم.</b>\n\n"
        "تم توجيه ملفك للمراجعة.\n\n"
        "<i>انتظر التأكيد أو التعليمات الإضافية.</i>"
    ),
    "vip_waiting_review_msg": (
        "<b>تقديم VIP الخاص بك قيد المراجعة.</b>\n\n"
        "لا يوجد شيء آخر عليك تقديمه الآن.\n\n"
        "<i>إذا احتجت المساعدة، اضغط تواصل مع الدعم.</i>"
    ),
    "aff_waiting_review_msg": (
        "<b>تقديم الشراكة الخاص بك قيد المراجعة.</b>\n\n"
        "لا يوجد شيء آخر عليك تقديمه الآن.\n\n"
        "<i>إذا احتجت المساعدة، اضغط تواصل مع الدعم.</i>"
    ),

    "support_body": "<b>تواصل مع الدعم</b>\n\nاختر المشرف الأنسب لسؤالك:",

    "approved_dm": (
        "<b>تمت الموافقة على تقديمك.</b>\n\n"
        "سيتواصل معك المشرف قريبًا بالخطوة التالية."
    ),
    "rejected_dm": (
        "<b>لم تتم الموافقة على تقديمك في هذه المرحلة.</b>\n\n"
        "تواصل مع الدعم لحل المشكلة."
    ),

    "nudge_24h": (
        "مجرد اطمئنان.\n\n"
        "إذا واجهت مشكلة أثناء إعداد ImperiumFX، اضغط /start للاستئناف - "
        "أو اضغط تواصل مع الدعم وسنساعدك."
    ),
    "nudge_72h_deposit": (
        "لقد حددت إيداعك كمكتمل - لا تنسَ تقديم "
        "<b>MT5 UID</b> حتى نكمل وصول VIP."
    ),
    "renewal_reminder": (
        "<b>تذكير تجديد VIP الممول</b>\n\n"
        "تجديدك مستحق خلال <b>{DAYS} يوم</b>.\n"
        "التجديد <b>80 يورو</b>. اضغط /start -> VIP مدفوع -> ممول للدفع.\n\n"
        "<b>المحافظ:</b>\n"
        "BTC: <code>{BTC}</code>\n"
        "ETH: <code>{ETH}</code>\n"
        "SOL: <code>{SOL}</code>"
    ),

    "fallback_msg": "لم أفهم ذلك — يرجى استخدام الأزرار أدناه.",
    "uid_bad_format": (
        "<b>لم يتم التعرف على UID.</b>\n"
        "فضلاً أرسل فقط رقم MT5 UID — مثال:\n"
        "<code>12345678</code>"
    ),
    "vip_uid_received": (
        "<b>تم استلام طلب VIP.</b>\n"
        "سيقوم فريقنا بمراجعته قريبًا وسيراسلك على الخاص عند الموافقة. ✅"
    ),
    "aff_uid_received": (
        "<b>تم استلام طلب الشراكة.</b>\n"
        "سيؤكد فريقنا حالة الشراكة الفرعية ويراسلك على الخاص. ✅"
    ),
    "funded_submit_bad_format": (
        "<b>الصيغة غير معروفة.</b>\n"
        "يرجى إرسال:\n"
        "<code>Amount: 80 EUR\nTX/Ref: &lt;الهاش أو المرجع&gt;\nMethod: BTC|ETH|SOL</code>\n"
        "أو إرسال صورة الإثبات مع نفس التعليق."
    ),
    "funded_submit_received": (
        "<b>تم استلام دفع VIP الممول.</b>\n"
        "نقوم بالتحقق الآن — سنراسلك فور فتح الوصول. 🔒"
    ),
    "nudge_incomplete": (
        "<b>لا تزال مهتمًا بـ VIP؟</b>\n"
        "لقد بدأت ولم تكمل — اضغط /start للعودة من حيث توقفت."
    ),

    "faq_q1": "ما هو وصول VIP؟",
    "faq_a1": (
        "<b>وصول VIP</b> يمنحك إشاراتنا الخاصة وإعدادات وتوصيات التداول. "
        "VIP المجاني يتطلب التسجيل تحت IB الخاص بنا والإيداع. "
        "VIP المدفوع (الممول) هو وصول مباشر لمتداولي الحسابات الممولة."
    ),
    "faq_q2": "ما هو IB؟",
    "faq_a2": (
        "<b>IB (وسيط تعريفي)</b> يعني أن حساب التداول الخاص بك مسجل أو منقول تحت رمز شريكنا. "
        "نحن نكسب عمولة صغيرة من الفارق - <b>بدون أي تكلفة إضافية عليك</b> - "
        "وفي المقابل تحصل على وصول VIP مجاني."
    ),
    "faq_q3": "كم تستغرق المراجعة؟",
    "faq_a3": (
        "المراجعات <b>عادة خلال 24 ساعة</b>. إذا كانت أطول، اضغط "
        "<b>تواصل مع الدعم</b> وسيتابع المشرف."
    ),
    "faq_q4": "لماذا لم يُقبل UID الخاص بي؟",
    "faq_a4": (
        "أسباب شائعة: الحساب ليس تحت رمز IB الخاص بنا، لم يتم الإيداع بعد، أو لم نستطع قراءة الـ UID. "
        "تأكد من استخدام الرمز <code>{IB_CODE}</code>، الإيداع، وأرسلت الأرقام فقط، مثل: <code>12345678</code>"
    ),
    "faq_q5": "كم يكلف VIP الممول؟",
    "faq_a5": (
        "<b>50 يورو</b> للشهر الأول، ثم <b>80 يورو</b>/شهر. "
        "يمكن الدفع بـ BTC أو ETH أو SOL. بعد الدفع، أرسل الإثبات مع التعليق "
        "<code>PAYMENT: FUNDED</code>."
    ),
    "faq_q6": "هل هناك حد أدنى للإيداع؟",
    "faq_a6": (
        "PU Prime يحدد الحد الأدنى للإيداع. نوصي بما لا يقل عن <b>200 دولار</b> "
        "لحجم مركز ذي معنى والتأهل بسلاسة لـ VIP."
    ),

    "btn_vip_access": "💎 الانضمام إلى VIP",
    "btn_ib_affiliate": "🤝 كن شريك IB",
    "btn_team": "👥 تعرف على الفريق",
    "btn_socials": "🌐 تابعنا",
    "btn_faq": "❓ الأسئلة الشائعة",
    "btn_support": "💬 تواصل مع الدعم",
    "btn_back": "◀️ رجوع",
    "btn_back_to_start": "🏠 العودة للبداية",
    "btn_back_to_vip": "◀️ العودة لقائمة VIP",
    "btn_back_to_affiliate": "◀️ العودة لقائمة الشراكة",
    "btn_yes_restart": "🔄 نعم، إعادة البدء",
    "btn_no_keep": "✅ لا، احتفظ بالتقدم",
    "btn_free_vip": "🎁 VIP مجاني",
    "btn_paid_vip": "👑 VIP مدفوع",
    "btn_new_to_pu": "🆕 جديد في PU Prime",
    "btn_existing_pu": "📂 لدي حساب PU Prime",
    "btn_live_account": "📊 حساب حقيقي",
    "btn_funded_account": "🏦 حساب ممول",
    "btn_dont_know_ib": "🤔 لا أعرف ما هو IB",
    "btn_already_know": "✅ أعرف بالفعل، متابعة",
    "btn_continue": "➡️ متابعة",
    "btn_step1_register": "1️⃣ الخطوة 1: التسجيل في PU Prime",
    "btn_step1_start_reg": "1️⃣ الخطوة 1: بدء التسجيل",
    "btn_step2_completed": "2️⃣ الخطوة 2: أكملت التسجيل",
    "btn_step3_deposited": "3️⃣ الخطوة 3: لقد أودعت",
    "btn_step4_submit_uid": "4️⃣ الخطوة 4: تقديم UID",
    "btn_step3_submit_uid": "3️⃣ الخطوة 3: تقديم UID",
    "btn_step1_view_email": "1️⃣ الخطوة 1: عرض بريد النقل",
    "btn_step2_sent_email": "2️⃣ الخطوة 2: لقد أرسلت البريد",
    "btn_view_btc": "₿ عرض عنوان BTC",
    "btn_view_eth": "Ξ عرض عنوان ETH",
    "btn_view_sol": "◎ عرض عنوان SOL",
    "btn_sent_payment": "💸 لقد دفعت",
    "btn_submit_proof": "📤 تقديم إثبات الدفع",
    "btn_waiting_payment_review": "⏳ بانتظار مراجعة الدفع",
    "btn_waiting_review": "⏳ بانتظار المراجعة",
    "btn_benefits": "🎯 فوائد IB",
    "btn_message": "💬 مراسلة",
    "btn_founder": "👑 المؤسس - Kratos",
    "btn_onboarding": "🚀 الاستقبال / عام - Apollo",
    "btn_signals": "📈 الإشارات - Plato",
    "btn_socials_admin": "📱 السوشيال - HD",
    "btn_change_language": "🌐 تغيير اللغة",
    "btn_approve": "✅ موافقة",
    "btn_reject": "❌ رفض",
    "btn_block_user": "🚫 حظر المستخدم",
}

TEXTS["es"] = {
    "lang_picker_title": "✨ <b>Bienvenido a ImperiumFX</b> ✨\n\nTu puerta al trading premium — señales VIP seleccionadas, alianzas IB y un equipo que realmente opera.\n\n🌐 <b>Por favor elige tu idioma para continuar.</b>\n<i>Puedes cambiarlo en cualquier momento con /language.</i>",
    "lang_set_ok": "✅ <b>Idioma configurado.</b> Cargando el menú principal…",

    "welcome_title": "💎 <b>Bienvenido a ImperiumFX</b> 💎",
    "welcome_body": "💎 <b>Bienvenido a ImperiumFX</b> 💎\n\nEl hogar de las señales VIP premium y alianzas IB para traders de PU Prime.\n\n<b>¿Qué te trae por aquí hoy?</b>\n\n💎 <b>Acceso VIP</b> — señales privadas, setups y llamadas en vivo\n🤝 <b>Afiliado IB</b> — conviértete en socio y gana comisiones\n👥 <b>Conoce al Equipo</b> — descubre quién está detrás de ImperiumFX\n🌐 <b>Síguenos</b> — Instagram y TikTok\n❓ <b>FAQ</b> — respuestas rápidas a preguntas comunes\n\n<i>Pulsa una opción abajo para continuar.</i>",
    "resume_prompt": (
        "<b>Ya tienes progreso en el bot.</b>\n\n"
        "¿Quieres <b>reiniciar</b> desde el principio o mantener tu progreso actual?"
    ),
    "restart_yes_msg": "💎 <b>Bienvenido a ImperiumFX</b> 💎\n\nElige tu ruta a continuación.",
    "restart_no_msg": "Progreso conservado. Pulsa un botón para continuar.",
    "back_short_welcome": "💎 <b>Bienvenido a ImperiumFX</b> 💎\n\nElige tu ruta a continuación.\n\n💎 <b>Acceso VIP</b> — únete a nuestro canal de señales VIP\n🤝 <b>Afiliado IB</b> — conviértete en afiliado y sigue el proceso IB\n\n<i>Por favor elige la opción que mejor se adapte a ti.</i>",

    "help_text": (
        "<b>Bot ImperiumFX - Ayuda</b>\n\n"
        "- /start - abrir el menú principal\n"
        "- /status - ver tu progreso\n"
        "- /language - cambiar idioma\n"
        "- /help - mostrar este mensaje\n\n"
        "Si te atascas, pulsa <b>Contactar Soporte</b> desde cualquier menú."
    ),
    "status_title": "<b>Tu estado</b>",
    "status_no_record": "No se encontró registro. Pulsa /start para comenzar.",
    "status_path": "Ruta",
    "status_flow": "Flujo",
    "status_vip_submitted": "VIP enviado",
    "status_aff_submitted": "Afiliado enviado",
    "status_funded": "VIP Funded",
    "yes": "sí",
    "no": "no",
    "status_field_status": "estado",
    "dash": "-",

    "access_disabled": "Acceso deshabilitado. Contacta soporte.",
    "slow_down": "Más despacio",
    "fallback_unknown": (
        "No entendí eso - aquí tienes el menú.\n"
        "Pulsa /start para comenzar, /status para ver tu progreso, o /help para ayuda."
    ),
    "fallback_media": "No entendí eso - aquí tienes el menú. Pulsa /start para comenzar.",

    "team_title": "<b>Conoce al Equipo</b>",
    "team_footer": "<i>Pulsa un botón para contactarlos directamente.</i>",
    "socials_body": (
        "<b>Sigue a ImperiumFX</b>\n\n"
        "Mantente al día con nuestro contenido, previews de señales y sorteos."
    ),
    "faq_intro": "<b>Preguntas Frecuentes</b>\n\nElige una pregunta abajo.",

    "vip_access_body": (
        "<b>Acceso VIP</b>\n\n"
        "Elige tu ruta VIP a continuación.\n\n"
        "<b>VIP Gratis</b>\n"
        "- para usuarios que vienen bajo nuestro IB\n"
        "- requiere registro/traslado bajo nosotros y depósito\n\n"
        "<b>VIP De Pago</b>\n"
        "- para usuarios que quieren acceso directo\n"
        "- cuentas funded pagan mensualmente\n\n"
        "<i>Selecciona la opción que coincida con tu situación.</i>"
    ),
    "vip_free_body": (
        "<b>VIP Gratis</b>\n\n"
        "Para calificar, debes hacer <b>uno</b> de lo siguiente:\n\n"
        "1. <b>Registrarte con PU Prime bajo nosotros</b>\n"
        "2. <b>Trasladar tu cuenta PU Prime existente bajo nosotros</b>\n\n"
        "<b>Reglas importantes:</b>\n"
        "- Debes estar bajo nuestro IB\n"
        "- Debes <b>depositar</b>\n"
        "- Sin esto, <b>no se otorgará acceso VIP gratis</b>\n\n"
        "<i>Selecciona la opción que coincida con tu situación.</i>"
    ),
    "vip_paid_body": (
        "<b>VIP De Pago</b>\n\n"
        "Elige el tipo de cuenta que usas.\n\n"
        "<b>Cuenta Real</b>\n"
        "- misma estructura que VIP gratis\n"
        "- debes estar bajo nuestro IB y depositar\n\n"
        "<b>Cuenta Funded</b>\n"
        "- <b>50 EUR</b> primer mes\n"
        "- <b>80 EUR</b> a partir del siguiente mes\n\n"
        "<i>Selecciona tu tipo de cuenta.</i>"
    ),
    "vip_paid_live_body": (
        "<b>VIP De Pago - Cuenta Real</b>\n\n"
        "Para cuentas reales, el acceso se maneja a través de nuestra estructura IB.\n\n"
        "Eso significa que debes:\n"
        "1. registrarte bajo nosotros o trasladar bajo nosotros\n"
        "2. depositar\n"
        "3. enviar tu UID\n\n"
        "<i>Selecciona tu ruta abajo.</i>"
    ),
    "vip_paid_funded_body": (
        "<b>VIP De Pago - Cuenta Funded</b>\n\n"
        "<b>Precios:</b>\n"
        "- <b>50 EUR</b> primer mes\n"
        "- <b>80 EUR</b> a partir del siguiente mes\n\n"
        "<b>Métodos de pago:</b>\n"
        "- BTC\n"
        "- ETH\n"
        "- SOL\n\n"
        "<b>Siguiente paso:</b>\n"
        "1. ver la dirección de wallet\n"
        "2. enviar el pago\n"
        "3. enviar comprobante de pago\n\n"
        "<i>Usa los botones abajo.</i>"
    ),
    "vip_new_body": (
        "<b>Acceso VIP - Nuevo en PU Prime</b>\n\n"
        "Sigue estos pasos en orden:\n\n"
        "1. <b>Regístrate usando nuestro enlace</b>\n"
        "2. Asegúrate de que el código sea <b>{IB_CODE}</b>\n"
        "3. Completa el registro\n"
        "4. <b>Deposita</b>\n"
        "5. Envía tu <b>MT5 UID / número de cuenta</b>\n\n"
        "<b>Importante:</b>\n"
        "- VIP es solo para usuarios bajo nosotros\n"
        "- Solo registrarse <b>no es suficiente</b>\n"
        "- Debes <b>depositar</b> antes de la revisión\n\n"
        "<i>Completa los pasos con cuidado.</i>"
    ),
    "vip_existing_body": (
        "<b>Acceso VIP - Usuario Existente PU Prime</b>\n\n"
        "Sigue estos pasos en orden:\n\n"
        "1. Envía el <b>correo de traslado IB</b>\n"
        "2. Espera la confirmación del traslado\n"
        "3. <b>Deposita</b>\n"
        "4. Envía tu <b>MT5 UID / número de cuenta</b>\n\n"
        "<b>Importante:</b>\n"
        "- Tu cuenta debe moverse bajo nuestro IB\n"
        "- Debes <b>depositar</b>\n"
        "- Sin esto, <b>no se otorgará acceso VIP</b>\n\n"
        "<i>Completa los pasos con cuidado.</i>"
    ),
    "vip_registered_msg": (
        "<b>Registro marcado como completado.</b>\n\n"
        "<b>Siguiente requisito:</b> debes <b>depositar</b> antes de enviar tu UID para revisión VIP.\n\n"
        "<i>No te saltes este paso.</i>"
    ),
    "vip_must_register_first": (
        "<b>Debes completar el registro primero.</b>\n\n"
        "Sigue los pasos en orden.\n\n"
        "<i>El paso 1 debe completarse antes del paso 3.</i>"
    ),
    "vip_deposit_done_msg": (
        "<b>Depósito marcado como completado.</b>\n\n"
        "Ahora puedes enviar tu <b>MT5 UID / número de cuenta</b> para revisión VIP."
    ),
    "vip_existing_deposit_done_msg": (
        "<b>Depósito marcado como completado.</b>\n\n"
        "Ahora puedes enviar tu <b>MT5 UID / número de cuenta</b> para revisión VIP."
    ),
    "vip_transfer_email_body": (
        "<b>Plantilla de Correo de Traslado VIP</b>\n\n"
        "<b>Para:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>Asunto:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>Cuerpo:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<b>Importante:</b> tras la confirmación del traslado, también debes <b>depositar</b> para calificar a VIP."
    ),
    "vip_transfer_sent_msg": (
        "<b>Correo de traslado marcado como enviado.</b>\n\n"
        "Espera a que PU Prime confirme el traslado IB.\n\n"
        "<b>Después:</b>\n"
        "- deposita\n"
        "- luego envía tu UID\n\n"
        "<i>Esto es requerido para la revisión VIP.</i>"
    ),
    "vip_must_send_transfer_first": (
        "<b>Debes enviar el correo de traslado primero.</b>\n\n"
        "Sigue los pasos de traslado VIP en orden."
    ),

    "ib_affiliate_body": (
        "<b>Configuración de Afiliado IB</b>\n\n"
        "Esta ruta es para usuarios que quieren entender el modelo IB y completar el proceso de afiliación.\n\n"
        "<i>Elige si necesitas la guía para principiantes o quieres continuar directamente.</i>"
    ),
    "what_is_ib_msg": (
        "Comienza con el <b>PDF tutorial</b> abajo.\n\n"
        "<b>Siguiente paso:</b> una vez leído, pulsa <b>Continuar</b>."
    ),
    "pdf_missing": "PDF tutorial no encontrado.\n\nPon <b>{PDF}</b> en la misma carpeta que <b>ib_bot.py</b>.",
    "pdf_caption": "Guía Tutorial IB",
    "affiliate_main_body": "<b>Menú de Afiliado IB</b>\n\nElige la ruta que coincida con tu situación.",
    "flow_new_body": (
        "<b>Afiliado IB - Nuevo en PU Prime</b>\n\n"
        "Sigue estos pasos en orden:\n\n"
        "1. <b>Comenzar Registro</b>\n"
        "2. Asegúrate de que el código sea <b>{IB_CODE}</b>\n"
        "3. Completa el registro y verificación\n"
        "4. Pulsa <b>Completé el Registro</b>\n"
        "5. Envía tu <b>MT5 UID / número de cuenta</b>\n\n"
        "<b>Importante:</b> no te saltes pasos.\n\n"
        "<i>Pulsa el paso 1 para comenzar.</i>"
    ),
    "flow_existing_body": (
        "<b>Afiliado IB - Usuario Existente PU Prime</b>\n\n"
        "Sigue estos pasos en orden:\n\n"
        "1. Abre la <b>plantilla de correo de traslado</b>\n"
        "2. Envía el correo a PU Prime\n"
        "3. Pulsa <b>Envié el Correo</b>\n"
        "4. Espera que PU Prime confirme el traslado\n"
        "5. Envía tu <b>MT5 UID / número de cuenta</b>\n\n"
        "<i>Completa cada paso en orden.</i>"
    ),
    "affiliate_registered_msg": (
        "<b>Registro marcado como completado.</b>\n\n"
        "Ahora puedes enviar tu <b>MT5 UID / número de cuenta</b> aquí.\n\n"
        "<i>Verifica que el formato UID sea correcto antes de enviarlo.</i>"
    ),
    "affiliate_transfer_email_body": (
        "<b>Plantilla de Correo de Traslado IB</b>\n\n"
        "<b>Para:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>Asunto:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>Cuerpo:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<i>Envía este correo, luego regresa y pulsa el paso 2.</i>"
    ),
    "affiliate_transfer_sent_msg": (
        "<b>Correo marcado como enviado.</b>\n\n"
        "Espera que PU Prime confirme el traslado IB.\n\n"
        "Una vez confirmado, envía tu <b>MT5 UID / número de cuenta</b> aquí."
    ),
    "affiliate_must_register": (
        "<b>Debes completar el registro primero.</b>\n\n"
        "Sigue los pasos de afiliado en orden."
    ),
    "affiliate_must_send_transfer": (
        "<b>Debes enviar el correo de traslado primero.</b>\n\n"
        "Sigue los pasos de afiliado en orden."
    ),
    "benefits_body": (
        "<b>Beneficios IB</b>\n\n"
        "- Onboarding estructurado\n"
        "- Soporte directo del admin\n"
        "- Proceso de configuración claro\n"
        "- Acceso a la siguiente etapa tras validación\n\n"
        "<i>Regresa y continúa la ruta correcta.</i>"
    ),

    "show_btc_body": (
        "<b>Dirección BTC</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Toca la dirección para copiar. Tras enviar el pago, pulsa Ya Pagué y luego envía tu comprobante.</i>"
    ),
    "show_eth_body": (
        "<b>Dirección ETH</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Toca la dirección para copiar. Tras enviar el pago, pulsa Ya Pagué y luego envía tu comprobante.</i>"
    ),
    "show_sol_body": (
        "<b>Dirección SOL</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Toca la dirección para copiar. Tras enviar el pago, pulsa Ya Pagué y luego envía tu comprobante.</i>"
    ),
    "funded_payment_sent_msg": (
        "<b>Pago marcado como enviado.</b>\n\n"
        "Ahora envía tu comprobante de pago.\n\n"
        "<b>Importante:</b> si envías una captura o documento, el caption debe ser:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "funded_already_submitted": (
        "<b>Tu comprobante de pago ya fue recibido.</b>\n\n"
        "Espera la revisión o contacta soporte si es necesario."
    ),
    "funded_must_send_first": (
        "<b>Debes marcar el pago como enviado primero.</b>\n\n"
        "Sigue los pasos de VIP Funded en orden."
    ),
    "funded_proof_prompt": (
        "Envía tu <b>comprobante de pago</b> ahora.\n\n"
        "<b>Formato de caption requerido:</b>\n"
        "<code>PAYMENT: FUNDED</code>\n\n"
        "<i>Solo captura o documento.</i>"
    ),
    "funded_waiting_review_msg": (
        "<b>Tu comprobante de pago VIP Funded está en revisión.</b>\n\n"
        "No hay nada más que enviar ahora.\n\n"
        "<i>Si necesitas ayuda, pulsa Contactar Soporte.</i>"
    ),
    "funded_proof_received": (
        "<b>Comprobante de pago recibido.</b>\n\n"
        "Tu pago VIP Funded está en revisión.\n\n"
        "<i>Espera la confirmación o instrucciones adicionales.</i>"
    ),

    "submit_uid_prompt": (
        "Envía tu <b>MT5 UID / número de cuenta</b> ahora.\n\n"
        "Solo escribe el número — por ejemplo:\n\n"
        "<code>12345678</code>\n\n"
        "<i>Si envías una captura o documento, incluye tu UID en el caption.</i>"
    ),
    "uid_format_guide": (
        "<b>UID no reconocido.</b>\n\n"
        "Por favor envía solo tu MT5 UID — por ejemplo:\n\n"
        "<code>12345678</code>"
    ),
    "payment_format_guide": (
        "<b>Formato de comprobante inválido.</b>\n\n"
        "Si envías comprobante, el caption debe ser exactamente:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>Caption sin UID.</b>\n\n"
        "Si envías captura o documento, el caption debe contener tu UID — por ejemplo:\n\n"
        "<code>12345678</code>"
    ),
    "uid_already_registered": (
        "<b>Este UID ya está registrado a otro usuario.</b>\n\n"
        "Si crees que es un error, contacta soporte."
    ),
    "uid_not_ready_new_vip": (
        "<b>Aún no estás listo para enviar UID.</b>\n\n"
        "Para acceso VIP como <b>usuario nuevo</b>, debes:\n"
        "1. registrarte bajo nosotros\n"
        "2. depositar\n"
        "3. luego enviar tu UID\n\n"
        "<i>Completa los pasos requeridos primero.</i>"
    ),
    "uid_not_ready_existing_vip": (
        "<b>Aún no estás listo para enviar UID.</b>\n\n"
        "Para acceso VIP como <b>usuario existente</b>, debes:\n"
        "1. enviar el correo de traslado\n"
        "2. esperar confirmación\n"
        "3. depositar\n"
        "4. luego enviar tu UID\n\n"
        "<i>Completa los pasos requeridos primero.</i>"
    ),
    "vip_already_submitted": (
        "<b>Tu envío VIP ya fue recibido.</b>\n\n"
        "Espera la revisión o contacta soporte si es necesario."
    ),
    "aff_already_submitted": (
        "<b>Tu envío de afiliado ya fue recibido.</b>\n\n"
        "Espera la revisión o contacta soporte si es necesario."
    ),
    "submission_received_text": (
        "<b>Envío recibido.</b>\n\n"
        "Tus detalles fueron reenviados para revisión.\n\n"
        "<i>Espera la confirmación o instrucciones adicionales.</i>"
    ),
    "submission_received_media": (
        "<b>Envío recibido.</b>\n\n"
        "Tu archivo fue reenviado para revisión.\n\n"
        "<i>Espera la confirmación o instrucciones adicionales.</i>"
    ),
    "vip_waiting_review_msg": (
        "<b>Tu envío VIP está en revisión.</b>\n\n"
        "No hay nada más que enviar ahora.\n\n"
        "<i>Si necesitas ayuda, pulsa Contactar Soporte.</i>"
    ),
    "aff_waiting_review_msg": (
        "<b>Tu envío de afiliado está en revisión.</b>\n\n"
        "No hay nada más que enviar ahora.\n\n"
        "<i>Si necesitas ayuda, pulsa Contactar Soporte.</i>"
    ),

    "support_body": "<b>Contactar Soporte</b>\n\nElige el admin más adecuado para tu consulta:",

    "approved_dm": (
        "<b>Tu envío ha sido aprobado.</b>\n\n"
        "Un admin te contactará pronto con el siguiente paso."
    ),
    "rejected_dm": (
        "<b>Tu envío no fue aprobado en esta etapa.</b>\n\n"
        "Contacta soporte para resolver el problema."
    ),

    "nudge_24h": (
        "Solo para ver cómo vas.\n\n"
        "Si te atascaste durante la configuración de ImperiumFX, pulsa /start para continuar - "
        "o pulsa Contactar Soporte y te ayudaremos."
    ),
    "nudge_72h_deposit": (
        "Marcaste tu depósito como hecho - no olvides enviar tu "
        "<b>MT5 UID</b> para finalizar tu acceso VIP."
    ),
    "renewal_reminder": (
        "<b>Recordatorio de renovación VIP Funded</b>\n\n"
        "Tu renovación vence en <b>{DAYS} día(s)</b>.\n"
        "La renovación es <b>80 EUR</b>. Pulsa /start -> VIP De Pago -> Funded para pagar.\n\n"
        "<b>Wallets:</b>\n"
        "BTC: <code>{BTC}</code>\n"
        "ETH: <code>{ETH}</code>\n"
        "SOL: <code>{SOL}</code>"
    ),

    "fallback_msg": "No entendí eso — por favor usa los botones de abajo.",
    "uid_bad_format": (
        "<b>UID no reconocido.</b>\n"
        "Por favor envía solo tu MT5 UID — por ejemplo:\n"
        "<code>12345678</code>"
    ),
    "vip_uid_received": (
        "<b>Solicitud VIP recibida.</b>\n"
        "Nuestro equipo la revisará en breve y te enviará un DM al aprobarla. ✅"
    ),
    "aff_uid_received": (
        "<b>Solicitud de afiliado recibida.</b>\n"
        "Nuestro equipo confirmará tu estado de subafiliado IB y te enviará un DM. ✅"
    ),
    "funded_submit_bad_format": (
        "<b>Formato no reconocido.</b>\n"
        "Por favor envía:\n"
        "<code>Amount: 80 EUR\nTX/Ref: &lt;hash o referencia&gt;\nMethod: BTC|ETH|SOL</code>\n"
        "O envía la imagen del comprobante con el mismo pie de foto."
    ),
    "funded_submit_received": (
        "<b>Pago de VIP Funded recibido.</b>\n"
        "Lo estamos verificando — te enviaremos un DM en cuanto se habilite el acceso. 🔒"
    ),
    "nudge_incomplete": (
        "<b>¿Sigues interesado en VIP?</b>\n"
        "Empezaste pero no terminaste — pulsa /start para continuar donde lo dejaste."
    ),

    "faq_q1": "¿Qué es el acceso VIP?",
    "faq_a1": (
        "<b>Acceso VIP</b> te da nuestras señales privadas, setups y trade calls. "
        "VIP Gratis requiere estar bajo nuestro IB y depositar. "
        "VIP De Pago (funded) es acceso directo para traders con cuenta funded."
    ),
    "faq_q2": "¿Qué es un IB?",
    "faq_a2": (
        "<b>IB (Introducing Broker)</b> significa que tu cuenta de trading está registrada o "
        "trasladada bajo nuestro código de partner. Ganamos una pequeña comisión del spread - "
        "<b>sin costo extra para ti</b> - y a cambio obtienes acceso VIP gratis."
    ),
    "faq_q3": "¿Cuánto tarda la revisión?",
    "faq_a3": (
        "Las revisiones son <b>usualmente en 24 horas</b>. Si ha pasado más, pulsa "
        "<b>Contactar Soporte</b> y un admin te dará seguimiento."
    ),
    "faq_q4": "¿Por qué no aceptaron mi UID?",
    "faq_a4": (
        "Razones comunes: cuenta no bajo nuestro código IB, sin depósito aún, "
        "o no pudimos leer tu UID. Verifica que usaste el código <code>{IB_CODE}</code>, "
        "depositaste, y enviaste solo los dígitos, ej: <code>12345678</code>"
    ),
    "faq_q5": "¿Cuánto cuesta VIP Funded?",
    "faq_a5": (
        "<b>50 EUR</b> el primer mes, luego <b>80 EUR</b>/mes. "
        "Pagable en BTC, ETH o SOL. Después del pago, envía comprobante con caption "
        "<code>PAYMENT: FUNDED</code>."
    ),
    "faq_q6": "¿Hay depósito mínimo?",
    "faq_a6": (
        "PU Prime establece el depósito mínimo. Recomendamos al menos <b>200 USD</b> "
        "para un tamaño de posición significativo y calificar a VIP con fluidez."
    ),

    "btn_vip_access": "💎 Acceso VIP",
    "btn_ib_affiliate": "🤝 Ser Afiliado IB",
    "btn_team": "👥 Conoce al Equipo",
    "btn_socials": "🌐 Síguenos",
    "btn_faq": "❓ Preguntas",
    "btn_support": "💬 Contactar Soporte",
    "btn_back": "◀️ Atrás",
    "btn_back_to_start": "🏠 Volver al Inicio",
    "btn_back_to_vip": "◀️ Volver al Menú VIP",
    "btn_back_to_affiliate": "◀️ Volver al Menú Afiliado",
    "btn_yes_restart": "🔄 Sí, reiniciar",
    "btn_no_keep": "✅ No, mantener progreso",
    "btn_free_vip": "🎁 VIP Gratis",
    "btn_paid_vip": "👑 VIP De Pago",
    "btn_new_to_pu": "🆕 Nuevo en PU Prime",
    "btn_existing_pu": "📂 Ya tengo PU Prime",
    "btn_live_account": "📊 Cuenta Real",
    "btn_funded_account": "🏦 Cuenta Funded",
    "btn_dont_know_ib": "🤔 No sé qué es IB",
    "btn_already_know": "✅ Ya sé, continuar",
    "btn_continue": "➡️ Continuar",
    "btn_step1_register": "1️⃣ Paso 1: Registrarte con PU Prime",
    "btn_step1_start_reg": "1️⃣ Paso 1: Comenzar Registro",
    "btn_step2_completed": "2️⃣ Paso 2: Completé el Registro",
    "btn_step3_deposited": "3️⃣ Paso 3: Ya Deposité",
    "btn_step4_submit_uid": "4️⃣ Paso 4: Enviar UID",
    "btn_step3_submit_uid": "3️⃣ Paso 3: Enviar UID",
    "btn_step1_view_email": "1️⃣ Paso 1: Ver Correo de Traslado",
    "btn_step2_sent_email": "2️⃣ Paso 2: Envié el Correo",
    "btn_view_btc": "₿ Ver Dirección BTC",
    "btn_view_eth": "Ξ Ver Dirección ETH",
    "btn_view_sol": "◎ Ver Dirección SOL",
    "btn_sent_payment": "💸 Ya Pagué",
    "btn_submit_proof": "📤 Enviar Comprobante",
    "btn_waiting_payment_review": "⏳ Esperando Revisión del Pago",
    "btn_waiting_review": "⏳ Esperando Revisión",
    "btn_benefits": "🎯 Beneficios IB",
    "btn_message": "💬 Mensaje",
    "btn_founder": "👑 Fundador - Kratos",
    "btn_onboarding": "🚀 Onboarding / General - Apollo",
    "btn_signals": "📈 Señales - Plato",
    "btn_socials_admin": "📱 Socials - HD",
    "btn_change_language": "🌐 Cambiar Idioma",
    "btn_approve": "✅ Aprobar",
    "btn_reject": "❌ Rechazar",
    "btn_block_user": "🚫 Bloquear Usuario",
}

TEXTS["ru"] = {
    "lang_picker_title": "✨ <b>Добро пожаловать в ImperiumFX</b> ✨\n\nВаш вход в премиум-трейдинг — отборные VIP-сигналы, IB-партнёрство и команда, которая реально торгует.\n\n🌐 <b>Пожалуйста, выберите язык, чтобы продолжить.</b>\n<i>Вы можете изменить его в любое время через /language.</i>",
    "lang_set_ok": "✅ <b>Язык установлен.</b> Загружаем главное меню…",
    "welcome_title": "💎 <b>Добро пожаловать в ImperiumFX</b> 💎",
    "welcome_body": "💎 <b>Добро пожаловать в ImperiumFX</b> 💎\n\nДом премиум VIP-сигналов и IB-партнёрств для трейдеров PU Prime.\n\n<b>Что привело вас сюда сегодня?</b>\n\n💎 <b>VIP Access</b> — приватные сигналы, сетапы и живые звонки\n🤝 <b>IB Affiliate</b> — станьте партнёром и зарабатывайте комиссии\n👥 <b>Команда</b> — узнайте, кто управляет ImperiumFX\n🌐 <b>Подписывайтесь</b> — Instagram и TikTok\n❓ <b>FAQ</b> — быстрые ответы на частые вопросы\n\n<i>Нажмите на одну из опций ниже, чтобы продолжить.</i>",
    "resume_prompt": "<b>У вас уже есть прогресс в боте.</b>\n\nХотите <b>начать заново</b> или оставить текущий прогресс?",
    "restart_yes_msg": "💎 <b>Добро пожаловать в ImperiumFX</b> 💎\n\nВыберите путь ниже.",
    "restart_no_msg": "Прогресс сохранён. Нажмите кнопку ниже, чтобы продолжить.",
    "back_short_welcome": "💎 <b>Добро пожаловать в ImperiumFX</b> 💎\n\nВыберите путь ниже.\n\n💎 <b>VIP Access</b> — присоединяйтесь к нашим VIP-сигналам\n🤝 <b>IB Affiliate</b> — станьте партнёром и пройдите IB-процесс\n\n<i>Выберите вариант, который вам подходит.</i>",
    "help_text": "<b>ImperiumFX Bot - Помощь</b>\n\n- /start - открыть главное меню\n- /status - посмотреть ваш прогресс\n- /language - сменить язык\n- /help - показать это сообщение\n\nЕсли что-то не получается, нажмите <b>Contact Support</b> из любого меню.",
    "status_title": "<b>Ваш статус</b>",
    "status_no_record": "Запись ещё не найдена. Нажмите /start, чтобы начать.",
    "status_path": "Путь",
    "status_flow": "Процесс",
    "status_vip_submitted": "VIP отправлен",
    "status_aff_submitted": "Affiliate отправлен",
    "status_funded": "Funded VIP",
    "yes": "да",
    "no": "нет",
    "status_field_status": "статус",
    "dash": "-",
    "access_disabled": "Доступ отключён. Свяжитесь с поддержкой.",
    "slow_down": "Не так быстро",
    "fallback_unknown": "Я не понял — вот меню.\nНажмите /start, чтобы начать.",
    "fallback_media": "Я не понял — вот меню. Нажмите /start, чтобы начать.",
    "team_title": "<b>Познакомьтесь с командой</b>",
    "team_footer": "<i>Нажмите кнопку ниже, чтобы написать напрямую.</i>",
    "socials_body": "<b>Подписывайтесь на ImperiumFX</b>\n\nБудьте в курсе нашего контента, сделок и обновлений команды.\n\nИспользуйте кнопки ниже, чтобы перейти на наши каналы.",
    "faq_intro": "<b>Часто задаваемые вопросы</b>\n\nВыберите вопрос ниже.",
    "vip_access_body": "<b>VIP Access</b>\n\nВыберите ваш VIP-маршрут ниже.\n\n<b>Free VIP</b> — зарегистрируйтесь под нашим IB и внесите депозит, чтобы получить доступ.\n<b>Paid VIP</b> — прямой доступ (счёт Live или Funded).",
    "vip_free_body": "<b>Free VIP</b>\n\nЧтобы получить доступ, вам нужно сделать <b>одно</b> из следующего:\n\n1. Открыть новый счёт PU Prime под нашим IB-кодом <code>{IB_CODE}</code>.\n2. Если вы уже пользуетесь PU Prime — перевести счёт под наш IB.\n\nВыберите ваш маршрут ниже для полного процесса.",
    "vip_paid_body": "<b>Paid VIP</b>\n\nВыберите тип счёта, который вы используете.\n\n<b>Live Account</b> — прямой доступ через депозит PU Prime.\n<b>Funded Account</b> — оплата в крипте для трейдеров funded-счетов.",
    "vip_paid_live_body": "<b>Paid VIP - Live Account</b>\n\nДля живых счетов доступ осуществляется через депозит PU Prime.\n\n<b>Требования:</b>\n- Счёт под нашим IB-кодом <code>{IB_CODE}</code>\n- Минимальный депозит внесён\n- Отправьте ваш MT5 UID / номер счёта\n\nНажмите <b>Submit UID</b> ниже, чтобы продолжить.",
    "vip_paid_funded_body": "<b>Paid VIP - Funded Account</b>\n\n<b>Цена:</b>\n- <b>EUR 50</b> за первый месяц\n- Затем <b>EUR 80</b>/месяц\n\n<b>Способы оплаты:</b>\nBTC / ETH / SOL — смотрите адреса ниже.\n\nПосле оплаты отправьте подтверждение транзакции.",
    "vip_new_body": "<b>VIP Access - Новый на PU Prime</b>\n\nСледуйте этим шагам по порядку:\n\n1️⃣ Зарегистрируйтесь под нашим IB-кодом <code>{IB_CODE}</code>\n2️⃣ Подтвердите, что регистрация завершена\n3️⃣ Внесите депозит на свой счёт\n4️⃣ Отправьте ваш MT5 UID",
    "vip_existing_body": "<b>VIP Access - Существующий пользователь PU Prime</b>\n\nСледуйте этим шагам по порядку:\n\n1️⃣ Посмотрите наш шаблон email для перевода\n2️⃣ Отправьте email в PU Prime\n3️⃣ Отправьте ваш MT5 UID",
    "vip_registered_msg": "<b>Регистрация отмечена как завершённая.</b>\n\n<b>Следующее требование:</b> внесите депозит для Free VIP.\nНажмите <b>Step 3: I Deposited</b>, когда будете готовы.",
    "vip_must_register_first": "<b>Сначала нужно завершить регистрацию.</b>\n\nПожалуйста, следуйте шагам по меню.",
    "vip_deposit_done_msg": "<b>Депозит отмечен как завершённый.</b>\n\nТеперь вы можете отправить ваш MT5 UID.",
    "vip_existing_deposit_done_msg": "<b>Депозит отмечен как завершённый.</b>\n\nТеперь вы можете отправить ваш MT5 UID.",
    "vip_transfer_email_body": "<b>Шаблон email для VIP-перевода</b>\n\n<b>Кому:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n<b>Тема:</b>\n<code>IB transfer request</code>\n\n<b>Текст:</b>\n<code>Hello,\nPlease transfer my PU Prime account to IB account {IB_ACCOUNT_NUMBER} (code {IB_CODE}).\nMT5 UID: &lt;your UID&gt;\nThanks.</code>\n\nНажмите <b>I Sent the Email</b> после отправки.",
    "vip_transfer_sent_msg": "<b>Email для перевода отмечен как отправленный.</b>\n\nПодождите подтверждения от PU Prime, затем отправьте ваш UID.",
    "vip_must_send_transfer_first": "<b>Сначала нужно отправить email для перевода.</b>\n\nПожалуйста, следуйте шагам по меню.",
    "ib_affiliate_body": "<b>Настройка IB Affiliate</b>\n\nЭтот путь для тех, кто хочет стать нашим суб-партнёром под PU Prime.\n\nЕсли вы не понимаете, что такое IB — начните с туториала.",
    "what_is_ib_msg": "Начните с <b>туториала в PDF</b> ниже.\n\n<b>Следующий шаг:</b> вернитесь в главное меню Affiliate, когда будете готовы.",
    "pdf_missing": "Туториал PDF не найден.\n\nПоместите <b>{PDF}</b> в ту же папку, что и бот.",
    "pdf_caption": "Руководство IB",
    "affiliate_main_body": "<b>Меню IB Affiliate</b>\n\nВыберите путь, соответствующий вашей ситуации.",
    "flow_new_body": "<b>IB Affiliate - Новый на PU Prime</b>\n\nСледуйте этим шагам по порядку:\n\n1️⃣ Зарегистрируйтесь под нашим IB-кодом <code>{IB_CODE}</code>\n2️⃣ Подтвердите, что регистрация завершена\n3️⃣ Отправьте ваш MT5 UID",
    "flow_existing_body": "<b>IB Affiliate - Существующий пользователь PU Prime</b>\n\nСледуйте этим шагам по порядку:\n\n1️⃣ Посмотрите наш шаблон email для перевода\n2️⃣ Отправьте email в PU Prime\n3️⃣ Отправьте ваш MT5 UID",
    "affiliate_registered_msg": "<b>Регистрация отмечена как завершённая.</b>\n\nТеперь вы можете отправить ваш MT5 UID.",
    "affiliate_transfer_email_body": "<b>Шаблон email для IB-перевода</b>\n\n<b>Кому:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n<b>Тема:</b>\n<code>IB transfer request</code>\n\n<b>Текст:</b>\n<code>Hello,\nPlease transfer my PU Prime account to IB account {IB_ACCOUNT_NUMBER} (code {IB_CODE}).\nMT5 UID: &lt;your UID&gt;\nThanks.</code>\n\nНажмите <b>I Sent the Email</b> после отправки.",
    "affiliate_transfer_sent_msg": "<b>Email отмечен как отправленный.</b>\n\nПодождите подтверждения от PU Prime, затем отправьте ваш UID.",
    "affiliate_must_register": "<b>Сначала нужно завершить регистрацию.</b>\n\nПожалуйста, следуйте шагам по меню.",
    "affiliate_must_send_transfer": "<b>Сначала нужно отправить email для перевода.</b>\n\nПожалуйста, следуйте шагам по меню.",
    "benefits_body": "<b>Преимущества IB</b>\n\n- Структурированный онбординг\n- Прямая поддержка администратора\n- Бесплатный доступ к VIP-сигналам\n- Структура суб-партнёрских комиссий\n- Эксклюзивные командные каналы",
    "show_btc_body": "<b>Адрес BTC</b>\n\n<code>{ADDR}</code>\n\n<i>Нажмите на адрес для копирования. После отправки нажмите <b>I Sent Payment</b>.</i>",
    "show_eth_body": "<b>Адрес ETH</b>\n\n<code>{ADDR}</code>\n\n<i>Нажмите на адрес для копирования. После отправки нажмите <b>I Sent Payment</b>.</i>",
    "show_sol_body": "<b>Адрес SOL</b>\n\n<code>{ADDR}</code>\n\n<i>Нажмите на адрес для копирования. После отправки нажмите <b>I Sent Payment</b>.</i>",
    "funded_payment_sent_msg": "<b>Оплата отмечена как отправленная.</b>\n\nТеперь отправьте подтверждение оплаты.",
    "funded_already_submitted": "<b>Ваше подтверждение оплаты уже получено.</b>\n\nПожалуйста, подождите нашей проверки.",
    "funded_must_send_first": "<b>Сначала отметьте оплату как отправленную.</b>\n\nПожалуйста, следуйте шагам.",
    "funded_proof_prompt": "Отправьте ваше <b>подтверждение оплаты</b> сейчас.\n\n<b>Требуемый формат подписи:</b>\n<code>Amount: 80 EUR\nTX/Ref: &lt;hash или reference&gt;\nMethod: BTC|ETH|SOL</code>\n\nВы можете отправить скриншот с этой подписью.",
    "funded_waiting_review_msg": "<b>Ваше подтверждение Funded VIP уже на проверке.</b>\n\nБольше ничего делать не нужно.",
    "funded_proof_received": "<b>Подтверждение оплаты получено.</b>\n\nВаша оплата Funded VIP теперь на проверке. Вам придёт DM после одобрения.",
    "submit_uid_prompt": "Отправьте ваш <b>MT5 UID / номер счёта</b>.\n\nПросто напишите число — например:\n\n<code>12345678</code>\n\n<i>Если вы отправляете скриншот или документ, укажите ваш UID в подписи.</i>",
    "uid_format_guide": "<b>UID не распознан.</b>\n\nПожалуйста, отправьте просто ваш MT5 UID — например:\n\n<code>12345678</code>",
    "payment_format_guide": "<b>Неверный формат подтверждения оплаты.</b>\n\nЕсли вы отправляете скриншот, добавьте в подпись:\n<code>Amount: 80 EUR\nTX/Ref: &lt;hash или reference&gt;\nMethod: BTC|ETH|SOL</code>",
    "uid_caption_invalid": "<b>В подписи нет UID.</b>\n\nЕсли вы отправляете скриншот или файл, укажите ваш UID в подписи — например:\n\n<code>12345678</code>",
    "uid_already_registered": "<b>Этот UID уже зарегистрирован за другим пользователем.</b>\n\nЕсли это ошибка — свяжитесь с поддержкой.",
    "uid_not_ready_new_vip": "<b>Вы ещё не готовы отправить UID.</b>\n\nДля VIP-доступа сначала зарегистрируйтесь и внесите депозит.",
    "uid_not_ready_existing_vip": "<b>Вы ещё не готовы отправить UID.</b>\n\nДля VIP-доступа сначала отправьте email для перевода.",
    "vip_already_submitted": "<b>Ваша VIP-заявка уже получена.</b>\n\nПожалуйста, подождите проверки.",
    "aff_already_submitted": "<b>Ваша заявка партнёра уже получена.</b>\n\nПожалуйста, подождите проверки.",
    "submission_received_text": "<b>Заявка получена.</b>\n\nВаши данные переданы на проверку. Вам придёт DM после одобрения.",
    "submission_received_media": "<b>Заявка получена.</b>\n\nВаш файл передан на проверку. Вам придёт DM после одобрения.",
    "vip_waiting_review_msg": "<b>Ваша VIP-заявка уже на проверке.</b>\n\nБольше ничего делать не нужно.",
    "aff_waiting_review_msg": "<b>Ваша заявка партнёра уже на проверке.</b>\n\nБольше ничего делать не нужно.",
    "support_body": "<b>Связаться с поддержкой</b>\n\nВыберите админа, наиболее подходящего для вашего вопроса.",
    "approved_dm": "<b>Ваша заявка одобрена.</b>\n\nАдмин свяжется с вами в ближайшее время со следующими шагами. 🎉",
    "rejected_dm": "<b>Ваша заявка не одобрена на этом этапе.</b>\n\nПожалуйста, свяжитесь с поддержкой для деталей.",
    "nudge_24h": "Просто проверяю связь.\n\nЕсли вы застряли в настройке ImperiumFX — свяжитесь с поддержкой или нажмите /start.",
    "nudge_72h_deposit": "Вы отметили депозит как выполненный — не забудьте отправить ваш UID.\nНажмите /start, чтобы продолжить.",
    "renewal_reminder": "<b>Напоминание о продлении Funded VIP</b>\n\nВаше продление подходит через <b>{DAYS} дн.</b>\nПродление — <b>EUR 80</b>. Нажмите /start -> Paid VIP -> Funded для оплаты.\n\n<b>Кошельки:</b>\nBTC: <code>{BTC}</code>\nETH: <code>{ETH}</code>\nSOL: <code>{SOL}</code>",
    "fallback_msg": "Я не понял — пожалуйста, используйте кнопки ниже.",
    "uid_bad_format": "<b>UID не распознан.</b>\nПожалуйста, отправьте просто ваш MT5 UID — например:\n<code>12345678</code>",
    "vip_uid_received": "<b>VIP-заявка получена.</b>\nНаша команда скоро её рассмотрит и напишет вам в DM после одобрения. ✅",
    "aff_uid_received": "<b>Заявка партнёра получена.</b>\nНаша команда подтвердит ваш статус IB суб-партнёра и напишет вам в DM. ✅",
    "funded_submit_bad_format": "<b>Формат не распознан.</b>\nПожалуйста, отправьте:\n<code>Amount: 80 EUR\nTX/Ref: &lt;hash или reference&gt;\nMethod: BTC|ETH|SOL</code>\nИли отправьте скриншот с такой же подписью.",
    "funded_submit_received": "<b>Оплата Funded VIP получена.</b>\nМы её сейчас проверяем — напишем в DM, как только откроем доступ. 🔒",
    "nudge_incomplete": "<b>Всё ещё интересует VIP?</b>\nВы начали, но не закончили — нажмите /start, чтобы продолжить с того места.",
    "faq_q1": "Что такое VIP-доступ?",
    "faq_a1": "<b>VIP-доступ</b> даёт вам наши приватные сигналы, сетапы и торговые идеи. Free VIP требует регистрацию под нашим IB и внесения депозита. Paid VIP (funded) — прямой доступ для трейдеров funded-счетов.",
    "faq_q2": "Что такое IB?",
    "faq_a2": "<b>IB (Introducing Broker)</b> означает, что ваш торговый счёт зарегистрирован или переведён под наш партнёрский код. Мы получаем небольшую комиссию из вашего спреда — <b>для вас это бесплатно</b> — а взамен вы получаете бесплатный VIP-доступ.",
    "faq_q3": "Сколько времени занимает проверка?",
    "faq_a3": "Проверка <b>обычно в течение 24 часов</b>. Если прошло больше — свяжитесь с поддержкой.",
    "faq_q4": "Почему мой UID не приняли?",
    "faq_a4": "Частые причины: счёт не под нашим IB-кодом <code>{IB_CODE}</code>, нет депозита или неверный формат. Убедитесь, что вы отправляете правильный UID и email.",
    "faq_q5": "Сколько стоит Funded VIP?",
    "faq_a5": "<b>EUR 50</b> за первый месяц, затем <b>EUR 80</b>/месяц. Оплата принимается в BTC, ETH или SOL.",
    "faq_q6": "Есть ли минимальный депозит?",
    "faq_a6": "PU Prime устанавливает минимальный депозит. Мы рекомендуем минимум <b>USD 100</b> для VIP-доступа.",
    "btn_vip_access": "💎 Получить VIP-доступ",
    "btn_ib_affiliate": "🤝 Стать IB-партнёром",
    "btn_team": "👥 Команда",
    "btn_socials": "🌐 Подписаться",
    "btn_faq": "❓ FAQ",
    "btn_support": "💬 Связаться с поддержкой",
    "btn_back": "◀️ Назад",
    "btn_back_to_start": "🏠 В начало",
    "btn_back_to_vip": "◀️ В меню VIP",
    "btn_back_to_affiliate": "◀️ В меню Affiliate",
    "btn_yes_restart": "🔄 Да, начать заново",
    "btn_no_keep": "✅ Нет, сохранить прогресс",
    "btn_free_vip": "🎁 Free VIP",
    "btn_paid_vip": "👑 Paid VIP",
    "btn_new_to_pu": "🆕 Новый на PU Prime",
    "btn_existing_pu": "📂 Уже на PU Prime",
    "btn_live_account": "📊 Live счёт",
    "btn_funded_account": "🏦 Funded счёт",
    "btn_dont_know_ib": "🤔 Я не знаю, что такое IB",
    "btn_already_know": "✅ Я знаю, продолжить",
    "btn_continue": "➡️ Продолжить",
    "btn_step1_register": "1️⃣ Шаг 1: Регистрация в PU Prime",
    "btn_step1_start_reg": "1️⃣ Шаг 1: Начать регистрацию",
    "btn_step2_completed": "2️⃣ Шаг 2: Регистрация завершена",
    "btn_step3_deposited": "3️⃣ Шаг 3: Депозит внесён",
    "btn_step4_submit_uid": "4️⃣ Шаг 4: Отправить UID",
    "btn_step3_submit_uid": "3️⃣ Шаг 3: Отправить UID",
    "btn_step1_view_email": "1️⃣ Шаг 1: Посмотреть email",
    "btn_step2_sent_email": "2️⃣ Шаг 2: Email отправлен",
    "btn_view_btc": "₿ Показать адрес BTC",
    "btn_view_eth": "Ξ Показать адрес ETH",
    "btn_view_sol": "◎ Показать адрес SOL",
    "btn_sent_payment": "💸 Я отправил оплату",
    "btn_submit_proof": "📤 Отправить подтверждение",
    "btn_waiting_payment_review": "⏳ Ожидание проверки оплаты",
    "btn_waiting_review": "⏳ Ожидание проверки",
    "btn_benefits": "🎯 Преимущества IB",
    "btn_message": "💬 Сообщение",
    "btn_founder": "👑 Основатель - Kratos",
    "btn_onboarding": "🚀 Онбординг / Общее - Apollo",
    "btn_signals": "📈 Сигналы - Plato",
    "btn_socials_admin": "📱 Соцсети - HD",
    "btn_change_language": "🌐 Сменить язык",
    "btn_approve": "✅ Одобрить",
    "btn_reject": "❌ Отклонить",
    "btn_block_user": "🚫 Заблокировать",
}


# ===================================================================
# FAQ (ordered list of keys)
# ===================================================================
FAQ_KEYS = [
    ("faq_1", "faq_q1", "faq_a1"),
    ("faq_2", "faq_q2", "faq_a2"),
    ("faq_3", "faq_q3", "faq_a3"),
    ("faq_4", "faq_q4", "faq_a4"),
    ("faq_5", "faq_q5", "faq_a5"),
    ("faq_6", "faq_q6", "faq_a6"),
]


# ===================================================================
# TRANSLATION HELPERS
# ===================================================================
def L(lang, key, **kwargs):
    """Look up a translated string by language + key. Falls back to English."""
    if lang not in TEXTS:
        lang = DEFAULT_LANG
    tpl = TEXTS[lang].get(key)
    if tpl is None:
        tpl = TEXTS[DEFAULT_LANG].get(key, key)
    if kwargs:
        try:
            return tpl.format(**kwargs)
        except Exception:
            return tpl
    return tpl


# ===================================================================
# DATABASE
# ===================================================================
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table):
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def db_init():
    conn = db()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            full_name      TEXT,
            lang           TEXT DEFAULT 'en',
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
    # Migration: add `lang` column for installs that existed before multilingual support
    cols = _table_columns(conn, "users")
    if "lang" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'en'")
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
            """INSERT INTO users (user_id, username, full_name, first_seen, last_seen, referrer, started_at, lang)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user.id, username, full_name, now_iso(), now_iso(), referrer, now_iso(), DEFAULT_LANG),
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


def get_lang(user_id):
    """Return the user's chosen language code, defaulting to 'en'."""
    row = get_user(user_id)
    if not row:
        return DEFAULT_LANG
    try:
        lang = row["lang"]
    except (KeyError, IndexError):
        lang = None
    return lang if lang in LANGS else DEFAULT_LANG


def set_lang(user_id, lang):
    if lang not in LANGS:
        lang = DEFAULT_LANG
    update_user(user_id, lang=lang)


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
    vip_pending = c.execute(
        "SELECT COUNT(*) AS n FROM users WHERE vip_submitted=1 AND vip_status='pending'"
    ).fetchone()["n"]
    vip_approved = c.execute("SELECT COUNT(*) AS n FROM users WHERE vip_status='approved'").fetchone()["n"]
    vip_rejected = c.execute("SELECT COUNT(*) AS n FROM users WHERE vip_status='rejected'").fetchone()["n"]
    aff_pending = c.execute(
        "SELECT COUNT(*) AS n FROM users WHERE aff_submitted=1 AND aff_status='pending'"
    ).fetchone()["n"]
    aff_approved = c.execute("SELECT COUNT(*) AS n FROM users WHERE aff_status='approved'").fetchone()["n"]
    funded_active = c.execute("SELECT COUNT(*) AS n FROM users WHERE funded_status='active'").fetchone()["n"]
    blocked = c.execute("SELECT COUNT(*) AS n FROM users WHERE blocked=1").fetchone()["n"]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    new_24h = c.execute("SELECT COUNT(*) AS n FROM users WHERE first_seen>=?", (cutoff,)).fetchone()["n"]
    by_lang = {
        r["lang"] or DEFAULT_LANG: r["n"]
        for r in c.execute("SELECT lang, COUNT(*) AS n FROM users GROUP BY lang").fetchall()
    }
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
        "by_lang": by_lang,
    }


# ===================================================================
# UTILITY HELPERS
# ===================================================================
def is_admin_chat(update: Update) -> bool:
    chat = update.effective_chat
    if chat is None:
        return False
    return chat.id == ADMIN_CHAT_ID


def admin_only(func):
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


# Telegram restricts regular bots to a specific set of reaction emoji.
# Anything outside this set raises BadRequest: REACTION_INVALID.
ALLOWED_REACTIONS = {
    "👍", "👎", "❤", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬",
    "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍",
    "🐳", "🌚", "🌭", "💯", "🤣", "⚡", "⚡️", "🍌", "🏆", "💔", "🤨", "😐",
    "🍓", "🍾", "💋", "🖕", "😈", "😴", "😭", "🤓", "👻", "👨‍💻", "👀",
    "🎃", "🙈", "😇", "😨", "🤝", "✍", "✍️", "🤗", "🫡", "🎅", "🎄", "☃",
    "☃️", "💅", "🤪", "🗿", "🆒", "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎",
    "👾", "🤷‍♂", "🤷‍♂️", "🤷", "🤷‍♀", "🤷‍♀️", "😡",
}


async def try_react(update, context, emoji="👍"):
    try:
        msg = update.effective_message
        if msg is None:
            return
        if emoji not in ALLOWED_REACTIONS:
            log.warning("try_react: emoji %r not in Telegram allowed set, skipping", emoji)
            return
        await context.bot.set_message_reaction(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            reaction=emoji,
        )
    except Exception as e:
        log.warning("try_react failed (%s): %s", emoji, e)


def parse_uid_submission(text: str):
    """
    Accept the user's UID with or without a 'UID:' prefix. Also tolerates an
    optional email on a separate line. Returns just the digit string, or None.
    """
    if not text:
        return None
    # Pick the first 5-20 digit run anywhere in the message. This matches:
    #   12345678
    #   UID: 12345678
    #   12345678\nuser@example.com
    #   uid 12345678  email: user@example.com
    m = re.search(r"(?<!\d)(\d{5,20})(?!\d)", text)
    return m.group(1) if m else None


def parse_payment_submission(text: str):
    if not text:
        return None
    m = re.fullmatch(r"PAYMENT:\s*FUNDED", text.strip(), flags=re.IGNORECASE)
    return "FUNDED" if m else None


# ===================================================================
# MENUS (all take `lang` and produce localized buttons)
# ===================================================================
def language_picker_menu():
    """Always shows native language names. Language-agnostic."""
    rows = []
    for code in LANGS:
        rows.append([InlineKeyboardButton(
            f"{LANG_FLAG[code]}  {LANG_LABELS[code]}",
            callback_data=f"setlang:{code}",
        )])
    return InlineKeyboardMarkup(rows)


def start_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_vip_access"), callback_data="vip_access")],
        [InlineKeyboardButton(L(lang, "btn_ib_affiliate"), callback_data="ib_affiliate")],
        [InlineKeyboardButton(L(lang, "btn_team"), callback_data="team"),
         InlineKeyboardButton(L(lang, "btn_socials"), callback_data="socials")],
        [InlineKeyboardButton(L(lang, "btn_faq"), callback_data="faq"),
         InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_change_language"), callback_data="change_lang")],
    ])


def confirm_restart_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_yes_restart"), callback_data="restart_yes"),
         InlineKeyboardButton(L(lang, "btn_no_keep"), callback_data="restart_no")],
    ])


def vip_entry_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_free_vip"), callback_data="vip_free")],
        [InlineKeyboardButton(L(lang, "btn_paid_vip"), callback_data="vip_paid")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="back_start")],
    ])


def vip_free_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_new_to_pu"), callback_data="vip_new")],
        [InlineKeyboardButton(L(lang, "btn_existing_pu"), callback_data="vip_existing")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="vip_access")],
    ])


def vip_paid_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_live_account"), callback_data="vip_paid_live")],
        [InlineKeyboardButton(L(lang, "btn_funded_account"), callback_data="vip_paid_funded")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="vip_access")],
    ])


def affiliate_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_dont_know_ib"), callback_data="what_is_ib")],
        [InlineKeyboardButton(L(lang, "btn_already_know"), callback_data="affiliate_main")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="back_start")],
    ])


def ib_pdf_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_continue"), callback_data="affiliate_main")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="ib_affiliate")],
    ])


def affiliate_main_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_new_to_pu"), callback_data="flow_new")],
        [InlineKeyboardButton(L(lang, "btn_existing_pu"), callback_data="flow_existing")],
        [InlineKeyboardButton(L(lang, "btn_benefits"), callback_data="benefits")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="back_start")],
    ])


def vip_new_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_step1_register"), url=IB_LINK)],
        [InlineKeyboardButton(L(lang, "btn_step2_completed"), callback_data="vip_registered")],
        [InlineKeyboardButton(L(lang, "btn_step3_deposited"), callback_data="vip_deposit_done")],
        [InlineKeyboardButton(L(lang, "btn_step4_submit_uid"), callback_data="submit_uid_vip")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="vip_free")],
    ])


def vip_existing_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_step1_view_email"), callback_data="vip_transfer_email")],
        [InlineKeyboardButton(L(lang, "btn_step2_sent_email"), callback_data="vip_sent_transfer")],
        [InlineKeyboardButton(L(lang, "btn_step3_deposited"), callback_data="vip_existing_deposit_done")],
        [InlineKeyboardButton(L(lang, "btn_step4_submit_uid"), callback_data="submit_uid_vip")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="vip_free")],
    ])


def funded_payment_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_view_btc"), callback_data="show_btc")],
        [InlineKeyboardButton(L(lang, "btn_view_eth"), callback_data="show_eth")],
        [InlineKeyboardButton(L(lang, "btn_view_sol"), callback_data="show_sol")],
        [InlineKeyboardButton(L(lang, "btn_sent_payment"), callback_data="funded_payment_sent")],
        [InlineKeyboardButton(L(lang, "btn_submit_proof"), callback_data="submit_payment_proof")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="vip_paid")],
    ])


def funded_review_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_waiting_payment_review"), callback_data="funded_waiting_review")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")],
    ])


def new_user_step_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_step1_start_reg"), url=IB_LINK)],
        [InlineKeyboardButton(L(lang, "btn_step2_completed"), callback_data="completed_registration")],
        [InlineKeyboardButton(L(lang, "btn_step3_submit_uid"), callback_data="submit_uid_affiliate")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="affiliate_main")],
    ])


def existing_user_step_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_step1_view_email"), callback_data="transfer_email_template")],
        [InlineKeyboardButton(L(lang, "btn_step2_sent_email"), callback_data="sent_transfer_email")],
        [InlineKeyboardButton(L(lang, "btn_step3_submit_uid"), callback_data="submit_uid_affiliate")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back"), callback_data="affiliate_main")],
    ])


def back_to_start(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")]
    ])


def back_to_affiliate_main(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_back_to_affiliate"), callback_data="affiliate_main")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
    ])


def back_to_vip_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_back_to_vip"), callback_data="vip_access")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
    ])


def vip_submitted_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_waiting_review"), callback_data="vip_waiting_review")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")],
    ])


def affiliate_submitted_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_waiting_review"), callback_data="affiliate_waiting_review")],
        [InlineKeyboardButton(L(lang, "btn_support"), callback_data="support")],
        [InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")],
    ])


def team_menu(lang):
    rows = []
    msg = L(lang, "btn_message")
    for info in ADMINS.values():
        rows.append([InlineKeyboardButton(
            f"{msg} {info['label']}",
            url=f"https://t.me/{info['username']}",
        )])
    rows.append([InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")])
    return InlineKeyboardMarkup(rows)


def socials_menu(lang):
    rows = [[InlineKeyboardButton(label, url=url)] for label, url in SOCIALS]
    rows.append([InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")])
    return InlineKeyboardMarkup(rows)


def faq_menu(lang):
    rows = []
    for fid, q_key, _ in FAQ_KEYS:
        rows.append([InlineKeyboardButton(L(lang, q_key), callback_data=fid)])
    rows.append([InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")])
    return InlineKeyboardMarkup(rows)


def support_admin_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L(lang, "btn_founder"),
                              url=f"https://t.me/{ADMINS['kratos']['username']}")],
        [InlineKeyboardButton(L(lang, "btn_onboarding"),
                              url=f"https://t.me/{ADMINS['apollo']['username']}")],
        [InlineKeyboardButton(L(lang, "btn_signals"),
                              url=f"https://t.me/{ADMINS['plato']['username']}")],
        [InlineKeyboardButton(L(lang, "btn_socials_admin"),
                              url=f"https://t.me/{ADMINS['hd']['username']}")],
        [InlineKeyboardButton(L(lang, "btn_back_to_start"), callback_data="back_start")],
    ])


def admin_review_menu(user_id, kind):
    """Admin buttons - always English."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve", callback_data=f"adm:app:{kind}:{user_id}"),
         InlineKeyboardButton("Reject",  callback_data=f"adm:rej:{kind}:{user_id}")],
        [InlineKeyboardButton("Block User", callback_data=f"adm:blk:{user_id}")],
    ])


# ===================================================================
# ADMIN NOTIFY
# ===================================================================
def _admin_action_keyboard(user_id: int, action_type: str):
    """Build approve/reject/block inline buttons for admin notifications."""
    if not user_id:
        return None
    # Only build review buttons for actionable events
    actionable = {"vip", "affiliate", "funded_payment"}
    if action_type not in actionable:
        return None
    rows = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"adm:approve:{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"adm:reject:{user_id}"),
        ],
        [
            InlineKeyboardButton("🚫 Block user", callback_data=f"adm:block:{user_id}"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


async def notify_admin(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup=None,
    user_id: int = None,
    action_type: str = None,
):
    # If caller passed user_id/action_type but no explicit keyboard, auto-build one.
    if reply_markup is None and user_id and action_type:
        reply_markup = _admin_action_keyboard(user_id, action_type)
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
# /start, /help, /status, /language
# ===================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    user = update.effective_user
    if is_blocked(user.id):
        return

    # Referral payload (e.g. /start ref_apollo)
    referrer = None
    if context.args:
        ref = " ".join(context.args).strip()
        if re.match(r"^[A-Za-z0-9_\-]{1,32}$", ref):
            referrer = ref

    existed = get_user(user.id) is not None
    upsert_user(user, referrer=referrer)
    log_event(user.id, "start", referrer or "")

    # First-time user: show language picker
    if not existed:
        await update.message.reply_text(
            L(DEFAULT_LANG, "lang_picker_title"),
            reply_markup=language_picker_menu(),
            parse_mode="HTML",
        )
        return

    lang = get_lang(user.id)

    # Restart protection
    if context.user_data and any(context.user_data.values()):
        await update.message.reply_text(
            L(lang, "resume_prompt"),
            reply_markup=confirm_restart_menu(lang),
            parse_mode="HTML",
        )
        return

    context.user_data.clear()
    await update.message.reply_text(
        L(lang, "welcome_body"),
        reply_markup=start_menu(lang),
        parse_mode="HTML",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(
        L(lang, "help_text"),
        parse_mode="HTML",
        reply_markup=back_to_start(lang),
    )


async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    await update.message.reply_text(
        L(DEFAULT_LANG, "lang_picker_title"),
        reply_markup=language_picker_menu(),
        parse_mode="HTML",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin_chat(update):
        return
    user = update.effective_user
    row = get_user(user.id)
    if not row:
        await update.message.reply_text(
            L(DEFAULT_LANG, "status_no_record"),
            parse_mode="HTML",
        )
        return
    lang = row["lang"] if row["lang"] in LANGS else DEFAULT_LANG
    dash = L(lang, "dash")
    yes = L(lang, "yes")
    no_ = L(lang, "no")
    st_word = L(lang, "status_field_status")
    parts = [
        L(lang, "status_title"),
        f"{L(lang, 'status_path')}: <b>{row['main_path'] or dash}</b>",
        f"{L(lang, 'status_flow')}: <b>{row['flow'] or dash}</b>",
        (f"{L(lang, 'status_vip_submitted')}: <b>{yes if row['vip_submitted'] else no_}</b>"
         + (f" ({st_word}: {row['vip_status']})" if row['vip_submitted'] else "")),
        (f"{L(lang, 'status_aff_submitted')}: <b>{yes if row['aff_submitted'] else no_}</b>"
         + (f" ({st_word}: {row['aff_status']})" if row['aff_submitted'] else "")),
    ]
    if row["funded_status"] and row["funded_status"] != "none":
        parts.append(f"{L(lang, 'status_funded')}: <b>{row['funded_status']}</b>")
    await update.message.reply_text(
        "\n".join(parts),
        parse_mode="HTML",
        reply_markup=back_to_start(lang),
    )


# ===================================================================
# BUTTON HANDLER (user flow + admin review callbacks + language picker)
# ===================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    data = query.data or ""
    # ---------- Admin chat: only admin review actions allowed ----------
    if is_admin_chat(update):
        if data.startswith("adm:"):
            await admin_action(update, context)
            return
        try:
            await query.answer()
        except Exception:
            pass
        return
    # ---------- User flow ----------
    user = query.from_user
    if is_blocked(user.id):
        try:
            await query.answer(L(get_lang(user.id), "access_disabled"), show_alert=True)
        except Exception:
            pass
        return
    # Language picker callback - handle BEFORE rate limiting so first-time users can always pick
    if data.startswith("setlang:"):
        new_lang = data.split(":", 1)[1]
        if new_lang not in LANGS:
            new_lang = DEFAULT_LANG
        upsert_user(user)
        set_lang(user.id, new_lang)
        try:
            await query.answer()
        except Exception:
            pass
        await query.message.reply_text(
            L(new_lang, "lang_set_ok"),
            parse_mode="HTML",
        )
        await query.message.reply_text(
            L(new_lang, "welcome_body"),
            reply_markup=start_menu(new_lang),
            parse_mode="HTML",
        )
        return
    if rate_limited(user.id):
        try:
            await query.answer(L(get_lang(user.id), "slow_down"))
        except Exception:
            pass
        return
    await query.answer()
    upsert_user(user)
    lang = get_lang(user.id)
    username = f"@{user.username}" if user.username else "No username"
    # ---------- Open language picker ----------
    if data == "change_lang":
        await query.message.reply_text(
            L(DEFAULT_LANG, "lang_picker_title"),
            reply_markup=language_picker_menu(),
            parse_mode="HTML",
        )
        return
    # ---------- Restart confirmation ----------
    if data == "restart_yes":
        context.user_data.clear()
        await query.message.reply_text(
            L(lang, "restart_yes_msg"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
        return
    if data == "restart_no":
        await query.message.reply_text(
            L(lang, "restart_no_msg"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
        return
    if data == "back_start":
        context.user_data.clear()
        await query.message.reply_text(
            L(lang, "back_short_welcome"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
        return
    # ---------- Team / Socials / FAQ ----------
    if data == "team":
        text = L(lang, "team_title") + "\n\n"
        for info in ADMINS.values():
            text += f"- <b>{info['label']}</b> - @{info['username']}\n"
        text += "\n" + L(lang, "team_footer")
        await query.message.reply_text(text, reply_markup=team_menu(lang), parse_mode="HTML")
        return
    if data == "socials":
        await query.message.reply_text(
            L(lang, "socials_body"),
            reply_markup=socials_menu(lang),
            parse_mode="HTML",
        )
        return
    if data == "faq":
        await query.message.reply_text(
            L(lang, "faq_intro"),
            reply_markup=faq_menu(lang),
            parse_mode="HTML",
        )
        return
    for fid, q_key, a_key in FAQ_KEYS:
        if data == fid:
            q = L(lang, q_key)
            a = L(lang, a_key, IB_CODE=IB_CODE)
            await query.message.reply_text(
                f"<b>{html.escape(q)}</b>\n\n{a}",
                reply_markup=faq_menu(lang),
                parse_mode="HTML",
            )
            return
    # ---------- VIP entry paths ----------
    if data == "vip_access":
        context.user_data["main_path"] = "vip"
        update_user(user.id, main_path="vip")
        await query.message.reply_text(
            L(lang, "vip_access_body"),
            reply_markup=vip_entry_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_free":
        context.user_data["vip_mode"] = "free"
        update_user(user.id, vip_mode="free")
        await query.message.reply_text(
            L(lang, "vip_free_body"),
            reply_markup=vip_free_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_paid":
        context.user_data["vip_mode"] = "paid"
        update_user(user.id, vip_mode="paid")
        await query.message.reply_text(
            L(lang, "vip_paid_body"),
            reply_markup=vip_paid_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_paid_live":
        context.user_data["vip_mode"] = "paid_live"
        update_user(user.id, vip_mode="paid_live")
        await query.message.reply_text(
            L(lang, "vip_paid_live_body"),
            reply_markup=vip_free_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_paid_funded":
        context.user_data["vip_mode"] = "paid_funded"
        context.user_data["flow"] = "vip_paid_funded"
        update_user(user.id, vip_mode="paid_funded", flow="vip_paid_funded")
        await query.message.reply_text(
            L(lang, "vip_paid_funded_body"),
            reply_markup=funded_payment_menu(lang),
            parse_mode="HTML",
        )
    elif data == "show_btc":
        await query.message.reply_text(
            L(lang, "show_btc_body", ADDR=BTC_ADDRESS),
            reply_markup=funded_payment_menu(lang),
            parse_mode="HTML",
        )
    elif data == "show_eth":
        await query.message.reply_text(
            L(lang, "show_eth_body", ADDR=ETHEREUM_ADDRESS),
            reply_markup=funded_payment_menu(lang),
            parse_mode="HTML",
        )
    elif data == "show_sol":
        await query.message.reply_text(
            L(lang, "show_sol_body", ADDR=SOLANA_ADDRESS),
            reply_markup=funded_payment_menu(lang),
            parse_mode="HTML",
        )
    elif data == "funded_payment_sent":
        context.user_data["funded_payment_sent"] = True
        log_event(user.id, "funded_payment_sent")
        await query.message.reply_text(
            L(lang, "funded_payment_sent_msg"),
            reply_markup=funded_payment_menu(lang),
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
                L(lang, "funded_already_submitted"),
                reply_markup=funded_review_menu(lang),
                parse_mode="HTML",
            )
            return
        if not context.user_data.get("funded_payment_sent"):
            await query.message.reply_text(
                L(lang, "funded_must_send_first"),
                reply_markup=funded_payment_menu(lang),
                parse_mode="HTML",
            )
            return
        context.user_data["awaiting_payment_proof"] = True
        await query.message.reply_text(
            L(lang, "funded_proof_prompt"),
            reply_markup=funded_payment_menu(lang),
            parse_mode="HTML",
        )
    elif data == "funded_waiting_review":
        await query.message.reply_text(
            L(lang, "funded_waiting_review_msg"),
            reply_markup=funded_review_menu(lang),
            parse_mode="HTML",
        )
    # ---------- Affiliate path ----------
    elif data == "ib_affiliate":
        context.user_data["main_path"] = "affiliate"
        update_user(user.id, main_path="affiliate")
        await query.message.reply_text(
            L(lang, "ib_affiliate_body"),
            reply_markup=affiliate_menu(lang),
            parse_mode="HTML",
        )
    elif data == "what_is_ib":
        await query.message.reply_text(
            L(lang, "what_is_ib_msg"),
            reply_markup=ib_pdf_menu(lang),
            parse_mode="HTML",
        )
        try:
            with open(TUTORIAL_PDF, "rb") as pdf:
                await query.message.reply_document(
                    document=pdf, caption=L(lang, "pdf_caption")
                )
        except FileNotFoundError:
            await query.message.reply_text(
                L(lang, "pdf_missing", PDF=TUTORIAL_PDF),
                reply_markup=ib_pdf_menu(lang),
                parse_mode="HTML",
            )
        try:
            with open(TUTORIAL_PDF_2, "rb") as pdf:
                await query.message.reply_document(
                    document=pdf, caption=L(lang, "pdf_caption")
                )
        except FileNotFoundError:
            await query.message.reply_text(
                L(lang, "pdf_missing", PDF=TUTORIAL_PDF_2),
                reply_markup=ib_pdf_menu(lang),
                parse_mode="HTML",
            )
    elif data == "affiliate_main":
        await query.message.reply_text(
            L(lang, "affiliate_main_body"),
            reply_markup=affiliate_main_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_new":
        context.user_data["flow"] = "vip_new"
        update_user(user.id, flow="vip_new")
        await query.message.reply_text(
            L(lang, "vip_new_body", IB_CODE=IB_CODE),
            reply_markup=vip_new_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_existing":
        context.user_data["flow"] = "vip_existing"
        update_user(user.id, flow="vip_existing")
        await query.message.reply_text(
            L(lang, "vip_existing_body"),
            reply_markup=vip_existing_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_registered":
        context.user_data["vip_registered"] = True
        log_event(user.id, "vip_registered")
        await query.message.reply_text(
            L(lang, "vip_registered_msg"),
            reply_markup=vip_new_menu(lang),
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
                L(lang, "vip_must_register_first"),
                reply_markup=vip_new_menu(lang),
                parse_mode="HTML",
            )
            return
        context.user_data["vip_deposit_done"] = True
        update_user(user.id, deposited_at=now_iso())
        log_event(user.id, "vip_deposit_done")
        await query.message.reply_text(
            L(lang, "vip_deposit_done_msg"),
            reply_markup=vip_new_menu(lang),
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
            L(lang, "vip_transfer_email_body",
              T1=TRANSFER_EMAIL_1, T2=TRANSFER_EMAIL_2,
              IB_ACCOUNT_NUMBER=IB_ACCOUNT_NUMBER),
            reply_markup=vip_existing_menu(lang),
            parse_mode="HTML",
        )
    elif data == "vip_sent_transfer":
        context.user_data["vip_transfer_sent"] = True
        log_event(user.id, "vip_transfer_sent")
        await query.message.reply_text(
            L(lang, "vip_transfer_sent_msg"),
            reply_markup=vip_existing_menu(lang),
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
                L(lang, "vip_must_send_transfer_first"),
                reply_markup=vip_existing_menu(lang),
                parse_mode="HTML",
            )
            return
        context.user_data["vip_existing_deposit_done"] = True
        update_user(user.id, deposited_at=now_iso())
        log_event(user.id, "vip_existing_deposit_done")
        await query.message.reply_text(
            L(lang, "vip_existing_deposit_done_msg"),
            reply_markup=vip_existing_menu(lang),
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
            L(lang, "flow_new_body", IB_CODE=IB_CODE),
            reply_markup=new_user_step_menu(lang),
            parse_mode="HTML",
        )
    elif data == "completed_registration":
        context.user_data["affiliate_registered"] = True
        log_event(user.id, "affiliate_registered")
        await query.message.reply_text(
            L(lang, "affiliate_registered_msg"),
            reply_markup=new_user_step_menu(lang),
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
            L(lang, "flow_existing_body"),
            reply_markup=existing_user_step_menu(lang),
            parse_mode="HTML",
        )
    elif data == "transfer_email_template":
        await query.message.reply_text(
            L(lang, "affiliate_transfer_email_body",
              T1=TRANSFER_EMAIL_1, T2=TRANSFER_EMAIL_2,
              IB_ACCOUNT_NUMBER=IB_ACCOUNT_NUMBER),
            reply_markup=existing_user_step_menu(lang),
            parse_mode="HTML",
        )
    elif data == "sent_transfer_email":
        context.user_data["affiliate_transfer_sent"] = True
        log_event(user.id, "affiliate_transfer_sent")
        await query.message.reply_text(
            L(lang, "affiliate_transfer_sent_msg"),
            reply_markup=existing_user_step_menu(lang),
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
            L(lang, "benefits_body"),
            reply_markup=back_to_affiliate_main(lang),
            parse_mode="HTML",
        )
    # ---------- UID submission gates ----------
    elif data == "submit_uid_vip":
        flow = context.user_data.get("flow")
        if context.user_data.get("vip_submitted"):
            await query.message.reply_text(
                L(lang, "vip_already_submitted"),
                reply_markup=vip_submitted_menu(lang),
                parse_mode="HTML",
            )
            return
        if flow == "vip_new" and not context.user_data.get("vip_deposit_done"):
            await query.message.reply_text(
                L(lang, "uid_not_ready_new_vip"),
                reply_markup=vip_new_menu(lang),
                parse_mode="HTML",
            )
            return
        if flow == "vip_existing" and not context.user_data.get("vip_existing_deposit_done"):
            await query.message.reply_text(
                L(lang, "uid_not_ready_existing_vip"),
                reply_markup=vip_existing_menu(lang),
                parse_mode="HTML",
            )
            return
        context.user_data["awaiting_uid"] = True
        context.user_data["uid_type"] = "vip"
        await query.message.reply_text(
            L(lang, "submit_uid_prompt"),
            reply_markup=back_to_vip_menu(lang),
            parse_mode="HTML",
        )
    elif data == "submit_uid_affiliate":
        flow = context.user_data.get("flow")
        if context.user_data.get("affiliate_submitted"):
            await query.message.reply_text(
                L(lang, "aff_already_submitted"),
                reply_markup=affiliate_submitted_menu(lang),
                parse_mode="HTML",
            )
            return
        if flow == "affiliate_new" and not context.user_data.get("affiliate_registered"):
            await query.message.reply_text(
                L(lang, "affiliate_must_register"),
                reply_markup=new_user_step_menu(lang),
                parse_mode="HTML",
            )
            return
        if flow == "affiliate_existing" and not context.user_data.get("affiliate_transfer_sent"):
            await query.message.reply_text(
                L(lang, "affiliate_must_send_transfer"),
                reply_markup=existing_user_step_menu(lang),
                parse_mode="HTML",
            )
            return
        context.user_data["awaiting_uid"] = True
        context.user_data["uid_type"] = "affiliate"
        await query.message.reply_text(
            L(lang, "submit_uid_prompt"),
            reply_markup=back_to_affiliate_main(lang),
            parse_mode="HTML",
        )
    elif data == "vip_waiting_review":
        await query.message.reply_text(
            L(lang, "vip_waiting_review_msg"),
            reply_markup=vip_submitted_menu(lang),
            parse_mode="HTML",
        )
    elif data == "affiliate_waiting_review":
        await query.message.reply_text(
            L(lang, "aff_waiting_review_msg"),
            reply_markup=affiliate_submitted_menu(lang),
            parse_mode="HTML",
        )
    elif data == "support":
        await query.message.reply_text(
            L(lang, "support_body"),
            reply_markup=support_admin_menu(lang),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>Support request received</b>\n"
                f"Name: {html.escape(user.full_name)}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Language: <b>{lang}</b>\n"
                f"Main Path: <b>{context.user_data.get('main_path', 'unknown')}</b>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                f"Flow: <b>{context.user_data.get('flow', 'unknown')}</b>"
            ),
        )
    else:
        await query.message.reply_text(
            L(lang, "fallback_msg"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )

# ---------------------------------------------------------------------------
# Text & media handlers (UID submissions, payment proofs)
# ---------------------------------------------------------------------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.effective_user or not update.message:
            return
        if is_admin_chat(update):
            return
        user = update.effective_user
        if is_blocked(user.id):
            return
        # NOTE: rate_limited returns True when the user is over the limit;
        # we return ONLY in that case. (Previous code had this inverted,
        # which caused every first message to silently drop.)
        if rate_limited(user.id):
            log.info("text_handler: rate limited user=%s", user.id)
            return
        upsert_user(user)
        lang = get_lang(user.id)
        text = (update.message.text or "").strip()
        log.info("text_handler: user=%s lang=%s awaiting_uid=%s awaiting_funded=%s text=%r",
                 user.id, lang,
                 context.user_data.get("awaiting_uid"),
                 context.user_data.get("awaiting_funded_proof"),
                 text[:80])
        if not text:
            return

        # Funded payment proof awaiting
        if context.user_data.get("awaiting_funded_proof"):
            parsed = parse_payment_submission(text)
            if not parsed:
                await update.message.reply_text(
                    L(lang, "funded_submit_bad_format"),
                    reply_markup=funded_review_menu(lang),
                    parse_mode="HTML",
                )
                return
            method = parsed  # parse_payment_submission returns "FUNDED"
            context.user_data["awaiting_funded_proof"] = False
            context.user_data["funded_submitted"] = True
            log_event(user.id, "funded_payment_submitted", f"method={method}")
            await try_react(update, context, "🔥")
            await update.message.reply_text(
                L(lang, "funded_submit_received"),
                reply_markup=start_menu(lang),
                parse_mode="HTML",
            )
            await notify_admin(
                context,
                (
                    "<b>💎 Funded VIP payment submitted</b>\n"
                    f"User: {html.escape(user.full_name)} "
                    f"(@{html.escape(user.username) if user.username else '—'})\n"
                    f"User ID: <code>{user.id}</code>\n"
                    f"Language: <b>{lang}</b>\n"
                    f"Method: <b>{method}</b>\n"
                    f"Raw: <code>{html.escape(text[:200])}</code>"
                ),
                user_id=user.id,
                action_type="funded_payment",
            )
            return

        # UID submission awaiting
        if context.user_data.get("awaiting_uid"):
            uid_type = context.user_data.get("uid_type", "vip")
            parsed = parse_uid_submission(text)
            if not parsed:
                log.info("text_handler: UID format bad user=%s raw=%r", user.id, text[:80])
                await update.message.reply_text(
                    L(lang, "uid_bad_format"),
                    reply_markup=back_to_start(lang) if uid_type == "vip" else back_to_affiliate_main(lang),
                    parse_mode="HTML",
                )
                return
            uid = parsed  # parse_uid_submission returns just the digits string
            context.user_data["awaiting_uid"] = False
            ok, existing = register_uid(uid, user.id, uid_type)
            await try_react(update, context, "👍" if ok else "👀")
            if uid_type == "vip":
                context.user_data["vip_submitted"] = True
                log_event(user.id, "vip_uid_submitted",
                          f"uid={uid} duplicate={'yes' if not ok else 'no'}")
                await update.message.reply_text(
                    L(lang, "vip_uid_received"),
                    reply_markup=vip_submitted_menu(lang),
                    parse_mode="HTML",
                )
            else:
                context.user_data["affiliate_submitted"] = True
                log_event(user.id, "affiliate_uid_submitted",
                          f"uid={uid} duplicate={'yes' if not ok else 'no'}")
                await update.message.reply_text(
                    L(lang, "aff_uid_received"),
                    reply_markup=affiliate_submitted_menu(lang),
                    parse_mode="HTML",
                )
            dup_line = ""
            if not ok and existing and existing != user.id:
                dup_line = f"\n⚠️ Duplicate — previously registered to user <code>{existing}</code>"
            await notify_admin(
                context,
                (
                    f"<b>{'🏆 VIP' if uid_type == 'vip' else '🤝 Affiliate'} UID submission</b>\n"
                    f"User: {html.escape(user.full_name)} "
                    f"(@{html.escape(user.username) if user.username else '—'})\n"
                    f"User ID: <code>{user.id}</code>\n"
                    f"Language: <b>{lang}</b>\n"
                    f"UID: <code>{html.escape(uid)}</code>"
                    f"{dup_line}"
                ),
                user_id=user.id,
                action_type=uid_type,
            )
            return

        # Any other free-text goes nowhere useful; gently guide back to the menu.
        await update.message.reply_text(
            L(lang, "fallback_msg"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
    except Exception:
        log.exception("text_handler crashed")
        try:
            lang = get_lang(update.effective_user.id) if update.effective_user else "en"
            await update.message.reply_text(
                L(lang, "fallback_msg"),
                reply_markup=start_menu(lang),
                parse_mode="HTML",
            )
        except Exception:
            log.exception("text_handler fallback reply also failed")


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.effective_user or not update.message:
            return
        if is_admin_chat(update):
            return
        user = update.effective_user
        if is_blocked(user.id):
            return
        if rate_limited(user.id):
            log.info("media_handler: rate limited user=%s", user.id)
            return
        upsert_user(user)
        lang = get_lang(user.id)
        caption = (update.message.caption or "").strip()
        log.info("media_handler: user=%s lang=%s awaiting_uid=%s awaiting_funded=%s caption=%r",
                 user.id, lang,
                 context.user_data.get("awaiting_uid"),
                 context.user_data.get("awaiting_funded_proof"),
                 caption[:80])

        # Funded payment proof with photo/doc caption
        if context.user_data.get("awaiting_funded_proof"):
            parsed = parse_payment_submission(caption) if caption else None
            if not parsed:
                await update.message.reply_text(
                    L(lang, "funded_submit_bad_format"),
                    reply_markup=funded_review_menu(lang),
                    parse_mode="HTML",
                )
                return
            method = parsed
            context.user_data["awaiting_funded_proof"] = False
            context.user_data["funded_submitted"] = True
            log_event(user.id, "funded_payment_submitted_media", f"method={method}")
            await try_react(update, context, "🔥")
            await update.message.reply_text(
                L(lang, "funded_submit_received"),
                reply_markup=start_menu(lang),
                parse_mode="HTML",
            )
            try:
                await update.message.forward(chat_id=ADMIN_CHAT_ID)
            except Exception:
                log.exception("Failed to forward funded payment proof")
            await notify_admin(
                context,
                (
                    "<b>💎 Funded VIP payment submitted (with media)</b>\n"
                    f"User: {html.escape(user.full_name)} "
                    f"(@{html.escape(user.username) if user.username else '—'})\n"
                    f"User ID: <code>{user.id}</code>\n"
                    f"Language: <b>{lang}</b>\n"
                    f"Method: <b>{method}</b>"
                ),
                user_id=user.id,
                action_type="funded_payment",
            )
            return

        # UID submission via caption
        if context.user_data.get("awaiting_uid"):
            uid_type = context.user_data.get("uid_type", "vip")
            parsed = parse_uid_submission(caption) if caption else None
            if not parsed:
                log.info("media_handler: UID format bad user=%s caption=%r", user.id, caption[:80])
                await update.message.reply_text(
                    L(lang, "uid_bad_format"),
                    reply_markup=back_to_start(lang) if uid_type == "vip" else back_to_affiliate_main(lang),
                    parse_mode="HTML",
                )
                return
            uid = parsed
            context.user_data["awaiting_uid"] = False
            ok, existing = register_uid(uid, user.id, uid_type)
            await try_react(update, context, "👍" if ok else "👀")
            if uid_type == "vip":
                context.user_data["vip_submitted"] = True
                log_event(user.id, "vip_uid_submitted_media",
                          f"uid={uid} duplicate={'yes' if not ok else 'no'}")
                await update.message.reply_text(
                    L(lang, "vip_uid_received"),
                    reply_markup=vip_submitted_menu(lang),
                    parse_mode="HTML",
                )
            else:
                context.user_data["affiliate_submitted"] = True
                log_event(user.id, "affiliate_uid_submitted_media",
                          f"uid={uid} duplicate={'yes' if not ok else 'no'}")
                await update.message.reply_text(
                    L(lang, "aff_uid_received"),
                    reply_markup=affiliate_submitted_menu(lang),
                    parse_mode="HTML",
                )
            try:
                await update.message.forward(chat_id=ADMIN_CHAT_ID)
            except Exception:
                log.exception("Failed to forward UID media")
            dup_line = ""
            if not ok and existing and existing != user.id:
                dup_line = f"\n⚠️ Duplicate — previously registered to user <code>{existing}</code>"
            await notify_admin(
                context,
                (
                    f"<b>{'🏆 VIP' if uid_type == 'vip' else '🤝 Affiliate'} UID submission (with media)</b>\n"
                    f"User: {html.escape(user.full_name)} "
                    f"(@{html.escape(user.username) if user.username else '—'})\n"
                    f"User ID: <code>{user.id}</code>\n"
                    f"Language: <b>{lang}</b>\n"
                    f"UID: <code>{html.escape(uid)}</code>"
                    f"{dup_line}"
                ),
                user_id=user.id,
                action_type=uid_type,
            )
            return

        # Unrelated media — acknowledge gently
        await update.message.reply_text(
            L(lang, "fallback_msg"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
    except Exception:
        log.exception("media_handler crashed")
        try:
            lang = get_lang(update.effective_user.id) if update.effective_user else "en"
            await update.message.reply_text(
                L(lang, "fallback_msg"),
                reply_markup=start_menu(lang),
                parse_mode="HTML",
            )
        except Exception:
            log.exception("media_handler fallback reply also failed")


# ---------------------------------------------------------------------------
# Admin callback actions (approve / reject / block)
# ---------------------------------------------------------------------------
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if not query.data or not query.data.startswith("adm:"):
        return
    try:
        _, action, uid_str = query.data.split(":", 2)
        target_id = int(uid_str)
    except Exception:
        await query.message.reply_text("Malformed admin action.")
        return

    target_lang = get_lang(target_id)
    actor = update.effective_user.full_name if update.effective_user else "admin"

    if action == "approve":
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=L(target_lang, "approved_dm"),
                parse_mode="HTML",
            )
        except Exception:
            log.exception("Failed to DM approved user")
        log_event(target_id, "admin_approved", f"by={actor}")
        await query.message.reply_text(
            f"Approved <code>{target_id}</code> ({target_lang}).",
            parse_mode="HTML",
        )
    elif action == "reject":
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=L(target_lang, "rejected_dm"),
                parse_mode="HTML",
            )
        except Exception:
            log.exception("Failed to DM rejected user")
        log_event(target_id, "admin_rejected", f"by={actor}")
        await query.message.reply_text(
            f"Rejected <code>{target_id}</code> ({target_lang}).",
            parse_mode="HTML",
        )
    elif action == "block":
        conn = db()
        try:
            conn.execute(
                "UPDATE users SET blocked = 1 WHERE user_id = ?",
                (target_id,),
            )
            conn.commit()
        finally:
            conn.close()
        log_event(target_id, "admin_blocked", f"by={actor}")
        await query.message.reply_text(
            f"Blocked <code>{target_id}</code>.",
            parse_mode="HTML",
        )
    else:
        await query.message.reply_text("Unknown admin action.")


# ---------------------------------------------------------------------------
# Admin commands
# ---------------------------------------------------------------------------
JOIN_FREE_POST = (
    "<b>Free Signals Channel</b>\n\n"
    "Tap the button below to join the ImperiumFX free-signals channel.\n"
    "Get daily trade ideas, market commentary, and previews of VIP plays."
)


def join_free_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Free Signals", url=f"https://t.me/{BOT_USERNAME}?start=freesignals")],
    ])


def _extract_custom_message(args: list[str]) -> str:
    return " ".join(args).strip()


@admin_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    snap = stats_snapshot()
    lines = ["<b>ImperiumFX Bot — Stats</b>"]
    lines.append(f"Total users: <b>{snap['total']}</b>")
    lines.append(f"New (24h): <b>{snap['new_24h']}</b>")
    lines.append(f"Started flow: <b>{snap['started']}</b>")
    lines.append(f"Blocked: <b>{snap['blocked']}</b>")
    lines.append("")
    lines.append(f"VIP pending: <b>{snap['vip_pending']}</b>")
    lines.append(f"VIP approved: <b>{snap['vip_approved']}</b>")
    lines.append(f"VIP rejected: <b>{snap['vip_rejected']}</b>")
    lines.append(f"Affiliate pending: <b>{snap['aff_pending']}</b>")
    lines.append(f"Affiliate approved: <b>{snap['aff_approved']}</b>")
    lines.append(f"Funded active: <b>{snap['funded_active']}</b>")
    lines.append("")
    lines.append("<b>By language:</b>")
    for code in LANGS:
        cnt = snap["by_lang"].get(code, 0)
        lines.append(f"  {LANG_FLAG[code]} {LANG_LABELS[code]}: <b>{cnt}</b>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@admin_only
async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /user <telegram_user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    row = get_user(uid)
    if not row:
        await update.message.reply_text(f"No record for <code>{uid}</code>.", parse_mode="HTML")
        return
    lang = row["lang"] if "lang" in row.keys() else DEFAULT_LANG
    text = (
        f"<b>User {uid}</b>\n"
        f"Name: {html.escape(row['full_name'] or '—')}\n"
        f"Username: @{html.escape(row['username']) if row['username'] else '—'}\n"
        f"Language: <b>{lang}</b> {LANG_FLAG.get(lang, '')}\n"
        f"Blocked: <b>{bool(row['blocked'])}</b>\n"
        f"First seen: {row['first_seen']}\n"
        f"Last seen: {row['last_seen']}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


@admin_only
async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    lang = get_lang(uid)
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=L(lang, "approved_dm"),
            parse_mode="HTML",
        )
        log_event(uid, "admin_approved_cmd")
        await update.message.reply_text(f"Approved <code>{uid}</code>.", parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"Failed: {exc}")


@admin_only
async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /reject <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    lang = get_lang(uid)
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=L(lang, "rejected_dm"),
            parse_mode="HTML",
        )
        log_event(uid, "admin_rejected_cmd")
        await update.message.reply_text(f"Rejected <code>{uid}</code>.", parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"Failed: {exc}")


@admin_only
async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /block <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    conn = db()
    try:
        conn.execute("UPDATE users SET blocked = 1 WHERE user_id = ?", (uid,))
        conn.commit()
    finally:
        conn.close()
    log_event(uid, "admin_blocked_cmd")
    await update.message.reply_text(f"Blocked <code>{uid}</code>.", parse_mode="HTML")


@admin_only
async def cmd_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    conn = db()
    try:
        conn.execute("UPDATE users SET blocked = 0 WHERE user_id = ?", (uid,))
        conn.commit()
    finally:
        conn.close()
    log_event(uid, "admin_unblocked_cmd")
    await update.message.reply_text(f"Unblocked <code>{uid}</code>.", parse_mode="HTML")


@admin_only
async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = _extract_custom_message(context.args)
    if not msg:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    conn = db()
    try:
        rows = conn.execute(
            "SELECT user_id FROM users WHERE blocked = 0"
        ).fetchall()
    finally:
        conn.close()
    sent = 0
    failed = 0
    for row in rows:
        try:
            await context.bot.send_message(
                chat_id=row["user_id"], text=msg, parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(
        f"Broadcast done. Sent: <b>{sent}</b> | Failed: <b>{failed}</b>",
        parse_mode="HTML",
    )


@admin_only
async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = _extract_custom_message(context.args)
    if not msg:
        await update.message.reply_text("Usage: /post <message>")
        return
    try:
        await context.bot.send_message(
            chat_id=MAIN_GROUP_CHAT_ID,
            text=msg,
            parse_mode="HTML",
        )
        await update.message.reply_text("Posted to main group.")
    except Exception as exc:
        await update.message.reply_text(f"Failed: {exc}")


@admin_only
async def cmd_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /send <user_id> <message>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    msg = _extract_custom_message(context.args[1:])
    try:
        await context.bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
        await update.message.reply_text(f"Sent to <code>{uid}</code>.", parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"Failed: {exc}")


@admin_only
async def cmd_sendbtn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /sendbtn <user_id> <button_text>|<url> :: <message>
    if not context.args:
        await update.message.reply_text(
            "Usage: /sendbtn <user_id> <button_text>|<url> :: <message>"
        )
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID must be a number.")
        return
    rest = " ".join(context.args[1:])
    if "::" not in rest or "|" not in rest.split("::", 1)[0]:
        await update.message.reply_text(
            "Format: /sendbtn <user_id> <button_text>|<url> :: <message>"
        )
        return
    btn_part, msg = rest.split("::", 1)
    btn_text, btn_url = btn_part.split("|", 1)
    btn_text = btn_text.strip()
    btn_url = btn_url.strip()
    msg = msg.strip()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(btn_text, url=btn_url)]])
    try:
        await context.bot.send_message(
            chat_id=uid, text=msg, parse_mode="HTML", reply_markup=kb
        )
        await update.message.reply_text(f"Sent to <code>{uid}</code>.", parse_mode="HTML")
    except Exception as exc:
        await update.message.reply_text(f"Failed: {exc}")


@admin_only
async def cmd_adminhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>ImperiumFX Admin Reference</b>\n\n"
        "<b>Moderation</b>\n"
        "/approve &lt;user_id&gt; — DM the approved template in their language\n"
        "/reject &lt;user_id&gt; — DM the rejection template\n"
        "/block &lt;user_id&gt; — block a user from the bot\n"
        "/unblock &lt;user_id&gt; — unblock a user\n\n"
        "<b>Communication</b>\n"
        "/send &lt;user_id&gt; &lt;message&gt; — DM an arbitrary message\n"
        "/sendbtn &lt;user_id&gt; &lt;text&gt;|&lt;url&gt; :: &lt;message&gt; — DM with a URL button\n"
        "/broadcast &lt;message&gt; — DM every non-blocked user (rate limited)\n"
        "/post &lt;message&gt; — post to the main group\n\n"
        "<b>Insights</b>\n"
        "/stats — total users, 24h events, UID count, language split\n"
        "/user &lt;user_id&gt; — profile snapshot for one user\n\n"
        "<b>Admins</b>\n"
        + "\n".join(
            f"• {v['role']}: {html.escape(v['name'])}"
            for v in ADMINS.values()
        )
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Scheduled jobs (nudges + renewal reminders)
# ---------------------------------------------------------------------------
async def job_nudges(context: ContextTypes.DEFAULT_TYPE):
    # Gentle nudge to users who never completed a submission in 48h.
    conn = db()
    try:
        rows = conn.execute(
            """
            SELECT u.user_id
            FROM users u
            WHERE u.blocked = 0
              AND datetime(u.first_seen) <= datetime('now', '-48 hours')
              AND u.user_id NOT IN (SELECT user_id FROM uid_registry)
            """
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        uid = row["user_id"]
        lang = get_lang(uid)
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=L(lang, "nudge_incomplete"),
                parse_mode="HTML",
                reply_markup=start_menu(lang),
            )
            log_event(uid, "nudge_incomplete_sent")
        except Exception:
            log.exception("Failed to send nudge to %s", uid)
        await asyncio.sleep(0.05)


async def job_renewals(context: ContextTypes.DEFAULT_TYPE):
    # Remind users 25 days after a successful VIP / funded payment.
    conn = db()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT e.user_id
            FROM events e
            WHERE (e.event = 'funded_payment_submitted'
                   OR e.event = 'admin_approved'
                   OR e.event = 'admin_approved_cmd')
              AND datetime(e.ts) BETWEEN datetime('now', '-26 days')
                                   AND datetime('now', '-25 days')
            """
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        uid = row["user_id"]
        lang = get_lang(uid)
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=L(lang, "renewal_reminder", DAYS=5),
                parse_mode="HTML",
                reply_markup=start_menu(lang),
            )
            log_event(uid, "renewal_reminder_sent")
        except Exception:
            log.exception("Failed to send renewal reminder to %s", uid)
        await asyncio.sleep(0.05)


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled error: %s", context.error)
    try:
        if isinstance(update, Update) and update.effective_user:
            lang = get_lang(update.effective_user.id)
            if update.effective_message:
                await update.effective_message.reply_text(
                    L(lang, "fallback_msg"),
                    reply_markup=start_menu(lang),
                    parse_mode="HTML",
                )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------
def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env var is required")

    # Python 3.14 event-loop compatibility
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
    except Exception:
        pass

    db_init()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands (users)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("language", cmd_language))

    # Commands (admin)
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("user", cmd_user))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("reject", cmd_reject))
    app.add_handler(CommandHandler("block", cmd_block))
    app.add_handler(CommandHandler("unblock", cmd_unblock))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("post", cmd_post))
    app.add_handler(CommandHandler("send", cmd_send))
    app.add_handler(CommandHandler("sendbtn", cmd_sendbtn))
    app.add_handler(CommandHandler("adminhelp", cmd_adminhelp))

    # Callback queries — admin actions first so adm:* wins the match
    app.add_handler(CallbackQueryHandler(admin_action, pattern=r"^adm:"))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Free text + media
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, media_handler))

    # Error handler
    app.add_error_handler(on_error)

    # Scheduled jobs
    jq = app.job_queue
    if jq is not None:
        jq.run_repeating(job_nudges, interval=6 * 60 * 60, first=30)
        jq.run_repeating(job_renewals, interval=12 * 60 * 60, first=60)

    log.info("ImperiumFX bot starting…")
    # drop_pending_updates + delete_webhook avoids "Conflict: terminated by other getUpdates"
    # errors when Railway redeploys before the old instance has fully released the long poll.
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()