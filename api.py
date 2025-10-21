#!/usr/bin/env python3
import re
import uvicorn
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

# ==== IMPORT scraper kamu ====
# Sesuaikan nama file modulnya:
from news_scrap import GoogleNewsScraper

# ==== PATH & APP ====
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Google News Scraper API", version="1.0.0")

# (Boleh aktif, tapi same-origin sudah cukup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Serve folder hasil ke /files
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")

# (Opsional) serve asset ke /static
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==== MODELS ====
class ScrapeRequest(BaseModel):
    keywords: List[str]
    max_articles: int = 10
    output_format: str = "csv"              # csv|json|sqlite|all
    report_format: Optional[str] = None     # markdown|html|both|None
    domain_filter: Optional[str] = None
    verbose: bool = False


# ==== PAGES ====
@app.get("/")
def root():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico")
def favicon():
    fav = BASE_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(fav)
    return RedirectResponse(url="/docs")


# ==== API ====
@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now().isoformat()}

@app.post("/scrape")

def scrape(req: ScrapeRequest):
    """
    Jalankan scraping untuk daftar keyword.
    Mengembalikan ringkasan hasil + link file bila dibuat.
    """
    scraper = GoogleNewsScraper(verbose=req.verbose, proxy_list=[], user_agents=[])
    all_articles: List[Dict[str, Any]] = []
    file_links: List[str] = []
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    for keyword in req.keywords:
        try:
            articles = scraper.scrape_articles(
                keyword=keyword,
                max_articles=req.max_articles,
                domain_filter=req.domain_filter
            )
            all_articles.extend(articles)

            safe_keyword = re.sub(r'[^\w\-_]', '_', keyword)

            # Output files
            if req.output_format in ("csv", "all"):
                csvf = OUTPUT_DIR / f"news_{safe_keyword}_{ts}.csv"
                scraper.save_to_csv(articles, str(csvf))
                file_links.append(f"/files/{csvf.name}")

            if req.output_format in ("json", "all"):
                jsonf = OUTPUT_DIR / f"news_{safe_keyword}_{ts}.json"
                scraper.save_to_json(articles, str(jsonf))
                file_links.append(f"/files/{jsonf.name}")

            if req.output_format in ("sqlite", "all"):
                dbf = OUTPUT_DIR / f"news_{ts}.db"
                scraper.save_to_sqlite(articles, str(dbf))
                if f"/files/{dbf.name}" not in file_links:
                    file_links.append(f"/files/{dbf.name}")

            # Reports
            if req.report_format in ("markdown", "both"):
                mdf = OUTPUT_DIR / f"report_{safe_keyword}_{ts}.md"
                scraper.export_to_markdown(articles, str(mdf))
                file_links.append(f"/files/{mdf.name}")

            if req.report_format in ("html", "both"):
                htf = OUTPUT_DIR / f"report_{safe_keyword}_{ts}.html"
                scraper.export_to_html(articles, str(htf))
                file_links.append(f"/files/{htf.name}")

        except Exception as e:
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

    return {
        "ok": True,
        "count": len(all_articles),
        "generated_at": datetime.now().isoformat(),
        "files": file_links,
        "articles": all_articles[:200]  # batasi payload
    }

@app.get("/articles")
def get_articles(keyword: str = Query(..., description="Filter berdasarkan keyword yang discrape"),
                 limit: int = 100):
    """
    Ambil dari file JSON terbaru sesuai keyword (read cepat).
    """
    safe_keyword = re.sub(r'[^\w\-_]', '_', keyword)
    pattern = f"news_{safe_keyword}_"
    candidates = sorted(
        [f for f in OUTPUT_DIR.glob("*.json") if f.name.startswith(pattern)],
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not candidates:
        return {"ok": True, "articles": []}
    import json
    with open(candidates[0], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {"ok": True, "articles": data[:limit]}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
