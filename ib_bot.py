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
# CONFIG
# ===================================================================
BOT_TOKEN = "8085633137:AAEM6MOSPirix26Bs4Ye9wqryX063L-FO60"
ADMIN_CHAT_ID = -1003919089074
MAIN_GROUP_CHAT_ID = -1003752395437
BOT_USERNAME = "imperiumfx_onboarding_bot"

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
LANGS = ["en", "zh", "ar", "es", "pt"]
DEFAULT_LANG = "en"

LANG_LABELS = {
    "en": "English",
    "zh": "中文 (Chinese)",
    "ar": "العربية (Arabic)",
    "es": "Espanol (Spanish)",
    "pt": "Portugues (Portuguese)",
}

LANG_FLAG = {
    "en": "EN",
    "zh": "CN",
    "ar": "AR",
    "es": "ES",
    "pt": "PT",
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
    "lang_picker_title": "<b>Please choose your language</b>\n\nYou can change it later with /language.",
    "lang_set_ok": "<b>Language set.</b> Loading the main menu...",

    # ---------- welcome / start ----------
    "welcome_title": "<b>Welcome to ImperiumFX Setup</b>",
    "welcome_body": (
        "<b>Welcome to ImperiumFX Setup</b>\n\n"
        "Choose your path below.\n\n"
        "- <b>VIP Access</b> - join our VIP signal access\n"
        "- <b>IB Affiliate</b> - become an affiliate and follow the IB onboarding process\n"
        "- <b>Meet the Team</b> - see who runs ImperiumFX\n"
        "- <b>Follow Us</b> - Instagram & TikTok\n"
        "- <b>FAQ</b> - quick answers to common questions\n\n"
        "<i>Please choose the option that matches what you want.</i>"
    ),
    "resume_prompt": (
        "<b>You already have progress in the bot.</b>\n\n"
        "Do you want to <b>restart</b> from the beginning, or keep your current progress?"
    ),
    "restart_yes_msg": "<b>Welcome to ImperiumFX Setup</b>\n\nChoose your path below.",
    "restart_no_msg": "Progress kept. Press a button below to continue.",
    "back_short_welcome": (
        "<b>Welcome to ImperiumFX Setup</b>\n\n"
        "Choose your path below.\n\n"
        "- <b>VIP Access</b> - join our VIP signal access\n"
        "- <b>IB Affiliate</b> - become an affiliate and follow the IB onboarding process\n\n"
        "<i>Please choose the option that matches what you want.</i>"
    ),

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
        "Send your <b>MT5 UID / account number</b> now in this exact format:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Important:</b>\n"
        "- write <code>UID:</code> first\n"
        "- then your number\n"
        "- digits only\n"
        "- no extra text\n\n"
        "If you send a screenshot or document, the <b>caption</b> must use the same format."
    ),
    "uid_format_guide": (
        "<b>Invalid UID format.</b>\n\n"
        "Send your UID in this exact format:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Rules:</b>\n"
        "- must start with <code>UID:</code>\n"
        "- numbers only after that\n"
        "- no extra words\n"
        "- no spaces before UID\n\n"
        "<i>Example:</i> <code>UID: 123517235</code>"
    ),
    "payment_format_guide": (
        "<b>Invalid payment proof format.</b>\n\n"
        "If you send payment proof, the caption must be exactly:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>Invalid caption format.</b>\n\n"
        "If you send a screenshot or document, the caption must be:\n\n"
        "<code>UID: 12345678</code>"
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
        "<b>Format not recognized.</b>\n"
        "Please send your UID and PU Prime email like this:\n"
        "<code>UID: 12345678\nEmail: you@example.com</code>"
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
        "or wrong UID format. Make sure you used code <code>{IB_CODE}</code>, "
        "deposited, and submitted in this exact format: <code>UID: 12345678</code>"
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
    "btn_vip_access": "Join VIP Access",
    "btn_ib_affiliate": "Become an IB Affiliate",
    "btn_team": "Meet the Team",
    "btn_socials": "Follow Us",
    "btn_faq": "FAQ",
    "btn_support": "Contact Support",
    "btn_back": "Back",
    "btn_back_to_start": "Back to Start",
    "btn_back_to_vip": "Back to VIP Menu",
    "btn_back_to_affiliate": "Back to Affiliate Menu",
    "btn_yes_restart": "Yes, restart",
    "btn_no_keep": "No, keep progress",
    "btn_free_vip": "Free VIP",
    "btn_paid_vip": "Paid VIP",
    "btn_new_to_pu": "New to PU Prime",
    "btn_existing_pu": "Already with PU Prime",
    "btn_live_account": "Live Account",
    "btn_funded_account": "Funded Account",
    "btn_dont_know_ib": "I don't know what IB is",
    "btn_already_know": "I already know, continue",
    "btn_continue": "Continue",
    "btn_step1_register": "Step 1: Register with PU Prime",
    "btn_step1_start_reg": "Step 1: Start Registration",
    "btn_step2_completed": "Step 2: I Completed Registration",
    "btn_step3_deposited": "Step 3: I Deposited",
    "btn_step4_submit_uid": "Step 4: Submit UID",
    "btn_step3_submit_uid": "Step 3: Submit UID",
    "btn_step1_view_email": "Step 1: View Transfer Email",
    "btn_step2_sent_email": "Step 2: I Sent the Email",
    "btn_view_btc": "View BTC Address",
    "btn_view_eth": "View ETH Address",
    "btn_view_sol": "View SOL Address",
    "btn_sent_payment": "I Sent Payment",
    "btn_submit_proof": "Submit Payment Proof",
    "btn_waiting_payment_review": "Waiting for Payment Review",
    "btn_waiting_review": "Waiting for Review",
    "btn_benefits": "IB Benefits",
    "btn_message": "Message",
    "btn_founder": "Founder - Kratos",
    "btn_onboarding": "Onboarding / General - Apollo",
    "btn_signals": "Signals - Plato",
    "btn_socials_admin": "Socials - HD",
    "btn_change_language": "Change Language",
    "btn_approve": "Approve",
    "btn_reject": "Reject",
    "btn_block_user": "Block User",
}

