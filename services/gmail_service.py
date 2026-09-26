import os
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


def get_gmail_credentials():
    """Retrieve Gmail credentials from system environment or .env."""
    user = os.environ.get("GMAIL_USER") or os.environ.get("IMAP_USER") or os.environ.get("EMAIL_USER")
    password = (
        os.environ.get("GMAIL_APP_PASSWORD")
        or os.environ.get("IMAP_PASSWORD")
        or os.environ.get("GMAIL_PASSWORD")
    )
    return user, password


def decode_str(header_value: str) -> str:
    """Decode encoded email header string (e.g. utf-8, iso-8859-1)."""
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            try:
                result.append(fragment.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                result.append(fragment.decode("latin-1", errors="replace"))
        else:
            result.append(str(fragment))
    return "".join(result)


def list_available_labels(mail: imaplib.IMAP4_SSL) -> List[str]:
    """Return a clean list of mailbox/label names available on the account."""
    status, mailboxes = mail.list()
    labels = []
    if status == "OK" and mailboxes:
        for mb in mailboxes:
            decoded = mb.decode("utf-8", errors="ignore")
            # Typical format: '(\\HasNoChildren) "/" "LinkedIn"'
            if '"' in decoded:
                parts = decoded.split('"')
                if len(parts) >= 2:
                    labels.append(parts[-2])
            else:
                labels.append(decoded.split()[-1])
    return labels


def fetch_emails_by_label(label: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Connect to Gmail via IMAP and fetch the latest `limit` emails under `label`.
    Returns list of dicts with subject, date, from, and html_body.
    """
    user, password = get_gmail_credentials()
    if not user:
        raise ValueError(
            "Falta definir la variable GMAIL_USER con tu dirección de correo en el archivo .env o en el sistema."
        )
    if not password:
        raise ValueError(
            "Falta la contraseña de aplicación de Gmail (GMAIL_APP_PASSWORD) en las variables de entorno."
        )

    # Clean password if it has spaces
    password = password.replace(" ", "")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(user, password)
    except imaplib.IMAP4.error as e:
        raise ConnectionError(f"Error de autenticación IMAP en Gmail: {str(e)}")
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar al servidor IMAP de Gmail: {str(e)}")

    try:
        # Try selecting the label directly
        status, _ = mail.select(f'"{label}"', readonly=True)
        if status != "OK":
            # Try without quotes
            status, _ = mail.select(label, readonly=True)

        if status != "OK":
            available = list_available_labels(mail)
            matching = [lbl for lbl in available if label.lower() in lbl.lower()]
            hint = f" Etiquetas similares encontradas: {', '.join(matching)}" if matching else ""
            raise ValueError(f"No se encontró la etiqueta '{label}' en tu Gmail.{hint}")

        # Search for all messages in this label
        status, data = mail.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []

        message_numbers = data[0].split()
        # Take the latest N messages
        recent_numbers = message_numbers[-limit:]
        recent_numbers.reverse()  # Newest first

        emails_result = []

        for num in recent_numbers:
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK" or not msg_data:
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = decode_str(msg.get("Subject", "(Sin asunto)"))
            date_str = decode_str(msg.get("Date", ""))
            from_str = decode_str(msg.get("From", ""))

            html_body = ""
            text_body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" in content_disposition:
                        continue

                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_text = payload.decode(charset, errors="replace")
                            if content_type == "text/html":
                                html_body = body_text
                            elif content_type == "text/plain":
                                text_body = body_text
                    except Exception:
                        continue
            else:
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or "utf-8"
                        body_text = payload.decode(charset, errors="replace")
                        if msg.get_content_type() == "text/html":
                            html_body = body_text
                        else:
                            text_body = body_text
                except Exception:
                    pass

            emails_result.append({
                "subject": subject,
                "date": date_str,
                "from": from_str,
                "html_body": html_body or text_body,
                "has_html": bool(html_body)
            })

        return emails_result

    finally:
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass
