import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlunparse
from bs4 import BeautifulSoup


# Words indicating non-job links (noise to ignore)
IGNORED_PATTERNS = [
    "unsubscribe", "cancelar suscrip", "dar de baja", "preferencias",
    "política de privacidad", "privacy", "terms", "términos", "ayuda",
    "help", "configuración", "gestionar alertas", "manage alert",
    "ver en el navegador", "view in browser", "descarga la app",
    "iniciar sesión", "sign in", "logo", "facebook", "twitter", "instagram"
]


def clean_job_url(raw_url: str) -> str:
    """Clean tracking params from URL to prevent duplicate listings."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url)
        # Keep scheme and netloc and path, strip query if it's mostly tracking tokens
        if "linkedin.com" in parsed.netloc and "/jobs/view/" in parsed.path:
            # Keep just the base path for LinkedIn jobs
            return f"https://www.linkedin.com{parsed.path}"
        return raw_url
    except Exception:
        return raw_url


def is_job_link(href: str, text: str) -> bool:
    """Heuristic check to determine if an <a> tag represents a job post."""
    if not href or href.startswith("mailto:") or href.startswith("tel:"):
        return False

    href_lower = href.lower()
    text_lower = text.lower().strip()

    # Reject typical footer or utility links
    for ignored in IGNORED_PATTERNS:
        if ignored in text_lower or ignored in href_lower:
            return False

    # Check strong signals in URL
    job_url_keywords = ["/jobs/view/", "/job/", "/jobs/", "gh_jid", "apply", "careers", "position"]
    has_job_url = any(k in href_lower for k in job_url_keywords)

    # Check strong signals in text length and format
    has_job_text = len(text_lower) >= 8 and len(text_lower.split()) >= 2

    return has_job_url or (has_job_text and ("http" in href_lower))


def extract_jobs_from_email_html(html_content: str, email_subject: str = "", email_date: str = "") -> List[Dict[str, Any]]:
    """
    Extract job titles, companies, links, and snippets from an HTML email digest.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    found_jobs = []
    seen_links = set()

    # Find all anchor tags
    anchors = soup.find_all("a", href=True)

    for a in anchors:
        href = a["href"].strip()
        text = a.get_text(separator=" ", strip=True)

        if not is_job_link(href, text):
            continue

        clean_url = clean_job_url(href)
        if clean_url in seen_links:
            continue

        # Extract title and context
        title = text
        # If the anchor text was short or a button (e.g. "Ver empleo"), look at parent container
        parent = a.find_parent(["td", "div", "li", "tr"])
        context_text = ""

        if parent:
            parent_full_text = parent.get_text(separator=" | ", strip=True)
            # Remove the link text itself from the context
            context_text = parent_full_text.replace(text, "").strip(" | ")
            # If the link text is just "Ver empleo" or similar, search inside parent for a heading or title
            if len(text.split()) < 3 and len(context_text) > 10:
                heading = parent.find(["h1", "h2", "h3", "h4", "strong", "b"])
                if heading and len(heading.get_text(strip=True)) > 5:
                    title = heading.get_text(strip=True)

        if not title or len(title) < 4:
            continue

        seen_links.add(clean_url)
        found_jobs.append({
            "title": title[:100],
            "company_or_context": (context_text[:120] if context_text else email_subject[:80]),
            "link": href,
            "snippet": (context_text[:200] if context_text else title),
            "email_subject": email_subject,
            "email_date": email_date
        })

    return found_jobs


def parse_emails_to_jobs(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a list of fetched emails and combine all extracted jobs."""
    all_jobs = []
    seen_urls = set()

    for email_item in emails:
        html = email_item.get("html_body", "")
        subject = email_item.get("subject", "")
        date = email_item.get("date", "")

        jobs = extract_jobs_from_email_html(html, email_subject=subject, email_date=date)
        for job in jobs:
            clean_url = clean_job_url(job["link"])
            if clean_url not in seen_urls:
                seen_urls.add(clean_url)
                all_jobs.append(job)

    return all_jobs
