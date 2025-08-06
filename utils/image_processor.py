import cv2
import numpy as np
import os

def create_montage(selfie_path: str, tie_path: str, output_folder: str) -> str:
    """
    کراوات را روی سلفی مونتاژ کرده و تصویر نهایی را ذخیره می‌کند.

    Returns:
        str: مسیر فایل مونتاژ شده.
    """
    # ۱. خواندن تصاویر
    selfie_img = cv2.imread(selfie_path)
    # کراوات را با کانال آلفا (شفافیت) می‌خوانیم
    tie_img = cv2.imread(tie_path, cv2.IMREAD_UNCHANGED)

    if selfie_img is None or tie_img is None:
        raise ValueError(f"یکی از مسیرهای عکس اشتباه است: selfie: {selfie_path}, tie: {tie_path}")

    # ۲. آماده‌سازی ماسک کراوات
    # اگر عکس کراوات کانال آلفا ندارد، یک ماسک ساده بر اساس رنگ سفید می‌سازیم
    if tie_img.shape[2] < 4:
        # تبدیل به خاکستری برای پیدا کردن پس‌زمینه
        gray_tie = cv2.cvtColor(tie_img, cv2.COLOR_BGR2GRAY)
        # تمام پیکسل‌هایی که سفید نیستند را به عنوان پیش‌زمینه در نظر می‌گیریم
        _, alpha_mask = cv2.threshold(gray_tie, 240, 255, cv2.THRESH_BINARY_INV)
    else:
        # اگر کانال آلفا وجود دارد، از آن به عنوان ماسک استفاده می‌کنیم
        alpha_mask = tie_img[:, :, 3]
        tie_img = tie_img[:, :, :3] # فقط کانال‌های رنگی را نگه می‌داریم

    # ۳. تغییر اندازه کراوات
    selfie_h, selfie_w, _ = selfie_img.shape
    # عرض کراوات را به ۱۸٪ عرض سلفی تغییر می‌دهیم (این مقدار تجربی است)
    new_tie_w = int(selfie_w * 0.18)
    # نسبت ابعاد کراوات را حفظ می‌کنیم
    ratio = new_tie_w / tie_img.shape[1]
    new_tie_h = int(tie_img.shape[0] * ratio)
    
    resized_tie = cv2.resize(tie_img, (new_tie_w, new_tie_h), interpolation=cv2.INTER_AREA)
    resized_mask = cv2.resize(alpha_mask, (new_tie_w, new_tie_h), interpolation=cv2.INTER_AREA)

    # ۴. پیدا کردن مختصات برای چسباندن
    # کراوات را در مرکز افقی و کمی پایین‌تر از بالای عکس قرار می‌دهیم
    # این مقادیر برای اکثر سلفی‌ها مناسب است و بعداً می‌توان آن را هوشمندتر کرد
    x_offset = (selfie_w - new_tie_w) // 2
    y_offset = int(selfie_h * 0.35) # ۳۵٪ از بالای عکس

    # ۵. چسباندن کراوات روی سلفی با استفاده از ماسک
    # منطقه‌ای از سلفی که کراوات روی آن قرار می‌گیرد را مشخص می‌کنیم
    y1, y2 = y_offset, y_offset + new_tie_h
    x1, x2 = x_offset, x_offset + new_tie_w
    
    # ماسک را برای ترکیب آماده می‌کنیم
    alpha_f = resized_mask / 255.0
    alpha_b = 1.0 - alpha_f

    # ترکیب کراوات و سلفی
    for c in range(0, 3):
        selfie_img[y1:y2, x1:x2, c] = (alpha_f * resized_tie[:, :, c] +
                                       alpha_b * selfie_img[y1:y2, x1:x2, c])

    # ۶. ذخیره فایل نهایی
    output_filename = "montage_output.png"
    output_path = os.path.join(output_folder, output_filename)
    cv2.imwrite(output_path, selfie_img)

    return output_path


# --- بخش تست مستقل ---
if __name__ == '__main__':
    print("شروع تست ماژول image_processor...")
    # مسیر فایل‌های نمونه خود را اینجا وارد کنید
    sample_selfie = 'dev_assets/sample_selfie.jpg'
    sample_tie = 'dev_assets/sample_tie.png'
    output_dir = 'user_uploads'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(sample_selfie) or not os.path.exists(sample_tie):
        print("خطا: فایل‌های نمونه سلفی یا کراوات در پوشه dev_assets یافت نشدند.")
        print("لطفا مطمئن شوید این دو فایل را در آن پوشه قرار داده‌اید.")
    else:
        try:
            final_image_path = create_montage(sample_selfie, sample_tie, output_dir)
            print(f"مونتاژ با موفقیت در مسیر زیر ذخیره شد: {final_image_path}")
            
            # نمایش تصویر ذخیره شده برای بررسی بصری
            result_img = cv2.imread(final_image_path)
            cv2.imshow('Montage Result', result_img)
            print("پنجره تصویر را ببندید تا برنامه تمام شود.")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"خطایی در حین پردازش تصویر رخ داد: {e}")
