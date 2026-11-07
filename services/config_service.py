import json
import os
from typing import Any, Dict
from ..utils.qt_compat import is_running_in_anki, mw


class ConfigService:
    """Gerencia a leitura e gravação das configurações do Add-on no Anki ou em modo local."""

    def __init__(self) -> None:
        self.addon_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.default_config_path = os.path.join(self.addon_root, "config.json")
        self.user_config_path = os.path.join(self.addon_root, "user_config.json")
        self._config: Dict[str, Any] = self._load()

    def _load_defaults(self) -> Dict[str, Any]:
        if os.path.isfile(self.default_config_path):
            try:
                with open(self.default_config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _load(self) -> Dict[str, Any]:
        defaults = self._load_defaults()
        loaded: Dict[str, Any] = {}

        if is_running_in_anki() and mw is not None:
            try:
                package_name = self._get_anki_package_name()
                anki_cfg = mw.addonManager.getConfig(package_name)
                if isinstance(anki_cfg, dict):
                    loaded = anki_cfg
            except Exception:
                pass

        if not loaded and os.path.isfile(self.user_config_path):
            try:
                with open(self.user_config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            except Exception:
                loaded = {}

        merged = dict(defaults)
        merged.update(loaded)
        return merged

    def _get_anki_package_name(self) -> str:
        if mw is not None and hasattr(mw, "addonManager"):
            try:
                return mw.addonManager.addonFromModule(__name__)
            except Exception:
                pass
        return os.path.basename(self.addon_root)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._config)

    def update(self, new_values: Dict[str, Any]) -> None:
        self._config.update(new_values)
        self.save()

    def save(self) -> None:
        if is_running_in_anki() and mw is not None:
            try:
                package_name = self._get_anki_package_name()
                mw.addonManager.writeConfig(package_name, self._config)
                return
            except Exception:
                pass

        try:
            with open(self.user_config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"Aviso: não foi possível salvar user_config.json: {exc}")
