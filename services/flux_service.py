import os
import requests
import base64
import time

# خواندن متغیرها از فایل .env
# مطمئن شوید کتابخانه python-dotenv نصب است: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()

FLUX_API_KEY = os.getenv("FLUX_API_KEY")
FLUX_API_URL = os.getenv("FLUX_API_URL")

# این همان Endpoint ای است که در مستندات پیدا کردیم
FLUX_KONTEXT_ENDPOINT = "/v1/flux-kontext-pro"

def image_to_base64(image_path: str) -> str:
    """یک عکس را از مسیر داده شده خوانده و به رشته Base64 تبدیل می‌کند."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def call_flux_api(montage_path: str, prompt: str) -> str:
    """
    عکس مونتاژ شده و پرامپت را به Flux API ارسال کرده و پس از تکمیل پردازش،
    لینک عکس نهایی را برمی‌گرداند.
    """
    if not FLUX_API_KEY or not FLUX_API_URL:
        raise ValueError("کلید یا URL مربوط به FLUX API در فایل .env تعریف نشده است.")

    full_url = FLUX_API_URL + FLUX_KONTEXT_ENDPOINT
    
    headers = {
        "accept": "application/json",
        "x-key": FLUX_API_KEY,
        "Content-Type": "application/json"
    }

    # تبدیل عکس مونتاژ به Base64
    encoded_image = image_to_base64(montage_path)

    payload = {
        "prompt": prompt,
        "input_image": encoded_image
    }

    # --- مرحله ۱: ارسال درخواست اولیه ---
    print("در حال ارسال درخواست به Flux API...")
    response = requests.post(full_url, json=payload, headers=headers)
    response.raise_for_status() # اگر خطای HTTP رخ داد، متوقف شو
    
    initial_data = response.json()
    polling_url = initial_data.get('polling_url')
    request_id = initial_data.get('id')
    
    if not polling_url:
        raise ConnectionError("پاسخ اولیه از API فاقد polling_url بود.")

    print(f"درخواست با موفقیت ارسال شد. ID: {request_id}")

    # --- مرحله ۲: پیگیری نتیجه تا زمان آماده شدن ---
    print("در حال پیگیری نتیجه...")
    while True:
        polling_response = requests.get(polling_url, headers={"x-key": FLUX_API_KEY})
        polling_response.raise_for_status()
        
        result_data = polling_response.json()
        status = result_data.get('status')
        print(f"وضعیت فعلی: {status}")

        if status == "Ready":
            final_image_url = result_data.get('result', {}).get('sample')
            if not final_image_url:
                raise ConnectionError("پردازش با موفقیت انجام شد ولی لینک عکس نهایی یافت نشد.")
            print("پردازش با موفقیت تمام شد.")
            return final_image_url
        
        elif status in ["Error", "Failed"]:
            raise ConnectionError(f"پردازش عکس با خطا مواجه شد: {result_data}")

        # 2 ثانیه صبر قبل از تلاش مجدد
        time.sleep(2)


# --- بخش تست مستقل ---
if __name__ == '__main__':
    # این بخش برای تست مستقیم این فایل است
    # یک فایل مونتاژ شده از مرحله قبل باید در این مسیر موجود باشد
    test_montage_path = 'user_uploads/montage_output.png'
    test_prompt = "A photorealistic high-quality photo of a man wearing this tie, sharp focus, studio lighting"

    if not os.path.exists(test_montage_path):
        print(f"خطا: فایل تست در مسیر {test_montage_path} یافت نشد.")
        print("لطفا ابتدا ماژول image_processor.py را با موفقیت اجرا کنید.")
    else:
        try:
            final_url = call_flux_api(test_montage_path, test_prompt)
            print("\n--- نتیجه نهایی ---")
            print(f"لینک عکس آماده شده: {final_url}")
            print("این لینک تا ۱۰ دقیقه معتبر است. آن را در مرورگر خود باز کنید.")
        except Exception as e:
            print(f"\nخطایی در ارتباط با API رخ داد: {e}")
