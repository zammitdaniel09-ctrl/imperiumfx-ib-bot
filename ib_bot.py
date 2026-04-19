import asyncio

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
ADMIN_CHAT_ID = 7121821750

IB_LINK = "https://www.puprime.partners/forex-trading-account/?affid=MjMyMTMwODY="
IB_CODE = "pOenf2oC"
IB_ACCOUNT_NUMBER = "23213086"
TUTORIAL_PDF = "IB_E_BOOK.pdf"

TRANSFER_EMAIL_1 = "aleksandra.stojkovic@puprime.com"
TRANSFER_EMAIL_2 = "info@puprime.com"


def welcome_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 I don’t know what IB is", callback_data="what_is_ib")],
        [InlineKeyboardButton("✅ I already know, continue", callback_data="continue_main")],
    ])


def ib_pdf_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Continue", callback_data="continue_main")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_welcome")],
    ])


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 New to PU Prime", callback_data="flow_new")],
        [InlineKeyboardButton("🔁 Already with PU Prime", callback_data="flow_existing")],
        [InlineKeyboardButton("💼 IB Benefits", callback_data="benefits")],
        [InlineKeyboardButton("🛠 Support", callback_data="support")],
    ])


def new_user_step_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Step 1: Start Registration", url=IB_LINK)],
        [InlineKeyboardButton("✅ Step 2: I Completed Registration", callback_data="completed_registration")],
        [InlineKeyboardButton("📩 Step 3: Submit UID", callback_data="submit_uid")],
        [InlineKeyboardButton("⬅ Back to Main Menu", callback_data="back_main")],
    ])


def existing_user_step_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Step 1: View Transfer Email", callback_data="transfer_email_template")],
        [InlineKeyboardButton("📨 Step 2: I Sent the Email", callback_data="sent_transfer_email")],
        [InlineKeyboardButton("📩 Step 3: Submit UID", callback_data="submit_uid")],
        [InlineKeyboardButton("⬅ Back to Main Menu", callback_data="back_main")],
    ])


