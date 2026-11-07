#!/usr/bin/env python3
"""
Empacota o projeto em dois arquivos `.ankiaddon` na pasta `dist/`:
1. `anki_reverso_ai_addon.ankiaddon` -> Para instalação manual local (inclui manifest.json).
2. `anki_reverso_ai_addon_ankiweb.ankiaddon` -> Formato exigido pelo site AnkiWeb para publicação (sem manifest.json).
Opcionalmente instala direto na pasta `addons21/` do Anki do usuário com `--install`.
"""

import argparse
import os
import shutil
import zipfile
from pathlib import Path

BASE_PATHS = [
    "__init__.py",
    "config.json",
    "config.md",
    "LICENSE",
    "controllers",
    "enums",
    "models",
    "services",
    "utils",
    "views",
]


def build_package(project_root: Path, output_file: Path, include_manifest: bool = True) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    paths = list(BASE_PATHS)
    if include_manifest:
        paths.append("manifest.json")

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_item in paths:
            full_path = project_root / rel_item
            if not full_path.exists():
                continue
            if full_path.is_file():
                zf.write(full_path, arcname=rel_item)
            else:
                for root, dirs, files in os.walk(full_path):
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for file in files:
                        if file.endswith((".pyc", ".pyo")):
                            continue
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(project_root)
                        zf.write(file_path, arcname=str(arcname))
    return output_file


def install_to_anki(project_root: Path, addon_folder_name: str = "anki_reverso_ai_addon") -> Path:
    home = Path.home()
    candidates = [
        home / ".local" / "share" / "Anki2" / "addons21",
        home / ".var" / "app" / "net.ankiweb.Anki" / "data" / "Anki2" / "addons21",
        home / "AppData" / "Roaming" / "Anki2" / "addons21",
        home / "Library" / "Application Support" / "Anki2" / "addons21",
    ]
    addons_dir = next((p for p in candidates if p.exists()), candidates[0])
    target_dir = addons_dir / addon_folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    for rel_item in BASE_PATHS + ["manifest.json"]:
        src = project_root / rel_item
        dst = target_dir / rel_item
        if not src.exists():
            continue
        if src.is_file():
            shutil.copy2(src, dst)
        else:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    return target_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Empacotador e instalador do Add-on Anki Reverso & AI")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Copia o add-on diretamente para a pasta addons21 do Anki local",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    local_pkg = project_root / "dist" / "anki_reverso_ai_addon.ankiaddon"
    ankiweb_pkg = project_root / "dist" / "anki_reverso_ai_addon_ankiweb.ankiaddon"

    build_package(project_root, local_pkg, include_manifest=True)
    build_package(project_root, ankiweb_pkg, include_manifest=False)

    print(f"Pacote para instalação manual local gerado em: {local_pkg}")
    print(f"Pacote para publicação no AnkiWeb gerado em:   {ankiweb_pkg}")

    if args.install:
        installed_dir = install_to_anki(project_root)
        print(f"Add-on atualizado na pasta do Anki em:         {installed_dir}")


if __name__ == "__main__":
    main()
