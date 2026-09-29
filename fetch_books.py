"""
دریافت اطلاعات ۵۰ کتاب از API عمومی Open Library،
فیلتر کتاب‌هایی که سال انتشارشان بعد از ۲۰۰۰ است،
و ذخیره در فایل CSV.

نصب نیازمندی:  pip install requests
اجرا:          python fetch_books.py
"""

import csv
import sys

import requests

# ---------- تنظیمات ----------
SEARCH_QUERY = "python"      # موضوع/عبارت جستجو (هر چیزی می‌تونی بذاری)
BOOK_LIMIT = 50              # تعداد کتاب برای دریافت
YEAR_THRESHOLD = 2000        # فقط کتاب‌های بعد از این سال نگه داشته می‌شن
OUTPUT_FILE = "books.csv"
API_URL = "https://openlibrary.org/search.json"
FIELDS = "key,title,author_name,first_publish_year,publisher,language,number_of_pages_median"
# ------------------------------


def fetch_books(query: str, limit: int) -> list[dict]:
    """کتاب‌ها را از Open Library می‌گیرد."""
    params = {"q": query, "limit": limit, "fields": FIELDS}
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"خطا در ارتباط با API: {e}")
    return response.json().get("docs", [])


def clean_book(doc: dict) -> dict:
    """فقط فیلدهای لازم را برمی‌دارد و به شکل مرتب درمی‌آورد."""
    return {
        "title": doc.get("title", ""),
        "authors": ", ".join(doc.get("author_name", [])[:3]),
        "first_publish_year": doc.get("first_publish_year"),
        "publisher": (doc.get("publisher") or [""])[0],
        "languages": ", ".join(doc.get("language", [])[:3]),
        "pages": doc.get("number_of_pages_median", ""),
        "url": f"https://openlibrary.org{doc['key']}" if "key" in doc else "",
    }


def main() -> None:
    print(f"در حال دریافت {BOOK_LIMIT} کتاب برای «{SEARCH_QUERY}» ...")
    docs = fetch_books(SEARCH_QUERY, BOOK_LIMIT)
    books = [clean_book(d) for d in docs]
    print(f"{len(books)} کتاب دریافت شد.")

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
