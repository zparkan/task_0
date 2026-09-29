"""
دریافت اطلاعات ۵۰ کتاب تصادفی و متنوع از API عمومی Open Library،
فیلتر کتاب‌هایی که سال انتشارشان بعد از ۲۰۰۰ است،
و ذخیره در فایل CSV.

نصب نیازمندی:  pip install requests
اجرا:          python fetch_books.py
"""

import csv
import random
import sys

import requests

# ---------- تنظیمات ----------
BOOK_LIMIT = 50              # تعداد کل کتاب برای دریافت
BOOKS_PER_SUBJECT = 5        # از هر موضوع چند کتاب بگیریم
MAX_RANDOM_OFFSET = 100      # شروع تصادفی از بین N کتاب اول هر موضوع
YEAR_THRESHOLD = 2000        # فقط کتاب‌های بعد از این سال نگه داشته می‌شن
OUTPUT_FILE = "books.csv"
API_URL = "https://openlibrary.org/search.json"
FIELDS = "key,title,author_name,first_publish_year,publisher,language,number_of_pages_median"

# هر بار اجرا، موضوع‌ها به‌صورت تصادفی از این لیست انتخاب می‌شن
# (می‌ توان موضوع‌های دلخواه هم اضافه کرد یا موضاعات فعلی را حذف نمود))
SUBJECTS = [
    "history", "science fiction", "fantasy", "cooking", "philosophy",
    "psychology", "biology", "physics", "mathematics", "art",
    "music", "travel", "business", "economics", "poetry",
    "mystery", "romance", "horror", "biography", "politics",
    "religion", "sports", "computers", "medicine", "architecture",
    "photography", "gardening", "education", "sociology", "astronomy",
]
# ------------------------------


def fetch_books(subject: str, limit: int, offset: int) -> list[dict]:
    """کتاب‌های یک موضوع را از Open Library می‌گیرد."""
    params = {
        "q": f'subject:"{subject}"',
        "limit": limit,
        "offset": offset,
        "fields": FIELDS,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  خطا برای موضوع «{subject}»: {e} (رد می‌شویم)")
        return []
    return response.json().get("docs", [])


def clean_book(doc: dict, subject: str) -> dict:
    """فقط فیلدهای لازم را برمی‌دارد و به شکل مرتب درمی‌آورد."""
    return {
        "title": doc.get("title", ""),
        "subject": subject,
        "authors": ", ".join(doc.get("author_name", [])[:3]),
        "first_publish_year": doc.get("first_publish_year"),
        "publisher": (doc.get("publisher") or [""])[0],
        "languages": ", ".join(doc.get("language", [])[:3]),
        "pages": doc.get("number_of_pages_median", ""),
        "url": f"https://openlibrary.org{doc['key']}" if "key" in doc else "",
    }


def collect_random_books() -> list[dict]:
    """از موضوع‌های تصادفی کتاب جمع می‌کند تا به BOOK_LIMIT برسد."""
    subjects = SUBJECTS.copy()
    random.shuffle(subjects)  # ترتیب موضوع‌ها را بُر می‌زند

    books = []
    seen_keys = set()  # برای جلوگیری از کتاب تکراری

    for subject in subjects:
        if len(books) >= BOOK_LIMIT:
            break

        offset = random.randint(0, MAX_RANDOM_OFFSET)
        print(f"موضوع: {subject} (شروع از {offset})")
        docs = fetch_books(subject, BOOKS_PER_SUBJECT, offset)

        for doc in docs:
            key = doc.get("key")
            if key in seen_keys or len(books) >= BOOK_LIMIT:
                continue
            seen_keys.add(key)
            books.append(clean_book(doc, subject))

    random.shuffle(books)  # ترتیب کتاب‌ها هم تصادفی بشه
    return books


def main() -> None:
    books = collect_random_books()
    print(f"\n{len(books)} کتاب دریافت شد.")

    if not books:
        sys.exit("هیچ کتابی دریافت نشد. اتصال اینترنت را بررسی کن.")

    # فیلتر: فقط سال انتشار بعد از ۲۰۰۰ (کتاب‌های بدون سال حذف می‌شن)
    filtered = [
        b for b in books
        if b["first_publish_year"] and b["first_publish_year"] > YEAR_THRESHOLD
    ]
    filtered.sort(key=lambda b: b["first_publish_year"])
    print(f"{len(filtered)} کتاب بعد از سال {YEAR_THRESHOLD} منتشر شده‌اند.")

    if not filtered:
        print("هیچ کتابی با این شرط پیدا نشد؛ فایلی ساخته نشد.")
        return

    # utf-8-sig باعث می‌شه اکسل متن فارسی/غیرانگلیسی رو درست نشون بده
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(filtered[0].keys()))
        writer.writeheader()
        writer.writerows(filtered)

    print(f"ذخیره شد: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
