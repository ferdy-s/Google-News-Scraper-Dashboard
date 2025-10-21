import os
import csv
import glob
import subprocess
import requests
from docx import Document
from datetime import datetime

# === 1. Input Keyword / Kategori dari User ===
focus_keyword = input("Masukkan keyword atau kategori berita: ").strip()
max_articles = input("Maksimal jumlah artikel (default 30): ").strip()
if not max_articles:
    max_articles = 30
else:
    max_articles = int(max_articles)

output_dir = "output"

# === 2. Jalankan Scraping dengan NewsCrap ===
print(f"🔎 Scraping berita untuk keyword: {focus_keyword} ...")
subprocess.run([
    "python", "news_scrap.py",
    focus_keyword,
    "--max-articles", str(max_articles),
    "--output-format", "csv",
    "--output-dir", output_dir
])

# === 3. Cari file CSV hasil terbaru ===
csv_files = sorted(glob.glob(f"{output_dir}/news_*.csv"))
if not csv_files:
    print("❌ Tidak ada hasil scrap ditemukan.")
    exit()
latest_csv = csv_files[-1]

# === 4. Baca isi CSV untuk judul & snippet ===
titles, snippets = [], []
with open(latest_csv, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("title"): titles.append(row["title"])
        if row.get("snippet"): snippets.append(row["snippet"])

# === 5. Ambil Related Search dari Google Suggest ===
related = []
try:
    r = requests.get(
        f"https://www.google.com/complete/search?client=firefox&q={focus_keyword}"
    )
    if r.status_code == 200:
        suggestions = r.json()[1]
        related = suggestions[:5]
except Exception as e:
    print("⚠️ Gagal ambil related search:", e)

# === 6. Bangun Dokumen Word ===
doc = Document()

# Judul
judul = f"Tren {focus_keyword.capitalize()} {datetime.now().year}: Peluang, Manfaat, dan Strategi"
doc.add_heading(judul, 0)

# Pembuka dengan lokasi & tanggal
lokasi = "Jakarta"
tanggal = datetime.now().strftime("%d %B %Y")
doc.add_paragraph(f"{lokasi}, {tanggal} — ")

# Penjelasan awal
doc.add_paragraph(
    f"Permintaan akan {focus_keyword} semakin meningkat seiring transformasi digital di Indonesia. "
    "Berbagai media melaporkan tren terbaru yang menegaskan bahwa topik ini kini menjadi sorotan utama "
    "dalam mendukung pertumbuhan ekonomi kreatif dan daya saing bisnis."
)

# Kutipan tokoh/ahli (placeholder)
doc.add_paragraph(
    f"Menurut pakar teknologi informasi, Dr. Andi Prasetyo: "
    f"“{focus_keyword.capitalize()} bukan sekadar tren, melainkan fondasi penting "
    "bagi perusahaan yang ingin bertahan di era digital.”"
)

# Subjudul 1: Apa Itu
doc.add_heading(f"Apa Itu {focus_keyword.capitalize()}?", level=1)
doc.add_paragraph(
    f"{focus_keyword.capitalize()} adalah layanan profesional untuk membantu bisnis "
    "mengembangkan aplikasi sesuai kebutuhan, baik Android, iOS, maupun web."
)

# Subjudul 2: Manfaat
doc.add_heading(f"Manfaat {focus_keyword.capitalize()}", level=1)
doc.add_paragraph(
    "- Meningkatkan efisiensi operasional\n"
    "- Memberikan pengalaman pelanggan yang lebih baik\n"
    "- Membuka peluang pasar digital baru\n"
    "- Meningkatkan brand value perusahaan"
)

# Subjudul 3: Langkah Memulai
doc.add_heading("Langkah Memulai", level=1)
doc.add_paragraph(
    "1. Tentukan kebutuhan bisnis\n"
    "2. Pilih software house yang berpengalaman\n"
    "3. Buat requirement aplikasi yang jelas\n"
    "4. Uji coba prototipe\n"
    "5. Rencanakan maintenance & update berkala"
)

# Subjudul 4: Tools
doc.add_heading("Tools & Teknologi Populer", level=1)
doc.add_paragraph(
    "Beberapa teknologi yang sering digunakan dalam pengembangan aplikasi adalah:\n"
    "- Flutter\n"
    "- React Native\n"
    "- Kotlin\n"
    "- Laravel / Node.js\n"
)

# Subjudul 5: Penutup
doc.add_heading("Penutup", level=1)
doc.add_paragraph(
    f"Dari rangkuman berita terbaru, {focus_keyword} terbukti menjadi sektor potensial "
    "yang mendukung percepatan digitalisasi di Indonesia. Dengan strategi yang tepat, "
    "bisnis dapat memaksimalkan peluang dan menghadapi tantangan global."
)

# Related Search
if related:
    doc.add_heading("Related Search", level=1)
    for r in related:
        doc.add_paragraph(f"- {r}")

# === 7. Simpan Dokumen Word ===
output_file = f"Artikel_{focus_keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"
doc.save(output_file)

print(f"✅ Artikel SEO berhasil dibuat → {output_file}")
