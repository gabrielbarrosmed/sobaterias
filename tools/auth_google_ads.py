"""
Gera o refresh_token com escopo Google Ads e cria o google-ads.yaml.
Execute: python tools/auth_google_ads.py
"""
import json
import os
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

CLIENT_ID = os.environ.get("GOOGLE_ADS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_ADS_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8080"
SCOPE = "https://www.googleapis.com/auth/adwords"

auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Autenticacao concluida! Pode fechar esta aba.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Erro: codigo nao encontrado.")

    def log_message(self, format, *args):
        pass  # silencia logs do servidor

def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    return "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)

def exchange_code_for_token(code):
    data = urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    developer_token = input("Cole seu Developer Token do Google Ads: ").strip()
    customer_id = input("Cole seu Customer ID (formato 123-456-7890): ").strip().replace("-", "")

    url = get_auth_url()
    print(f"\nAbrindo navegador para autorizacao...")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    print("Aguardando callback em http://localhost:8080 ...")
    server.handle_request()

    if not auth_code:
        print("Erro: nao foi possivel obter o codigo de autorizacao.")
        return

    print("Trocando codigo por token...")
    token_data = exchange_code_for_token(auth_code)
    refresh_token = token_data.get("refresh_token")

    if not refresh_token:
        print(f"Erro: refresh_token nao retornado. Resposta: {token_data}")
        return

    yaml_content = f"""developer_token: {developer_token}
client_id: {CLIENT_ID}
client_secret: {CLIENT_SECRET}
refresh_token: {refresh_token}
login_customer_id: {customer_id}
use_proto_plus: True
"""

    yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "google-ads.yaml")
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"\nArquivo google-ads.yaml criado em: {yaml_path}")
    print("Autenticacao concluida com sucesso!")

if __name__ == "__main__":
    main()
