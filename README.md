# Reverso Context & AI Lookup + TTS & Images (Anki Add-on)

Add-on nativo para o **Anki** focado no estudo de idiomas. Permite buscar frases contextualizadas no **Reverso Context**, gerar exemplos personalizados e explicações gramaticais com **Inteligência Artificial (LLM)**, anexar **Imagens** (via busca web, IA, área de transferência ou arquivo) e adicionar **Text-to-Speech (TTS)** neural diretamente nos seus flashcards.

## Principais Funcionalidades

- **Integração Nativa com o Anki (`aqt` & `mw.col`)**:
  - Funciona diretamente dentro do Anki via menu **Ferramentas -> Reverso Context & AI Lookup...** (`Ctrl+Shift+R`) ou pelo botão **Reverso AI** no editor de cards.
  - Cria automaticamente o modelo de nota estilizado **`Reverso AI Card`** (com campos para Frase, Tradução, Explicação Contextual, Imagem, Áudio e Palavra) ou permite mapear para qualquer Note Type já existente.
  - Zero dependência de Node.js, Playwright ou AnkiConnect.
- **Busca Instantânea no Reverso Context**:
  - Cliente HTTP em Python puro que retorna traduções diretas e exemplos reais com a palavra-alvo destacada.
- **Geração de Frases e Explicações com IA**:
  - Gere frases inéditas adaptadas ao seu nível de proficiência (**A1 a C2**) e estilo (*Conversação natural, Formal/Profissional, Viagem, Expressões Idiomáticas, Acadêmico*).
  - Botão **Explicar com IA** em qualquer frase (inclusive do Reverso) para gerar notas gramaticais e semânticas para o verso do card.
  - Suporte a **Google Gemini**, **OpenAI**, **Groq** e **Ollama (Local)**.
- **Imagens nos Cards (Web, IA, Clipboard e Arquivo Local)**:
  - Botão **Imagem** em cada frase para anexar ilustrações ao card.
  - Inclui **Busca de Imagens na Web** gratuita (Wikimedia Commons / Openverse), **Geração de Imagem com IA** (OpenAI DALL-E, Gemini Imagen ou motor gratuito Pollinations), **Colar da Área de Transferência** e seleção de arquivo do computador.
- **Text-to-Speech (TTS) feito por IA**:
  - Botão **Ouvir** em cada frase para pré-escuta imediata usando o player nativo do Anki.
  - Anexação automática do arquivo de áudio (`[sound:...]`) na pasta `collection.media` do Anki ao enviar os cards.
  - Suporte a **Modo Gratuito (Vozes Neurais / Sem API Key)**, **OpenAI Audio TTS** (`gpt-4o-mini-tts` / `tts-1`), **Google Gemini Audio TTS** e **ElevenLabs**.

---

## Como Instalar no Anki

### Opção 1: Instalação Automática (Desenvolvimento)
Execute o script de empacotamento com a flag `--install` para copiar o add-on diretamente para a pasta `addons21` do seu Anki:

```bash
python3 scripts/build_addon.py --install
```

Depois, basta reiniciar o Anki.

### Opção 2: Gerar arquivos `.ankiaddon`
Para gerar os pacotes instaláveis `.ankiaddon` na pasta `dist/`:

```bash
python3 scripts/build_addon.py
```

No Anki, acesse **Ferramentas -> Complementos (Add-ons) -> Instalar a partir de arquivo...** e selecione `dist/anki_reverso_ai_addon.ankiaddon`.
