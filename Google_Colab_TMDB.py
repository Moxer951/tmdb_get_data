# نصب کتابخانه‌ها و ابزار لازم
!pip install pandas openpyxl --quiet
!apt-get install -y p7zip-full --quiet

import os
import requests
import pandas as pd
from google.colab import drive

# اتصال به گوگل درایو فقط برای ذخیره ZIP نهایی
drive.mount('/content/drive')

# پارامترها
API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/original"
mode = 6  # تغییر بده بین 1 تا 6

endpoint_map = {
    1: ("movie/now_playing", "movie"),
    2: ("tv/airing_today", "tv"),
    3: ("tv/on_the_air", "tv"),
    4: ("movie/upcoming", "movie"),
    5: ("trending/all/day", "all"),
    6: ("trending/all/week", "all"),
}

endpoint, default_type = endpoint_map.get(mode, (None, None))
if not endpoint:
    raise ValueError("عدد ایندکس نامعتبر است (باید بین 1 تا 6 باشد).")

# مسیرهای موقت برای دو زبان
base_temp_path = "/content/tmdb_temp"
languages = {
    "fa": "fa-IR",
    "en": "en-US"
}

def fetch_data_and_images(lang_code, lang_name):
    print(f"در حال پردازش زبان: {lang_name} ...")
    lang_path = os.path.join(base_temp_path, f"Data_{lang_name}")
    excel_path = os.path.join(lang_path, "excel")
    images_path = os.path.join(lang_path, "images")
    os.makedirs(excel_path, exist_ok=True)
    os.makedirs(images_path, exist_ok=True)

    url = f"{BASE_URL}/{endpoint}?api_key={API_KEY}&language={lang_code}&page=1"
    response = requests.get(url)
    results = response.json().get("results", [])[:20]

    data_list = []
    for idx, item in enumerate(results, start=1):
        item_id = item.get("id")
        item_type = default_type if default_type != "all" else item.get("media_type")

        detail_url = f"{BASE_URL}/{item_type}/{item_id}?api_key={API_KEY}&language={lang_code}&append_to_response=credits,videos"
        detail = requests.get(detail_url).json()

        poster_path = detail.get("poster_path")
        poster_filename = f"{idx}.jpg"
        if poster_path:
            try:
                poster_url = IMG_BASE_URL + poster_path
                poster_data = requests.get(poster_url).content
                with open(os.path.join(images_path, poster_filename), "wb") as f:
                    f.write(poster_data)
            except:
                poster_filename = "خطا در دانلود"
        else:
            poster_filename = "ندارد"

        duration = "نامشخص"
        if item_type == "movie":
            duration = detail.get("runtime", "نامشخص")
        elif item_type == "tv":
            run_times = detail.get("episode_run_time")
            if isinstance(run_times, list) and run_times:
                duration = run_times[0]

        crew = detail.get("credits", {}).get("crew", [])
        director = next((c["name"] for c in crew if c.get("job") in ["Director", "Creator", "Executive Producer"]), "نامشخص")

        cast = detail.get("credits", {}).get("cast", [])
        top_cast = ", ".join([a["name"] for a in cast[:3]]) if cast else "ندارد"

        row = {
            "ردیف": idx,
            "نوع": item_type,
            "عنوان": detail.get("title") or detail.get("name", "نامشخص"),
            "تاریخ انتشار": detail.get("release_date") or detail.get("first_air_date", "نامشخص"),
            "ژانرها": ", ".join([g["name"] for g in detail.get("genres", [])]),
            "امتیاز": detail.get("vote_average", "نامشخص"),
            "تعداد رأی": detail.get("vote_count", "نامشخص"),
            "مدت زمان": duration,
            "کشورها": ", ".join([c["name"] for c in detail.get("production_countries", [])]),
            "زبان اصلی": detail.get("original_language", "نامشخص"),
            "کارگردان / سازنده": director,
            "بازیگران": top_cast,
            "خلاصه": detail.get("overview", "ندارد"),
            "پوستر": poster_filename,
        }
        data_list.append(row)

    df = pd.DataFrame(data_list)
    excel_file = os.path.join(excel_path, f"tmdb_data_{lang_name}.xlsx")
    df.to_excel(excel_file, index=False)
    return lang_path

# اجرای دو زبان و گرفتن مسیر هر کدوم
paths = []
for lang_name, lang_code in languages.items():
    p = fetch_data_and_images(lang_code, lang_name)
    paths.append(p)

# ساخت فایل زیپ نهایی با پوشه‌های Data_Fa و Data_En داخلش
zip_path = "/content/drive/MyDrive/TMDB_Data_Fa_En.7z"
os.system(f'7z a -mx9 "{zip_path}" ' + " ".join(paths))

print(f"✅ فایل زیپ دو زبانه با موفقیت ساخته و در گوگل درایو ذخیره شد:\n{zip_path}")

#---------------LOG----------
import datetime

# متن لاگ (مثال، می‌تونی هر چیزی که دلت خواست اضافه کنی)
log_text = f"""
TMDB Data Fetching Log
زمان شروع: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
نوع محتوا (mode): {mode}
کل داده‌های پردازش شده: {len(data_list)}
فایل ZIP ساخته شده: {zip_path}

توضیحات:
- داده‌ها برای زبان‌ها: {', '.join(languages.keys())}
- محل ذخیره موقت: {base_temp_path}
"""

# مسیر فایل لاگ کنار فایل زیپ
log_file_path = zip_path.replace(".7z", "_log.txt")

# ذخیره لاگ در فایل
with open(log_file_path, "w", encoding="utf-8") as f:
    f.write(log_text)

print(f"✅ فایل لاگ ذخیره شد: {log_file_path}")
