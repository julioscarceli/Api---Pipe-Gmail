from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup
import re
import requests
from config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN

class GmailListener:
    def __init__(self):
        self.creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token'
        )
        self.service = build('gmail', 'v1', credentials=self.creds)

    def check_unread_emails(self, query, source):
        results = self.service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            q=query
        ).execute()

        messages = results.get('messages', [])
        parsed_emails = []

        for msg in messages:
            msg_data = self.service.users().messages().get(
                userId='me',
                id=msg['id']
            ).execute()

            headers = msg_data['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')

            body = self.extract_body(msg_data['payload'])
            parsed = self.parse_autodigitacao(body)

            parsed.update({
                'from': from_email,
                'subject': subject,
                'message_id': msg['id']
            })

            print("📤 Enviando para API Flask:")
            print(parsed)

            if not parsed.get("CPF"):
                print("⚠️ Ignorado: CPF ausente, email fora do padrão.")
                continue

            try:
                # 🚨 IP da máquina A com porta 8000 e rota correta
                response = requests.post("https://b350e818909a.ngrok-free.app/api/autodigitacao", json=parsed)
                print(f"✅ Resposta da API: {response.status_code} - {response.text}")
            except Exception as e:
                print("❌ Erro ao enviar para API Flask:", str(e))

            parsed_emails.append(parsed)

            # Marca como lido
            self.service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

        return parsed_emails

    def extract_body(self, payload):
        if 'body' in payload and 'data' in payload['body']:
            raw_data = payload['body']['data']
            decoded = urlsafe_b64decode(raw_data).decode('utf-8')
            if payload.get('mimeType', '').startswith('text/html'):
                return self.clean_html(decoded)
            return decoded

        if 'parts' in payload:
            for part in payload['parts']:
                result = self.extract_body(part)
                if result:
                    return result

        return ""

    def clean_html(self, raw_html):
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def parse_autodigitacao(self, body):
        parsed = {
            "CPF": "",
            "OPERAÇÃO": "",
            "ENTIDADE": "",
            "TELEFONE": "",
            "BANCO": "",
            "AGÊNCIA": "",
            "CONTA": "",
            "DÍGITO DA CONTA": ""
        }

        linhas = [linha.strip() for linha in body.splitlines() if linha.strip()]

        try:
            if linhas[0].upper() == "NOVA PROPOSTA":
                linhas = linhas[1:]

            if len(linhas) < 7:
                raise ValueError("Email com número de linhas insuficiente")

            parsed["CPF"] = linhas[0]
            parsed["OPERAÇÃO"] = linhas[1]
            parsed["ENTIDADE"] = linhas[2]
            # Formatando o telefone: remove tudo que não for dígito e remove o +55 se houver
            telefone_bruto = linhas[3]
            telefone_limpo = re.sub(r'\D', '', telefone_bruto)

            if telefone_limpo.startswith("55") and len(telefone_limpo) > 11:
                telefone_limpo = telefone_limpo[2:]

            parsed["TELEFONE"] = telefone_limpo




            parsed["BANCO"] = linhas[4]
            parsed["AGÊNCIA"] = linhas[5]

            conta_cheia = linhas[6]
            if "-" in conta_cheia:
                conta, digito = conta_cheia.split("-")
                parsed["CONTA"] = conta.strip()
                parsed["DÍGITO DA CONTA"] = digito.strip()
            else:
                parsed["CONTA"] = conta_cheia.strip()

            if len(linhas) >= 8 and "-" in linhas[7]:
                conta2, digito2 = linhas[7].split("-")
                parsed["CONTA"] = conta2.strip()
                parsed["DÍGITO DA CONTA"] = digito2.strip()

        except Exception as e:
            print("❌ Erro ao processar e-mail:")
            print(str(e))
            print("Conteúdo recebido:")
            for i, linha in enumerate(linhas):
                print(f"{i}: {linha}")

        return parsed















