import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from bs4 import BeautifulSoup


# Words indicating non-job links (noise to ignore)
IGNORED_PATTERNS = [
    "unsubscribe", "cancelar suscrip", "dar de baja", "preferencias",
    "política de privacidad", "privacy", "terms", "términos", "ayuda",
    "help", "configuración", "gestionar alertas", "manage alert",
    "ver en el navegador", "view in browser", "descarga la app",
    "iniciar sesión", "sign in", "logo", "facebook", "twitter", "instagram"
]


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_name", "utm_placement", "utm_creative",
    "gclid", "fbclid", "mc_cid", "mc_eid", "dclid", "msclkid",
    "igshid", "hsa_acc", "hsa_ad", "hsa_cam", "hsa_grp", "hsa_kw",
    "hsa_mt", "hsa_net", "hsa_src", "hsa_ver", "hsa_tgt"
}


def normalize_text(value: str) -> str:
    """Normalize title/text for comparison and dedupe."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower()


def clean_job_url(raw_url: str) -> str:
    """Clean tracking params from URL to prevent duplicate listings."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url)
        clean_query = []
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
            if key.lower() not in TRACKING_PARAMS and key.lower().startswith("utm_") is False:
                clean_query.append((key, values[-1]))
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(clean_query),
            "",
        ))

        if "linkedin.com" in parsed.netloc and "/jobs/view/" in parsed.path:
            return f"https://www.linkedin.com{parsed.path}"
        return clean_url.lower()
    except Exception:
        return raw_url.strip().lower()


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
    seen_jobs = set()

    # Find all anchor tags
    anchors = soup.find_all("a", href=True)

    for a in anchors:
        href = a["href"].strip()
        text = a.get_text(separator=" ", strip=True)

        if not is_job_link(href, text):
            continue

        clean_url = clean_job_url(href)
        normalized_title = normalize_text(text)
        dedupe_key = (clean_url, normalized_title)
        if not clean_url or dedupe_key in seen_jobs:
            continue

        # Extract title and context
        title = text
        parent = a.find_parent(["td", "div", "li", "tr", "p", "span"])
        context_text = ""

        if parent:
            parent_full_text = parent.get_text(separator=" | ", strip=True)
            context_text = parent_full_text.replace(text, "").strip(" | ")
            if len(text.split()) < 3 and len(context_text) > 10:
                heading = parent.find(["h1", "h2", "h3", "h4", "strong", "b"])
                if heading and len(heading.get_text(strip=True)) > 5:
                    title = heading.get_text(strip=True)

        if not title or len(title) < 4:
            continue

        title = title.strip()
        if len(title) > 120:
            title = title[:120].strip()

        context_value = context_text[:120].strip() if context_text else ""
        if not context_value and "glassdoor" not in email_subject.lower() and "linkedin" not in email_subject.lower():
            context_value = ""

        if not context_value:
            context_value = ""

        seen_jobs.add(dedupe_key)
        found_jobs.append({
            "title": title,
            "company_or_context": context_value,
            "link": clean_url,
            "snippet": context_value or title,
            "email_subject": email_subject,
            "email_date": email_date
        })

    return found_jobs


def parse_emails_to_jobs(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a list of fetched emails and combine all extracted jobs."""
    all_jobs = []
    seen_jobs = set()

    for email_item in emails:
        html = email_item.get("html_body", "")
        subject = email_item.get("subject", "")
        date = email_item.get("date", "")

        jobs = extract_jobs_from_email_html(html, email_subject=subject, email_date=date)
        for job in jobs:
            job_key = (
                clean_job_url(job.get("link", "")),
                normalize_text(job.get("title", "")),
            )
            if job_key in seen_jobs:
                continue
            if not job_key[0]:
                continue
            seen_jobs.add(job_key)
            all_jobs.append(job)

    return all_jobs
