import os
import re
import requests
import time

# Paths
BASE_API_URL = "https://en.wiktionary.org/w/api.php"
HEADERS = {"User-Agent": "WiktionaryTemplateFetcher/1.0 (by Ben)"}
DATA_DIR = r"C:\Users\benau\wiktionary-db\data"
TEMPLATE_PATH = os.path.join(DATA_DIR, "Template")
MODULE_PATH = os.path.join(DATA_DIR, "Module")
TEMPLATE_LIST = os.path.join(DATA_DIR, "unique_template_names.txt")

os.makedirs(TEMPLATE_PATH, exist_ok=True)
os.makedirs(MODULE_PATH, exist_ok=True)

# Keep track of downloaded items
downloaded_templates = set()
downloaded_modules = set()

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def fetch_wikitext(title):
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvslots": "main",
        "rvprop": "content"
    }
    response = requests.get(BASE_API_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions")
        if revs:
            return revs[0]["slots"]["main"]["*"]
    return None

def save_file(path, title, content, ext):
    filename = sanitize_filename(title.replace("Template:", "").replace("Module:", "")) + ext
    filepath = os.path.join(path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def extract_modules(wikitext):
    return re.findall(r"#invoke:([^\|\s}]+)", wikitext)

def download_module(module_name):
    if module_name in downloaded_modules:
        return
    title = f"Module:{module_name}"
    print(f"⚙️  Fetching module: {module_name}")
    content = fetch_wikitext(title)
    if content:
        save_file(MODULE_PATH, title, content, ".lua")
        downloaded_modules.add(module_name)
        for m in extract_modules(content):  # handle nested modules
            download_module(m)
    time.sleep(0.1)

def download_template(template_name):
    if template_name in downloaded_templates:
        return
    title = f"Template:{template_name}"
    print(f"📄 Fetching template: {template_name}")
    content = fetch_wikitext(title)
    if content:
        save_file(TEMPLATE_PATH, title, content, ".txt")
        downloaded_templates.add(template_name)
        for m in extract_modules(content):
            download_module(m)
    time.sleep(0.1)

def main():
    with open(TEMPLATE_LIST, "r", encoding="utf-8") as f:
        template_names = [line.strip() for line in f if line.strip()]

    for name in template_names:
        download_template(name)

    print(f"\n✅ Done! Downloaded {len(downloaded_templates)} templates and {len(downloaded_modules)} modules.")

if __name__ == "__main__":
    main()
