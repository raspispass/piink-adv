#! /usr/bin/python3
import imaplib
import smtplib
import email
import socket
import time
import os
import sys
import json

#########################
# Configuration
#########################

# configuration file location (app folder)
APPPATH = os.path.dirname("/home/user/PiInk/")
# Email
username = "CHANGEME"
password = "CHANGEME"
imap_server = "CHANGEME"
smtp_server = "CHANGEME"

# Target folder
folder_name = "/home/user/PiInk/img/"
# Get current time for setting the target filenames (group to latest transmitted)
timestr = time.strftime("%Y%m%d--%H-%M")


## Credits: https://thepythoncode.com/article/reading-emails-in-python
# create an IMAP4 class with SSL
imap = imaplib.IMAP4_SSL(imap_server)
# authenticate
imap.login(username, password)
# messages = number of mails
status, messages = imap.select("INBOX")
status, messages = imap.search(None, '(UNSEEN)')
isAttachment = False
if status == "OK" and messages[0]:
    # Get the list of email IDs
    email_ids = messages[0].split()
    if email_ids:
            # Fetch the last email (most recent one)
            latest_email_id = email_ids[-1]

            # Fetch the email message by ID
            res, msg = imap.fetch(latest_email_id, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    # Parse a bytes email into a message object
                    message = email.message_from_bytes(response[1])
                    # Decode the email subject
                    subject, encoding = email.header.decode_header(message["Subject"])[0]
                    if isinstance(subject, bytes):
                        # If it's a bytes, decode to str
                        subject = subject.decode(encoding)
                    # Decode email sender
                    From, encoding = email.header.decode_header(message.get("From"))[0]
                    if isinstance(From, bytes):
                        From = From.decode(encoding)
                    # If the email message is multipart
                    if message.is_multipart():
                        # Iterate over email parts
                        for part in message.walk():
                            # Extract content type of email
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_disposition is not None and "attachment" in content_disposition:
                                # Download attachment
                                filename = part.get_filename()
                                if filename:
                                    # Set filename to 20250309--10-00_original-filename
                                    filename_mod = timestr + "_" + filename
                                    if not os.path.isdir(folder_name):
                                        os.mkdir(folder_name)
                                    filepath = os.path.join(folder_name, filename_mod)
                                    # Download attachment and save it
                                    open(filepath, "wb").write(part.get_payload(decode=True))
                                    isAttachment = True
                                    # Display picture
                                    cmd = "curl -X POST -F file=@" + filepath + " 127.0.0.1"
                                    os.system(cmd)

    # Email confirmation
    nachricht = email.message.EmailMessage()
    if isAttachment:
        nachricht.set_content("Vielen Dank für Deine Bilder. Wir sind gerade dabei die Bilder zur Anzeige aufzubereiten.")
        nachricht["Subject"] = "[PhotoFrame] Bilderempfangsbestätigung"
    else:
        nachricht.set_content("Leider gab es Probleme und die letzte eingegangene Email enthielt keine Anhänge. Versuche es ruhig erneut.")
        nachricht["Subject"] = "[PhotoFrame] Fehlgeschlagener Bilderempfang"
    nachricht["From"] = username
    nachricht["To"] = From
    try:
        # Send mail
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(username, password)
        server.send_message(nachricht)
        print("Email wurde erfolgreich versendet")
    
    except smtplib.SMTPAuthenticationError:
        print("Fehler beim einloggen am SMTP-Server.")
        print("Benutzername, oder Passwort falsch!")

    except ConnectionRefusedError:
        print("Die Verbindung zum SMTP-Server konnte hergestellt werden.")
        print("Bitte prüfen Sie den SMTP-Server und die Portnummer auf Fehler")

    except socket.gaierror:
        print("Fehlerhafte Angabe des SMTP-Servers.")
        print("Nachricht konnte nicht versendet werden.")

# close the connection and logout
imap.close()
imap.logout()