def back_to_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back to Main Menu", callback_data="back_main")]
    ])


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str):
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
        parse_mode="HTML"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Welcome to ImperiumFX IB Setup.</b>\n\n"
        "Before continuing, choose one option below."
    )

    await update.message.reply_text(
        text,
        reply_markup=welcome_menu(),
        parse_mode="HTML"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    username = f"@{user.username}" if user.username else "No username"

    if query.data == "back_welcome":
        await query.message.reply_text(
            "<b>Welcome Menu</b>",
            reply_markup=welcome_menu(),
            parse_mode="HTML"
        )

    elif query.data == "back_main":
        await query.message.reply_text(
            "<b>Main Setup Menu</b>\n\n"
            "Choose the path that matches your situation.",
            reply_markup=main_menu(),
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
                f"Put <b>{TUTORIAL_PDF}</b> in the same folder as <b>ib_bot.py</b>.",
                reply_markup=ib_pdf_menu(),
                parse_mode="HTML"
            )

    elif query.data == "continue_main":
        await query.message.reply_text(
            "<b>Main Setup Menu</b>\n\n"
            "Choose the path that matches your situation.",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )

    elif query.data == "flow_new":
        await query.message.reply_text(
            "<b>New to PU Prime</b>\n\n"
            "Follow these steps in order:\n\n"
            "1. <b>Start Registration</b>\n"
            f"2. Make sure the code is <b>{IB_CODE}</b>\n"
            "3. Complete registration and verification\n"
            "4. Press <b>I Completed Registration</b>\n"
            "5. Submit your <b>MT5 UID / account number</b>\n\n"
            "<b>Next step:</b> press <b>Step 1: Start Registration</b>.",
            reply_markup=new_user_step_menu(),
            parse_mode="HTML"
        )

    elif query.data == "completed_registration":
        await query.message.reply_text(
            "<b>Registration marked as completed.</b>\n\n"
            "You can now send your <b>MT5 UID / account number</b> here.\n\n"
            "<b>Next step:</b> press <b>Step 3: Submit UID</b>.",
            reply_markup=new_user_step_menu(),
            parse_mode="HTML"
        )

        await notify_admin(
            context,
            (
                "<b>User completed registration</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>"
            )
        )

    elif query.data == "flow_existing":
        await query.message.reply_text(
            "<b>Already with PU Prime</b>\n\n"
            "Follow these steps in order:\n\n"
            "1. Open the <b>transfer email template</b>\n"
            "2. Send the email to PU Prime\n"
            "3. Press <b>I Sent the Email</b>\n"
            "4. Wait for PU Prime to confirm the transfer\n"
            "5. Submit your <b>MT5 UID / account number</b>\n\n"
            "<b>Next step:</b> press <b>Step 1: View Transfer Email</b>.",
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
            "<b>Next step:</b> send this email, then press <b>Step 2: I Sent the Email</b>.",
            reply_markup=existing_user_step_menu(),
            parse_mode="HTML"
        )

    elif query.data == "sent_transfer_email":
        await query.message.reply_text(
            "<b>Email marked as sent.</b>\n\n"
            "Wait for PU Prime to confirm the IB transfer.\n\n"
            "Once they confirm it, send your <b>MT5 UID / account number</b> here.\n\n"
            "<b>Next step:</b> after confirmation, press <b>Step 3: Submit UID</b>.",
            reply_markup=existing_user_step_menu(),
            parse_mode="HTML"
        )

        await notify_admin(
            context,
            (
                "<b>User says they sent the IB transfer email</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>"
            )
        )

    elif query.data == "benefits":
        await query.message.reply_text(
            "<b>IB Benefits</b>\n\n"
            "• Structured onboarding\n"
            "• Direct support\n"
            "• Faster and cleaner account handling\n"
            "• Bonus structure after setup\n\n"
            "<b>Next step:</b> go back and choose the correct setup path.",
            reply_markup=back_to_main_menu(),
            parse_mode="HTML"
        )

    elif query.data == "submit_uid":
        context.user_data["awaiting_uid"] = True
        await query.message.reply_text(
            "Send your <b>MT5 account number / UID</b> now.\n\n"
            "You can also send a <b>screenshot</b> or <b>document</b> if needed.\n\n"
            "<b>Next step:</b> send your UID in this chat now.",
            reply_markup=back_to_main_menu(),
            parse_mode="HTML"
        )

    elif query.data == "support":
        await query.message.reply_text(
            "Your <b>support request</b> has been sent.\n\n"
            "An admin will contact you shortly.\n\n"
            "<b>Next step:</b> wait for a reply here.",
            reply_markup=back_to_main_menu(),
            parse_mode="HTML"
        )

        await notify_admin(
            context,
            (
                "<b>Support request received</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>"
            )
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else "No username"

    if context.user_data.get("awaiting_uid"):
        submitted_text = update.message.text.strip() if update.message.text else "No text provided"

        await update.message.reply_text(
            "<b>Submission received.</b>\n\n"
            "Your details have been forwarded for review.\n\n"
            "<b>Next step:</b> wait for confirmation or further instructions.",
            reply_markup=main_menu(),
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
                "<b>New UID / Submission received</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Submission: <code>{submitted_text}</code>"
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

    if context.user_data.get("awaiting_uid"):
        await update.message.reply_text(
            "<b>Submission received.</b>\n\n"
            "Your file has been forwarded for review.\n\n"
            "<b>Next step:</b> wait for confirmation or further instructions.",
            reply_markup=main_menu(),
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

        caption = update.message.caption.strip() if update.message.caption else "No caption provided"

        await notify_admin(
            context,
            (
                "<b>New media submission received</b>\n"
                f"Name: {user.full_name}\n"
                f"Username: {username}\n"
                f"User ID: <code>{user.id}</code>\n"
                f"Caption: <code>{caption}</code>"
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