TEXTS["zh"] = {
    "lang_picker_title": "<b>请选择您的语言</b>\n\n稍后可以通过 /language 更改。",
    "lang_set_ok": "<b>语言已设置。</b> 正在加载主菜单...",

    "welcome_title": "<b>欢迎来到 ImperiumFX</b>",
    "welcome_body": (
        "<b>欢迎来到 ImperiumFX</b>\n\n"
        "请在下方选择您的路径。\n\n"
        "- <b>VIP 通道</b> - 加入我们的 VIP 信号通道\n"
        "- <b>IB 代理</b> - 成为代理并完成 IB 注册流程\n"
        "- <b>团队介绍</b> - 了解 ImperiumFX 的团队\n"
        "- <b>关注我们</b> - Instagram 与 TikTok\n"
        "- <b>常见问题</b> - 常见疑问的快速解答\n\n"
        "<i>请选择最符合您需求的选项。</i>"
    ),
    "resume_prompt": (
        "<b>您在机器人中已有进度。</b>\n\n"
        "是否要<b>重新开始</b>,还是保留当前进度?"
    ),
    "restart_yes_msg": "<b>欢迎来到 ImperiumFX</b>\n\n请在下方选择您的路径。",
    "restart_no_msg": "进度已保留。请点击下方按钮继续。",
    "back_short_welcome": (
        "<b>欢迎来到 ImperiumFX</b>\n\n"
        "请在下方选择您的路径。\n\n"
        "- <b>VIP 通道</b> - 加入我们的 VIP 信号通道\n"
        "- <b>IB 代理</b> - 成为代理并完成 IB 注册流程\n\n"
        "<i>请选择最符合您需求的选项。</i>"
    ),

    "help_text": (
        "<b>ImperiumFX 机器人 - 帮助</b>\n\n"
        "- /start - 打开主菜单\n"
        "- /status - 查看您的进度\n"
        "- /language - 更改语言\n"
        "- /help - 显示此信息\n\n"
        "如果遇到问题,请点击任意菜单中的 <b>联系客服</b>。"
    ),
    "status_title": "<b>您的状态</b>",
    "status_no_record": "尚未找到记录。请按 /start 开始。",
    "status_path": "路径",
    "status_flow": "流程",
    "status_vip_submitted": "VIP 已提交",
    "status_aff_submitted": "代理已提交",
    "status_funded": "资金账户 VIP",
    "yes": "是",
    "no": "否",
    "status_field_status": "状态",
    "dash": "-",

    "access_disabled": "访问已禁用。请联系客服。",
    "slow_down": "请慢一点",
    "fallback_unknown": (
        "未能识别您的输入 - 这是菜单。\n"
        "按 /start 开始,/status 查看进度,/help 获取帮助。"
    ),
    "fallback_media": "未能识别您的输入 - 这是菜单。按 /start 开始。",

    "team_title": "<b>团队介绍</b>",
    "team_footer": "<i>点击下方按钮直接联系他们。</i>",
    "socials_body": (
        "<b>关注 ImperiumFX</b>\n\n"
        "关注我们获取最新内容、信号预览和福利活动。"
    ),
    "faq_intro": "<b>常见问题</b>\n\n请在下方选择一个问题。",

    "vip_access_body": (
        "<b>VIP 通道</b>\n\n"
        "请在下方选择您的 VIP 路径。\n\n"
        "<b>免费 VIP</b>\n"
        "- 适用于在我们 IB 下注册的用户\n"
        "- 需要在我们名下注册/转移并入金\n\n"
        "<b>付费 VIP</b>\n"
        "- 适用于想要直接访问的用户\n"
        "- 资金账户按月付费\n\n"
        "<i>请选择符合您情况的选项。</i>"
    ),
    "vip_free_body": (
        "<b>免费 VIP</b>\n\n"
        "要获得资格,您必须<b>选择其中一项</b>:\n\n"
        "1. <b>在我们名下注册 PU Prime</b>\n"
        "2. <b>将您现有的 PU Prime 账户转移到我们名下</b>\n\n"
        "<b>重要规则:</b>\n"
        "- 您必须在我们的 IB 下\n"
        "- 您必须<b>入金</b>\n"
        "- 否则<b>将无法获得免费 VIP 访问权限</b>\n\n"
        "<i>请在下方选择符合您情况的选项。</i>"
    ),
    "vip_paid_body": (
        "<b>付费 VIP</b>\n\n"
        "请选择您使用的账户类型。\n\n"
        "<b>真实账户</b>\n"
        "- 结构与免费 VIP 相同\n"
        "- 您必须在我们的 IB 下并入金\n\n"
        "<b>资金账户</b>\n"
        "- 首月 <b>50 欧元</b>\n"
        "- 此后每月 <b>80 欧元</b>\n\n"
        "<i>请在下方选择您的账户类型。</i>"
    ),
    "vip_paid_live_body": (
        "<b>付费 VIP - 真实账户</b>\n\n"
        "对于真实账户,您的访问通过我们的 IB 结构处理。\n\n"
        "这意味着您必须:\n"
        "1. 在我们名下注册或转移\n"
        "2. 入金\n"
        "3. 提交您的 UID\n\n"
        "<i>请在下方选择您的路径。</i>"
    ),
    "vip_paid_funded_body": (
        "<b>付费 VIP - 资金账户</b>\n\n"
        "<b>价格:</b>\n"
        "- 首月 <b>50 欧元</b>\n"
        "- 此后每月 <b>80 欧元</b>\n\n"
        "<b>支付方式:</b>\n"
        "- BTC\n"
        "- ETH\n"
        "- SOL\n\n"
        "<b>下一步:</b>\n"
        "1. 查看钱包地址\n"
        "2. 发送付款\n"
        "3. 提交付款证明\n\n"
        "<i>请使用下方按钮。</i>"
    ),
    "vip_new_body": (
        "<b>VIP 通道 - PU Prime 新用户</b>\n\n"
        "请按顺序完成以下步骤:\n\n"
        "1. <b>使用我们的链接注册</b>\n"
        "2. 确保代码为 <b>{IB_CODE}</b>\n"
        "3. 完成注册\n"
        "4. <b>入金</b>\n"
        "5. 提交您的 <b>MT5 UID / 账户号码</b>\n\n"
        "<b>重要:</b>\n"
        "- VIP 仅适用于在我们名下的用户\n"
        "- 仅仅注册<b>是不够的</b>\n"
        "- 您必须<b>入金</b>后才会审核\n\n"
        "<i>请仔细按照下方步骤操作。</i>"
    ),
    "vip_existing_body": (
        "<b>VIP 通道 - PU Prime 现有用户</b>\n\n"
        "请按顺序完成以下步骤:\n\n"
        "1. 发送 <b>IB 转移邮件</b>\n"
        "2. 等待转移确认\n"
        "3. <b>入金</b>\n"
        "4. 提交您的 <b>MT5 UID / 账户号码</b>\n\n"
        "<b>重要:</b>\n"
        "- 您的账户必须转移到我们的 IB 下\n"
        "- 您必须<b>入金</b>\n"
        "- 否则<b>将无法获得 VIP 访问权限</b>\n\n"
        "<i>请仔细按照下方步骤操作。</i>"
    ),
    "vip_registered_msg": (
        "<b>注册已标记为完成。</b>\n\n"
        "<b>下一项要求:</b>在提交 UID 进行 VIP 审核之前,您现在必须<b>入金</b>。\n\n"
        "<i>请勿跳过此步骤。</i>"
    ),
    "vip_must_register_first": (
        "<b>您必须先完成注册。</b>\n\n"
        "请按顺序执行步骤。\n\n"
        "<i>第 3 步之前必须完成第 1 步。</i>"
    ),
    "vip_deposit_done_msg": (
        "<b>入金已标记为完成。</b>\n\n"
        "您现在可以提交 <b>MT5 UID / 账户号码</b> 进行 VIP 审核。"
    ),
    "vip_existing_deposit_done_msg": (
        "<b>入金已标记为完成。</b>\n\n"
        "您现在可以提交 <b>MT5 UID / 账户号码</b> 进行 VIP 审核。"
    ),
    "vip_transfer_email_body": (
        "<b>VIP 转移邮件模板</b>\n\n"
        "<b>收件人:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>主题:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>正文:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<b>重要:</b>转移确认后,您还必须<b>入金</b>才能获得 VIP 资格。"
    ),
    "vip_transfer_sent_msg": (
        "<b>转移邮件已标记为已发送。</b>\n\n"
        "等待 PU Prime 确认 IB 转移。\n\n"
        "<b>之后:</b>\n"
        "- 入金\n"
        "- 然后提交您的 UID\n\n"
        "<i>这是 VIP 审核所必需的。</i>"
    ),
    "vip_must_send_transfer_first": (
        "<b>您必须先发送转移邮件。</b>\n\n"
        "请按顺序执行 VIP 转移步骤。"
    ),

    "ib_affiliate_body": (
        "<b>IB 代理设置</b>\n\n"
        "此路径适用于希望了解 IB 模式并完成代理注册流程的用户。\n\n"
        "<i>选择您需要入门指南还是直接继续。</i>"
    ),
    "what_is_ib_msg": (
        "请先查看下方的<b>教程 PDF</b>。\n\n"
        "<b>下一步:</b>阅读完成后,请按 <b>继续</b>。"
    ),
    "pdf_missing": "教程 PDF 未找到。\n\n请将 <b>{PDF}</b> 放在 <b>ib_bot.py</b> 同一文件夹中。",
    "pdf_caption": "IB 教程指南",
    "affiliate_main_body": "<b>IB 代理菜单</b>\n\n请选择符合您情况的路径。",
    "flow_new_body": (
        "<b>IB 代理 - PU Prime 新用户</b>\n\n"
        "请按顺序完成以下步骤:\n\n"
        "1. <b>开始注册</b>\n"
        "2. 确保代码为 <b>{IB_CODE}</b>\n"
        "3. 完成注册和验证\n"
        "4. 按 <b>我已完成注册</b>\n"
        "5. 提交您的 <b>MT5 UID / 账户号码</b>\n\n"
        "<b>重要:</b>请勿跳过步骤。\n\n"
        "<i>请按下方的第 1 步开始。</i>"
    ),
    "flow_existing_body": (
        "<b>IB 代理 - PU Prime 现有用户</b>\n\n"
        "请按顺序完成以下步骤:\n\n"
        "1. 打开<b>转移邮件模板</b>\n"
        "2. 将邮件发送给 PU Prime\n"
        "3. 按 <b>我已发送邮件</b>\n"
        "4. 等待 PU Prime 确认转移\n"
        "5. 提交您的 <b>MT5 UID / 账户号码</b>\n\n"
        "<i>请按顺序完成每个步骤。</i>"
    ),
    "affiliate_registered_msg": (
        "<b>注册已标记为完成。</b>\n\n"
        "您现在可以在此处发送您的 <b>MT5 UID / 账户号码</b>。\n\n"
        "<i>发送前请确保 UID 格式正确。</i>"
    ),
    "affiliate_transfer_email_body": (
        "<b>IB 转移邮件模板</b>\n\n"
        "<b>收件人:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>主题:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>正文:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<i>发送此邮件,然后返回这里按第 2 步。</i>"
    ),
    "affiliate_transfer_sent_msg": (
        "<b>邮件已标记为已发送。</b>\n\n"
        "等待 PU Prime 确认 IB 转移。\n\n"
        "确认后,在此处提交您的 <b>MT5 UID / 账户号码</b>。"
    ),
    "affiliate_must_register": (
        "<b>您必须先完成注册。</b>\n\n"
        "请按顺序执行代理步骤。"
    ),
    "affiliate_must_send_transfer": (
        "<b>您必须先发送转移邮件。</b>\n\n"
        "请按顺序执行代理步骤。"
    ),
    "benefits_body": (
        "<b>IB 福利</b>\n\n"
        "- 结构化入门流程\n"
        "- 直接管理员支持\n"
        "- 清晰的设置流程\n"
        "- 验证后可进入下一阶段\n\n"
        "<i>请返回并继续正确的路径。</i>"
    ),

    "show_btc_body": (
        "<b>BTC 地址</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>点击地址复制。发送付款后,按 我已付款 并提交证明。</i>"
    ),
    "show_eth_body": (
        "<b>ETH 地址</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>点击地址复制。发送付款后,按 我已付款 并提交证明。</i>"
    ),
    "show_sol_body": (
        "<b>SOL 地址</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>点击地址复制。发送付款后,按 我已付款 并提交证明。</i>"
    ),
    "funded_payment_sent_msg": (
        "<b>付款已标记为已发送。</b>\n\n"
        "现在请提交您的付款证明。\n\n"
        "<b>重要:</b>如果您发送截图或文档,标题必须是:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "funded_already_submitted": (
        "<b>您的付款证明已收到。</b>\n\n"
        "请等待审核或在需要时联系客服。"
    ),
    "funded_must_send_first": (
        "<b>您必须先将付款标记为已发送。</b>\n\n"
        "请按顺序执行资金 VIP 步骤。"
    ),
    "funded_proof_prompt": (
        "现在请发送您的<b>付款证明</b>。\n\n"
        "<b>必需的标题格式:</b>\n"
        "<code>PAYMENT: FUNDED</code>\n\n"
        "<i>仅限截图或文档。</i>"
    ),
    "funded_waiting_review_msg": (
        "<b>您的资金 VIP 付款证明已在审核中。</b>\n\n"
        "您现在无需再提交任何内容。\n\n"
        "<i>如需帮助,请按 联系客服。</i>"
    ),
    "funded_proof_received": (
        "<b>付款证明已收到。</b>\n\n"
        "您的资金 VIP 付款正在审核中。\n\n"
        "<i>请等待确认或进一步指示。</i>"
    ),

    "submit_uid_prompt": (
        "请以此精确格式立即发送您的 <b>MT5 UID / 账户号码</b>:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>重要:</b>\n"
        "- 首先写 <code>UID:</code>\n"
        "- 然后是您的号码\n"
        "- 仅数字\n"
        "- 不要有多余文本\n\n"
        "如果您发送截图或文档,<b>标题</b>必须使用相同格式。"
    ),
    "uid_format_guide": (
        "<b>UID 格式无效。</b>\n\n"
        "请以此精确格式发送您的 UID:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>规则:</b>\n"
        "- 必须以 <code>UID:</code> 开头\n"
        "- 之后仅限数字\n"
        "- 不要有多余的词\n"
        "- UID 前不要有空格\n\n"
        "<i>示例:</i> <code>UID: 123517235</code>"
    ),
    "payment_format_guide": (
        "<b>付款证明格式无效。</b>\n\n"
        "如果您发送付款证明,标题必须完全是:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>标题格式无效。</b>\n\n"
        "如果您发送截图或文档,标题必须是:\n\n"
        "<code>UID: 12345678</code>"
    ),
    "uid_already_registered": (
        "<b>此 UID 已在另一用户名下注册。</b>\n\n"
        "如果您认为这是错误,请联系客服。"
    ),
    "uid_not_ready_new_vip": (
        "<b>您还没有准备好提交 UID。</b>\n\n"
        "作为<b>新用户</b>获得 VIP 访问权限,您必须:\n"
        "1. 在我们名下注册\n"
        "2. 入金\n"
        "3. 然后提交您的 UID\n\n"
        "<i>请先完成必要的步骤。</i>"
    ),
    "uid_not_ready_existing_vip": (
        "<b>您还没有准备好提交 UID。</b>\n\n"
        "作为<b>现有用户</b>获得 VIP 访问权限,您必须:\n"
        "1. 发送转移邮件\n"
        "2. 等待确认\n"
        "3. 入金\n"
        "4. 然后提交您的 UID\n\n"
        "<i>请先完成必要的步骤。</i>"
    ),
    "vip_already_submitted": (
        "<b>您的 VIP 提交已收到。</b>\n\n"
        "请等待审核或在需要时联系客服。"
    ),
    "aff_already_submitted": (
        "<b>您的代理提交已收到。</b>\n\n"
        "请等待审核或在需要时联系客服。"
    ),
    "submission_received_text": (
        "<b>提交已收到。</b>\n\n"
        "您的详细信息已转发进行审核。\n\n"
        "<i>请等待确认或进一步指示。</i>"
    ),
    "submission_received_media": (
        "<b>提交已收到。</b>\n\n"
        "您的文件已转发进行审核。\n\n"
        "<i>请等待确认或进一步指示。</i>"
    ),
    "vip_waiting_review_msg": (
        "<b>您的 VIP 提交已在审核中。</b>\n\n"
        "您现在无需再提交任何内容。\n\n"
        "<i>如需帮助,请按 联系客服。</i>"
    ),
    "aff_waiting_review_msg": (
        "<b>您的代理提交已在审核中。</b>\n\n"
        "您现在无需再提交任何内容。\n\n"
        "<i>如需帮助,请按 联系客服。</i>"
    ),

    "support_body": "<b>联系客服</b>\n\n选择最适合您问题的管理员:",

    "approved_dm": (
        "<b>您的提交已获批准。</b>\n\n"
        "管理员将很快跟进下一步。"
    ),
    "rejected_dm": (
        "<b>您的提交在此阶段未获批准。</b>\n\n"
        "请联系客服解决问题。"
    ),

    "nudge_24h": (
        "简单问候一下。\n\n"
        "如果您在 ImperiumFX 设置过程中遇到困难,请按 /start 继续 - "
        "或点击 联系客服,我们会帮助您。"
    ),
    "nudge_72h_deposit": (
        "您已将入金标记为完成 - 别忘了提交您的 "
        "<b>MT5 UID</b> 以便我们完成 VIP 访问设置。"
    ),
    "renewal_reminder": (
        "<b>资金 VIP 续费提醒</b>\n\n"
        "您的续费将在 <b>{DAYS} 天</b> 后到期。\n"
        "续费金额为 <b>80 欧元</b>。按 /start -> 付费 VIP -> 资金账户 付款。\n\n"
        "<b>钱包:</b>\n"
        "BTC: <code>{BTC}</code>\n"
        "ETH: <code>{ETH}</code>\n"
        "SOL: <code>{SOL}</code>"
    ),

    "fallback_msg": "我没听懂 — 请使用下方按钮。",
    "uid_bad_format": (
        "<b>格式无法识别。</b>\n"
        "请按以下格式发送您的 UID 和 PU Prime 邮箱:\n"
        "<code>UID: 12345678\nEmail: you@example.com</code>"
    ),
    "vip_uid_received": (
        "<b>VIP 提交已收到。</b>\n"
        "我们的团队将尽快审核,审核通过后会私信您。 ✅"
    ),
    "aff_uid_received": (
        "<b>合作伙伴提交已收到。</b>\n"
        "我们的团队会确认您的 IB 子联盟身份并私信您。 ✅"
    ),
    "funded_submit_bad_format": (
        "<b>格式无法识别。</b>\n"
        "请发送:\n"
        "<code>Amount: 80 EUR\nTX/Ref: &lt;哈希或参考号&gt;\nMethod: BTC|ETH|SOL</code>\n"
        "或发送付款截图并附上相同说明。"
    ),
    "funded_submit_received": (
        "<b>付费 VIP 付款已收到。</b>\n"
        "我们正在核实,一旦开通将私信通知您。 🔒"
    ),
    "nudge_incomplete": (
        "<b>还对 VIP 感兴趣吗?</b>\n"
        "您已开始但尚未完成 — 点击 /start 继续上次的操作。"
    ),

    "faq_q1": "什么是 VIP 访问权限?",
    "faq_a1": (
        "<b>VIP 访问权限</b>为您提供我们的私有信号、设置和交易提示。"
        "免费 VIP 需要您在我们的 IB 下注册并入金。"
        "付费 VIP(资金)为资金账户交易者提供直接访问。"
    ),
    "faq_q2": "什么是 IB?",
    "faq_a2": (
        "<b>IB(介绍经纪商)</b>意味着您的交易账户在我们的合作伙伴代码下注册或转移。"
        "我们从您的点差中赚取小额佣金 - <b>对您没有额外费用</b> - "
        "作为回报,您将获得免费 VIP 访问权限。"
    ),
    "faq_q3": "审核需要多长时间?",
    "faq_a3": (
        "审核<b>通常在 24 小时内</b>完成。如果超过时间,请按 "
        "<b>联系客服</b>,管理员将跟进。"
    ),
    "faq_q4": "为什么我的 UID 未被接受?",
    "faq_a4": (
        "常见原因:账户不在我们的 IB 代码下、尚未入金或 UID 格式错误。"
        "请确保您使用了代码 <code>{IB_CODE}</code>、已入金,"
        "并以此精确格式提交:<code>UID: 12345678</code>"
    ),
    "faq_q5": "资金 VIP 多少钱?",
    "faq_a5": (
        "首月 <b>50 欧元</b>,之后每月 <b>80 欧元</b>。"
        "可使用 BTC、ETH 或 SOL 支付。付款后,发送证明并附上标题 "
        "<code>PAYMENT: FUNDED</code>。"
    ),
    "faq_q6": "有最低入金要求吗?",
    "faq_a6": (
        "PU Prime 设定最低入金额。我们建议至少 <b>200 美元</b>,"
        "以获得有意义的头寸规模,并顺利获得 VIP 资格。"
    ),

    "btn_vip_access": "加入 VIP 通道",
    "btn_ib_affiliate": "成为 IB 代理",
    "btn_team": "团队介绍",
    "btn_socials": "关注我们",
    "btn_faq": "常见问题",
    "btn_support": "联系客服",
    "btn_back": "返回",
    "btn_back_to_start": "返回主页",
    "btn_back_to_vip": "返回 VIP 菜单",
    "btn_back_to_affiliate": "返回代理菜单",
    "btn_yes_restart": "是,重新开始",
    "btn_no_keep": "否,保留进度",
    "btn_free_vip": "免费 VIP",
    "btn_paid_vip": "付费 VIP",
    "btn_new_to_pu": "PU Prime 新用户",
    "btn_existing_pu": "已有 PU Prime 账户",
    "btn_live_account": "真实账户",
    "btn_funded_account": "资金账户",
    "btn_dont_know_ib": "我不知道什么是 IB",
    "btn_already_know": "我已了解,继续",
    "btn_continue": "继续",
    "btn_step1_register": "第 1 步:在 PU Prime 注册",
    "btn_step1_start_reg": "第 1 步:开始注册",
    "btn_step2_completed": "第 2 步:我已完成注册",
    "btn_step3_deposited": "第 3 步:我已入金",
    "btn_step4_submit_uid": "第 4 步:提交 UID",
    "btn_step3_submit_uid": "第 3 步:提交 UID",
    "btn_step1_view_email": "第 1 步:查看转移邮件",
    "btn_step2_sent_email": "第 2 步:我已发送邮件",
    "btn_view_btc": "查看 BTC 地址",
    "btn_view_eth": "查看 ETH 地址",
    "btn_view_sol": "查看 SOL 地址",
    "btn_sent_payment": "我已付款",
    "btn_submit_proof": "提交付款证明",
    "btn_waiting_payment_review": "等待付款审核",
    "btn_waiting_review": "等待审核",
    "btn_benefits": "IB 福利",
    "btn_message": "联系",
    "btn_founder": "创始人 - Kratos",
    "btn_onboarding": "入门 / 综合 - Apollo",
    "btn_signals": "信号 - Plato",
    "btn_socials_admin": "社交 - HD",
    "btn_change_language": "更改语言",
    "btn_approve": "批准",
    "btn_reject": "拒绝",
    "btn_block_user": "封禁用户",
}

