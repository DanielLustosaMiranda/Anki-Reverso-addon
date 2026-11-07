from typing import Dict, List

# Mapeamento completo de idiomas suportados pelo Reverso, IA e TTS
LANGUAGE_INFO: Dict[str, Dict[str, str]] = {
    "english": {
        "label": "Inglês (English)",
        "reverso_code": "eng",
        "iso_code": "en",
        "locale": "en-US",
        "reverso_voice": "Heather22k",
        "edge_voice": "en-US-AriaNeural",
    },
    "portuguese": {
        "label": "Português (Portuguese)",
        "reverso_code": "por",
        "iso_code": "pt",
        "locale": "pt-BR",
        "reverso_voice": "Celia22k",
        "edge_voice": "pt-BR-FranciscaNeural",
    },
    "spanish": {
        "label": "Espanhol (Spanish)",
        "reverso_code": "spa",
        "iso_code": "es",
        "locale": "es-ES",
        "reverso_voice": "Ines22k",
        "edge_voice": "es-ES-ElviraNeural",
    },
    "french": {
        "label": "Francês (French)",
        "reverso_code": "fra",
        "iso_code": "fr",
        "locale": "fr-FR",
        "reverso_voice": "Alice22k",
        "edge_voice": "fr-FR-DeniseNeural",
    },
    "german": {
        "label": "Alemão (German)",
        "reverso_code": "ger",
        "iso_code": "de",
        "locale": "de-DE",
        "reverso_voice": "Claudia22k",
        "edge_voice": "de-DE-KatjaNeural",
    },
    "italian": {
        "label": "Italiano (Italian)",
        "reverso_code": "ita",
        "iso_code": "it",
        "locale": "it-IT",
        "reverso_voice": "Chiara22k",
        "edge_voice": "it-IT-ElsaNeural",
    },
    "japanese": {
        "label": "Japonês (Japanese)",
        "reverso_code": "jpn",
        "iso_code": "ja",
        "locale": "ja-JP",
        "reverso_voice": "Sakura22k",
        "edge_voice": "ja-JP-NanamiNeural",
    },
    "chinese": {
        "label": "Chinês (Chinese)",
        "reverso_code": "chi",
        "iso_code": "zh-CN",
        "locale": "zh-CN",
        "reverso_voice": "Lulu22k",
        "edge_voice": "zh-CN-XiaoxiaoNeural",
    },
    "russian": {
        "label": "Russo (Russian)",
        "reverso_code": "rus",
        "iso_code": "ru",
        "locale": "ru-RU",
        "reverso_voice": "Alyona22k",
        "edge_voice": "ru-RU-SvetlanaNeural",
    },
    "dutch": {
        "label": "Holandês (Dutch)",
        "reverso_code": "dut",
        "iso_code": "nl",
        "locale": "nl-NL",
        "reverso_voice": "Femke22k",
        "edge_voice": "nl-NL-ColetteNeural",
    },
    "polish": {
        "label": "Polonês (Polish)",
        "reverso_code": "pol",
        "iso_code": "pl",
        "locale": "pl-PL",
        "reverso_voice": "Ania22k",
        "edge_voice": "pl-PL-ZofiaNeural",
    },
    "arabic": {
        "label": "Árabe (Arabic)",
        "reverso_code": "ara",
        "iso_code": "ar",
        "locale": "ar-SA",
        "reverso_voice": "Mehdi22k",
        "edge_voice": "ar-SA-ZariyahNeural",
    },
    "hebrew": {
        "label": "Hebraico (Hebrew)",
        "reverso_code": "heb",
        "iso_code": "he",
        "locale": "he-IL",
        "reverso_voice": "he-IL-Asaf",
        "edge_voice": "he-IL-AvriNeural",
    },
    "romanian": {
        "label": "Romeno (Romanian)",
        "reverso_code": "rum",
        "iso_code": "ro",
        "locale": "ro-RO",
        "reverso_voice": "ro-RO-Andrei",
        "edge_voice": "ro-RO-AlinaNeural",
    },
    "turkish": {
        "label": "Turco (Turkish)",
        "reverso_code": "tur",
        "iso_code": "tr",
        "locale": "tr-TR",
        "reverso_voice": "Ipek22k",
        "edge_voice": "tr-TR-EmelNeural",
    },
    "ukrainian": {
        "label": "Ucraniano (Ukrainian)",
        "reverso_code": "ukr",
        "iso_code": "uk",
        "locale": "uk-UA",
        "reverso_voice": "",
        "edge_voice": "uk-UA-PolinaNeural",
    },
}

LANGUAGES: List[str] = list(LANGUAGE_INFO.keys())

AI_LEVELS: List[str] = ["A1", "A2", "B1", "B2", "C1", "C2"]

AI_STYLES: List[str] = [
    "Conversação natural",
    "Formal / Profissional",
    "Viagem e Cotidiano",
    "Expressões Idiomáticas e Gírias",
    "Acadêmico / Leitura",
]

OPENAI_TTS_VOICES: List[str] = [
    "alloy",
    "ash",
    "coral",
    "echo",
    "fable",
    "onyx",
    "nova",
    "sage",
    "shimmer",
]
