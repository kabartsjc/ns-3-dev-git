
import requests

# Substitua pelos valores corretos
client_id = "kabart@gmail.com-api-client"
client_secret = "QCi4051bsTpXkVKM4Z51U2S0DXYvvWJo"

# URL de autenticação para pegar o token
url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
}

# Solicitando o token
response = requests.post(url, headers=headers, data=data)

# Verificando se obtemos o token com sucesso
if response.status_code == 200:
    access_token = response.json().get("access_token")
else:
    print("Erro ao obter token:", response.status_code)
    print(response.text)
    exit()  # Se não obter o token, interrompe o fluxo

# URL da API de voos
api_url = "https://opensky-network.org/api/flights/arrival?airport=EDDF&begin=1517227200&end=1517230800"
flight_headers = {
    "Authorization": f"Bearer {access_token}"
}

# Requisição para obter os voos
flight_response = requests.get(api_url, headers=flight_headers)

# Verificando a resposta da API de voos
if flight_response.status_code == 200:
    flights = flight_response.json()
    if flights:
        for f in flights:
            print(f)
    else:
        print("Nenhum voo encontrado.")
else:
    print("Erro na API de voos:", flight_response.status_code)
    print(flight_response.text)
