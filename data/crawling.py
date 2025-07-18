from bs4 import BeautifulSoup, Tag
import requests
import hashlib
import pprint
import json

# Global containers
full_contents = []
detailed_chunks = []

def get_doc_id(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest()

def clean_html(article_soup: Tag):
    """Removes noisy elements from the provided article soup tag."""
    for tag in article_soup.find_all(['script', 'style', 'figure', 'img', 'table', 'div']):
        if not (tag.name == 'div' and tag.get('id') == 'ftwp-postcontent'):
            tag.decompose()
    return article_soup

def extract_text_between_tags(start_tag: Tag, end_tag: Tag = None):
    """Extracts all text content between a start tag and an end tag."""
    content = []
    for sibling in start_tag.find_next_siblings():
        if sibling == end_tag:
            break
        if sibling.name in ['p', 'ul', 'ol', 'li']:
            content.append(sibling.get_text(separator=' ', strip=True))
    return "\n".join(content)

def process_html_to_documents(url):
    """
    Processes a single article, correctly handling nested headings and
    headings that act only as containers.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None, []

    soup = BeautifulSoup(response.text, "html.parser")
    main_article = soup.find(id="ftwp-postcontent")
    if not main_article:
        return None, []

    full_text = main_article.get_text(separator="\n", strip=True)
    full_doc = {
        "metadata": {"url": url, "doc_id": get_doc_id(url)},
        "text": full_text
    }

    clean_article = clean_html(main_article)
    headings = clean_article.find_all(['h2', 'h3', 'h4'])
    h1_tag = soup.find('h1')
    context_map = {"section_h1": h1_tag.get_text(strip=True) if h1_tag else "N/A"}

    chunks = []
    for i, current_heading in enumerate(headings):
        heading_level = current_heading.name
        heading_text = current_heading.get_text(strip=True)

        if heading_level == 'h2':
            context_map["section_h2"] = heading_text
            context_map.pop("section_h3", None)
            context_map.pop("section_h4", None)
        elif heading_level == 'h3':
            context_map["section_h3"] = heading_text
            context_map.pop("section_h4", None)
        elif heading_level == 'h4':
            context_map["section_h4"] = heading_text

        end_tag = headings[i + 1] if i + 1 < len(headings) else None
        content = extract_text_between_tags(current_heading, end_tag)

        if content.strip():
            # Sao chép context_map tại thời điểm này để tạo metadata
            metadata = context_map.copy()
            metadata["url"] = url
            metadata["doc_id"] = get_doc_id(url)
            chunks.append({
                "text": heading_text + ": " + content,
                "metadata": metadata
            })

    return full_doc, chunks

# main URL
source_url = "https://vnvc.vn/benh-thuong-gap-o-tre-em-duoi-5-tuoi/"

# Run
full_doc, chunks = process_html_to_documents(source_url)

if full_doc:
    full_contents.append(full_doc)
detailed_chunks.extend(chunks)

# Get all VNVC links from the main page
url = "https://vnvc.vn/benh-thuong-gap-o-tre-em-duoi-5-tuoi/"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
main_article = soup.find(id="ftwp-postcontent")

vnvc_links = main_article.find_all(
    "a",
    href=lambda x: x and x.startswith("https://vnvc.vn")
) if main_article else []

# Process all found links
for link in vnvc_links:
    full_doc, chunks = process_html_to_documents(link["href"])

    if full_doc:
        full_contents.append(full_doc)
    detailed_chunks.extend(chunks)
    
# Save data to JSON files
with open("detailed_chunks.json", "w", encoding="utf-8") as f:
    json.dump(detailed_chunks, f, ensure_ascii=False, indent=2)
print("Saved to detailed_chunks.json")

with open("full_contents.json", "w", encoding="utf-8") as f:
    json.dump(full_contents, f, ensure_ascii=False, indent=2)
print("Saved to full_contents.json")