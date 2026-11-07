from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NoteExportConfig:
    deck_name: str
    note_type_name: str = "Reverso AI Card"
    use_custom_note_type: bool = True
    include_audio: bool = True
    include_explanation: bool = True
    include_image: bool = True
    tags: List[str] = field(default_factory=lambda: ["reverso-ai"])
    field_mapping: Dict[str, str] = field(
        default_factory=lambda: {
            "front": "Front",
            "back": "Back",
            "explanation": "",
            "image": "",
            "audio": "Front",
        }
    )
