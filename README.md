# PY_VPN
>>>>>>> 7f54489 (Initial commit)
# PY_VPN
>>>>>>> fd9d070 (Commit inicial do projeto com setup de produção)
# Projeto Site de Reviews de VPNs

## 1. Visão Geral

Este projeto é uma aplicação web construída com Django (Python) destinada a ser um site completo de reviews de VPNs. Ele permite que administradores gerenciem conteúdo de VPNs, categorias, cupões de desconto e páginas personalizadas através de um dashboard intuitivo. O frontend público exibe essas informações de forma organizada e amigável para os usuários finais, ajudando-os a escolher a melhor VPN para as suas necessidades.

## 2. Funcionalidades Principais

### 2.1. Dashboard de Administração (`/dashboard/`)

*   **Gestão de VPNs:**
    *   Criação, Leitura, Atualização e Exclusão (CRUD) de entradas de VPNs.
    *   Upload de logos de VPNs (com prioridade sobre URLs externas).
    *   Uso do CKEditor 5 para edição rica de reviews completas, prós e contras.
    *   Definição de classificações detalhadas (velocidade, streaming, privacidade, etc.).
    *   Configuração de links de afiliados.
*   **Gestão de Categorias:**
    *   CRUD para categorias de VPNs (ex: "Melhores VPNs para Streaming", "VPNs para Privacidade").
*   **Gestão de Cupões:**
    *   CRUD para cupões de desconto associados a VPNs.
*   **Gestão de Páginas Personalizadas:**
    *   Criação de páginas com conteúdo estático/informativo usando CKEditor 5.
*   **Configurações do Site:**
    *   (Funcionalidade a ser detalhada ou implementada)
*   **Visão Geral de Analytics:**
    *   Exibição de gráficos de visitas, bots e cliques de afiliados (usando Chart.js).

### 2.2. Frontend Público

*   **Homepage (`/`):**
    *   Destaque para as 3 VPNs com melhor classificação geral e marcadas para exibição na homepage.
*   **Páginas de Listagem de VPNs:**
    *   Exibição de VPNs filtradas por categoria (ex: `/best-vpns-for-privacy/`).
*   **Páginas de Detalhe de VPNs (ex: `/vpn/nordvpn/`):**
    *   Review completa da VPN.
    *   Exibição do logo (upload > URL externa > placeholder).
    *   Classificações detalhadas em formato de barras de progresso.
    *   Lista de prós e contras.
    *   Dispositivos suportados.
    *   Informações como país de origem, número de servidores, política de logs.
    *   Link de afiliado proeminente.
    *   Schema.org (JSON-LD) para SEO.
*   **Páginas de Categorias:**
    *   Lista de VPNs pertencentes a uma categoria específica.

### 2.3. Funcionalidades Técnicas

*   **Design Responsivo:** Interface adaptável a diferentes tamanhos de ecrã utilizando Tailwind CSS.
*   **Elementos de UI Interativos:**
    *   Alpine.js para funcionalidades como pré-visualização de logo no upload (dashboard).
*   **Content Security Policy (CSP):**
    *   Implementação de uma política de segurança de conteúdo robusta para mitigar ataques XSS, configurada em `core/middleware.py`.
*   **Rastreamento de Cliques de Afiliados:**
    *   Registo anónimo de cliques nos links de afiliados para fins de análise.
*   **Serviço de Arquivos Estáticos:**
    *   Whitenoise para servir arquivos estáticos em produção.
*   **Variáveis de Ambiente:**
    *   Uso de `python-dotenv` para gerir configurações sensíveis.

## 3. Stack Tecnológica

*   **Backend:**
    *   Python 3.x
    *   Django 5.2.3 (ou a versão em `requirements.txt`)
*   **Frontend:**
    *   HTML5
    *   Tailwind CSS (para estilização)
    *   Alpine.js (para interatividade leve)
    *   Chart.js (para gráficos no dashboard)
    *   Font Awesome (para ícones)
*   **Base de Dados:**
    *   SQLite (padrão para desenvolvimento)
    *   (Pode ser configurado para PostgreSQL, MySQL, etc., para produção)
*   **Pacotes Django e Python Notáveis:**
    *   `django-ckeditor-5`: Editor de texto rico.
    *   `whitenoise`: Servir arquivos estáticos.
    *   `python-dotenv`: Gerir variáveis de ambiente.
    *   `Pillow`: Processamento de imagens para uploads.

## 4. Estrutura do Projeto

O projeto segue a estrutura padrão de aplicações Django, com as seguintes apps principais:

*   `core/`: Configurações centrais do projeto, middleware (CSP), URLs principais, template base (`base.html`).
*   `vpn/`: Modelos, views e templates relacionados às VPNs (entidades, detalhes públicos, listagens).
*   `categories/`: Modelos, views e templates para as categorias de VPNs.
*   `dashboard/`: Views e templates para a área administrativa (gestão de VPNs, categorias, etc.).
*   `analytics/`: Modelo e lógica para o rastreamento de analytics (visitas, cliques).
*   `coupons/`: Modelos, views e templates para os cupões de desconto.
*   `custom_pages/`: Modelos, views e templates para páginas personalizadas.
*   `static/`: Contém arquivos estáticos globais (CSS, JS, imagens). Cada app também pode ter a sua própria pasta `static/`.
*   `media/`: Diretório onde os arquivos de upload (como logos de VPNs) são armazenados.
*   `templates/`: Contém templates HTML globais. Cada app também tem a sua própria pasta `templates/` (ex: `vpn/templates/vpn/`).

## 5. Configuração e Instalação

Siga os passos abaixo para configurar e executar o projeto localmente:

1.  **Pré-requisitos:**
    *   Python 3.8 ou superior.
    *   `pip` (gerenciador de pacotes Python).
    *   Git.

2.  **Clonar o Repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd <NOME_DA_PASTA_DO_PROJETO>
    ```
    (Substitua `<URL_DO_REPOSITORIO>` e `<NOME_DA_PASTA_DO_PROJETO>` pelos valores corretos)

3.  **Criar e Ativar Ambiente Virtual:**
    ```bash
    python -m venv venv
    # No Windows
    # venv\Scripts\activate
    # No macOS/Linux
    source venv/bin/activate
    ```

4.  **Instalar Dependências:**
    Certifique-se de que o arquivo `requirements.txt` está na raiz do projeto.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configurar Variáveis de Ambiente:**
    *   Crie um arquivo chamado `.env` na raiz do projeto (ao lado de `manage.py`).
    *   Adicione as seguintes variáveis (ajuste conforme necessário):
        ```env
        SECRET_KEY='django_insecure_your_secret_key_here'  # Substitua por uma chave secreta forte
        DEBUG=True
        ALLOWED_HOSTS='127.0.0.1,localhost'

        # Configurações de Email (opcional, para funcionalidades de email)
        # EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
        # EMAIL_HOST='smtp.example.com'
        # EMAIL_PORT=587
        # EMAIL_USE_TLS=True
        # EMAIL_HOST_USER='your_email@example.com'
        # EMAIL_HOST_PASSWORD='your_email_password'
        ```
    *   **Importante:** Para produção, `DEBUG` deve ser `False` e `SECRET_KEY` deve ser única e secreta.

6.  **Aplicar Migrações da Base de Dados:**
    Isso criará as tabelas da base de dados (SQLite por padrão).
    ```bash
    python manage.py migrate
    ```

7.  **Criar um Superusuário:**
    Este usuário será usado para aceder ao dashboard de administração.
    ```bash
    python manage.py createsuperuser
    ```
    Siga as instruções para definir nome de usuário, email e senha.

8.  **Coletar Arquivos Estáticos (Necessário se `DEBUG=False`):**
    Embora não seja estritamente necessário para `DEBUG=True` com o servidor de desenvolvimento, é uma boa prática.
    ```bash
    python manage.py collectstatic
    ```

9.  **Executar o Servidor de Desenvolvimento:**
    ```bash
    python manage.py runserver
    ```
    A aplicação estará disponível em `http://127.0.0.1:8000/`.

## 6. Uso

*   **Dashboard de Administração:** Acesse `http://127.0.0.1:8000/dashboard/` e faça login com as credenciais do superusuário criado.
*   **Site Público:** Navegue a partir de `http://127.0.0.1:8000/`.

## 7. Detalhes de Funcionalidades Chave

### 7.1. Gestão de VPNs e Logos

*   Ao adicionar ou editar uma VPN no dashboard, você pode:
    *   Fazer upload de um arquivo de imagem para o logo.
    *   Fornecer uma URL para um logo externo.
*   **Lógica de Exibição do Logo:** O sistema prioriza a exibição de logos da seguinte forma:
    1.  Logo carregado via upload (`vpn.logo_upload`).
    2.  Logo de URL externa (`vpn.logo`).
    3.  Imagem placeholder (`static/dashboard/images/placeholder.png`) se nenhum dos anteriores estiver disponível.
*   O CKEditor 5 é usado para os campos "Full Review", "Pros" e "Cons", permitindo formatação rica.

### 7.2. Content Security Policy (CSP)

*   A CSP é definida no middleware `core.middleware.SecurityHeadersMiddleware`.
*   Ela ajuda a prevenir ataques XSS restringindo as fontes de onde os scripts, estilos, imagens, etc., podem ser carregados.
*   A política inclui:
    *   `default-src 'self'`: Permite conteúdo do próprio domínio por padrão.
    *   `script-src 'self' https://cdn.jsdelivr.net 'nonce-{request.csp_nonce}' 'unsafe-inline' 'unsafe-eval'`: Permite scripts do próprio domínio, do CDN `jsdelivr.net`, scripts inline com um `nonce` gerado por requisição, e (`'unsafe-inline'`, `'unsafe-eval'` foram adicionados para compatibilidade com Alpine.js e Chart.js, mas idealmente seriam removidos/refinados para maior segurança).
    *   `style-src 'self' https://fonts.googleapis.com https://cdn.jsdelivr.net 'unsafe-inline'`: Permite estilos do próprio domínio, Google Fonts, `jsdelivr.net` e estilos inline.
    *   Outras diretivas para `img-src`, `font-src`, etc.
*   Um `nonce` é gerado para cada requisição e pode ser usado para permitir scripts inline específicos (ex: scripts de dados para Chart.js).

### 7.3. Analytics

*   A app `analytics` possui um modelo `Analytics` que regista eventos como:
    *   Visitas a páginas (middleware de rastreamento de visitas).
    *   Cliques em links de afiliados.
*   Os dados agregados são usados para popular os gráficos no dashboard.
    *   (Detalhes sobre o middleware de rastreamento de visitas podem ser adicionados se explorados).

## 8. Arquivos Estáticos e de Mídia

## Scripts Auxiliares e Estrutura Adicional

- `manage.sh`: Menu interativo para instalação, backup, restore e visualização do `.env` em ambiente Docker.
- `auto_setup_production.sh`: Automatiza deploy completo em VPS (Nginx, Gunicorn, banco, SSL).
- `lighthouse_audit.sh`: Gera relatórios Lighthouse para múltiplas rotas do site.
- `backups/`: Pasta onde os arquivos de backup são salvos/restaurados.
- `lighthouse_reports/`: Relatórios de performance/acessibilidade.
- `prize_wheel/`: App de roleta de prêmios, com popup JS, integração backend/frontend e lógica para sorteios.

## Observações Importantes

- **Arquivos grandes** (>100MB) não são suportados no GitHub. Use [Git LFS](https://git-lfs.github.com/) se necessário.
- `.env`, arquivos de backup e outros dados sensíveis estão no `.gitignore` e não devem ser versionados.


*   **Arquivos Estáticos (`static/`):**
    *   CSS, JavaScript, imagens que fazem parte do design do site.
    *   Geridos pelo Django durante o desenvolvimento.
    *   Whitenoise é configurado para servir arquivos estáticos em um ambiente de produção.
    *   `STATIC_URL = '/static/'`
    *   `STATIC_ROOT` é para onde `collectstatic` copia os arquivos.
*   **Arquivos de Mídia (`media/`):**
    *   Arquivos carregados pelo usuário, como logos de VPNs.
    *   `MEDIA_URL = '/media/'`
    *   `MEDIA_ROOT = BASE_DIR / 'media'`
    *   A configuração de URLs em `core/urls.py` inclui o necessário para servir arquivos de mídia durante o desenvolvimento (`DEBUG=True`).

## 9. Possíveis Melhorias Futuras

*   Testes automatizados (unitários e de integração).
*   Refinamento da CSP para remover `'unsafe-inline'` e `'unsafe-eval'` se possível (ex: usando builds CSP-friendly de bibliotecas JS ou refatorando scripts).
*   Paginação para listas longas (VPNs, categorias).
*   Funcionalidade de pesquisa avançada para VPNs.
*   Internacionalização (i18n) e Localização (l10n).
*   Otimizações de performance (caching, otimização de queries de base de dados).
*   Implementação completa da seção "Configurações do Site" no dashboard.
*   Melhorar a segurança e validação de todos os formulários.

---

Este README.md visa fornecer uma visão abrangente do projeto. Sinta-se à vontade para atualizá-lo conforme o projeto evolui!

---

Atualizado para refletir todos os scripts, apps e práticas reais do projeto PY_VPN (incluindo prize_wheel, backups, lighthouse_reports, e scripts de gestão).

A production-ready, modern, and secure VPN Review platform built with Django 5, Django Templates, TailwindCSS, Alpine.js, HTMX, Lucide Icons, and Font Awesome.

## Features
- **Custom Admin Dashboard** (`/dashboard`) with Tabler-inspired UI, analytics cards, CRUD for VPNs, categories, coupons, blog, and settings
- **Public Site**: Homepage, dynamic category pages, VPN cards, reviews, coupons, blog, FAQ, contact
- **Modern UI**: TailwindCSS, Alpine.js, HTMX, Lucide, Font Awesome
- **SEO & Accessibility**: Dynamic meta tags, JSON-LD, OpenGraph, ARIA, keyboard navigation
- **Responsive**: Mobile-first, fully responsive design
- **Analytics**: Custom middleware for visits, bots, affiliate clicks
- **Security**: CSRF, login protection, production settings

## Quick Start

### 1. Clone & Install
```bash
git clone <repo-url>
cd PY_VPN
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file or export variables:
```
DJANGO_SECRET_KEY=your-production-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1
```

### 3. Database & Static Files
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

### 4. Sample Data (optional)
```bash
python scripts/sample_data.py
```

### 5. Run Locally
```bash
python manage.py runserver
```

### 6. Production (example: Gunicorn + Nginx)
- Use Gunicorn: `gunicorn core.wsgi:application`
- Serve static files via Nginx
- Set all env vars and DEBUG=False

## Deployment
- All static/media files configured for production
- SEO: Sitemap.xml, robots.txt, meta tags, JSON-LD
- Secure admin, CSRF, and proper ALLOWED_HOSTS

## Tech Stack
- Django 5.x
- TailwindCSS (CDN)
- Alpine.js, HTMX, Lucide, Font Awesome (CDN)

## Folder Structure
- `core/` – Main settings and URLs
- `vpn/` – VPN models, views, templates
- `categories/`, `coupons/`, `blog/`, `dashboard/`, `settings/`
- `templates/` – All HTML templates
- `static/` – Static files (collected)
- `scripts/` – Sample data scripts

## Accessibility & SEO
- ARIA roles, landmarks, skip links
- Keyboard navigation
- Dynamic meta tags and structured data

## Contributing
Pull requests welcome! Please lint and test before submitting.

---

For issues or questions, open an issue or contact via the site’s contact form.
>>>>>>> fd9d070 (Commit inicial do projeto com setup de produção)
>>>>>>> fd9d070 (Commit inicial do projeto com setup de produção)
>>>>>>> 7f54489 (Initial commit)
