"""
Passo 1: Gera URL de autorização Google Ads
Execute: python3 tools/get_ads_token.py
"""
from urllib.parse import urlencode

CLIENT_ID = "948827079596-ggfoi1b29ll2uid7g8sshnl835ceboqf.apps.googleusercontent.com"
REDIRECT_URI = "http://localhost"
SCOPE = "https://www.googleapis.com/auth/adwords"

params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",
}

url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)
print("\n=== PASSO 1: Acesse esta URL no navegador ===")
print(url)
print("\n=== PASSO 2: Após autorizar, copie o valor do parametro 'code' da URL de redirecionamento ===")
print("A URL vai parecer: http://localhost/?code=XXXX&scope=...")
print("Copie apenas o valor de 'code' e me passe.\n")
