# file: bot/handlers.py

import os
import glob
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes,
    CallbackQueryHandler, ConversationHandler
)
from telegram.constants import ChatAction
from core.image_engine import generate_final_image, ImageGenerationError
from services.openai_service import get_style_advice

# --- تعریف متغیرهای ثابت (بدون تغییر) ---
USER_SELFIE_DIR = os.path.join("user_uploads", "selfies") # مسیر صحیح شده
TIES_ASSETS_DIR = "assets/ties"
os.makedirs(USER_SELFIE_DIR, exist_ok=True)
# os.makedirs(TIES_ASSETS_DIR, exist_ok=True) # این پوشه باید از قبل موجود باشد

# ===================================================================
# ↓↓↓ شروع تغییرات: تعریف حالت‌های جدید برای مکالمه پرو مجازی ↓↓↓
# ===================================================================
(AWAIT_SUIT_COLOR, AWAIT_SHIRT_COLOR, AWAIT_FINAL_SELFIE,
 AWAIT_ADVISOR_OCCASION, AWAIT_ADVISOR_SHIRT_COLOR) = range(5)
# ===================================================================
# ↑↑↑ پایان تغییرات ↑↑↑
# ===================================================================


# کیبورد اصلی و دسته‌بندی‌ها (بدون تغییر)
MAIN_MENU_KEYBOARD = [["ویترین فروشگاه", "مشاور استایل"], ["تماس با پشتیبانی", "صفحه اصلی"]]
MAIN_MENU_MARKUP = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True, input_field_placeholder="از منوی زیر انتخاب کنید:")
TIE_CATEGORIES = {"paisley": "بته جقه", "knit": "بافت", "special": "طرح خاص", "plain": "ساده", "striped": "راه راه", "dotted": "داتد", "floral": "گلدار", "houndstooth": "پیچازی", "grenadine": "گرانادین", "pinpoint": "جودون", "stealth": "طرح مخفی", "foulard": "فولادر"}

def get_category_keyboard(categories_dict):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"category_{key}")] for key, name in categories_dict.items()]
    return InlineKeyboardMarkup(keyboard)

# --- هندلرهای پایه (بدون تغییر) ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("به ربات استایلیست مجازی کراوات خوش آمدید!", reply_markup=MAIN_MENU_MARKUP)
async def store_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("لطفاً یکی از دسته‌بندی‌های زیر را انتخاب کنید:", reply_markup=get_category_keyboard(TIE_CATEGORIES))
async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("شما می‌توانید از طریق آیدی @SupportID با ما در تماس باشید.")
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد.", reply_markup=MAIN_MENU_MARKUP)
    return ConversationHandler.END

