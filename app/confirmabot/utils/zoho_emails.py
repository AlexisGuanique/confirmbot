#!/usr/bin/env python3
"""
Script simplificado para obtener emails de ZohoMail usando IMAP
"""

import imaplib
from email import message_from_bytes
from email.header import decode_header
from email.utils import parsedate_to_datetime

def get_emails_imap(email, password):
    """Obtiene emails no leídos usando IMAP"""
    print(f"📬 Conectando a ZohoMail para {email}...")
    
    try:
        mail = imaplib.IMAP4_SSL("imap.zoho.com", 993)
        mail.login(email, password)
        mail.select("INBOX")
        
        # Buscar emails no leídos
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            print("📭 No hay emails no leídos")
            mail.close()
            mail.logout()
            return []
        
        email_ids = messages[0].split()
        print(f"📧 Emails no leídos encontrados: {len(email_ids)}")
        
        emails_data = []
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status == "OK":
                email_message = message_from_bytes(msg_data[0][1])
                
                # Obtener información básica
                subject = email_message["Subject"]
                from_addr = email_message["From"]
                date = email_message["Date"]
                
                # Decodificar subject
                if subject:
                    decoded_subject = decode_header(subject)[0][0]
                    if isinstance(decoded_subject, bytes):
                        decoded_subject = decoded_subject.decode()
                    subject = decoded_subject
                
                # Obtener contenido
                content = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        elif part.get_content_type() == "text/html" and not content:
                            content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                else:
                    content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                emails_data.append({
                    'id': email_id,
                    'subject': subject or "",
                    'from': from_addr or "",
                    'date': date or "",
                    'content': content.strip() if content else ""
                })
        
        mail.close()
        mail.logout()
        print("✅ Conexión cerrada")
        return emails_data
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Error IMAP: {e}")
        if "IMAP for your account" in str(e):
            print("💡 Necesitas habilitar IMAP en tu cuenta de ZohoMail")
        raise e
    except Exception as e:
        print(f"❌ Error general: {e}")
        raise e

def mark_email_as_read(email, password, email_id):
    """Marca un email específico como leído"""
    try:
        mail = imaplib.IMAP4_SSL("imap.zoho.com", 993)
        mail.login(email, password)
        mail.select("INBOX")
        mail.store(email_id, '+FLAGS', '\\Seen')
        mail.close()
        mail.logout()
        return True
    except Exception as e:
        print(f"❌ Error marcando email como leído: {e}")
        return False