TEXTS["ar"] = {
    "lang_picker_title": "<b>الرجاء اختيار لغتك</b>\n\nيمكنك تغييرها لاحقًا باستخدام /language.",
    "lang_set_ok": "<b>تم تعيين اللغة.</b> جاري تحميل القائمة الرئيسية...",

    "welcome_title": "<b>مرحبًا بك في ImperiumFX</b>",
    "welcome_body": (
        "<b>مرحبًا بك في ImperiumFX</b>\n\n"
        "اختر مسارك من الأسفل.\n\n"
        "- <b>وصول VIP</b> - انضم إلى قناة إشاراتنا الحصرية\n"
        "- <b>شراكة IB</b> - كن شريكًا واتبع خطوات تسجيل IB\n"
        "- <b>تعرف على الفريق</b> - تعرف على فريق ImperiumFX\n"
        "- <b>تابعنا</b> - Instagram و TikTok\n"
        "- <b>الأسئلة الشائعة</b> - إجابات سريعة للأسئلة المتكررة\n\n"
        "<i>الرجاء اختيار الخيار الذي يناسب احتياجك.</i>"
    ),
    "resume_prompt": (
        "<b>لديك تقدم حالي في البوت.</b>\n\n"
        "هل تريد <b>إعادة البدء</b> من البداية، أم الاحتفاظ بتقدمك الحالي؟"
    ),
    "restart_yes_msg": "<b>مرحبًا بك في ImperiumFX</b>\n\nاختر مسارك من الأسفل.",
    "restart_no_msg": "تم الاحتفاظ بالتقدم. اضغط على زر من الأسفل للمتابعة.",
    "back_short_welcome": (
        "<b>مرحبًا بك في ImperiumFX</b>\n\n"
        "اختر مسارك من الأسفل.\n\n"
        "- <b>وصول VIP</b> - انضم إلى قناة إشاراتنا الحصرية\n"
        "- <b>شراكة IB</b> - كن شريكًا واتبع خطوات تسجيل IB\n\n"
        "<i>الرجاء اختيار الخيار الذي يناسب احتياجك.</i>"
    ),

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
        "أرسل <b>MT5 UID / رقم الحساب</b> الآن بهذا التنسيق الدقيق:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>مهم:</b>\n"
        "- اكتب <code>UID:</code> أولاً\n"
        "- ثم رقمك\n"
        "- أرقام فقط\n"
        "- بدون نص إضافي\n\n"
        "إذا أرسلت لقطة شاشة أو مستندًا، يجب أن يستخدم <b>التعليق</b> نفس التنسيق."
    ),
    "uid_format_guide": (
        "<b>تنسيق UID غير صالح.</b>\n\n"
        "أرسل UID بهذا التنسيق الدقيق:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>القواعد:</b>\n"
        "- يجب أن يبدأ بـ <code>UID:</code>\n"
        "- أرقام فقط بعد ذلك\n"
        "- بدون كلمات إضافية\n"
        "- بدون مسافات قبل UID\n\n"
        "<i>مثال:</i> <code>UID: 123517235</code>"
    ),
    "payment_format_guide": (
        "<b>تنسيق إثبات الدفع غير صالح.</b>\n\n"
        "إذا أرسلت إثبات الدفع، يجب أن يكون التعليق بالضبط:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>تنسيق التعليق غير صالح.</b>\n\n"
        "إذا أرسلت لقطة شاشة أو مستندًا، يجب أن يكون التعليق:\n\n"
        "<code>UID: 12345678</code>"
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
        "<b>الصيغة غير معروفة.</b>\n"
        "يرجى إرسال UID وبريدك في PU Prime بهذا الشكل:\n"
        "<code>UID: 12345678\nEmail: you@example.com</code>"
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
        "أسباب شائعة: الحساب ليس تحت رمز IB الخاص بنا، لم يتم الإيداع بعد، أو تنسيق UID خاطئ. "
        "تأكد من استخدام الرمز <code>{IB_CODE}</code>، الإيداع، والتقديم بهذا التنسيق: <code>UID: 12345678</code>"
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

    "btn_vip_access": "الانضمام إلى VIP",
    "btn_ib_affiliate": "كن شريك IB",
    "btn_team": "تعرف على الفريق",
    "btn_socials": "تابعنا",
    "btn_faq": "الأسئلة الشائعة",
    "btn_support": "تواصل مع الدعم",
    "btn_back": "رجوع",
    "btn_back_to_start": "العودة للبداية",
    "btn_back_to_vip": "العودة لقائمة VIP",
    "btn_back_to_affiliate": "العودة لقائمة الشراكة",
    "btn_yes_restart": "نعم، إعادة البدء",
    "btn_no_keep": "لا، احتفظ بالتقدم",
    "btn_free_vip": "VIP مجاني",
    "btn_paid_vip": "VIP مدفوع",
    "btn_new_to_pu": "جديد في PU Prime",
    "btn_existing_pu": "لدي حساب PU Prime",
    "btn_live_account": "حساب حقيقي",
    "btn_funded_account": "حساب ممول",
    "btn_dont_know_ib": "لا أعرف ما هو IB",
    "btn_already_know": "أعرف بالفعل، متابعة",
    "btn_continue": "متابعة",
    "btn_step1_register": "الخطوة 1: التسجيل في PU Prime",
    "btn_step1_start_reg": "الخطوة 1: بدء التسجيل",
    "btn_step2_completed": "الخطوة 2: أكملت التسجيل",
    "btn_step3_deposited": "الخطوة 3: لقد أودعت",
    "btn_step4_submit_uid": "الخطوة 4: تقديم UID",
    "btn_step3_submit_uid": "الخطوة 3: تقديم UID",
    "btn_step1_view_email": "الخطوة 1: عرض بريد النقل",
    "btn_step2_sent_email": "الخطوة 2: لقد أرسلت البريد",
    "btn_view_btc": "عرض عنوان BTC",
    "btn_view_eth": "عرض عنوان ETH",
    "btn_view_sol": "عرض عنوان SOL",
    "btn_sent_payment": "لقد دفعت",
    "btn_submit_proof": "تقديم إثبات الدفع",
    "btn_waiting_payment_review": "بانتظار مراجعة الدفع",
    "btn_waiting_review": "بانتظار المراجعة",
    "btn_benefits": "فوائد IB",
    "btn_message": "مراسلة",
    "btn_founder": "المؤسس - Kratos",
    "btn_onboarding": "الاستقبال / عام - Apollo",
    "btn_signals": "الإشارات - Plato",
    "btn_socials_admin": "السوشيال - HD",
    "btn_change_language": "تغيير اللغة",
    "btn_approve": "موافقة",
    "btn_reject": "رفض",
    "btn_block_user": "حظر المستخدم",
}