# --- جریان نمایش محصولات (بدون تغییر) ---
async def category_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    category_key = query.data.split('_')[1]
    category_name = TIE_CATEGORIES.get(category_key, "ناشناخته")
    await query.message.reply_text(f"در حال جستجوی محصولات دسته «{category_name}»...")
    search_pattern = os.path.join(TIES_ASSETS_DIR, f"{category_key}_*.png")
    product_images = glob.glob(search_pattern)
    if not product_images:
        await query.message.reply_text(f"متاسفانه در حال حاضر محصولی در دسته «{category_name}» یافت نشد.")
        return
    for image_path in product_images:
        tie_filename = os.path.basename(image_path)
        caption = f"مدل: {tie_filename.replace('.png', '')}"
        keyboard = [[InlineKeyboardButton("✅ پرو مجازی این کراوات", callback_data=f"try_on_{tie_filename}")]]
        await query.message.reply_photo(photo=open(image_path, "rb"), caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# ===================================================================
# ↓↓↓ شروع تغییرات: بازطراحی کامل مکالمه پرو مجازی ↓↓↓
# ===================================================================

# --- مکالمه پرو مجازی هوشمند (ConversationHandler جدید) ---

async def virtual_try_on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند پرو مجازی با پرسیدن رنگ کت."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    tie_filename = query.data.split('try_on_')[1]
    context.user_data['selected_tie'] = tie_filename
    
    await query.message.reply_text(
        "عالی! برای شبیه‌سازی دقیق‌تر، لطفاً رنگ کت و شلوار خود را وارد کنید.\n(مثال: مشکی، سرمه‌ای، طوسی)\n\nبرای لغو /cancel را بزنید."
    )
    return AWAIT_SUIT_COLOR

async def receive_suit_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت رنگ کت و پرسیدن رنگ پیراهن."""
    context.user_data['suit_color'] = update.message.text
    await update.message.reply_text(
        "متشکرم. حالا لطفاً رنگ پیراهن خود را وارد کنید.\n(مثال: سفید، آبی روشن، صورتی)\n\nبرای لغو /cancel را بزنید."
    )
    return AWAIT_SHIRT_COLOR

async def receive_shirt_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت رنگ پیراهن و درخواست نهایی برای سلفی."""
    context.user_data['shirt_color'] = update.message.text
    await update.message.reply_text(
        "فوق‌العاده است! اکنون لطفاً یک عکس سلفی واضح از خودتان (از سینه به بالا) با نور مناسب ارسال کنید.\n\nبرای لغو /cancel را بزنید."
    )
    return AWAIT_FINAL_SELFIE

async def receive_final_selfie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت سلفی، فراخوانی موتور تصویر با اطلاعات کامل و ارسال نتیجه."""
    await update.message.reply_text("متشکرم! تصویر شما دریافت شد. لطفاً چند لحظه صبر کنید، استایلیست هوشمند در حال آماده‌سازی استایل شماست...", reply_markup=MAIN_MENU_MARKUP)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)

    photo_file = await update.message.photo[-1].get_file()
    selfie_save_path = os.path.join(USER_SELFIE_DIR, f"{update.message.from_user.id}_{photo_file.file_unique_id}.jpg")
    await photo_file.download_to_drive(selfie_save_path)
    
    # استخراج تمام اطلاعات جمع‌آوری شده
    tie_filename = context.user_data.get('selected_tie')
    style_context = {
        'suit_color': context.user_data.get('suit_color', ''),
        'shirt_color': context.user_data.get('shirt_color', '')
    }
    
    try:
        # فراخوانی موتور تصویر با امضای جدید
        final_image_url = generate_final_image(
            selfie_path=selfie_save_path,
            tie_filename=tie_filename,
            style_context=style_context
        )
        await update.message.reply_photo(photo=final_image_url, caption="این هم از استایل جدید شما! ✨")
    except ImageGenerationError as e:
        print(f"خطا از موتور تصویر: {e}")
        await update.message.reply_text("متاسفانه در حال حاضر امکان پرو مجازی وجود ندارد. لطفاً بعداً دوباره تلاش کنید.")
    
    context.user_data.clear()
    return ConversationHandler.END

# --- مکالمه مشاور استایل (بدون تغییر ساختاری، فقط شماره حالت‌ها عوض شده) ---
async def style_advisor_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("به بخش مشاور استایل خوش آمدید!\nبرای چه مناسبتی به دنبال کراوات هستید؟\nبرای لغو /cancel را بزنید.")
    return AWAIT_ADVISOR_OCCASION
# ... (بقیه توابع مشاور استایل بدون تغییر باقی می‌مانند) ...

# --- تابع ثبت کننده هندلرها با ConversationHandler جدید ---
def register_handlers(application: Application) -> None:
    # مکالمه پرو مجازی (بازنویسی شده)
    try_on_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(virtual_try_on_start, pattern="^try_on_")],
        states={
            AWAIT_SUIT_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_suit_color)],
            AWAIT_SHIRT_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shirt_color)],
            AWAIT_FINAL_SELFIE: [MessageHandler(filters.PHOTO, receive_final_selfie)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_message=False
    )
    
    # مکالمه مشاور استایل (بدون تغییر)
    style_advisor_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT("مشاور استایل"), style_advisor_start)],
        states={
            AWAIT_ADVISOR_OCCASION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_occasion_handler)], # این تابع‌ها در کد شما موجودند
            AWAIT_ADVISOR_SHIRT_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_shirt_color_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_message=False
    )
    
    # ثبت هندلرهای اصلی (بدون تغییر)
    application.add_handler(CommandHandler("start", start_handler))
    # ... (بقیه application.add_handler ها)

    # ثبت مکالمات
    application.add_handler(style_advisor_conv)
    application.add_handler(try_on_conv)
    application.add_handler(CallbackQueryHandler(category_callback_handler, pattern="^category_"))
# ===================================================================
# ↑↑↑ پایان تغییرات ↑↑↑
# ===================================================================
