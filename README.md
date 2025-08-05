Anki-lookup Anki Add-on (Auxiliador de Estudos de Idiomas)

Este é um auxiliar de estudos de idiomas que utiliza uma API não oficial do Reverso Context para criar flashcards automaticamente e enviá-los para o Anki.

⚠️ Funciona como add-on externo ao Anki — você roda ele separadamente, como uma aplicação.
obs: a parte de add-on ainda está sendo desenvolvida

# Pré-requisitos

Antes de usar, você precisa ter instalado:

- Node.js + npm
- Python 3

# Instalação

Para instalar todas as dependências (Python e Node.js), execute:
```bash
    ./start.sh
```
Esse script irá:

    - Criar um ambiente virtual Python (venv)

    - Instalar os pacotes do requirements.txt

    - Instalar as dependências do npm e do playwright dentro da pasta reverso_scraper

# Como usar

Após instalar as dependências, ative o ambiente virtual e inicie o app:
```bash
    source venv/bin/activate
    python3 app.py
```
Certifique-se de estar na raiz do projeto para executar os comandos acima.
