#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit local sans modification des sources de Task Coach.

Utilisation :
  python audit_taskcoach.py /chemin/vers/le/depot
  python audit_taskcoach_v2.py /chemin/vers/le/depot --isolation
  python audit_taskcoach_v2.py /chemin/vers/le/depot --smoke

Par défaut : compilation syntaxique et validation des imports internes de tous
les fichiers Python. Avec --smoke : tentative de lancement isolé de 15 secondes.
"""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import tokenize


def locate_sources(path: Path) -> Path:
    root = path.expanduser().resolve()
    if (root / "taskcoach.py").is_file() and (root / "taskcoachlib").is_dir():
        return root
    if (root / "taskcoach" / "taskcoach.py").is_file():
        return root / "taskcoach"
    raise SystemExit(
        "Dossier invalide : fournir la racine du dépôt ou le sous-dossier taskcoach/"
    )


def module_exists(root: Path, module: str) -> bool:
    parts = module.split(".")
    path = root.joinpath(*parts)
    return path.with_suffix(".py").is_file() or (
        path.is_dir() and (path / "__init__.py").is_file()
    )


def check_sources(root: Path) -> tuple[int, list[str], list[str], list[str]]:
    pyfiles = sorted(
        p for p in root.rglob("*.py")
        if not any(part in {".git", ".idea", "__pycache__", ".venv", "venv"} for part in p.parts)
    )
    syntax_errors: list[str] = []
    missing_modules: list[str] = []
    wx_imports: list[str] = []
    for file in pyfiles:
        rel = file.relative_to(root)
        try:
            with tokenize.open(file) as fh:
                text = fh.read()
            tree = ast.parse(text, filename=str(rel))
            compile(tree, str(rel), "exec")
        except (SyntaxError, UnicodeError, OSError) as exc:
            where = getattr(exc, "lineno", "?")
            syntax_errors.append(f"{rel}:{where} : {type(exc).__name__}: {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "wx" or alias.name.startswith("wx."):
                        wx_imports.append(f"{rel}:{node.lineno} : import {alias.name}")
                    if alias.name.startswith("taskcoachlib.") and not module_exists(root, alias.name):
                        missing_modules.append(f"{rel}:{node.lineno} : import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if node.level and mod:
                    # Les imports relatifs demandent une résolution du package et
                    # sont laissés à l'exécution ; pas de faux positifs ici.
                    continue
                if node.level:
                    continue
                if mod == "wx" or mod.startswith("wx."):
                    wx_imports.append(f"{rel}:{node.lineno} : from {mod} import ...")
                if mod.startswith("taskcoachlib.") and not module_exists(root, mod):
                    missing_modules.append(f"{rel}:{node.lineno} : from {mod} import ...")
    return len(pyfiles), syntax_errors, sorted(set(missing_modules)), wx_imports


def smoke_test(root: Path, seconds: int) -> None:
    with tempfile.TemporaryDirectory(prefix="taskcoach-audit-") as temp:
        h = Path(temp)
        env = os.environ.copy()
        env.update({
            "HOME": str(h),
            "XDG_CONFIG_HOME": str(h / "config"),
            "XDG_DATA_HOME": str(h / "data"),
            "XDG_CACHE_HOME": str(h / "cache"),
            "PYTHONUNBUFFERED": "1",
        })
        command = [sys.executable, "taskcoach.py", "--gui", "tk", "--ini", str(h / "TaskCoach.ini")]
        if not env.get("DISPLAY"):
            xvfb = shutil.which("xvfb-run")
            if xvfb is None:
                print("\nLANCEMENT : non effectué (DISPLAY et xvfb-run absents).")
                return
            command = [xvfb, "-a"] + command
        print("\nLANCEMENT :", " ".join(command))
        print(f"Environnement de configuration isolé ; durée maximale {seconds} s.")
        try:
            proc = subprocess.Popen(
                command, cwd=root, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, start_new_session=(os.name == "posix")
            )
        except OSError as exc:
            print(f"Impossible de lancer le processus : {exc}")
            return
        try:
            out, err = proc.communicate(timeout=seconds)
            print(f"Processus terminé, code retour = {proc.returncode}")
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGTERM)
            else:
                proc.terminate()
            try:
                out, err = proc.communicate(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err = proc.communicate()
            print("Processus toujours actif à l'échéance : boucle Tk possible, PAS une preuve de bon fonctionnement.")
        for name, txt in (("stdout", out), ("stderr", err)):
            if txt:
                print(f"--- {name} (8 000 derniers caractères) ---\n{txt[-8000:]}")
        log_files = sorted(h.rglob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
        for logfile in log_files[:5]:
            try:
                lines = logfile.read_text(errors="replace")
                errors = [l for l in lines.splitlines() if "ERROR" in l or "Traceback" in l or "Exception" in l]
                if errors:
                    print(f"--- Extraits du journal {logfile.relative_to(h)} ---")
                    print("\n".join(errors[-30:]))
            except OSError:
                pass




def isolation_test(root: Path) -> None:
    """Teste l'import Tkinter dans un processus neuf qui interdit wxPython.

    Ne cree pas de racine graphique, n'ouvre aucun fichier de taches et ne
    modifie pas le depot. La premiere erreur est affichee avec sa pile.
    """
    code = r'''import importlib.abc
import sys

class ForbiddenWx(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "wx" or fullname.startswith("wx."):
            raise ModuleNotFoundError(
                "wxPython interdit pendant le test d'isolation Tkinter",
                name=fullname,
            )
        return None

sys.meta_path.insert(0, ForbiddenWx())
from taskcoachlib.config.arguments import set_gui
set_gui("tk")
from taskcoachlib.application.tkapplication import TkinterApplication
print("OK : tkapplication importable sans wxPython")
'''
    with tempfile.TemporaryDirectory(prefix="taskcoach-import-isolation-") as temp:
        env = os.environ.copy()
        h = Path(temp)
        env.update({
            "HOME": str(h),
            "XDG_CONFIG_HOME": str(h / "config"),
            "XDG_DATA_HOME": str(h / "data"),
            "XDG_CACHE_HOME": str(h / "cache"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        })
        print("\nISOLATION TKINTER : import de TkinterApplication avec wxPython interdit")
        try:
            result = subprocess.run(
                [sys.executable, "-c", code], cwd=root, env=env,
                capture_output=True, text=True, timeout=30, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print("Test non termine :", exc)
            return
        print("Code retour :", result.returncode)
        if result.stdout:
            print("stdout :\n", result.stdout[-5000:])
        if result.stderr:
            print("stderr :\n", result.stderr[-11000:])
        if result.returncode:
            print("ECHEC : une erreur d'import reste a traiter. Elle peut concerner wx ou une autre dependance.")
        else:
            print("SUCCES PARTIEL : imports OK, mais GUI et fonctions non testes.")

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Python statique et démarrage isolé de Task Coach")
    parser.add_argument("repo", nargs="?", default=".", type=Path,
                        help="Racine du dépôt Git ou sous-dossier taskcoach/")
    parser.add_argument("--isolation", action="store_true",
                        help="Teste les imports du backend Tk dans un nouveau Python sans wxPython")
    parser.add_argument("--smoke", action="store_true",
                        help="Tente un démarrage dans un HOME temporaire ; ne valide pas les fonctions GUI")
    parser.add_argument("--seconds", type=int, default=15)
    args = parser.parse_args()
    root = locate_sources(args.repo)
    count, syntax, missing, wx = check_sources(root)
    print(f"Dossier : {root}")
    print(f"Python : {sys.version.split()[0]}")
    print(f"Fichiers Python analysés : {count}")
    for label, findings in (("ERREURS SYNTAXIQUES", syntax),
                            ("MODULES INTERNES INTROUVABLES", missing),
                            ("IMPORTS wx DIRECTS (inventaire)", wx)):
        print(f"\n{label} : {len(findings)}")
        for result in findings:
            print(" -", result)
    print("\nLimites : les imports de symboles, leurs cycles, les événements Tk, les dépendances externes")
    print("et le comportement métier nécessitent des tests exécutables ; cet audit statique ne les prouve pas.")
    if args.isolation:
        isolation_test(root)
    if args.smoke:
        smoke_test(root, max(args.seconds, 1))
    return 1 if syntax or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
