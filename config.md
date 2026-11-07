# Configurações do Add-on: Reverso Context & AI Lookup + TTS

Você pode editar estas configurações diretamente pela interface do Add-on clicando no botão **Configurações** ou alterando o JSON ao lado.

## Campos Principais

- **`default_source_lang` / `default_target_lang`**: Idiomas padrão de origem e destino (ex: `"english"`, `"portuguese"`, `"spanish"`, `"french"`, `"german"`, `"italian"`, `"japanese"`).
- **`use_custom_note_type`**: Quando `true`, o add-on pode criar/usar o modelo de nota dedicado **`Reverso AI Card`** com campos para Frase, Tradução, Explicação da IA e Áudio.
- **`auto_generate_tts_on_send`**: Quando `true`, gera e anexa automaticamente o áudio (`[sound:...]`) para todas as frases enviadas ao Anki.

## Provedor de IA (`ai_provider`)

Opções suportadas:
- `"gemini"`: Google Gemini API (ex: `gemini-2.5-flash` ou `gemini-2.0-flash`).
- `"openai"`: OpenAI API (ex: `gpt-4o-mini`, `gpt-4o`).
- `"groq"`: Groq API (ex: `llama-3.3-70b-versatile`).
- `"ollama"`: Servidor local Ollama ou endpoint compatível com OpenAI (`ai_base_url`, ex: `http://localhost:11434/v1`).

## Provedor de Text-to-Speech (`tts_provider`)

Opções suportadas:
- `"free_neural"`: Vozes neurais gratuitas (Microsoft Edge Neural / Google / Reverso Voice) sem necessidade de chave de API.
- `"openai"`: OpenAI Audio Speech (`gpt-4o-mini-tts` ou `tts-1`, vozes: `alloy`, `ash`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`).
- `"gemini"`: Geração de áudio nativo com modelos Gemini (`gemini-2.0-flash` / `gemini-2.5-flash-preview-tts`).
- `"elevenlabs"`: ElevenLabs Multilingual v2 (`eleven_multilingual_v2`).
