# file: core/image_engine.py
import os
from utils.image_processor import create_montage
from services.flux_service import call_flux_api

# تعریف یک خطای سفارشی برای این ماژول (بدون تغییر)
class ImageGenerationError(Exception):
    """خطای سفارشی برای زمانی که تولید عکس با مشکل مواجه می‌شود."""
    pass

# ===================================================================
# ↓↓↓ شروع تغییرات در این تابع ↓↓↓
# ===================================================================
def generate_final_image(selfie_path: str, tie_filename: str, style_context: dict) -> str:
    """
    ارکستراتور اصلی: با دریافت اطلاعات زمینه، پرامپت هوشمند ساخته و تصویر نهایی را تولید می‌کند.
    
    Args:
        selfie_path (str): مسیر فایل سلفی کاربر.
        tie_filename (str): نام فایل کراوات انتخاب شده.
        style_context (dict): دیکشنری شامل اطلاعات استایل مانند رنگ کت و پیراهن.
                               مثال: {'suit_color': 'سرمه‌ای', 'shirt_color': 'سفید'}
    """
    print("شروع فرآیند تولید تصویر نهایی با اطلاعات زمینه...")
    try:
        tie_path = os.path.join('assets/ties', tie_filename)
        output_folder = 'user_uploads'

        # ۱. ساخت مونتاژ اولیه (بدون تغییر)
        print(f"۱. در حال ساخت مونتاژ...")
        montage_path = create_montage(selfie_path, tie_path, output_folder)
        print(f"   مونتاژ اولیه در {montage_path} ساخته شد.")

        # ۲. ساخت پرامپت هوشمند و داینامیک (بخش جدید و کلیدی)
        suit_color = style_context.get('suit_color', '')
        shirt_color = style_context.get('shirt_color', '')
        
        # ساخت بخش‌های مختلف پرامپت
        base_prompt = "A professional, photorealistic high-quality photo of a man wearing"
        shirt_part = f" a {shirt_color} shirt" if shirt_color else ""
        suit_part = f" and a {suit_color} suit" if suit_color else ""
        tie_part = " with this tie"
        style_part = ", sharp focus, studio lighting, looking great"
        
        # ترکیب نهایی پرامپت
        prompt = f"{base_prompt}{shirt_part}{suit_part}{tie_part}{style_part}"
        print(f"   پرامپت هوشمند ساخته شد: {prompt}")

        # ۳. ارسال به سرویس واقعی‌سازی (بدون تغییر)
        print("۳. در حال ارسال مونتاژ به Flux API برای واقعی‌سازی...")
        final_image_url = call_flux_api(montage_path, prompt)
        print("   لینک تصویر نهایی از Flux دریافت شد.")
        
        return final_image_url

    except Exception as e:
        print(f"خطا در image_engine: {e}")
        raise ImageGenerationError(f"متاسفانه در فرآیند تولید تصویر خطایی رخ داد: {e}")
# ===================================================================
# ↑↑↑ پایان تغییرات در این تابع ↑↑↑
# ===================================================================
