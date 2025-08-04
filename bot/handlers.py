# bot/handlers.py

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تعریف دکمه های منوی اصلی با اموجی
MAIN_MENU_KEYBOARD = [
    ["🛍️ ویترین فروشگاه", "🏠 صفحه اصلی"],
    ["✨ مشاور استایل", "📞 تماس با پشتیبانی"],
]

# ساخت کیبورد سفارشی با تنظیمات دلخواه
MAIN_MENU_MARKUP = ReplyKeyboardMarkup(
    MAIN_MENU_KEYBOARD, 
    resize_keyboard=True, 
    input_field_placeholder="از منوی زیر انتخاب کنید:"
)

# --- هندلرهای دکمه های منو ---

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دستور /start و دکمه 'صفحه اصلی'"""
    user = update.effective_user
    await update.message.reply_html(
        f"سلام {user.mention_html()}! به ربات تایلند خوش آمدی.",
        reply_markup=MAIN_MENU_MARKUP,
    )

async def store_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دکمه 'ویترین فروشگاه'"""
    await update.message.reply_text("شما وارد ویترین فروشگاه شدید. (این بخش در آینده تکمیل می شود)")

async def style_advisor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دکمه 'مشاور استایل'"""
    await update.message.reply_text("شما وارد بخش مشاور استایل شدید. (این بخش در آینده تکمیل می شود)")

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دکمه 'تماس با پشتیبانی'"""
    await update.message.reply_text("اطلاعات تماس با پشتیبانی. (این بخش در آینده تکمیل می شود)")


# --- تابع ثبت کننده هندلرها ---

def register_handlers(application: Application) -> None:
    """تمام دستورات و کنترل کننده های ربات را در اینجا ثبت می کند."""
    # دستور اصلی
    application.add_handler(CommandHandler("start", start_handler))
    
    # هندلرهای دکمه های منوی اصلی با استفاده از فیلتر متن دقیق
    application.add_handler(MessageHandler(filters.Text("🏠 صفحه اصلی"), start_handler))
    application.add_handler(MessageHandler(filters.Text("🛍️ ویترین فروشگاه"), store_handler))
    application.add_handler(MessageHandler(filters.Text("✨ مشاور استایل"), style_advisor_handler))
    application.add_handler(MessageHandler(filters.Text("📞 تماس با پشتیبانی"), support_handler))
