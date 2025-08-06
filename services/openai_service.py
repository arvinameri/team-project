# file: services/openai_service.py
import os
import openai
from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_style_advice(user_context: dict, available_categories: list[str]) -> list[str]:
    """
    اطلاعات کاربر و لیست دسته‌بندی‌های موجود را به سرویس OpenAI ارسال کرده
    و لیستی از دسته‌بندی‌های مناسب را برمی‌گرداند.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("کلید OPENAI_API_KEY در فایل .env تعریف نشده است.")
    
    categories_str = ", ".join(available_categories)
    
    system_prompt = f"""You are a professional fashion stylist specializing in men's ties. 
    Your task is to recommend tie categories from a predefined list based on user's needs. 
    The available categories are: [{categories_str}]. 
    Only respond with the names of the recommended categories from this list, separated by commas. 
    Do not add any extra text, explanation or greeting."""

    user_prompt = f"The user is looking for a tie for the following context: {user_context}. Which categories do you recommend?"

    try:
        response = client.chat.completions.create(
            # --- تغییر در این خط ---
            model="gpt-4o",
            # --------------------
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5
        )
        recommended_str = response.choices[0].message.content
        # خروجی را تمیز کرده و فقط دسته‌بندی‌های معتبر را برمی‌گردانیم
        recommended_list = [cat.strip() for cat in recommended_str.split(',') if cat.strip() in available_categories]
        return recommended_list
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return [] # در صورت خطا، لیست خالی برگردان