TEXTS["es"] = {
    "lang_picker_title": "<b>Elige tu idioma</b>\n\nPuedes cambiarlo luego con /language.",
    "lang_set_ok": "<b>Idioma configurado.</b> Cargando el menú principal...",

    "welcome_title": "<b>Bienvenido a ImperiumFX</b>",
    "welcome_body": (
        "<b>Bienvenido a ImperiumFX</b>\n\n"
        "Elige tu ruta a continuación.\n\n"
        "- <b>Acceso VIP</b> - únete a nuestro canal de señales VIP\n"
        "- <b>Afiliado IB</b> - conviértete en afiliado y completa el proceso IB\n"
        "- <b>Conoce al Equipo</b> - descubre quién está detrás de ImperiumFX\n"
        "- <b>Síguenos</b> - Instagram y TikTok\n"
        "- <b>Preguntas Frecuentes</b> - respuestas rápidas a dudas comunes\n\n"
        "<i>Selecciona la opción que mejor se adapte a tu necesidad.</i>"
    ),
    "resume_prompt": (
        "<b>Ya tienes progreso en el bot.</b>\n\n"
        "¿Quieres <b>reiniciar</b> desde el principio o mantener tu progreso actual?"
    ),
    "restart_yes_msg": "<b>Bienvenido a ImperiumFX</b>\n\nElige tu ruta a continuación.",
    "restart_no_msg": "Progreso conservado. Pulsa un botón para continuar.",
    "back_short_welcome": (
        "<b>Bienvenido a ImperiumFX</b>\n\n"
        "Elige tu ruta a continuación.\n\n"
        "- <b>Acceso VIP</b> - únete a nuestro canal de señales VIP\n"
        "- <b>Afiliado IB</b> - conviértete en afiliado y completa el proceso IB\n\n"
        "<i>Selecciona la opción que mejor se adapte a tu necesidad.</i>"
    ),

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
        "Envía tu <b>MT5 UID / número de cuenta</b> ahora con este formato exacto:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Importante:</b>\n"
        "- escribe <code>UID:</code> primero\n"
        "- luego tu número\n"
        "- solo dígitos\n"
        "- sin texto extra\n\n"
        "Si envías una captura o documento, el <b>caption</b> debe usar el mismo formato."
    ),
    "uid_format_guide": (
        "<b>Formato UID inválido.</b>\n\n"
        "Envía tu UID con este formato exacto:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Reglas:</b>\n"
        "- debe comenzar con <code>UID:</code>\n"
        "- solo números después\n"
        "- sin palabras extra\n"
        "- sin espacios antes de UID\n\n"
        "<i>Ejemplo:</i> <code>UID: 123517235</code>"
    ),
    "payment_format_guide": (
        "<b>Formato de comprobante inválido.</b>\n\n"
        "Si envías comprobante, el caption debe ser exactamente:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>Formato de caption inválido.</b>\n\n"
        "Si envías captura o documento, el caption debe ser:\n\n"
        "<code>UID: 12345678</code>"
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
        "<b>Formato no reconocido.</b>\n"
        "Por favor envía tu UID y correo de PU Prime así:\n"
        "<code>UID: 12345678\nEmail: tu@ejemplo.com</code>"
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
        "o formato UID incorrecto. Verifica que usaste el código <code>{IB_CODE}</code>, "
        "depositaste, y enviaste con este formato exacto: <code>UID: 12345678</code>"
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

    "btn_vip_access": "Acceso VIP",
    "btn_ib_affiliate": "Ser Afiliado IB",
    "btn_team": "Conoce al Equipo",
    "btn_socials": "Síguenos",
    "btn_faq": "Preguntas",
    "btn_support": "Contactar Soporte",
    "btn_back": "Atrás",
    "btn_back_to_start": "Volver al Inicio",
    "btn_back_to_vip": "Volver al Menú VIP",
    "btn_back_to_affiliate": "Volver al Menú Afiliado",
    "btn_yes_restart": "Sí, reiniciar",
    "btn_no_keep": "No, mantener progreso",
    "btn_free_vip": "VIP Gratis",
    "btn_paid_vip": "VIP De Pago",
    "btn_new_to_pu": "Nuevo en PU Prime",
    "btn_existing_pu": "Ya tengo PU Prime",
    "btn_live_account": "Cuenta Real",
    "btn_funded_account": "Cuenta Funded",
    "btn_dont_know_ib": "No sé qué es IB",
    "btn_already_know": "Ya sé, continuar",
    "btn_continue": "Continuar",
    "btn_step1_register": "Paso 1: Registrarte con PU Prime",
    "btn_step1_start_reg": "Paso 1: Comenzar Registro",
    "btn_step2_completed": "Paso 2: Completé el Registro",
    "btn_step3_deposited": "Paso 3: Ya Deposité",
    "btn_step4_submit_uid": "Paso 4: Enviar UID",
    "btn_step3_submit_uid": "Paso 3: Enviar UID",
    "btn_step1_view_email": "Paso 1: Ver Correo de Traslado",
    "btn_step2_sent_email": "Paso 2: Envié el Correo",
    "btn_view_btc": "Ver Dirección BTC",
    "btn_view_eth": "Ver Dirección ETH",
    "btn_view_sol": "Ver Dirección SOL",
    "btn_sent_payment": "Ya Pagué",
    "btn_submit_proof": "Enviar Comprobante",
    "btn_waiting_payment_review": "Esperando Revisión del Pago",
    "btn_waiting_review": "Esperando Revisión",
    "btn_benefits": "Beneficios IB",
    "btn_message": "Mensaje",
    "btn_founder": "Fundador - Kratos",
    "btn_onboarding": "Onboarding / General - Apollo",
    "btn_signals": "Señales - Plato",
    "btn_socials_admin": "Socials - HD",
    "btn_change_language": "Cambiar Idioma",
    "btn_approve": "Aprobar",
    "btn_reject": "Rechazar",
    "btn_block_user": "Bloquear Usuario",
}

