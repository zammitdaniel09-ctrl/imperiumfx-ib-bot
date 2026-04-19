

import asyncio
import re
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
BOT_TOKEN = "8085633137:AAEM6MOSPirix26Bs4Ye9wqryX063L-FO60"
ADMIN_CHAT_ID = -1003919089074
IB_LINK = "https://www.puprime.partners/forex-trading-account/?affid=MjMyMTMwODY="
IB_CODE = "pOenf2oC"
IB_ACCOUNT_NUMBER = "23213086"
TUTORIAL_PDF = "IB_E_BOOK.pdf"
TRANSFER_EMAIL_1 = "aleksandra.stojkovic@puprime.com"
TRANSFER_EMAIL_2 = "info@puprime.com"
SOLANA_ADDRESS = "GrSbxLK1Z6ZgEhEtViY4ibLEq7xYuXiuGCxVFYjzwazt"
ETHEREUM_ADDRESS = "0x2474F60027Fda971aaA773031f07Fd58F3e14627"
BTC_ADDRESS = "bc1pzzz24czpr9yem4st5p727gcm30fw6c6yfnt07pypr6esxu56092smassch"
def start_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join VIP Access", callback_data="vip_access")],
        [InlineKeyboardButton("💼 Become an IB Affiliate", callback_data="ib_affiliate")],
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
        [InlineKeyboardButton("📘 I don’t know what IB is", callback_data="what_is_ib")],
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
async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str):
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
        parse_mode="HTML"
    )
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = (
        "<b>Welcome to ImperiumFX Setup</b>\n\n"
        "Choose your path below.\n\n"
        "• <b>VIP Access</b> — join our VIP signal access\n"
        "• <b>IB Affiliate</b> — become an affiliate and follow the IB onboarding process\n\n"
        "<i>Please choose the option that matches what you want.</i>"
    )
    await update.message.reply_text(
        text,
        reply_markup=start_menu(),
        parse_mode="HTML"
    )
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    username = f"@{user.username}" if user.username else "No username"
    if query.data == "back_start":
        context.user_data.clear()
        await query.message.reply_text(
            "<b>Welcome to ImperiumFX Setup</b>\n\n"
            "Choose your path below.\n\n"
            "• <b>VIP Access</b> — join our VIP signal access\n"
            "• <b>IB Affiliate</b> — become an affiliate and follow the IB onboarding process\n\n"
            "<i>Please choose the option that matches what you want.</i>",
            reply_markup=start_menu(),
            parse_mode="HTML"
        )
    elif query.data == "vip_access":
        context.user_data["main_path"] = "vip"
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
            parse_mode="HTML"
        )
    elif query.data == "vip_free":
        context.user_data["vip_mode"] = "free"
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
            parse_mode="HTML"
        )
    elif query.data == "vip_paid":
        context.user_data["vip_mode"] = "paid"
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
            parse_mode="HTML"
        )
    elif query.data == "vip_paid_live":
        context.user_data["vip_mode"] = "paid_live"
        await query.message.reply_text(
            "<b>Paid VIP — Live Account</b>\n\n"
            "For live accounts, your access is handled through our IB structure.\n\n"
            "That means you must:\n"
            "1. register under us or transfer under us\n"
            "2. deposit\n"
            "3. submit your UID\n\n"
            "<i>Select your route below.</i>",
            reply_markup=vip_free_menu(),
            parse_mode="HTML"
        )
    elif query.data == "vip_paid_funded":
        context.user_data["vip_mode"] = "paid_funded"
        context.user_data["flow"] = "vip_paid_funded"
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
            parse_mode="HTML"
        )
    elif query.data == "show_btc":
        await query.message.reply_text(
            "<b>BTC Address</b>\n\n"
            f"<code>{BTC_ADDRESS}</code>\n\n"
            "<i>After sending payment, press I Sent Payment and then submit your proof.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML"
        )
    elif query.data == "show_eth":
        await query.message.reply_text(
            "<b>ETH Address</b>\n\n"
            f"<code>{ETHEREUM_ADDRESS}</code>\n\n"
            "<i>After sending payment, press I Sent Payment and then submit your proof.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML"
        )
    elif query.data == "show_sol":
        await query.message.reply_text(
            "<b>SOL Address</b>\n\n"
            f"<code>{SOLANA_ADDRESS}</code>\n\n"
            "<i>After sending payment, press I Sent Payment and then submit your proof.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML"
        )
    elif query.data == "funded_payment_sent":
        context.user_data["funded_payment_sent"] = True
        await query.message.reply_text(
            "<b>Payment marked as sent.</b>\n\n"
            "Now submit your payment proof.\n\n"
            "<b>Important:</b> if you send a screenshot or document, the caption must be:\n\n"
            "<code>PAYMENT: FUNDED</code>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>Funded VIP user says they sent payment</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>VIP Paid Funded</b>"
            )
        )
    elif query.data == "submit_payment_proof":
        if context.user_data.get("funded_submitted"):
            await query.message.reply_text(
                "<b>Your payment proof has already been received.</b>\n\n"
                "Please wait for review or contact support if needed.",
                reply_markup=funded_review_menu(),
                parse_mode="HTML"
            )
            return
        if not context.user_data.get("funded_payment_sent"):
            await query.message.reply_text(
                "<b>You must mark payment as sent first.</b>\n\n"
                "Please follow the funded VIP steps in order.",
                reply_markup=funded_payment_menu(),
                parse_mode="HTML"
            )
            return
        context.user_data["awaiting_payment_proof"] = True
        await query.message.reply_text(
            "Send your <b>payment proof</b> now.\n\n"
            "<b>Required caption format:</b>\n"
            "<code>PAYMENT: FUNDED</code>\n\n"
            "<i>Screenshot or document only.</i>",
            reply_markup=funded_payment_menu(),
            parse_mode="HTML"
        )
    elif query.data == "funded_waiting_review":
        await query.message.reply_text(
            "<b>Your funded VIP payment proof is already under review.</b>\n\n"
            "There is nothing else you need to submit right now.\n\n"
            "<i>If you need help, press Contact Support.</i>",
            reply_markup=funded_review_menu(),
            parse_mode="HTML"
        )
    elif query.data == "ib_affiliate":
        context.user_data["main_path"] = "affiliate"
        await query.message.reply_text(
            "<b>IB Affiliate Setup</b>\n\n"
            "This path is for users who want to understand the IB model and complete the affiliate onboarding process.\n\n"
            "<i>Choose whether you need the beginner guide or want to continue directly.</i>",
            reply_markup=affiliate_menu(),
            parse_mode="HTML"
        )
    elif query.data == "what_is_ib":
        await query.message.reply_text(
            "Start with the <b>tutorial PDF</b> below.\n\n"
            "<b>Next step:</b> once you’ve read it, press <b>Continue</b>.",
            reply_markup=ib_pdf_menu(),
            parse_mode="HTML"
        )
        try:
            with open(TUTORIAL_PDF, "rb") as pdf:
                await query.message.reply_document(
                    document=pdf,
                    caption="IB Tutorial Guide"
                )
        except FileNotFoundError:
            await query.message.reply_text(
                f"Tutorial PDF not found.\n\n"
                f"Put <b>{TUTORIAL_PDF}</b> in the same folder as <b>IB_bot.py</b>.",
                reply_markup=ib_pdf_menu(),
                parse_mode="HTML"
            )
    elif query.data == "affiliate_main":
        await query.message.reply_text(
            "<b>IB Affiliate Menu</b>\n\n"
            "Choose the path that matches your situation.",
            reply_markup=affiliate_main_menu(),
            parse_mode="HTML"
        )
    elif query.data == "vip_new":
        context.user_data["flow"] = "vip_new"
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
            parse_mode="HTML"
        )
    elif query.data == "vip_existing":
        context.user_data["flow"] = "vip_existing"
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
            parse_mode="HTML"
        )
    elif query.data == "vip_registered":
        context.user_data["vip_registered"] = True
        await query.message.reply_text(
            "<b>Registration marked as completed.</b>\n\n"
            "<b>Next requirement:</b> you must now <b>deposit</b> before submitting your UID for VIP review.\n\n"
            "<i>Do not skip this step.</i>",
            reply_markup=vip_new_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>VIP user completed registration</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP New User</b>"
            )
        )
    elif query.data == "vip_deposit_done":
        if not context.user_data.get("vip_registered"):
            await query.message.reply_text(
                "<b>You must complete registration first.</b>\n\n"
                "Please follow the steps in order.\n\n"
                "<i>Step 1 must be completed before Step 3.</i>",
                reply_markup=vip_new_menu(),
                parse_mode="HTML"
            )
            return
        context.user_data["vip_deposit_done"] = True
        await query.message.reply_text(
            "<b>Deposit marked as completed.</b>\n\n"
            "You can now submit your <b>MT5 UID / account number</b> for VIP review.",
            reply_markup=vip_new_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>VIP user says they deposited</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP New User</b>"
            )
        )
    elif query.data == "vip_transfer_email":
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
            parse_mode="HTML"
        )
    elif query.data == "vip_sent_transfer":
        context.user_data["vip_transfer_sent"] = True
        await query.message.reply_text(
            "<b>Transfer email marked as sent.</b>\n\n"
            "Wait for PU Prime to confirm the IB transfer.\n\n"
            "<b>After that:</b>\n"
            "• deposit\n"
            "• then submit your UID\n\n"
            "<i>This is required for VIP review.</i>",
            reply_markup=vip_existing_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>VIP user says they sent the transfer email</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP Existing User</b>"
            )
        )
    elif query.data == "vip_existing_deposit_done":
        if not context.user_data.get("vip_transfer_sent"):
            await query.message.reply_text(
                "<b>You must send the transfer email first.</b>\n\n"
                "Please follow the VIP transfer steps in order.",
                reply_markup=vip_existing_menu(),
                parse_mode="HTML"
            )
            return
        context.user_data["vip_existing_deposit_done"] = True
        await query.message.reply_text(
            "<b>Deposit marked as completed.</b>\n\n"
            "You can now submit your <b>MT5 UID / account number</b> for VIP review.",
            reply_markup=vip_existing_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>VIP existing user says they deposited</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                "Flow: <b>VIP Existing User</b>"
            )
        )
    elif query.data == "flow_new":
        context.user_data["flow"] = "affiliate_new"
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
            parse_mode="HTML"
        )
    elif query.data == "completed_registration":
        context.user_data["affiliate_registered"] = True
        await query.message.reply_text(
            "<b>Registration marked as completed.</b>\n\n"
            "You can now send your <b>MT5 UID / account number</b> here.\n\n"
            "<i>Please make sure the UID format is correct before sending it.</i>",
            reply_markup=new_user_step_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>Affiliate user completed registration</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>Affiliate New User</b>"
            )
        )
    elif query.data == "flow_existing":
        context.user_data["flow"] = "affiliate_existing"
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
            parse_mode="HTML"
        )
    elif query.data == "transfer_email_template":
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
            parse_mode="HTML"
        )
    elif query.data == "sent_transfer_email":
        context.user_data["affiliate_transfer_sent"] = True
        await query.message.reply_text(
            "<b>Email marked as sent.</b>\n\n"
            "Wait for PU Prime to confirm the IB transfer.\n\n"
            "Once confirmed, submit your <b>MT5 UID / account number</b> here.",
            reply_markup=existing_user_step_menu(),
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>Affiliate user says they sent the IB transfer email</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>Affiliate Existing User</b>"
            )
        )
    elif query.data == "benefits":
        await query.message.reply_text(
            "<b>IB Benefits</b>\n\n"
            "• Structured onboarding\n"
            "• Direct admin support\n"
            "• Clear setup process\n"
            "• Access to the next stage after validation\n\n"
            "<i>Go back and continue the correct path.</i>",
            reply_markup=back_to_affiliate_main(),
            parse_mode="HTML"
        )
    elif query.data == "submit_uid_vip":
        flow = context.user_data.get("flow")
        if context.user_data.get("vip_submitted"):
            await query.message.reply_text(
                "<b>Your VIP submission has already been received.</b>\n\n"
                "Please wait for review or contact support if needed.",
                reply_markup=vip_submitted_menu(),
                parse_mode="HTML"
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
                parse_mode="HTML"
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
                parse_mode="HTML"
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
            parse_mode="HTML"
        )
    elif query.data == "submit_uid_affiliate":
        flow = context.user_data.get("flow")
        if context.user_data.get("affiliate_submitted"):
            await query.message.reply_text(
                "<b>Your affiliate submission has already been received.</b>\n\n"
                "Please wait for review or contact support if needed.",
                reply_markup=affiliate_submitted_menu(),
                parse_mode="HTML"
            )
            return
        if flow == "affiliate_new" and not context.user_data.get("affiliate_registered"):
            await query.message.reply_text(
                "<b>You must complete registration first.</b>\n\n"
                "Please follow the affiliate steps in order.",
                reply_markup=new_user_step_menu(),
                parse_mode="HTML"
            )
            return
        if flow == "affiliate_existing" and not context.user_data.get("affiliate_transfer_sent"):
            await query.message.reply_text(
                "<b>You must send the transfer email first.</b>\n\n"
                "Please follow the affiliate steps in order.",
                reply_markup=existing_user_step_menu(),
                parse_mode="HTML"
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
            parse_mode="HTML"
        )
    elif query.data == "vip_waiting_review":
        await query.message.reply_text(
            "<b>Your VIP submission is already under review.</b>\n\n"
            "There is nothing else you need to submit right now.\n\n"
            "<i>If you need help, press Contact Support.</i>",
            reply_markup=vip_submitted_menu(),
            parse_mode="HTML"
        )
    elif query.data == "affiliate_waiting_review":
        await query.message.reply_text(
            "<b>Your affiliate submission is already under review.</b>\n\n"
            "There is nothing else you need to submit right now.\n\n"
            "<i>If you need help, press Contact Support.</i>",
            reply_markup=affiliate_submitted_menu(),
            parse_mode="HTML"
        )
    elif query.data == "support":
        reply_markup = back_to_start()
        if context.user_data.get("flow") == "vip_paid_funded":
            reply_markup = funded_payment_menu()
        elif context.user_data.get("main_path") == "vip":
            reply_markup = back_to_vip_menu()
        elif context.user_data.get("main_path") == "affiliate":
            reply_markup = back_to_affiliate_main()
        await query.message.reply_text(
            "Your <b>support request</b> has been sent.\n\n"
            "An admin will contact you shortly.\n\n"
            "<i>Please wait for a reply here.</i>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        await notify_admin(
            context,
            (
                "<b>Support request received</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Main Path: <b>{context.user_data.get('main_path', 'unknown')}</b>\n"
                f"VIP Mode: <b>{context.user_data.get('vip_mode', 'unknown')}</b>\n"
                f"Flow: <b>{context.user_data.get('flow', 'unknown')}</b>"
            )
        )
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else "No username"
    if context.user_data.get("awaiting_uid"):
        submitted_text = update.message.text.strip() if update.message.text else ""
        parsed_uid = parse_uid_submission(submitted_text)
        if not parsed_uid:
            await update.message.reply_text(
                uid_format_guide(),
                parse_mode="HTML"
            )
            return
        uid_type = context.user_data.get("uid_type", "unknown")
        flow = context.user_data.get("flow", "unknown")
        if uid_type == "vip":
            reply_markup = vip_submitted_menu()
            context.user_data["vip_submitted"] = True
        else:
            reply_markup = affiliate_submitted_menu()
            context.user_data["affiliate_submitted"] = True
        await update.message.reply_text(
            "<b>Submission received.</b>\n\n"
            "Your details have been forwarded for review.\n\n"
            "<i>Please wait for confirmation or further instructions.</i>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
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
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"UID: <code>{parsed_uid}</code>"
            )
        )
        context.user_data["awaiting_uid"] = False
    else:
        await update.message.reply_text(
            "To begin the setup, press <b>/start</b>.",
            parse_mode="HTML"
        )
