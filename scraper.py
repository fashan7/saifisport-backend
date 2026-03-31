"""
Saifi Sport Website Scraper — v3
===================================
6-digit SKU system:
  - Site has 4-digit SKU (e.g. 1003) → extend to 6 digits: 100301, 100302...
  - Site has no SKU → generate from category prefix map: 100101, 100102...

Usage:
  python scraper.py --dry-run     # test, no upload
  python scraper.py               # full run
"""

import requests, json, time, re, os, sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ── Config ────────────────────────────────────────────────────────────────────
BASE_SITE      = "https://saifisport.com"
API_BASE       = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL    = "fashanzak4@gmail.com"        # ← change
ADMIN_PASSWORD = "Nahsaf#1997"          # ← change
DELAY          = 1.5

# ── SKU prefix map ────────────────────────────────────────────────────────────
# 4-digit prefix per subcategory (matches existing site pattern)
# Full 6-digit SKU = PREFIX + 2-digit sequence (01-99)
SKU_PREFIX = {
    # Fight Gear
    "boxing gloves":              "1001",
    "grappling gloves":           "1201",
    "head guards":                "1401",
    "shin in steps":              "2001",
    "chest guards":               "2101",
    "focus mitts":                "1301",
    "belly pads":                 "2003",
    "thai pads":                  "1501",
    "groin gaurds":               "1910",
    "punching bags":              "1703",
    "speed balls":                "1803",
    "double end balls":           "2301",
    "hand wraps":                 "2201",
    # Martial Arts
    "karate uniforms":            "3001",
    "taekwondo uniforms":         "3103",
    "judo uniforms":              "3201",
    "jiu jitsu uniforms":         "3301",
    "karate gloves":              "3401",
    "taekwondo gloves":           "3501",
    "belts":                      "3601",
    "weight lifting gloves":      "3701",
    "weight lifting belts":       "3800",
    "baseball uniforms":          "3901",
    "basketball uniforms":        "4001",
    "american football uniforms": "4104",
    "goal keeper uniforms":       "4201",
    "rugby uniforms":             "4304",
    "t-shirts":                   "4401",
    "polo shirts":                "4501",
    "sweat shirts":               "5101",
    "compression shirts":         "5201",
    "bomber jackets":             "4701",
    "varsity jackets":            "4801",
    "puffer jackets":             "4901",
    "wind breaker jackets":       "5001",
    "fitness bra":                "5305",
    "fitness leggings":           "5401",
    "fitness shorts":             "5501",
    "rash guards":                "5601",
    "mma shorts":                 "5701",
    "thai shorts":                "5801",
    "trousers":                   "5903",
}

# Per-prefix sequence counters (reset each run)
sku_counters = {}

def next_sku(prefix):
    """Return next 6-digit SKU for the given 4-digit prefix."""
    if prefix not in sku_counters:
        sku_counters[prefix] = 1
    seq = sku_counters[prefix]
    sku_counters[prefix] += 1
    return f"{prefix}{seq:02d}"

def build_sku(site_sku, category_name):
    """
    Priority:
    1. Site has 4-digit SKU → extend to 6 digits (100301, 100302...)
    2. Site SKU is already 5+ chars → use as-is
    3. No site SKU → generate from category map
    """
    s = (site_sku or "").strip()

    if s and re.match(r'^\d{4}$', s):
        # 4-digit site SKU — extend with sequence
        return next_sku(s)

    if s and len(s) >= 5:
        # Already a longer SKU — use it
        return s

    # No usable SKU — generate from category
    prefix = SKU_PREFIX.get((category_name or "").lower(), "9901")
    return next_sku(prefix)


# ── HTTP helpers ──────────────────────────────────────────────────────────────
session = requests.Session()
session.headers["User-Agent"] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/120 Safari/537.36"
)

def get_soup(url):
    time.sleep(DELAY)
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")