TEXTS["pt"] = {
    "lang_picker_title": "<b>Escolha seu idioma</b>\n\nVocê pode mudar depois com /language.",
    "lang_set_ok": "<b>Idioma definido.</b> Carregando o menu principal...",

    "welcome_title": "<b>Bem-vindo ao ImperiumFX</b>",
    "welcome_body": (
        "<b>Bem-vindo ao ImperiumFX</b>\n\n"
        "Escolha seu caminho abaixo.\n\n"
        "- <b>Acesso VIP</b> - entre no nosso canal de sinais VIP\n"
        "- <b>Afiliado IB</b> - torne-se afiliado e siga o processo IB\n"
        "- <b>Conheça a Equipe</b> - saiba quem está por trás do ImperiumFX\n"
        "- <b>Siga-nos</b> - Instagram e TikTok\n"
        "- <b>Perguntas Frequentes</b> - respostas rápidas para dúvidas comuns\n\n"
        "<i>Selecione a opção que melhor atende ao seu objetivo.</i>"
    ),
    "resume_prompt": (
        "<b>Você já tem progresso no bot.</b>\n\n"
        "Quer <b>recomeçar</b> do início, ou manter seu progresso atual?"
    ),
    "restart_yes_msg": "<b>Bem-vindo ao ImperiumFX</b>\n\nEscolha seu caminho abaixo.",
    "restart_no_msg": "Progresso mantido. Toque em um botão para continuar.",
    "back_short_welcome": (
        "<b>Bem-vindo ao ImperiumFX</b>\n\n"
        "Escolha seu caminho abaixo.\n\n"
        "- <b>Acesso VIP</b> - entre no nosso canal de sinais VIP\n"
        "- <b>Afiliado IB</b> - torne-se afiliado e siga o processo IB\n\n"
        "<i>Selecione a opção que melhor atende ao seu objetivo.</i>"
    ),

    "help_text": (
        "<b>Bot ImperiumFX - Ajuda</b>\n\n"
        "- /start - abrir o menu principal\n"
        "- /status - ver seu progresso\n"
        "- /language - mudar idioma\n"
        "- /help - mostrar esta mensagem\n\n"
        "Se travar, toque em <b>Falar com Suporte</b> em qualquer menu."
    ),
    "status_title": "<b>Seu status</b>",
    "status_no_record": "Nenhum registro encontrado. Toque /start para começar.",
    "status_path": "Caminho",
    "status_flow": "Fluxo",
    "status_vip_submitted": "VIP enviado",
    "status_aff_submitted": "Afiliado enviado",
    "status_funded": "VIP Funded",
    "yes": "sim",
    "no": "não",
    "status_field_status": "status",
    "dash": "-",

    "access_disabled": "Acesso desativado. Contate o suporte.",
    "slow_down": "Mais devagar",
    "fallback_unknown": (
        "Não entendi - aqui está o menu.\n"
        "Toque /start para começar, /status para ver progresso, ou /help para ajuda."
    ),
    "fallback_media": "Não entendi - aqui está o menu. Toque /start para começar.",

    "team_title": "<b>Conheça a Equipe</b>",
    "team_footer": "<i>Toque num botão para falar com eles diretamente.</i>",
    "socials_body": (
        "<b>Siga o ImperiumFX</b>\n\n"
        "Fique por dentro do nosso conteúdo, previews de sinais e sorteios."
    ),
    "faq_intro": "<b>Perguntas Frequentes</b>\n\nEscolha uma pergunta abaixo.",

    "vip_access_body": (
        "<b>Acesso VIP</b>\n\n"
        "Escolha sua rota VIP abaixo.\n\n"
        "<b>VIP Grátis</b>\n"
        "- para usuários que vêm sob nosso IB\n"
        "- requer registro/transferência sob nós e depósito\n\n"
        "<b>VIP Pago</b>\n"
        "- para usuários que querem acesso direto\n"
        "- contas funded pagam mensalmente\n\n"
        "<i>Selecione a opção que corresponde à sua situação.</i>"
    ),
    "vip_free_body": (
        "<b>VIP Grátis</b>\n\n"
        "Para se qualificar, você precisa fazer <b>um</b> dos seguintes:\n\n"
        "1. <b>Registrar-se no PU Prime sob nós</b>\n"
        "2. <b>Transferir sua conta PU Prime existente para nós</b>\n\n"
        "<b>Regras importantes:</b>\n"
        "- Você precisa estar sob nosso IB\n"
        "- Precisa <b>depositar</b>\n"
        "- Sem isso, <b>acesso VIP grátis não será concedido</b>\n\n"
        "<i>Selecione a opção que corresponde à sua situação abaixo.</i>"
    ),
    "vip_paid_body": (
        "<b>VIP Pago</b>\n\n"
        "Escolha o tipo de conta que você usa.\n\n"
        "<b>Conta Real</b>\n"
        "- mesma estrutura do VIP grátis\n"
        "- precisa estar sob nosso IB e depositar\n\n"
        "<b>Conta Funded</b>\n"
        "- <b>EUR 50</b> primeiro mês\n"
        "- <b>EUR 80</b> a partir do mês seguinte\n\n"
        "<i>Selecione seu tipo de conta abaixo.</i>"
    ),
    "vip_paid_live_body": (
        "<b>VIP Pago - Conta Real</b>\n\n"
        "Para contas reais, seu acesso é feito pela nossa estrutura IB.\n\n"
        "Isso significa que você precisa:\n"
        "1. registrar sob nós ou transferir sob nós\n"
        "2. depositar\n"
        "3. enviar seu UID\n\n"
        "<i>Selecione sua rota abaixo.</i>"
    ),
    "vip_paid_funded_body": (
        "<b>VIP Pago - Conta Funded</b>\n\n"
        "<b>Preços:</b>\n"
        "- <b>EUR 50</b> primeiro mês\n"
        "- <b>EUR 80</b> a partir do mês seguinte\n\n"
        "<b>Métodos de pagamento:</b>\n"
        "- BTC\n"
        "- ETH\n"
        "- SOL\n\n"
        "<b>Próximo passo:</b>\n"
        "1. ver o endereço da wallet\n"
        "2. enviar o pagamento\n"
        "3. enviar comprovante\n\n"
        "<i>Use os botões abaixo.</i>"
    ),
    "vip_new_body": (
        "<b>Acesso VIP - Novo no PU Prime</b>\n\n"
        "Siga estes passos em ordem:\n\n"
        "1. <b>Registre-se usando nosso link</b>\n"
        "2. Confira que o código é <b>{IB_CODE}</b>\n"
        "3. Complete o registro\n"
        "4. <b>Deposite</b>\n"
        "5. Envie seu <b>MT5 UID / número da conta</b>\n\n"
        "<b>Importante:</b>\n"
        "- VIP é só para usuários que vêm sob nós\n"
        "- Apenas o registro <b>não basta</b>\n"
        "- Precisa <b>depositar</b> antes da revisão\n\n"
        "<i>Complete os passos com cuidado.</i>"
    ),
    "vip_existing_body": (
        "<b>Acesso VIP - Usuário Existente PU Prime</b>\n\n"
        "Siga estes passos em ordem:\n\n"
        "1. Envie o <b>email de transferência IB</b>\n"
        "2. Aguarde confirmação da transferência\n"
        "3. <b>Deposite</b>\n"
        "4. Envie seu <b>MT5 UID / número da conta</b>\n\n"
        "<b>Importante:</b>\n"
        "- Sua conta precisa ser movida sob nosso IB\n"
        "- Precisa <b>depositar</b>\n"
        "- Sem isso, <b>acesso VIP não será concedido</b>\n\n"
        "<i>Complete os passos com cuidado.</i>"
    ),
    "vip_registered_msg": (
        "<b>Registro marcado como concluído.</b>\n\n"
        "<b>Próximo requisito:</b> você agora precisa <b>depositar</b> antes de enviar seu UID para revisão VIP.\n\n"
        "<i>Não pule este passo.</i>"
    ),
    "vip_must_register_first": (
        "<b>Você precisa completar o registro primeiro.</b>\n\n"
        "Siga os passos em ordem.\n\n"
        "<i>O passo 1 deve ser completado antes do passo 3.</i>"
    ),
    "vip_deposit_done_msg": (
        "<b>Depósito marcado como concluído.</b>\n\n"
        "Agora você pode enviar seu <b>MT5 UID / número da conta</b> para revisão VIP."
    ),
    "vip_existing_deposit_done_msg": (
        "<b>Depósito marcado como concluído.</b>\n\n"
        "Agora você pode enviar seu <b>MT5 UID / número da conta</b> para revisão VIP."
    ),
    "vip_transfer_email_body": (
        "<b>Modelo de Email de Transferência VIP</b>\n\n"
        "<b>Para:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>Assunto:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>Corpo:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<b>Importante:</b> após a confirmação, você também precisa <b>depositar</b> para se qualificar ao VIP."
    ),
    "vip_transfer_sent_msg": (
        "<b>Email de transferência marcado como enviado.</b>\n\n"
        "Aguarde o PU Prime confirmar a transferência IB.\n\n"
        "<b>Depois disso:</b>\n"
        "- deposite\n"
        "- então envie seu UID\n\n"
        "<i>Isso é necessário para a revisão VIP.</i>"
    ),
    "vip_must_send_transfer_first": (
        "<b>Você precisa enviar o email de transferência primeiro.</b>\n\n"
        "Siga os passos de transferência VIP em ordem."
    ),

    "ib_affiliate_body": (
        "<b>Configuração de Afiliado IB</b>\n\n"
        "Este caminho é para usuários que querem entender o modelo IB e completar o processo de afiliação.\n\n"
        "<i>Escolha se precisa do guia para iniciantes ou quer continuar direto.</i>"
    ),
    "what_is_ib_msg": (
        "Comece com o <b>PDF tutorial</b> abaixo.\n\n"
        "<b>Próximo passo:</b> depois de ler, toque em <b>Continuar</b>."
    ),
    "pdf_missing": "PDF tutorial não encontrado.\n\nColoque <b>{PDF}</b> na mesma pasta do <b>ib_bot.py</b>.",
    "pdf_caption": "Guia Tutorial IB",
    "affiliate_main_body": "<b>Menu de Afiliado IB</b>\n\nEscolha o caminho que corresponde à sua situação.",
    "flow_new_body": (
        "<b>Afiliado IB - Novo no PU Prime</b>\n\n"
        "Siga estes passos em ordem:\n\n"
        "1. <b>Iniciar Registro</b>\n"
        "2. Confira que o código é <b>{IB_CODE}</b>\n"
        "3. Complete o registro e verificação\n"
        "4. Toque <b>Completei o Registro</b>\n"
        "5. Envie seu <b>MT5 UID / número da conta</b>\n\n"
        "<b>Importante:</b> não pule passos.\n\n"
        "<i>Toque no passo 1 para começar.</i>"
    ),
    "flow_existing_body": (
        "<b>Afiliado IB - Usuário Existente PU Prime</b>\n\n"
        "Siga estes passos em ordem:\n\n"
        "1. Abra o <b>modelo de email de transferência</b>\n"
        "2. Envie o email ao PU Prime\n"
        "3. Toque <b>Enviei o Email</b>\n"
        "4. Aguarde o PU Prime confirmar\n"
        "5. Envie seu <b>MT5 UID / número da conta</b>\n\n"
        "<i>Complete cada passo em ordem.</i>"
    ),
    "affiliate_registered_msg": (
        "<b>Registro marcado como concluído.</b>\n\n"
        "Agora você pode enviar seu <b>MT5 UID / número da conta</b> aqui.\n\n"
        "<i>Confira que o formato do UID está correto antes de enviar.</i>"
    ),
    "affiliate_transfer_email_body": (
        "<b>Modelo de Email de Transferência IB</b>\n\n"
        "<b>Para:</b>\n<code>{T1}</code>\n<code>{T2}</code>\n\n"
        "<b>Assunto:</b>\n<code>Move account under IB {IB_ACCOUNT_NUMBER}</code>\n\n"
        "<b>Corpo:</b>\n"
        "<code>Hello,\n\n"
        "Please move my PU Prime account under IB {IB_ACCOUNT_NUMBER}.\n\n"
        "Full Name: [Your Name and Surname]\n"
        "Account Email: [Your PU Prime account email]\n\n"
        "Please confirm once this has been completed.\n\n"
        "Thank you.</code>\n\n"
        "<i>Envie este email, depois volte e toque no passo 2.</i>"
    ),
    "affiliate_transfer_sent_msg": (
        "<b>Email marcado como enviado.</b>\n\n"
        "Aguarde o PU Prime confirmar a transferência IB.\n\n"
        "Após a confirmação, envie seu <b>MT5 UID / número da conta</b> aqui."
    ),
    "affiliate_must_register": (
        "<b>Você precisa completar o registro primeiro.</b>\n\n"
        "Siga os passos de afiliado em ordem."
    ),
    "affiliate_must_send_transfer": (
        "<b>Você precisa enviar o email de transferência primeiro.</b>\n\n"
        "Siga os passos de afiliado em ordem."
    ),
    "benefits_body": (
        "<b>Benefícios IB</b>\n\n"
        "- Onboarding estruturado\n"
        "- Suporte direto do admin\n"
        "- Processo de configuração claro\n"
        "- Acesso à próxima etapa após validação\n\n"
        "<i>Volte e continue o caminho correto.</i>"
    ),

    "show_btc_body": (
        "<b>Endereço BTC</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Toque no endereço para copiar. Após enviar o pagamento, toque Paguei e depois envie o comprovante.</i>"
    ),
    "show_eth_body": (
        "<b>Endereço ETH</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Toque no endereço para copiar. Após enviar o pagamento, toque Paguei e depois envie o comprovante.</i>"
    ),
    "show_sol_body": (
        "<b>Endereço SOL</b>\n\n"
        "<code>{ADDR}</code>\n\n"
        "<i>Toque no endereço para copiar. Após enviar o pagamento, toque Paguei e depois envie o comprovante.</i>"
    ),
    "funded_payment_sent_msg": (
        "<b>Pagamento marcado como enviado.</b>\n\n"
        "Agora envie seu comprovante de pagamento.\n\n"
        "<b>Importante:</b> se você enviar print ou documento, a legenda precisa ser:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "funded_already_submitted": (
        "<b>Seu comprovante já foi recebido.</b>\n\n"
        "Aguarde a revisão ou fale com o suporte se precisar."
    ),
    "funded_must_send_first": (
        "<b>Você precisa marcar o pagamento como enviado primeiro.</b>\n\n"
        "Siga os passos do VIP Funded em ordem."
    ),
    "funded_proof_prompt": (
        "Envie seu <b>comprovante de pagamento</b> agora.\n\n"
        "<b>Formato da legenda requerido:</b>\n"
        "<code>PAYMENT: FUNDED</code>\n\n"
        "<i>Apenas print ou documento.</i>"
    ),
    "funded_waiting_review_msg": (
        "<b>Seu comprovante VIP Funded já está em revisão.</b>\n\n"
        "Não há mais nada para enviar agora.\n\n"
        "<i>Se precisar de ajuda, toque em Falar com Suporte.</i>"
    ),
    "funded_proof_received": (
        "<b>Comprovante recebido.</b>\n\n"
        "Seu pagamento VIP Funded está em revisão.\n\n"
        "<i>Aguarde confirmação ou instruções adicionais.</i>"
    ),

    "submit_uid_prompt": (
        "Envie seu <b>MT5 UID / número da conta</b> agora neste formato exato:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Importante:</b>\n"
        "- escreva <code>UID:</code> primeiro\n"
        "- depois seu número\n"
        "- só dígitos\n"
        "- sem texto extra\n\n"
        "Se enviar print ou documento, a <b>legenda</b> precisa usar o mesmo formato."
    ),
    "uid_format_guide": (
        "<b>Formato de UID inválido.</b>\n\n"
        "Envie seu UID neste formato exato:\n\n"
        "<code>UID: 12345678</code>\n\n"
        "<b>Regras:</b>\n"
        "- precisa começar com <code>UID:</code>\n"
        "- só números depois\n"
        "- sem palavras extras\n"
        "- sem espaços antes de UID\n\n"
        "<i>Exemplo:</i> <code>UID: 123517235</code>"
    ),
    "payment_format_guide": (
        "<b>Formato de comprovante inválido.</b>\n\n"
        "Se enviar comprovante, a legenda precisa ser exatamente:\n\n"
        "<code>PAYMENT: FUNDED</code>"
    ),
    "uid_caption_invalid": (
        "<b>Formato de legenda inválido.</b>\n\n"
        "Se enviar print ou documento, a legenda precisa ser:\n\n"
        "<code>UID: 12345678</code>"
    ),
    "uid_already_registered": (
        "<b>Este UID já está registrado a outro usuário.</b>\n\n"
        "Se você acha que é erro, fale com o suporte."
    ),
    "uid_not_ready_new_vip": (
        "<b>Você ainda não está pronto para enviar UID.</b>\n\n"
        "Para acesso VIP como <b>novo usuário</b>, você precisa:\n"
        "1. registrar sob nós\n"
        "2. depositar\n"
        "3. então enviar seu UID\n\n"
        "<i>Complete os passos requeridos primeiro.</i>"
    ),
    "uid_not_ready_existing_vip": (
        "<b>Você ainda não está pronto para enviar UID.</b>\n\n"
        "Para acesso VIP como <b>usuário existente</b>, você precisa:\n"
        "1. enviar o email de transferência\n"
        "2. aguardar confirmação\n"
        "3. depositar\n"
        "4. então enviar seu UID\n\n"
        "<i>Complete os passos requeridos primeiro.</i>"
    ),
    "vip_already_submitted": (
        "<b>Seu envio VIP já foi recebido.</b>\n\n"
        "Aguarde a revisão ou fale com o suporte se precisar."
    ),
    "aff_already_submitted": (
        "<b>Seu envio de afiliado já foi recebido.</b>\n\n"
        "Aguarde a revisão ou fale com o suporte se precisar."
    ),
    "submission_received_text": (
        "<b>Envio recebido.</b>\n\n"
        "Seus dados foram encaminhados para revisão.\n\n"
        "<i>Aguarde confirmação ou instruções adicionais.</i>"
    ),
    "submission_received_media": (
        "<b>Envio recebido.</b>\n\n"
        "Seu arquivo foi encaminhado para revisão.\n\n"
        "<i>Aguarde confirmação ou instruções adicionais.</i>"
    ),
    "vip_waiting_review_msg": (
        "<b>Seu envio VIP já está em revisão.</b>\n\n"
        "Não há mais nada para enviar agora.\n\n"
        "<i>Se precisar de ajuda, toque em Falar com Suporte.</i>"
    ),
    "aff_waiting_review_msg": (
        "<b>Seu envio de afiliado já está em revisão.</b>\n\n"
        "Não há mais nada para enviar agora.\n\n"
        "<i>Se precisar de ajuda, toque em Falar com Suporte.</i>"
    ),

    "support_body": "<b>Falar com Suporte</b>\n\nEscolha o admin mais adequado para sua dúvida:",

    "approved_dm": (
        "<b>Seu envio foi aprovado.</b>\n\n"
        "Um admin vai te contatar em breve com o próximo passo."
    ),
    "rejected_dm": (
        "<b>Seu envio não foi aprovado nesta etapa.</b>\n\n"
        "Fale com o suporte para resolver o problema."
    ),

    "nudge_24h": (
        "Só passando pra ver se está tudo bem.\n\n"
        "Se travou na configuração do ImperiumFX, toque /start para retomar - "
        "ou toque em Falar com Suporte e a gente ajuda."
    ),
    "nudge_72h_deposit": (
        "Você marcou seu depósito como feito - não esqueça de enviar seu "
        "<b>MT5 UID</b> para finalizar seu acesso VIP."
    ),
    "renewal_reminder": (
        "<b>Lembrete de renovação VIP Funded</b>\n\n"
        "Sua renovação vence em <b>{DAYS} dia(s)</b>.\n"
        "A renovação é <b>EUR 80</b>. Toque /start -> VIP Pago -> Funded para pagar.\n\n"
        "<b>Wallets:</b>\n"
        "BTC: <code>{BTC}</code>\n"
        "ETH: <code>{ETH}</code>\n"
        "SOL: <code>{SOL}</code>"
    ),

    "fallback_msg": "Não entendi — por favor use os botões abaixo.",
    "uid_bad_format": (
        "<b>Formato não reconhecido.</b>\n"
        "Envie seu UID e email da PU Prime assim:\n"
        "<code>UID: 12345678\nEmail: voce@exemplo.com</code>"
    ),
    "vip_uid_received": (
        "<b>Envio VIP recebido.</b>\n"
        "Nossa equipe analisará em breve e enviará DM ao aprovar. ✅"
    ),
    "aff_uid_received": (
        "<b>Envio de afiliado recebido.</b>\n"
        "Nossa equipe confirmará seu status de subafiliado IB e enviará DM. ✅"
    ),
    "funded_submit_bad_format": (
        "<b>Formato não reconhecido.</b>\n"
        "Envie:\n"
        "<code>Amount: 80 EUR\nTX/Ref: &lt;hash ou referência&gt;\nMethod: BTC|ETH|SOL</code>\n"
        "Ou envie a imagem do comprovante com a mesma legenda."
    ),
    "funded_submit_received": (
        "<b>Pagamento do VIP Funded recebido.</b>\n"
        "Estamos verificando — você receberá DM assim que o acesso for liberado. 🔒"
    ),
    "nudge_incomplete": (
        "<b>Ainda interessado em VIP?</b>\n"
        "Você começou mas não terminou — toque /start para continuar de onde parou."
    ),

    "faq_q1": "O que é acesso VIP?",
    "faq_a1": (
        "<b>Acesso VIP</b> dá a você nossos sinais privados, setups e trade calls. "
        "VIP Grátis exige estar sob nosso IB e depositar. "
        "VIP Pago (funded) é acesso direto para traders com conta funded."
    ),
    "faq_q2": "O que é um IB?",
    "faq_a2": (
        "<b>IB (Introducing Broker)</b> significa que sua conta de trading está registrada ou "
        "transferida sob o código do nosso parceiro. Ganhamos uma pequena comissão do spread - "
        "<b>sem custo extra para você</b> - e em troca você ganha acesso VIP grátis."
    ),
    "faq_q3": "Quanto tempo leva a revisão?",
    "faq_a3": (
        "As revisões são <b>normalmente em 24 horas</b>. Se passou mais, toque em "
        "<b>Falar com Suporte</b> e um admin dará sequência."
    ),
    "faq_q4": "Por que meu UID não foi aceito?",
    "faq_a4": (
        "Motivos comuns: conta não está sob nosso código IB, sem depósito ainda, "
        "ou formato UID errado. Confira que usou o código <code>{IB_CODE}</code>, "
        "depositou, e enviou neste formato exato: <code>UID: 12345678</code>"
    ),
    "faq_q5": "Quanto custa o VIP Funded?",
    "faq_a5": (
        "<b>EUR 50</b> no primeiro mês, depois <b>EUR 80</b>/mês. "
        "Pagável em BTC, ETH ou SOL. Após pagar, envie o comprovante com a legenda "
        "<code>PAYMENT: FUNDED</code>."
    ),
    "faq_q6": "Existe depósito mínimo?",
    "faq_a6": (
        "O PU Prime define o depósito mínimo. Recomendamos pelo menos <b>USD 200</b> "
        "para um tamanho de posição significativo e qualificar ao VIP tranquilamente."
    ),

    "btn_vip_access": "Acesso VIP",
    "btn_ib_affiliate": "Ser Afiliado IB",
    "btn_team": "Conheça a Equipe",
    "btn_socials": "Siga-nos",
    "btn_faq": "Perguntas",
    "btn_support": "Falar com Suporte",
    "btn_back": "Voltar",
    "btn_back_to_start": "Voltar ao Início",
    "btn_back_to_vip": "Voltar ao Menu VIP",
    "btn_back_to_affiliate": "Voltar ao Menu Afiliado",
    "btn_yes_restart": "Sim, recomeçar",
    "btn_no_keep": "Não, manter progresso",
    "btn_free_vip": "VIP Grátis",
    "btn_paid_vip": "VIP Pago",
    "btn_new_to_pu": "Novo no PU Prime",
    "btn_existing_pu": "Já tenho PU Prime",
    "btn_live_account": "Conta Real",
    "btn_funded_account": "Conta Funded",
    "btn_dont_know_ib": "Não sei o que é IB",
    "btn_already_know": "Já sei, continuar",
    "btn_continue": "Continuar",
    "btn_step1_register": "Passo 1: Registrar no PU Prime",
    "btn_step1_start_reg": "Passo 1: Iniciar Registro",
    "btn_step2_completed": "Passo 2: Completei o Registro",
    "btn_step3_deposited": "Passo 3: Já Depositei",
    "btn_step4_submit_uid": "Passo 4: Enviar UID",
    "btn_step3_submit_uid": "Passo 3: Enviar UID",
    "btn_step1_view_email": "Passo 1: Ver Email de Transferência",
    "btn_step2_sent_email": "Passo 2: Enviei o Email",
    "btn_view_btc": "Ver Endereço BTC",
    "btn_view_eth": "Ver Endereço ETH",
    "btn_view_sol": "Ver Endereço SOL",
    "btn_sent_payment": "Paguei",
    "btn_submit_proof": "Enviar Comprovante",
    "btn_waiting_payment_review": "Aguardando Revisão do Pagamento",
    "btn_waiting_review": "Aguardando Revisão",
    "btn_benefits": "Benefícios IB",
    "btn_message": "Mensagem",
    "btn_founder": "Fundador - Kratos",
    "btn_onboarding": "Onboarding / Geral - Apollo",
    "btn_signals": "Sinais - Plato",
    "btn_socials_admin": "Socials - HD",
    "btn_change_language": "Mudar Idioma",
    "btn_approve": "Aprovar",
    "btn_reject": "Rejeitar",
    "btn_block_user": "Bloquear Usuário",
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


async def try_react(update, context, emoji="👍"):
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
    m = re.fullmatch(r"UID:\s*(\d{5,20})", text, flags=re.IGNORECASE)
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
    if not update.effective_user or not update.message:
        return
    if is_admin_chat(update):
        return
    user = update.effective_user
    if is_blocked(user.id):
        return
    if not rate_limited(user.id):
        return
    lang = get_lang(user.id)
    text = (update.message.text or "").strip()
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
        amount, tx, method = parsed
        context.user_data["awaiting_funded_proof"] = False
        context.user_data["funded_submitted"] = True
        log_event(user.id, "funded_payment_submitted",
                  f"method={method} amount={amount} tx={tx}")
        await update.message.reply_text(
            L(lang, "funded_submit_received"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
        await notify_admin(
            context,
            (
                "<b>Funded VIP payment submitted</b>\n"
                f"User: {html.escape(user.full_name)} "
                f"(@{html.escape(user.username) if user.username else '—'})\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Language: <b>{lang}</b>\n"
                f"Method: <b>{method}</b>\n"
                f"Amount: <code>{html.escape(amount)}</code>\n"
                f"TX/Ref: <code>{html.escape(tx)}</code>"
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
            menu = (
                vip_submitted_menu(lang) if uid_type == "vip"
                else affiliate_submitted_menu(lang)
            )
            await update.message.reply_text(
                L(lang, "uid_bad_format"),
                reply_markup=back_to_start(lang) if uid_type == "vip" else back_to_affiliate_main(lang),
                parse_mode="HTML",
            )
            return
        uid, email = parsed
        context.user_data["awaiting_uid"] = False
        register_uid(user.id, uid, email, uid_type)
        if uid_type == "vip":
            context.user_data["vip_submitted"] = True
            log_event(user.id, "vip_uid_submitted", f"uid={uid} email={email}")
            await update.message.reply_text(
                L(lang, "vip_uid_received"),
                reply_markup=vip_submitted_menu(lang),
                parse_mode="HTML",
            )
        else:
            context.user_data["affiliate_submitted"] = True
            log_event(user.id, "affiliate_uid_submitted", f"uid={uid} email={email}")
            await update.message.reply_text(
                L(lang, "aff_uid_received"),
                reply_markup=affiliate_submitted_menu(lang),
                parse_mode="HTML",
            )
        await notify_admin(
            context,
            (
                f"<b>{'VIP' if uid_type == 'vip' else 'Affiliate'} UID submission</b>\n"
                f"User: {html.escape(user.full_name)} "
                f"(@{html.escape(user.username) if user.username else '—'})\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Language: <b>{lang}</b>\n"
                f"UID: <code>{html.escape(uid)}</code>\n"
                f"Email: <code>{html.escape(email)}</code>"
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


async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    if is_admin_chat(update):
        return
    user = update.effective_user
    if is_blocked(user.id):
        return
    if not rate_limited(user.id):
        return
    lang = get_lang(user.id)
    caption = (update.message.caption or "").strip()

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
        amount, tx, method = parsed
        context.user_data["awaiting_funded_proof"] = False
        context.user_data["funded_submitted"] = True
        log_event(user.id, "funded_payment_submitted_media",
                  f"method={method} amount={amount} tx={tx}")
        await update.message.reply_text(
            L(lang, "funded_submit_received"),
            reply_markup=start_menu(lang),
            parse_mode="HTML",
        )
        try:
            await update.message.forward(chat_id=ADMIN_CHAT_ID)
        except Exception:
            logger.exception("Failed to forward funded payment proof")
        await notify_admin(
            context,
            (
                "<b>Funded VIP payment submitted (with media)</b>\n"
                f"User: {html.escape(user.full_name)} "
                f"(@{html.escape(user.username) if user.username else '—'})\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Language: <b>{lang}</b>\n"
                f"Method: <b>{method}</b>\n"
                f"Amount: <code>{html.escape(amount)}</code>\n"
                f"TX/Ref: <code>{html.escape(tx)}</code>"
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
            await update.message.reply_text(
                L(lang, "uid_bad_format"),
                reply_markup=back_to_start(lang) if uid_type == "vip" else back_to_affiliate_main(lang),
                parse_mode="HTML",
            )
            return
        uid, email = parsed
        context.user_data["awaiting_uid"] = False
        register_uid(user.id, uid, email, uid_type)
        if uid_type == "vip":
            context.user_data["vip_submitted"] = True
            log_event(user.id, "vip_uid_submitted_media", f"uid={uid} email={email}")
            await update.message.reply_text(
                L(lang, "vip_uid_received"),
                reply_markup=vip_submitted_menu(lang),
                parse_mode="HTML",
            )
        else:
            context.user_data["affiliate_submitted"] = True
            log_event(user.id, "affiliate_uid_submitted_media", f"uid={uid} email={email}")
            await update.message.reply_text(
                L(lang, "aff_uid_received"),
                reply_markup=affiliate_submitted_menu(lang),
                parse_mode="HTML",
            )
        try:
            await update.message.forward(chat_id=ADMIN_CHAT_ID)
        except Exception:
            logger.exception("Failed to forward UID media")
        await notify_admin(
            context,
            (
                f"<b>{'VIP' if uid_type == 'vip' else 'Affiliate'} UID submission (with media)</b>\n"
                f"User: {html.escape(user.full_name)} "
                f"(@{html.escape(user.username) if user.username else '—'})\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Language: <b>{lang}</b>\n"
                f"UID: <code>{html.escape(uid)}</code>\n"
                f"Email: <code>{html.escape(email)}</code>"
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
            logger.exception("Failed to DM approved user")
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
            logger.exception("Failed to DM rejected user")
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


def _extract_custom_message(args: List[str]) -> str:
    return " ".join(args).strip()


@admin_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    snap = stats_snapshot()
    lines = ["<b>ImperiumFX Bot — Stats</b>"]
    lines.append(f"Total users: <b>{snap['total_users']}</b>")
    lines.append(f"Blocked: <b>{snap['blocked']}</b>")
    lines.append(f"Events (24h): <b>{snap['events_24h']}</b>")
    lines.append(f"UID submissions: <b>{snap['uid_total']}</b>")
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
        f"First seen: {row['created_at']}\n"
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
              AND datetime(u.created_at) <= datetime('now', '-48 hours')
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
            logger.exception("Failed to send nudge to %s", uid)
        await asyncio.sleep(0.05)


async def job_renewals(context: ContextTypes.DEFAULT_TYPE):
    # Remind users 25 days after a successful VIP / funded payment.
    conn = db()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT e.user_id
            FROM events e
            WHERE (e.event_type = 'funded_payment_submitted'
                   OR e.event_type = 'admin_approved'
                   OR e.event_type = 'admin_approved_cmd')
              AND datetime(e.created_at) BETWEEN datetime('now', '-26 days')
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
            logger.exception("Failed to send renewal reminder to %s", uid)
        await asyncio.sleep(0.05)


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled error: %s", context.error)
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

    logger.info("ImperiumFX bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()