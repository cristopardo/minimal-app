# minimal_app/parser.py
from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    name: str       # nombre lógico del módulo (p.ej. "app" o "mini_ds")
    path: Path      # ruta al archivo .py
    tree: ast.Module


def parse_files(paths: List[Path]) -> Dict[str, ModuleInfo]:
    """
    Parsea una lista de archivos Python y devuelve un dict {module_name: ModuleInfo}.
    Usamos el stem del archivo como nombre de módulo (app, mini_ds, ...).
    """
    logger.info("Iniciando parseo de %d archivo(s) Python", len(paths))
    modules: Dict[str, ModuleInfo] = {}

    for p in paths:
        logger.debug("Leyendo archivo %s", p)
        source = p.read_text(encoding="utf-8")

        logger.debug("Parseando AST para %s", p)
        tree = ast.parse(source, filename=str(p))
        name = p.stem

        modules[name] = ModuleInfo(name=name, path=p, tree=tree)
        logger.info("Módulo parseado: name=%s, path=%s", name, p)

    logger.info("Parseo completado. Total de módulos: %d", len(modules))
    return modules
