# Pontos de Destaque do Projeto para Currículo (Cultura Viva Tacima)

Aqui estão sugestões de textos, conquistas e tecnologias deste projeto estruturados em formatos comumente utilizados em currículos, perfis do LinkedIn ou portfólios.

---

## 📝 Descrição Sintética do Projeto (Para Resumo Profissional)

> **Cultura Viva Tacima** — Plataforma digital desenvolvida para impulsionar a economia criativa e a visibilidade de artistas locais em Tacima/PB. Trata-se de uma aplicação monolítica robusta contendo loja virtual própria, gestão de eventos, divulgação de projetos sociais e integração completa com o gateway de pagamentos Asaas para automação de cobranças e faturamento.

---

## 🛠️ Tecnologias a Destacar

- **Linguagens e Frameworks**: Python, Django, Celery
- **Bancos de Dados e Cache**: PostgreSQL, SQLite, Redis (Caching)
- **Mensageria & Filas**: RabbitMQ, Celery Workers
- **DevOps & Infraestrutura**: Docker, Docker Compose, Shell Scripting (`entrypoint.sh`), Git, `django-environ`
- **Integrações**: API REST do Asaas (Pagamentos), Webhooks HTTP, Django Summernote (Rich Text Editor)

---

## 🎯 Conquistas e Responsabilidades (Formato Bullet Points)

Você pode copiar e colar estes tópicos diretamente na seção de **Experiência Profissional** ou **Projetos**:

- **Arquitetura Modular**: Desenhei e implementei uma arquitetura desacoplada em Django composta por mais de 10 aplicações internas (ex: `shop`, `payments`, `events`, `artistas`), garantindo alta manutenibilidade, separação de conceitos e extensibilidade do código.
- **Processamento Assíncrono**: Configurei **Celery** com **RabbitMQ** e **Redis** para a execução de tarefas em segundo plano (como disparo de e-mails transacionais e sincronização de dados), otimizando a latência do ciclo requisição-resposta.
- **Integração Financeira Avançada**: Implementei do zero a integração com a **API do gateway Asaas**, abrangendo fluxos de pagamento via Pix, Cartão de Crédito e Boleto Bancário, além de conceber um receptor de **Webhooks** robusto para conciliação bancária em tempo real.
- **Containerização Completa**: Criei e mantive arquivos de configuração **Docker** e **Docker Compose** para padronizar o ambiente de desenvolvimento e produção entre a base de dados PostgreSQL, mensageria RabbitMQ e servidor web Django.
- **Automação de Inicialização**: Desenvolvi scripts em bash (`entrypoint.sh`) para automatizar a verificação de saúde do banco de dados, migrações automáticas de schema (`migrate`) e provisionamento dinâmico de superusuários administrativos em novos deploys.
- **Gerenciamento de Conteúdo Dinâmico**: Acoplei o editor de texto rico **Django Summernote** para permitir que criadores de conteúdo e administradores façam upload de mídias e formatem artigos/projetos sem necessidade de conhecimento técnico.

---

## 💡 Exemplos de Descrição de Projeto por Nível

### Versão Curta (Foco em Espaço)
> **Desenvolvedor de Software | Cultura Viva Tacima (Django/Docker/Celery)**
> Plataforma voltada para a economia criativa local com e-commerce e catálogo de artistas. Implementei a integração de pagamentos (Asaas API e Webhooks), processamento assíncrono de tarefas com Celery/RabbitMQ e containerizei todo o ecossistema com Docker, facilitando o deploy e a escalabilidade da aplicação.

### Versão Detalhada (Foco em Impacto Técnico)
> **Cultura Viva Tacima — Plataforma de E-commerce e Gestão Cultural**
> *Tecnologias: Python, Django, Celery, PostgreSQL, Redis, RabbitMQ, Docker, Asaas API*
> - Desenvolvi uma plataforma integrada de e-commerce e rede de artistas com suporte a múltiplos perfis de usuários.
> - Integrei a API do Asaas e criei endpoints para consumir Webhooks com segurança, atualizando o status de transações de forma assíncrona.
> - Reduzi o tempo de setup local e inconsistências entre ambientes a zero através da containerização de todos os serviços usando Docker e Docker Compose.
> - Otimizei o processamento do servidor principal implementando filas de tarefas assíncronas com Celery e Redis.