def clean(text):
    return re.sub(r'\s+', ' ', text or "").strip()


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_token():
    r = requests.post(f"{API_BASE}/auth/login/",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    r.raise_for_status()
    print("✓ Authenticated")
    return r.json()["access"]

def hdrs(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Category upload ───────────────────────────────────────────────────────────
def upload_categories(cats, token):
    print("\n📂 Uploading categories...")
    id_map = {}

    def slug(name, sfx=""):
        base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        return f"{base}-{sfx}" if sfx else base

    def upload(cat, parent_id, level):
        name = cat["name"]
        pl   = {
            "name":   {l: name for l in ["fr","en","de","es","sv"]},
            "slug":   slug(name) if level == 1 else slug(name, str(int(time.time()*1000))[-6:]),
            "level":  level,
        }
        if parent_id:
            pl["parent"] = parent_id

        for attempt in range(2):
            r = requests.post(f"{API_BASE}/categories/", json=pl, headers=hdrs(token), timeout=15)
            if r.status_code == 201:
                did = r.json()["id"]
                id_map[name.lower()] = did
                print(f"   {'  '*(level-1)}✓ L{level}: {name} → {did}")
                return did
            if attempt == 0 and r.status_code == 400:
                pl["slug"] = slug(name, str(int(time.time()*1000)))
            else:
                print(f"   ⚠️  {name}: {r.text[:60]}")
                return None
        return None

    for cat in cats:
        cid = upload(cat, None, 1)
        for sub in cat.get("children", []):
            if sub.get("url") == "#":
                sid = upload(sub, cid, 2)
                for ss in sub.get("children", []):
                    upload(ss, sid, 3)
            else:
                sid = upload(sub, cid, 2)
                for ss in sub.get("children", []):
                    upload(ss, sid, 3)

    print(f"   ✓ {len(id_map)} categories")
    return id_map


def fetch_django_cats(token):
    id_map = {}
    for lvl in [1, 2, 3]:
        r = requests.get(f"{API_BASE}/categories/?level={lvl}", headers=hdrs(token), timeout=15)
        for cat in r.json():
            name = cat.get("name", "")
            if isinstance(name, dict):
                name = name.get("fr") or name.get("en") or ""
            id_map[name.lower()] = cat["id"]
    print(f"   ✓ {len(id_map)} Django categories loaded")
    return id_map


# ── Product URL collection ────────────────────────────────────────────────────
def get_product_urls(cat_url):
    urls = set()
    for page in range(1, 50):
        url = f"{cat_url}page/{page}/" if page > 1 else cat_url
        try:
            soup = get_soup(url)
        except Exception:
            break

        links = (
            soup.select("ul.products li.product a.woocommerce-loop-product__link") or
            soup.select(".product-grid-item a.product-image-link") or
            soup.select("ul.products li.product .wd-entities-title a") or
            soup.select("li.product a[href*='/product/']")
        )
        if not links:
            break

        new = {a["href"] for a in links if "/product/" in a.get("href", "")}
        if not new or new.issubset(urls):
            break

        urls.update(new)
        print(f"      Page {page}: +{len(new)}")

        if not soup.select_one("a.next.page-numbers"):
            break
    return list(urls)


# ── Scrape single product ─────────────────────────────────────────────────────
def scrape_product(url):
    try:
        soup = get_soup(url)
    except Exception:
        return None

    p = {"url": url}

    h1 = (soup.select_one("h1.product_title") or
          soup.select_one("h1.wd-entities-title") or
          soup.select_one("h1.entry-title"))
    p["name"] = clean(h1.get_text()) if h1 else ""

    sku_el       = soup.select_one("span.sku")
    p["site_sku"] = clean(sku_el.get_text()) if sku_el else ""

    short = soup.select_one("div.woocommerce-product-details__short-description")
    p["short_html"] = str(short) if short else ""

    long_el = (soup.select_one("div.woocommerce-Tabs-panel--description .wc-tab-inner") or
               soup.select_one(".woocommerce-Tabs-panel--description"))
    p["desc_html"] = str(long_el) if long_el else p["short_html"]

    imgs, seen = [], set()
    for fig in soup.select(".woocommerce-product-gallery__image"):
        a = fig.select_one("a")
        src = (a.get("href") or a.get("data-large_image")) if a else None
        if not src:
            img = fig.select_one("img")
            src = img.get("data-large_image") or img.get("src") if img else None
        if src and src.startswith("http") and src not in seen:
            seen.add(src)
            imgs.append(src)
    p["image_urls"] = imgs[:5]
    return p


# ── Image upload ──────────────────────────────────────────────────────────────
def upload_image(url, token):
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        fname = os.path.basename(urlparse(url).path) or "img.jpg"
        ct    = r.headers.get("Content-Type", "image/jpeg").split(";")[0]
        res   = requests.post(
            f"{API_BASE}/media/upload/",
            files={"file": (fname, r.content, ct)},
            data={"aspect_ratio": "1:1"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        if res.status_code == 201:
            return res.json()["id"]
    except Exception as e:
        print(f"         ⚠️  {e}")
    return None


# ── Product upload ────────────────────────────────────────────────────────────
def upload_product(prod, token, cat_name, cat_id, sub_id):
    name = prod.get("name", "")
    if not name:
        return None, None

    sku = build_sku(prod.get("site_sku"), cat_name)

    image_ids = []
    for img_url in prod.get("image_urls", []):
        print(f"         📸 {os.path.basename(urlparse(img_url).path)}")
        mid = upload_image(img_url, token)
        if mid:
            image_ids.append(mid)

    pl = {
        "name":        {l: name for l in ["fr","en","de","es","sv"]},
        "sku":         sku,
        "description": {"fr": prod.get("desc_html",""), "en": prod.get("desc_html","")},
        "material":    {"fr": "", "en": ""},
        "available_materials": ["cowhide","buffalo","pu","pvc"],
        "moq": 50, "featured": False,
        "category": cat_id, "subcategory": sub_id,
        "product_type": None, "image_ids": image_ids,
    }

    for attempt in range(2):
        r = requests.post(f"{API_BASE}/products/", json=pl, headers=hdrs(token), timeout=20)
        if r.status_code == 201:
            return r.json()["id"], sku
        if "sku" in r.text.lower() and attempt == 0:
            pl["sku"] = build_sku("", cat_name)  # generate fresh
        else:
            print(f"      ⚠️  {r.text[:100]}")
            return None, sku
    return None, sku


# ── Recursive processor ───────────────────────────────────────────────────────
def process(cats, token, django_cats, stats, parent_name=None, parent_id=None):
    for cat in cats:
        name     = cat["name"]
        url      = cat.get("url","")
        children = cat.get("children",[])
        level    = cat.get("level",1)
        cat_id   = django_cats.get(name.lower())

        if url == "#" or not url or children:
            process(children, token, django_cats, stats,
                    parent_name=name, parent_id=cat_id)
            continue

        display = f"{parent_name} → {name}" if parent_name else name
        print(f"\n   📁 {display}")

        scrape_cat_id = parent_id if level == 2 else (
            django_cats.get((parent_name or "").lower()) if level == 3 else cat_id
        )
        scrape_sub_id = cat_id if level in [2, 3] else None

        for prod_url in get_product_urls(url):
            prod = scrape_product(prod_url)
            if not prod or not prod.get("name"):
                stats["failed"] += 1
                continue

            site_sku = prod.get("site_sku") or "—"
            print(f"\n      📦 {prod['name']}")
            print(f"         Site SKU: {site_sku}  "
                  f"| Images: {len(prod.get('image_urls',[]))}")

            pid, final_sku = upload_product(
                prod, token, name, scrape_cat_id, scrape_sub_id
            )
            if pid:
                stats["uploaded"] += 1
                stats["log"].append({
                    "name":     prod["name"],
                    "site_sku": site_sku,
                    "sku":      final_sku,
                    "category": display,
                })
                print(f"         ✓ ID: {pid} | SKU: {final_sku}")
            else:
                stats["failed"] += 1


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Saifi Sport Scraper v3")
    print("=" * 60)
    token = get_token()
    cats  = json.load(open("scraped_categories.json"))
    upload_categories(cats, token)
    django_cats = fetch_django_cats(token)
    print("\n🛍️  Scraping products...")
    stats = {"uploaded": 0, "failed": 0, "log": []}
    process(cats, token, django_cats, stats)
    json.dump(stats["log"], open("sku_log.json","w"), indent=2, ensure_ascii=False)
    print(f"\n✅  Uploaded: {stats['uploaded']}  Failed: {stats['failed']}")
    print(f"   SKU log → sku_log.json")


# ── Dry run ───────────────────────────────────────────────────────────────────
def dry_run():
    print("DRY RUN — no upload")
    cats = json.load(open("scraped_categories.json"))

    def first_leaf(cs):
        for c in cs:
            if c.get("url") and c["url"] != "#" and not c.get("children"):
                return c
            r = first_leaf(c.get("children",[]))
            if r: return r
        return None

    leaf = first_leaf(cats)
    if not leaf: return

    print(f"\nCategory: {leaf['name']}")
    urls = get_product_urls(leaf["url"])
    print(f"Product URLs found: {len(urls)}\n")

    print("SKU preview:")
    for url in urls[:5]:
        prod = scrape_product(url)
        if not prod: continue
        site_sku = prod.get("site_sku") or ""
        our_sku  = build_sku(site_sku, leaf["name"])
        print(f"  {prod['name']}")
        print(f"    Site SKU: '{site_sku}' → Our SKU: {our_sku}")
        print(f"    Images: {len(prod.get('image_urls',[]))}")
        for img in prod.get("image_urls",[]):
            print(f"      {img}")


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        dry_run()
    else:
        main()