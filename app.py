import os
import threading
import time
import traceback
from flask import Flask, jsonify
from gmail_listener import GmailListener

app = Flask(__name__)

QUERY_PIPEFY = 'is:unread subject:"NOVA PROPOSTA"'

def loop_checker(query, source):
    gmail_listener = GmailListener()
    while True:
        try:
            emails = gmail_listener.check_unread_emails(query, source) or []
            print(f"\n📬 Verificando [{source}]... Emails encontrados: {len(emails)}\n")

            for email in emails:
                print("📨 Novo e-mail:")
                for k, v in email.items():
                    print(f"{k}: {v}")
                print("-" * 40)

            time.sleep(15)
        except Exception as e:
            print(f"Erro ao verificar e-mails ({source}): {e}")
            traceback.print_exc()
            time.sleep(30)

@app.route("/listen-emails", methods=["GET"])
def listen_emails():
    return jsonify({"status": "listening"})

# Inicia automaticamente mesmo na Railway
threading.Thread(target=loop_checker, args=(QUERY_PIPEFY, "autodigitacao"), daemon=True).start()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))





