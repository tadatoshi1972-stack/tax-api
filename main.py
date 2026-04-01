from fastapi import FastAPI, Query, HTTPException
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, quote

app = FastAPI()

# ======================
# e-Gov 法令検索
# ======================

@app.get("/search_law")
def search_law(query: str):
    url = "https://laws.e-gov.go.jp/api/2/laws"
    params = {"keyword": query}
    r = requests.get(url, params=params)
    data = r.json()

    results = []
    for item in data.get("laws", [])[:5]:
        results.append({
            "law_id": item.get("lawId"),
            "law_name": item.get("lawName")
        })

    return {"results": results}


@app.get("/get_law")
def get_law(law_id: str):
    url = f"https://laws.e-gov.go.jp/api/2/law_data/{law_id}"
    r = requests.get(url)

    root = ET.fromstring(r.text)
    texts = []

    for elem in root.iter():
        if elem.text:
            texts.append(elem.text.strip())

    return {"text": "\n".join(texts[:2000])}


# ======================
# 国税庁検索
# ======================

@app.get("/search_nta")
def search_nta(query: str):
    search_url = f"https://www.nta.go.jp/search.htm?qt={quote(query)}"
    r = requests.get(search_url)

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    for a in soup.find_all("a"):
        href = a.get("href")
        text = a.get_text(strip=True)

        if href and "nta.go.jp" in href and text:
            results.append({
                "title": text,
                "url": href
            })

    return {"results": results[:5]}


@app.get("/get_nta_page")
def get_nta_page(url: str):
    parsed = urlparse(url)

    if "nta.go.jp" not in parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid domain")

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    texts = []
    for tag in soup.find_all(["h1", "h2", "p", "li"]):
        t = tag.get_text(strip=True)
        if t:
            texts.append(t)

    return {"content": "\n".join(texts[:2000])}
