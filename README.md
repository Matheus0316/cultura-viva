# Cultura Viva Tacima

Plataforma cultural de Tacima (PB) que reúne perfis de artistas e grupos, notícias, acervo, eventos e uma loja com produtos e serviços locais. O projeto também oferece recursos de pedidos, agendamentos e pagamentos integrados ao Asaas.

## Funcionalidades

- Cadastro e perfis de artistas, grupos culturais e usuários.
- Publicações, comentários e acervo cultural.
- Agenda de eventos e lembretes.
- Loja de produtos e serviços com pedidos e agendamentos.
- Pagamentos por Pix ou cartão de crédito via Asaas, com suporte a subcontas e divisão de valores.
- Painel administrativo do Django para gerenciar o conteúdo.

## Tecnologias

- Python 3.12 e Django 6.0
- PostgreSQL ou SQLite
- Celery e RabbitMQ para tarefas em segundo plano
- Redis para cache
- Asaas para pagamentos e webhooks
- Docker Compose para desenvolvimento

## Aplicações Django

| Aplicação | Responsabilidade |
| --- | --- |
| `home` | Página inicial e páginas institucionais |
| `artistas` | Perfis e acompanhamento de artistas |
| `grupos` | Grupos, coletivos e projetos sociais |
| `post` | Publicações e notícias |
| `acervo` | Acervo cultural |
| `events` | Eventos e lembretes |
| `comments` | Comentários |
| `perfil` | Perfis de usuário e endereços |
| `shop` | Produtos, serviços, pedidos e agendamentos |
| `payments` | Pagamentos e processamento de webhooks |
| `banking` | Dados bancários e subcontas Asaas |
| `team` | Equipe do projeto |
| `app` | Configurações principais do Django e Celery |

## Requisitos

Para executar localmente, use Python 3.12. Para a opção com containers, instale Docker e Docker Compose.

O SQLite é usado por padrão quando `DB_HOST` não está definido. PostgreSQL é configurado ao definir `DB_HOST`. RabbitMQ é o broker do Celery. Redis é o backend de cache; o `docker-compose.yml` atual não inicia um container Redis, então configure um Redis acessível e defina `REDIS_URL` se a aplicação precisar usar cache.

## Configuração local

1. Crie e ative um ambiente virtual:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

   No Windows, ative com `.venv\Scripts\activate`.

2. Instale as dependências:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto. Para começar com SQLite, as configurações abaixo são suficientes; credenciais de serviços externos são opcionais até que esses recursos sejam usados:

   ```env
   SECRET_KEY=cole-uma-chave-aleatoria-aqui
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # E-mail (opcional)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=
   EMAIL_HOST_PASSWORD=

   # Celery / RabbitMQ
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//

   # Cache / Redis
   REDIS_URL=redis://127.0.0.1:6379/1

   # Asaas: use sandbox durante o desenvolvimento
   ASAAS_API_KEY=
   ASAAS_ENVIRONMENT=sandbox
   WEBHOOK_BASE_URL=https://seu-host-publico
   ```

   Para usar PostgreSQL, defina também `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` e `DB_PORT`. Se `DB_HOST` estiver definido, esses valores selecionam a conexão PostgreSQL.

4. Aplique as migrações e inicie o servidor:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. Para processar tarefas em segundo plano, inicie um worker Celery em outro terminal. RabbitMQ deve estar ativo e acessível pela URL em `CELERY_BROKER_URL`:

   ```bash
   celery -A app worker -l info
   ```

Crie um usuário administrador local com `python manage.py createsuperuser`.

## Executar com Docker Compose

O Compose inicia PostgreSQL, RabbitMQ, a aplicação web e o worker Celery:

```bash
docker compose up --build
```

Endereços locais:

- Aplicação: <http://localhost:8000>
- Administração: <http://localhost:8000/admin/>
- Gerenciamento do RabbitMQ: <http://localhost:15672/> (`guest` / `guest` no ambiente local)

O `entrypoint.sh` aguarda o PostgreSQL, gera e aplica migrações e coleta os arquivos estáticos. Quando iniciado sem comando explícito, também cria o usuário `admin` com senha `admin`; essa conta serve apenas para desenvolvimento local. Altere a senha antes de usar qualquer ambiente acessível por outras pessoas.

Para encerrar os containers, use `docker compose down`. Os dados do PostgreSQL ficam no volume `postgres_data`; para removê-los junto com os containers, use `docker compose down -v`.

## Pagamentos e webhook Asaas

Configure `ASAAS_API_KEY` e `ASAAS_ENVIRONMENT` no `.env`. Use `sandbox` para desenvolvimento e `production` para credenciais de produção. A URL do webhook é formada com `WEBHOOK_BASE_URL` e a rota abaixo:

```text
https://seu-host-publico/api/webhook/asaas/
```

O Asaas precisa conseguir acessar essa URL pela internet. Para desenvolvimento local, use um túnel HTTPS e informe o host público em `WEBHOOK_BASE_URL`. Ao executar com Docker Compose, o arquivo `.env` é lido pelo Django a partir da raiz montada do projeto.

## Rotas principais

| Recurso | Rota |
| --- | --- |
| Início | `/` |
| Artistas | `/artistas/` |
| Acervo | `/acervo/` |
| Grupos e projetos | `/grupos/` |
| Publicações | `/publicações/` |
| Eventos | `/events/` |
| Loja | `/loja/` |
| Pagamentos | `/pagamentos/` |
| Banking | `/banking/` |
| Webhook Asaas | `/api/webhook/asaas/` |
| Administração | `/admin/` |
