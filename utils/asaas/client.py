import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AsaasClient:
    """
    Cliente para integração com a API do Asaas.
    Documentação: https://docs.asaas.com/
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.ASAAS_API_KEY
        self.base_url = settings.ASAAS_BASE_URL
        self.headers = {
            'access_token': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'CulturaVivaTacima/1.0'
        }

    def _post(self, endpoint, data):
        url = f"{self.base_url}/{endpoint}"
        print(f' Chave: {self.api_key}')
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Asaas API Error (POST {endpoint}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    return e.response.json()
                except ValueError:
                    return {"errors": [{"description": e.response.text}]}
            return {"errors": [{"description": str(e)}]}

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Asaas API Error (GET {endpoint}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    return e.response.json()
                except ValueError:
                    return {"errors": [{"description": e.response.text}]}
            return {"errors": [{"description": str(e)}]}

    def create_subaccount(self, data):
        """
        Cria uma subconta para um vendedor (Split de Pagamentos).
        """
        return self._post("accounts", data)

    def list_subaccounts(self, cpfCnpj=None):
        """
        Lista as subcontas vinculadas à conta principal.
        """
        params = {}
        if cpfCnpj: params['cpfCnpj'] = cpfCnpj
        return self._get("accounts", params=params)

    def create_payment(self, data):
        """
        Cria uma nova cobrança (Pix, Cartão de Crédito ou Boleto).
        """
        return self._post("payments", data)

    def get_payment(self, payment_id):
        """
        Recupera os detalhes de um pagamento específico.
        """
        return self._get(f"payments/{payment_id}")

    def get_payment_pix_data(self, payment_id):
        """
        Retorna o QR Code e o código 'Copia e Cola' para pagamentos via Pix.
        """
        return self._get(f"payments/{payment_id}/pixQrCode")

    def get_or_create_customer(self, data):
        """
        Busca um cliente pelo e-mail. Se não existir, cria um novo.
        """
        email = data.get('email')
        resp = self._get("customers", params={"email": email})
        
        if resp.get('data') and len(resp['data']) > 0:
            customer = resp['data'][0]
            # Se o cliente existe mas não tem CPF e nós temos um CPF para fornecer
            if not customer.get('cpfCnpj') and data.get('cpfCnpj'):
                return self.update_customer(customer['id'], {"cpfCnpj": data['cpfCnpj']})
            return customer
        
        return self.create_customer(data)

    def create_customer(self, data):
        """
        Cria um novo cliente no sistema do Asaas.
        """
        return self._post("customers", data)

    def get_onboarding_link(self):
        """
        Gera a URL para o fluxo de verificação de identidade (KYC).
        No Asaas v3, o onboardingUrl vem dentro da lista de documentos.
        """
        resp = self._get("myAccount/documents")
        if resp.get('data') and len(resp['data']) > 0:
            # Pegamos a onboardingUrl do primeiro documento pendente
            for doc in resp['data']:
                if doc.get('onboardingUrl'):
                    return {"onboardingUrl": doc['onboardingUrl']}
        
        return resp

    def create_subaccount_api_key(self, account_id):
        """
        Gera uma nova chave de API para uma subconta (requer chave da conta principal).
        """
        return self._post(f"accounts/{account_id}/apiKey", {})

    def sandbox_approve_account(self):
        """
        Aprova automaticamente a conta no ambiente de Sandbox.
        """
        return self._post("sandbox/myAccount/approve", {})

    def refund_payment(self, payment_id, value=None, description=None):
        """
        Realiza o estorno de uma cobrança confirmada.
        """
        data = {}
        if value: data['value'] = value
        if description: data['description'] = description
        return self._post(f"payments/{payment_id}/refund", data)

    def cancel_payment(self, payment_id):
        """
        Cancela uma cobrança pendente.
        """
        return self._post(f"payments/{payment_id}/cancel", {})

    def transfer_funds(self, wallet_id, value):
        """
        Realiza uma transferência interna da conta principal para uma subconta.
        Utilizado para repasse manual de splits retidos.
        """
        data = {
            "walletId": wallet_id,
            "value": float(value)
        }
        return self._post("transfers", data)

    def list_payments(self, params=None):
        """
        Lista e filtra cobranças do sistema.
        """
        return self._get("payments", params=params)

    def get_balance(self):
        """
        Retorna o saldo disponível na conta.
        """
        return self._get("finance/balance")

    def update_customer(self, customer_id, data):
        """
        Atualiza as informações de um cliente cadastrado.
        """
        return self._post(f"customers/{customer_id}", data)
