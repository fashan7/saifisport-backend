"""
Saifi Sport — Bulk Translation Script
======================================
Three separate commands:

  python translate.py cats        → wipe all langs except EN on categories, retranslate
  python translate.py prod-names  → wipe all langs except EN on product names, retranslate
  python translate.py prod-desc   → only where FR desc == EN desc (not translated), fix FR

Add --dry-run to any command to preview without saving:
  python translate.py cats --dry-run
  python translate.py prod-names --dry-run
  python translate.py prod-desc --dry-run
"""

import requests, time, sys, re
from urllib.parse import quote

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE       = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL    = "fashanzak4@gmail.com"#"your@email.com"
ADMIN_PASSWORD = "Nahsaf#1997" 

TARGET_LANGS    = ["fr", "de", "es", "sv", "it", "nl"]
DELAY_TRANSLATE = 0.4   # seconds between Google Translate calls
DELAY_API       = 0.1   # seconds between Django PATCH calls

COMMAND = sys.argv[1] if len(sys.argv) > 1 else None
DRY_RUN = "--dry-run" in sys.argv


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_token():
    r = requests.post(f"{API_BASE}/auth/login/",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                      timeout=10)
    r.raise_for_status()
    print("✓ Authenticated")
    return r.json()["access"]

def hdrs(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Google Translate (free public endpoint) ───────────────────────────────────
def gtranslate(text, target_lang):
    if not text or not text.strip():
        return ""
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl={target_lang}&dt=t&q={quote(text)}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return "".join(item[0] for item in r.json()[0] if item[0])
    except Exception as e:
        print(f"      ⚠️  Translate error [{target_lang}]: {e}")
        return ""


def strip_html(html):
    return re.sub(r'<[^>]+>', ' ', html or "").strip()


# ── Fetch helpers ─────────────────────────────────────────────────────────────
def fetch_all(url, token):
    r = requests.get(url, headers=hdrs(token), timeout=15)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    results = data.get("results", [])
    while data.get("next"):
        r = requests.get(data["next"], headers=hdrs(token), timeout=15)
        data = r.json()
        results.extend(data.get("results", []))
    return results


def patch(url, payload, token):
    time.sleep(DELAY_API)
    r = requests.patch(url, json=payload, headers=hdrs(token), timeout=15)
    return r


# ── Get EN source from a translations dict ────────────────────────────────────
def get_en(field):
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        return (
            field.get("en") or
            field.get("fr") or
            next((v for v in field.values() if v and str(v).strip()), None)
        ) or ""
    return ""


# ── Build fully translated dict from EN source ────────────────────────────────
def build_translations(en_source, label=""):
    result = {"en": en_source}
    for lang in TARGET_LANGS:
        time.sleep(DELAY_TRANSLATE)
        t = gtranslate(en_source, lang)
        result[lang] = t if t else en_source
        print(f"      [{lang}] {result[lang][:70]}")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 1: translate cats
# Wipe all language values except EN on every category (L1/L2/L3)
# then retranslate EN → FR, DE, ES, SV, IT, NL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def cmd_cats(token):
    print("\n📂 Categories — wipe all langs, retranslate from EN")
    total = updated = skipped = 0

    for level in [1, 2, 3]:
        items = fetch_all(f"{API_BASE}/categories/?level={level}", token)
        print(f"\n   Level {level}: {len(items)} entries")

        for cat in items:
            total += 1
            cid    = cat["id"]
            en_src = get_en(cat.get("name", {}))

            if not en_src.strip():
                print(f"   ⚠️  ID:{cid} — no EN source, skipping")
                skipped += 1
                continue

            print(f"\n   ✎ [{level}] {en_src}")

            new_name = build_translations(en_src)

            if DRY_RUN:
                print(f"      DRY RUN — would update ID:{cid}")
                updated += 1
                continue

            r = patch(f"{API_BASE}/categories/{cid}/", {"name": new_name}, token)
            if r.status_code in [200, 201]:
                updated += 1
                print(f"      ✓ ID:{cid} updated")
            else:
                print(f"      ⚠️  ID:{cid} failed: {r.text[:80]}")
                skipped += 1

    print(f"\n   Result: {total} total | {updated} updated | {skipped} skipped")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 2: translate prod-names
# Wipe all language values except EN on every product name
# then retranslate EN → FR, DE, ES, SV, IT, NL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def cmd_prod_names(token):
    print("\n🛍️  Product names — wipe all langs, retranslate from EN")
    products = fetch_all(f"{API_BASE}/products/", token)
    print(f"   Found {len(products)} products\n")
    total = updated = skipped = 0

    for i, prod in enumerate(products, 1):
        total += 1
        pid    = prod["id"]
        sku    = prod.get("sku", "?")
        en_src = get_en(prod.get("name", {}))

        if not en_src.strip():
            print(f"   [{i}] SKU:{sku} ⚠️  no EN source — skipping")
            skipped += 1
            continue

        print(f"\n   [{i}/{len(products)}] {en_src} (SKU:{sku})")

        new_name = build_translations(en_src)

        if DRY_RUN:
            print(f"      DRY RUN — would update product {pid}")
            updated += 1
            continue

        r = patch(f"{API_BASE}/products/{pid}/", {"name": new_name}, token)
        if r.status_code in [200, 201]:
            updated += 1
            print(f"      ✓ Updated")
        else:
            print(f"      ⚠️  Failed ({r.status_code}): {r.text[:80]}")
            skipped += 1

    print(f"\n   Result: {total} total | {updated} updated | {skipped} skipped")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND 3: translate prod-desc
# Only fix descriptions where FR text == EN text (meaning FR was never translated)
# Retranslates EN → all target languages for those products
# Skips products where FR already differs from EN (already translated)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def cmd_prod_desc(token):
    print("\n📝  Product descriptions — fix where FR == EN (not translated)")
    products = fetch_all(f"{API_BASE}/products/", token)
    print(f"   Found {len(products)} products\n")
    total = updated = skipped = already_ok = 0

    for i, prod in enumerate(products, 1):
        total += 1
        pid   = prod["id"]
        sku   = prod.get("sku", "?")
        desc  = prod.get("description", {})
        name  = get_en(prod.get("name", {})) or sku

        if isinstance(desc, str):
            desc = {"en": desc}
        if not isinstance(desc, dict):
            desc = {}

        en_html = desc.get("en", "")
        fr_html = desc.get("fr", "")
        en_text = strip_html(en_html).strip().lower()
        fr_text = strip_html(fr_html).strip().lower()

        print(f"   [{i}/{len(products)}] {name} (SKU:{sku})")

        # Skip if no EN content
        if not en_text:
            print(f"      ⚠️  No EN description — skipping")
            skipped += 1
            continue

        # Skip if FR already differs from EN (properly translated)
        if fr_text and fr_text != en_text:
            print(f"      ✓ FR already translated — skipping")
            already_ok += 1
            continue

        reason = "FR is empty" if not fr_text else "FR == EN (copy, not translated)"
        print(f"      ↻ {reason}")

        # Translate plain text (strip HTML for input, store as plain text)
        en_source_text = strip_html(en_html)
        new_desc = {"en": en_html}  # keep original EN HTML intact

        for lang in TARGET_LANGS:
            time.sleep(DELAY_TRANSLATE)
            t = gtranslate(en_source_text, lang)
            new_desc[lang] = t if t else en_source_text
            print(f"      [{lang}] {new_desc[lang][:70]}")

        if DRY_RUN:
            print(f"      DRY RUN — would update product {pid}")
            updated += 1
            continue

        r = patch(f"{API_BASE}/products/{pid}/", {"description": new_desc}, token)
        if r.status_code in [200, 201]:
            updated += 1
            print(f"      ✓ Updated")
        else:
            print(f"      ⚠️  Failed ({r.status_code}): {r.text[:80]}")
            skipped += 1

    print(f"\n   Result: {total} total | {updated} updated | "
          f"{already_ok} already translated | {skipped} skipped")


# ── Main ──────────────────────────────────────────────────────────────────────
COMMANDS = {
    "cats":       cmd_cats,
    "prod-names": cmd_prod_names,
    "prod-desc":  cmd_prod_desc,
}

def main():
    if COMMAND not in COMMANDS:
        print("Usage:")
        print("  python translate.py cats        — translate all categories")
        print("  python translate.py prod-names  — translate product names")
        print("  python translate.py prod-desc   — fix product descriptions (FR==EN)")
        print("\nAdd --dry-run to preview without saving:")
        print("  python translate.py cats --dry-run")
        return

    print("=" * 60)
    mode = "DRY RUN" if DRY_RUN else "LIVE"
    print(f"  [{mode}] Command: {COMMAND}")
    print(f"  Target langs: {', '.join(TARGET_LANGS)}")
    print("=" * 60)

    token = get_token()
    COMMANDS[COMMAND](token)
    print("\n✅ Done!" + (" (dry run — nothing was saved)" if DRY_RUN else ""))


if __name__ == "__main__":
    main()