async def media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else "No username"
    if context.user_data.get("awaiting_payment_proof"):
        caption = update.message.caption.strip() if update.message.caption else ""
        payment_type = parse_payment_submission(caption)
        if not payment_type:
            await update.message.reply_text(
                payment_format_guide(),
                parse_mode="HTML"
            )
            return
        context.user_data["funded_submitted"] = True
        context.user_data["awaiting_payment_proof"] = False
        await update.message.reply_text(
            "<b>Payment proof received.</b>\n\n"
            "Your funded VIP payment is now under review.\n\n"
            "<i>Please wait for confirmation or further instructions.</i>",
            reply_markup=funded_review_menu(),
            parse_mode="HTML"
        )
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
        except Exception:
            pass
        await notify_admin(
            context,
            (
                "<b>Funded VIP payment proof received</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                "Flow: <b>VIP Paid Funded</b>\n"
                "Payment Type: <b>FUNDED</b>"
            )
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
                parse_mode="HTML"
            )
            return
        if uid_type == "vip":
            reply_markup = vip_submitted_menu()
            context.user_data["vip_submitted"] = True
        else:
            reply_markup = affiliate_submitted_menu()
            context.user_data["affiliate_submitted"] = True
        await update.message.reply_text(
            "<b>Submission received.</b>\n\n"
            "Your file has been forwarded for review.\n\n"
            "<i>Please wait for confirmation or further instructions.</i>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
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
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"UID From Caption: <code>{parsed_uid}</code>"
            )
        )
        context.user_data["awaiting_uid"] = False
    else:
        await update.message.reply_text(
            "To begin the setup, press <b>/start</b>.",
            parse_mode="HTML"
        )
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).job_queue(None).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, media_handler))
    print("Bot is running...")
    app.run_polling()
if __name__ == "__main__":
    main()
