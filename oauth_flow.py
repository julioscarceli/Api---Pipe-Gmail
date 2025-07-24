# Script para gerar o refresh_token

from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    # 1️⃣ Inicia o fluxo com offline e consent!
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://mail.google.com/']
    )

    creds = flow.run_local_server(port=8000, access_type='offline', prompt='consent')

    print('ACCESS TOKEN:', creds.token)
    print('REFRESH TOKEN:', creds.refresh_token)

if __name__ == '__main__':
    main()
