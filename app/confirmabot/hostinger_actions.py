

import imaplib
import smtplib
import email
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import ssl
import os
import sys
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Configuración de logging sin archivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HostingerEmailClient:
    """Cliente para conectarse a la casilla de correo de Hostinger"""
    
    def __init__(self, email_address: str, password: str):
        """
        Inicializa el cliente de email
        
        Args:
            email_address: Dirección de correo electrónico
            password: Contraseña de la cuenta
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = None
        self.connected = False
        
        # Configuración del servidor IMAP de Hostinger
        self.imap_host = 'imap.hostinger.com'
        self.imap_port = 993
        
        # Configuración del servidor SMTP de Hostinger
        self.smtp_host = 'smtp.hostinger.com'
        self.smtp_port = 587
        self.smtp_server = None
        
    def connect(self) -> bool:
        """
        Conecta al servidor IMAP de Hostinger
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            logger.info(f"Conectando a {self.imap_host}:{self.imap_port}")
            
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Conectar al servidor IMAP con SSL
            self.imap_server = imaplib.IMAP4_SSL(self.imap_host, self.imap_port, ssl_context=context)
            
            # Autenticar
            self.imap_server.login(self.email_address, self.password)
            
            self.connected = True
            logger.info("Conexión exitosa al servidor de correo")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"Error de autenticación IMAP: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al conectar: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del servidor IMAP"""
        if self.imap_server and self.connected:
            try:
                # Solo cerrar si estamos en estado SELECTED
                try:
                    self.imap_server.close()
                except imaplib.IMAP4.error:
                    # Si no estamos en estado SELECTED, ignorar el error
                    pass
                
                self.imap_server.logout()
                self.connected = False
                logger.info("Desconectado del servidor de correo")
            except Exception as e:
                logger.error(f"Error al desconectar: {e}")
    
    def connect_smtp(self) -> bool:
        """
        Conecta al servidor SMTP de Hostinger para envío de correos
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Conectar al servidor SMTP con STARTTLS
            self.smtp_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            self.smtp_server.starttls(context=context)
            
            # Autenticar
            self.smtp_server.login(self.email_address, self.password)
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            return False
        except Exception as e:
            return False
    
    def disconnect_smtp(self):
        """Desconecta del servidor SMTP"""
        if self.smtp_server:
            try:
                self.smtp_server.quit()
                self.smtp_server = None
            except Exception as e:
                pass
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   is_html: bool = False, attachments: List[str] = None) -> bool:
        """
        Envía un correo electrónico
        
        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            body: Cuerpo del correo
            is_html: Si el cuerpo es HTML (default: False)
            attachments: Lista de rutas de archivos adjuntos (opcional)
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        try:
            # Conectar al servidor SMTP si no está conectado
            if not self.smtp_server:
                if not self.connect_smtp():
                    return False
            
            # Crear el mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Agregar el cuerpo del mensaje
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Agregar adjuntos si los hay
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
                    else:
                        pass
            
            # Enviar el correo
            text = msg.as_string()
            self.smtp_server.sendmail(self.email_address, to_email, text)
            
            return True
            
        except Exception as e:
            return False
    
    def send_simple_email(self, to_email: str, subject: str, message: str) -> bool:
        """
        Envía un correo electrónico simple (texto plano)
        
        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            message: Mensaje de texto plano
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        return self.send_email(to_email, subject, message, is_html=False)
    
    def send_html_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envía un correo electrónico con contenido HTML
        
        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        return self.send_email(to_email, subject, html_content, is_html=True)
    
    def send_email_with_attachment(self, to_email: str, subject: str, body: str, 
                                  attachment_path: str) -> bool:
        """
        Envía un correo electrónico con un archivo adjunto
        
        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            body: Cuerpo del correo
            attachment_path: Ruta del archivo adjunto
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        return self.send_email(to_email, subject, body, attachments=[attachment_path])
    
    def list_folders(self) -> List[str]:
        """
        Lista todas las carpetas disponibles en el servidor de correo
        
        Returns:
            List[str]: Lista de nombres de carpetas
        """
        if not self.connected:
            logger.error("No hay conexión activa al servidor")
            return []
        
        try:
            status, folders = self.imap_server.list()
            if status != 'OK':
                logger.error("Error al listar carpetas")
                return []
            
            folder_names = []
            print(f"\n🔍 DEBUG: Analizando {len(folders)} carpetas...")
            
            for i, folder in enumerate(folders):
                # Parsear el nombre de la carpeta
                folder_str = folder.decode('utf-8')
                print(f"DEBUG {i+1}: {folder_str}")
                
                # Método mejorado para extraer el nombre
                folder_name = None
                
                # Método 1: Buscar entre comillas dobles (más común)
                if '"' in folder_str:
                    parts = folder_str.split('"')
                    if len(parts) >= 3:
                        folder_name = parts[-2]
                        print(f"  → Método 1 (comillas): '{folder_name}'")
                
                # Método 2: Buscar después del último espacio
                if not folder_name or folder_name == '.':
                    parts = folder_str.split()
                    if len(parts) >= 3:
                        folder_name = parts[-1]
                        print(f"  → Método 2 (último espacio): '{folder_name}'")
                
                # Método 3: Usar regex para encontrar el nombre
                if not folder_name or folder_name == '.':
                    import re
                    # Buscar texto entre comillas
                    match = re.search(r'"([^"]+)"', folder_str)
                    if match:
                        folder_name = match.group(1)
                        print(f"  → Método 3 (regex comillas): '{folder_name}'")
                
                # Método 4: Buscar después de "INBOX" o similar
                if not folder_name or folder_name == '.':
                    if 'INBOX' in folder_str:
                        parts = folder_str.split()
                        for j, part in enumerate(parts):
                            if 'INBOX' in part and j + 1 < len(parts):
                                folder_name = parts[j + 1]
                                print(f"  → Método 4 (después INBOX): '{folder_name}'")
                                break
                
                # Método 5: Buscar cualquier palabra que no sea punto
                if not folder_name or folder_name == '.':
                    words = folder_str.split()
                    for word in words:
                        if word != '.' and len(word) > 1 and not word.startswith('('):
                            folder_name = word
                            print(f"  → Método 5 (palabra válida): '{folder_name}'")
                            break
                
                if folder_name and folder_name != '.':
                    folder_names.append(folder_name)
                    print(f"  ✅ Carpeta agregada: '{folder_name}'")
                else:
                    print(f"  ❌ No se pudo parsear: '{folder_str}'")
            
            print(f"\n📁 Carpetas finales: {folder_names}")
            logger.info(f"Se encontraron {len(folder_names)} carpetas: {folder_names}")
            return folder_names
            
        except Exception as e:
            logger.error(f"Error al listar carpetas: {e}")
            return []
    
    def go_to_confirmar_folder(self, limit: int = 10) -> List[Dict]:
        """
        Va directamente a la carpeta 'Confirmar' y obtiene sus emails
        
        Args:
            limit: Número máximo de emails a obtener
            
        Returns:
            List[Dict]: Lista de diccionarios con información de los emails
        """
        if not self.connected:
            logger.error("No hay conexión activa al servidor")
            return []
        
        try:
            # Intentar diferentes variaciones del nombre de la carpeta
            possible_names = [
                'INBOX.Confirmar',  # Nombre real encontrado
                'Confirmar', 
                'CONFIRMAR', 
                'confirmar', 
                'Confirm', 
                'CONFIRM', 
                'confirm'
            ]
            
            for folder_name in possible_names:
                try:
                    logger.info(f"Intentando acceder a la carpeta '{folder_name}'")
                    emails = self.get_emails_from_folder(folder_name, limit)
                    if emails:
                        logger.info(f"Encontrados {len(emails)} emails no leidos en la carpeta '{folder_name}'")
                        return emails
                except Exception as e:
                    logger.debug(f"No se pudo acceder a '{folder_name}': {e}")
                    continue
            
            logger.warning("No se pudo encontrar la carpeta 'Confirmar' con ningún nombre")
            return []
            
        except Exception as e:
            logger.error(f"Error al acceder a la carpeta Confirmar: {e}")
            return []

    def get_unread_emails_from_folder(self, folder_name: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene SOLO emails NO LEÍDOS de una carpeta específica
        
        Args:
            folder_name: Nombre de la carpeta
            limit: Número máximo de emails a obtener
            
        Returns:
            List[Dict]: Lista de diccionarios con información de los emails NO LEÍDOS
        """
        if not self.connected:
            logger.error("No hay conexión activa al servidor")
            return []
        
        try:
            # Seleccionar la carpeta específica
            status, messages = self.imap_server.select(folder_name)
            if status != 'OK':
                logger.error(f"Error al seleccionar la carpeta '{folder_name}'")
                return []
            
            # Buscar SOLO emails NO LEÍDOS
            status, messages = self.imap_server.search(None, 'UNSEEN')
            
            if status != 'OK' or not messages[0]:
                logger.info(f"No hay emails NO LEÍDOS en la carpeta '{folder_name}'")
                return []
            
            email_ids = messages[0].split()
            
            # Limitar el número de emails
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Obtener los más recientes
            
            emails = []
            
            for email_id in email_ids:
                try:
                    # Obtener el email
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parsear el email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extraer información del email
                    email_info = self._parse_email(email_message)
                    emails.append(email_info)
                    
                except Exception as e:
                    logger.error(f"Error al procesar email {email_id}: {e}")
                    continue
            
            logger.info(f"Se obtuvieron {len(emails)} emails NO LEÍDOS de la carpeta '{folder_name}'")
            
            # Ordenar emails del más nuevo al más viejo
            emails = self._sort_emails_by_date(emails)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error al obtener emails NO LEÍDOS de la carpeta '{folder_name}': {e}")
            return []

    def get_emails_from_folder(self, folder_name: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene emails de una carpeta específica
        
        Args:
            folder_name: Nombre de la carpeta
            limit: Número máximo de emails a obtener
            
        Returns:
            List[Dict]: Lista de diccionarios con información de los emails
        """
        if not self.connected:
            logger.error("No hay conexión activa al servidor")
            return []
        
        try:
            # Seleccionar la carpeta específica
            status, messages = self.imap_server.select(folder_name)
            if status != 'OK':
                logger.error(f"Error al seleccionar la carpeta '{folder_name}'")
                return []
            
            # Buscar emails no leídos primero, si no hay ninguno, buscar todos
            status, messages = self.imap_server.search(None, 'UNSEEN')
            
            # Si no hay emails no leídos, buscar todos los emails
            if status != 'OK' or not messages[0]:
                logger.info("No hay emails no leidos, buscando todos los emails...")
                status, messages = self.imap_server.search(None, 'ALL')
            
            if status != 'OK':
                logger.error("Error al buscar emails")
                return []
            
            email_ids = messages[0].split()
            
            # Limitar el número de emails
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Obtener los más recientes
            
            emails = []
            
            for email_id in email_ids:
                try:
                    # Obtener el email
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parsear el email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extraer información del email
                    email_info = self._parse_email(email_message)
                    emails.append(email_info)
                    
                except Exception as e:
                    logger.error(f"Error al procesar email {email_id}: {e}")
                    continue
            
            logger.info(f"Se obtuvieron {len(emails)} emails no leidos de la carpeta '{folder_name}'")
            
            # Ordenar emails del más nuevo al más viejo
            emails = self._sort_emails_by_date(emails)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error al obtener emails de la carpeta '{folder_name}': {e}")
            return []

    def get_inbox_emails(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene SOLO emails NO LEÍDOS de la bandeja de entrada
        
        Args:
            limit: Número máximo de emails a obtener
            
        Returns:
            List[Dict]: Lista de diccionarios con información de los emails NO LEÍDOS
        """
        if not self.connected:
            logger.error("No hay conexión activa al servidor")
            return []
        
        try:
            # Seleccionar la bandeja de entrada
            self.imap_server.select('INBOX')
            
            # Buscar SOLO emails NO LEÍDOS
            status, messages = self.imap_server.search(None, 'UNSEEN')
            
            if status != 'OK' or not messages[0]:
                logger.info("No hay emails NO LEÍDOS en la bandeja de entrada")
                return []
            
            email_ids = messages[0].split()
            
            # Limitar el número de emails
            if len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Obtener los más recientes
            
            emails = []
            
            for email_id in email_ids:
                try:
                    # Obtener el email
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parsear el email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extraer información del email
                    email_info = self._parse_email(email_message)
                    emails.append(email_info)
                    
                except Exception as e:
                    logger.error(f"Error al procesar email {email_id}: {e}")
                    continue
            
            logger.info(f"Se obtuvieron {len(emails)} emails NO LEÍDOS")
            
            # Ordenar emails del más nuevo al más viejo
            emails = self._sort_emails_by_date(emails)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error al obtener emails: {e}")
            return []
    
    def _parse_email(self, email_message) -> Dict:
        """
        Parsea un mensaje de email y extrae información relevante
        
        Args:
            email_message: Objeto email.message.Message
            
        Returns:
            Dict: Diccionario con información del email
        """
        email_info = {
            'subject': '',
            'from': '',
            'to': '',
            'date': '',
            'body': '',
            'attachments': []
        }
        
        try:
            # Asunto
            email_info['subject'] = email_message.get('Subject', 'Sin asunto')
            
            # Remitente
            email_info['from'] = email_message.get('From', 'Desconocido')
            
            # Destinatario
            email_info['to'] = email_message.get('To', 'Desconocido')
            
            # Fecha
            email_info['date'] = email_message.get('Date', 'Fecha desconocida')
            
            # Cuerpo del mensaje
            email_info['body'] = self._extract_body(email_message)
            
            # Adjuntos (si los hay)
            email_info['attachments'] = self._extract_attachments(email_message)
            
        except Exception as e:
            logger.error(f"Error al parsear email: {e}")
        
        return email_info
    
    def _extract_body(self, email_message) -> str:
        """
        Extrae el cuerpo del mensaje de email
        
        Args:
            email_message: Objeto email.message.Message
            
        Returns:
            str: Cuerpo del mensaje
        """
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Solo procesar partes de texto que no sean adjuntos
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        try:
                            body = part.get_payload(decode=True).decode('latin-1')
                            break
                        except:
                            continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8')
            except:
                try:
                    body = email_message.get_payload(decode=True).decode('latin-1')
                except:
                    body = str(email_message.get_payload())
        
        return body
    
    def _extract_attachments(self, email_message) -> List[str]:
        """
        Extrae información de adjuntos
        
        Args:
            email_message: Objeto email.message.Message
            
        Returns:
            List[str]: Lista de nombres de archivos adjuntos
        """
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
        
        return attachments
    
    def _sort_emails_by_date(self, emails: List[Dict]) -> List[Dict]:
        """
        Ordena los emails del más nuevo al más viejo
        
        Args:
            emails: Lista de emails
            
        Returns:
            List[Dict]: Lista de emails ordenada por fecha
        """
        def parse_email_date(email_info):
            """Extrae la fecha del email y la convierte a datetime"""
            try:
                date_str = email_info.get('date', '')
                if not date_str:
                    return datetime.min
                
                # Parsear diferentes formatos de fecha
                from email.utils import parsedate_to_datetime
                try:
                    return parsedate_to_datetime(date_str)
                except:
                    # Si falla, intentar parsear manualmente
                    import re
                    # Buscar patrones comunes de fecha
                    patterns = [
                        r'(\w{3}),?\s+(\d{1,2})\s+(\w{3})\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})',
                        r'(\d{1,2})\s+(\w{3})\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, date_str)
                        if match:
                            # Intentar crear datetime básico
                            try:
                                from datetime import datetime
                                return datetime.strptime(match.group(0), '%d %b %Y %H:%M:%S')
                            except:
                                continue
                    
                    return datetime.min
                    
            except Exception as e:
                logger.debug(f"Error al parsear fecha '{date_str}': {e}")
                return datetime.min
        
        # Ordenar por fecha (más nuevo primero)
        try:
            sorted_emails = sorted(emails, key=parse_email_date, reverse=True)
            logger.info("Emails ordenados del más nuevo al más viejo")
            return sorted_emails
        except Exception as e:
            logger.error(f"Error al ordenar emails: {e}")
            return emails
    
    def mark_as_read(self, email_id: str) -> bool:
        """
        Marca un email como leído
        
        Args:
            email_id: ID del email
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            self.imap_server.store(email_id, '+FLAGS', '\\Seen')
            logger.info(f"Email {email_id} marcado como leído")
            return True
        except Exception as e:
            logger.error(f"Error al marcar email como leído: {e}")
            return False
    
    def mark_email_as_read_by_content(self, email_content: str) -> bool:
        """
        Marca un email como leído basándose en su contenido
        Busca el email que coincida con el contenido y lo marca como leído
        
        Args:
            email_content: Contenido del email a buscar
            
        Returns:
            bool: True si fue exitoso, False en caso contrario
        """
        try:
            # Buscar emails no leídos
            status, messages = self.imap_server.search(None, 'UNSEEN')
            if status != 'OK':
                return False
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                try:
                    # Obtener el email
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # Parsear el email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extraer contenido
                    body = self._extract_body(email_message)
                    
                    # Verificar si el contenido coincide
                    if email_content in body:
                        # Marcar como leído
                        self.imap_server.store(email_id, '+FLAGS', '\\Seen')
                        logger.info(f"Email con contenido coincidente marcado como leído: {email_id}")
                        return True
                        
                except Exception as e:
                    logger.error(f"Error procesando email {email_id}: {e}")
                    continue
            
            logger.warning("No se encontró email con contenido coincidente")
            return False
            
        except Exception as e:
            logger.error(f"Error al marcar email como leído por contenido: {e}")
            return False


def extract_confirmation_url(email_info: Dict) -> Optional[str]:
    """
    Extrae la URL de confirmación de un email de 33mail.com
    
    Args:
        email_info: Diccionario con información del email
        
    Returns:
        Optional[str]: URL de confirmación si se encuentra, None en caso contrario
    """
    try:
        # Verificar si es un email de 33mail.com
        subject = email_info.get('subject', '').lower()
        from_email = email_info.get('from', '').lower()
        body = email_info.get('body', '')
        
        # Verificar si es un email de 33mail.com signup
        is_33mail_signup = (
            '33mail.com signup' in subject or 
            '33mail' in from_email or
            '33mail' in body.lower()
        )
        
        if not is_33mail_signup:
            return None
        
        # Buscar URL de confirmación en el cuerpo del email
        # Patrón para URLs de confirmación de 33mail.com
        url_patterns = [
            r'https://www\.33mail\.com/user/confirm/[a-zA-Z0-9]+',
            r'https://33mail\.com/user/confirm/[a-zA-Z0-9]+',
            r'http://www\.33mail\.com/user/confirm/[a-zA-Z0-9]+',
            r'http://33mail\.com/user/confirm/[a-zA-Z0-9]+'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, body)
            if match:
                url = match.group(0)
                logger.info(f"URL de confirmación encontrada: {url}")
                return url
        
        logger.warning("No se encontró URL de confirmación en el email")
        return None
        
    except Exception as e:
        logger.error(f"Error al extraer URL de confirmación: {e}")
        return None


def print_email_full(email_info: Dict, email_number: int):
    """Muestra un email completo con formato legible"""
    print(f"\nEMAIL #{email_number}")
    print("=" * 80)
    print(f"Asunto: {email_info['subject']}")
    print(f"De: {email_info['from']}")
    print(f"Para: {email_info['to']}")
    print(f"Fecha: {email_info['date']}")
    
    if email_info['attachments']:
        print(f"Adjuntos: {', '.join(email_info['attachments'])}")
    
    print("\nCONTENIDO:")
    print("-" * 80)
    
    body = email_info['body']
    if body:
        lines = body.split('\n')
        for line in lines[:50]:
            if line.strip():
                print(f"   {line}")
        
        if len(lines) > 50:
            print(f"\n   ... (mostrando solo las primeras 50 lineas de {len(lines)} total)")
    else:
        print("   (Sin contenido de texto)")
    
    print("-" * 80)


def wait_for_confirmation_email(email_address: str, password: str, timeout_seconds: int = 45) -> Tuple[bool, Optional[str]]:
    """
    Espera hasta que llegue un nuevo email de 33mail.com y extrae la URL de confirmación
    
    Args:
        email_address: Dirección de correo electrónico
        password: Contraseña de la cuenta
        timeout_seconds: Tiempo máximo de espera en segundos (default: 45)
    
    Returns:
        Tuple[bool, Optional[str]]: (True, URL) si encuentra la URL, (False, None) si no encuentra nada
    """
    # Crear cliente de email
    email_client = HostingerEmailClient(email_address, password)
    
    try:
        # Conectar al servidor
        if not email_client.connect():
            logger.error("No se pudo conectar al servidor de correo")
            return False, None
        
        logger.info("Conexión exitosa al servidor de correo")
        logger.info(f"⏳ Esperando nuevos emails de 33mail.com (timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        last_email_count = 0
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Verificar SOLO emails NO LEÍDOS en la carpeta Confirmar
                emails = email_client.get_unread_emails_from_folder('INBOX.Confirmar', limit=5)
                
                if not emails:
                    # Si no hay emails no leídos en Confirmar, verificar bandeja de entrada principal
                    emails = email_client.get_inbox_emails(limit=5)
                
                current_email_count = len(emails)
                
                # Si hay emails NO LEÍDOS y es el primer chequeo o hay más emails que antes
                if emails and (last_email_count == 0 or current_email_count > last_email_count):
                    logger.info(f"📧 Se encontraron {current_email_count} emails NO LEÍDOS")
                    
                    # Buscar en el email más reciente NO LEÍDO (primer elemento de la lista ordenada)
                    latest_email = emails[0]
                    logger.info(f"🔍 Analizando email más reciente NO LEÍDO: {latest_email.get('subject', 'Sin asunto')}")
                    
                    # Intentar extraer URL de confirmación
                    confirmation_url = extract_confirmation_url(latest_email)
                    
                    if confirmation_url:
                        logger.info(f"✅ URL de confirmación encontrada!")
                        logger.info(f"📧 Asunto: {latest_email.get('subject', 'Sin asunto')}")
                        logger.info(f"🔗 URL: {confirmation_url}")
                        return True, confirmation_url
                    else:
                        logger.debug(f"❌ No se encontró URL de confirmación en el email más reciente NO LEÍDO")
                
                last_email_count = current_email_count
                
                # Esperar 3 segundos antes del siguiente chequeo
                logger.debug(f"⏱️ Esperando 3 segundos... (tiempo transcurrido: {int(time.time() - start_time)}s)")
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Error durante la verificación: {e}")
                time.sleep(3)
                continue
        
        logger.warning(f"⏰ Timeout alcanzado ({timeout_seconds}s). No se encontró URL de confirmación.")
        return False, None
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return False, None
    
    finally:
        # Desconectar
        email_client.disconnect()


def extract_latest_confirmation_url(email_address: str, password: str):
    """
    Función automatizada que extrae la URL de confirmación del email más reciente de 33mail.com
    Sin requerir interacción del usuario
    
    Args:
        email_address: Dirección de correo electrónico
        password: Contraseña de la cuenta
    
    Returns:
        Optional[str]: URL de confirmación si se encuentra, None en caso contrario
    """
    # Crear cliente de email
    email_client = HostingerEmailClient(email_address, password)
    
    try:
        # Conectar al servidor
        if not email_client.connect():
            logger.error("No se pudo conectar al servidor de correo")
            return None
        
        logger.info("Conexión exitosa al servidor de correo")
        
        # Ir directamente a la carpeta Confirmar
        emails = email_client.go_to_confirmar_folder(limit=10)
        
        if not emails:
            logger.warning("No se encontraron emails en la carpeta 'Confirmar'")
            # Verificar también la bandeja de entrada principal
            emails = email_client.get_inbox_emails(limit=10)
        
        if emails:
            logger.info(f"Se encontraron {len(emails)} emails")
            
            # Buscar en los emails más recientes
            for i, email_info in enumerate(emails):
                logger.info(f"Analizando email #{i+1}: {email_info.get('subject', 'Sin asunto')}")
                
                # Intentar extraer URL de confirmación
                confirmation_url = extract_confirmation_url(email_info)
                
                if confirmation_url:
                    logger.info(f"✅ URL de confirmación encontrada en email #{i+1}")
                    logger.info(f"📧 Asunto: {email_info.get('subject', 'Sin asunto')}")
                    logger.info(f"🔗 URL: {confirmation_url}")
                    return confirmation_url
                else:
                    logger.debug(f"❌ No se encontró URL de confirmación en email #{i+1}")
            
            logger.warning("No se encontró ningún email de 33mail.com con URL de confirmación")
            return None
        else:
            logger.warning("No se encontraron emails en ninguna carpeta")
            return None
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return None
    
    finally:
        # Desconectar
        email_client.disconnect()


def go_directly_to_confirmar(email_address: str, password: str):
    """Función para ir directamente a la carpeta Confirmar"""
    
    # Crear cliente de email
    email_client = HostingerEmailClient(email_address, password)
    
    try:
        # Conectar al servidor
        if not email_client.connect():
            logger.error("No se pudo conectar al servidor de correo")
            return
        
        print("Conexion exitosa!")
        print("Buscando carpeta 'Confirmar'...")
        
        # Ir directamente a la carpeta Confirmar
        emails = email_client.go_to_confirmar_folder(limit=20)
        
        if emails:
            print(f"Se encontraron {len(emails)} emails en la carpeta 'Confirmar'")
            print("Mostrando el email mas reciente automaticamente...")
            input("Presiona Enter para ver el email...")
            
            # Mostrar automáticamente el primer email (más nuevo)
            print_email_full(emails[0], 1)
            
            # Preguntar si quiere ver más emails
            while True:
                print(f"\nOPCIONES:")
                print("2-{}: Ver otro email especifico".format(len(emails)))
                print("a: Ver todos los emails")
                print("0: Salir")
                
                try:
                    choice = input(f"\nSelecciona una opcion (0-{len(emails)}, a): ").strip().lower()
                    
                    if choice == '0':
                        print("Hasta luego!")
                        break
                    elif choice == 'a':
                        # Mostrar todos los emails uno por uno
                        for i, email_info in enumerate(emails, 1):
                            if i > 1:  # Saltar el primero que ya se mostró
                                print_email_full(email_info, i)
                                input(f"\nPresiona Enter para continuar al siguiente email...")
                        continue
                    elif choice.isdigit():
                        email_num = int(choice)
                        if 1 <= email_num <= len(emails):
                            print_email_full(emails[email_num - 1], email_num)
                            input(f"\nPresiona Enter para volver al menu...")
                        else:
                            print("Numero de email invalido")
                            input("Presiona Enter para continuar...")
                    else:
                        print("Opcion invalida")
                        input("Presiona Enter para continuar...")
                        
                except KeyboardInterrupt:
                    print("\nHasta luego!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    input("Presiona Enter para continuar...")
        else:
            print("No se encontraron emails en la carpeta 'Confirmar'")
            print("Verificando bandeja de entrada principal...")
            
            # Verificar también la bandeja de entrada principal
            inbox_emails = email_client.get_inbox_emails(limit=10)
            if inbox_emails:
                print(f"Se encontraron {len(inbox_emails)} emails en la bandeja de entrada principal")
                print("Mostrando el email mas reciente...")
                input("Presiona Enter para ver el email...")
                print_email_full(inbox_emails[0], 1)
            else:
                print("No se encontraron emails en ninguna carpeta")
                print("Intentando mostrar todas las carpetas disponibles...")
                
                # Mostrar carpetas disponibles para debug
                folders = email_client.list_folders()
                if folders:
                    print(f"\nCarpetas encontradas:")
                    for i, folder in enumerate(folders, 1):
                        print(f"{i}. {folder}")
                else:
                    print("No se pudieron obtener las carpetas")
    
    except KeyboardInterrupt:
        logger.info("Script interrumpido por el usuario")
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
    
    finally:
        # Desconectar
        email_client.disconnect()


def send_quick_email(email_address: str, password: str, to_email: str, 
                    subject: str, message: str) -> bool:
    """
    Función rápida para enviar un correo electrónico simple
    
    Args:
        email_address: Dirección de correo del remitente
        password: Contraseña de la cuenta
        to_email: Dirección de correo del destinatario
        subject: Asunto del correo
        message: Mensaje de texto plano
        
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    email_client = HostingerEmailClient(email_address, password)
    
    try:
        if email_client.connect_smtp():
            success = email_client.send_simple_email(to_email, subject, message)
            return success
        else:
            return False
    except Exception as e:
        return False
    finally:
        email_client.disconnect_smtp()


def send_html_email_quick(email_address: str, password: str, to_email: str, 
                        subject: str, html_content: str) -> bool:
    """
    Función rápida para enviar un correo electrónico con contenido HTML
    
    Args:
        email_address: Dirección de correo del remitente
        password: Contraseña de la cuenta
        to_email: Dirección de correo del destinatario
        subject: Asunto del correo
        html_content: Contenido HTML del correo
        
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    email_client = HostingerEmailClient(email_address, password)
    
    try:
        if email_client.connect_smtp():
            success = email_client.send_html_email(to_email, subject, html_content)
            return success
        else:
            return False
    except Exception as e:
        return False
    finally:
        email_client.disconnect_smtp()


def send_email_with_file(email_address: str, password: str, to_email: str, 
                        subject: str, body: str, attachment_path: str) -> bool:
    """
    Función rápida para enviar un correo electrónico con archivo adjunto
    
    Args:
        email_address: Dirección de correo del remitente
        password: Contraseña de la cuenta
        to_email: Dirección de correo del destinatario
        subject: Asunto del correo
        body: Cuerpo del correo
        attachment_path: Ruta del archivo adjunto
        
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    email_client = HostingerEmailClient(email_address, password)
    
    try:
        if email_client.connect_smtp():
            success = email_client.send_email_with_attachment(to_email, subject, body, attachment_path)
            return success
        else:
            return False
    except Exception as e:
        return False
    finally:
        email_client.disconnect_smtp()


if __name__ == "__main__":
    # Función automatizada que espera por nuevos emails y extrae la URL
    print("🔍 Esperando nuevos emails de 33mail.com para extraer URL de confirmación...")
    # Nota: Esta función ahora requiere credenciales como parámetros
    print("⚠️ Esta función ahora requiere credenciales como parámetros.")
    print("   Usa: wait_for_confirmation_email(email_address, password, timeout_seconds)")
    print("\n📧 Funciones de envío de correos disponibles:")
    print("   - send_quick_email(email_address, password, to_email, subject, message)")
    print("   - send_html_email_quick(email_address, password, to_email, subject, html_content)")
    print("   - send_email_with_file(email_address, password, to_email, subject, body, attachment_path)")
