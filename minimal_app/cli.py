# minimal_app/cli.py
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

from .parser import parse_files
from .optimizer import optimize_project
from .minifier import minify_module, to_source

logger = logging.getLogger(__name__)


def collect_python_files(project_dir: Path) -> List[Path]:
    """
    Recolecta todos los archivos .py en el directorio del proyecto.
    """
    logger.info("Buscando archivos .py en el directorio: %s", project_dir)
    if not project_dir.is_dir():
        logger.error("La ruta proporcionada no es un directorio: %s", project_dir)
        raise ValueError(f"{project_dir} no es un directorio.")

    files = sorted(project_dir.glob("*.py"))
    logger.info("Archivos .py encontrados: %d", len(files))
    for f in files:
        logger.debug("  - %s", f)
    return files


def run(project_dir: Path, entrypoint: str, output_dir: Path) -> None:
    """
    Ejecuta el pipeline completo:
    - Parseo
    - Optimización por reachability
    - Minificación
    - Escritura en carpeta output (_ma.py)
    """
    logger.info("=== Inicio de ejecución minimal_app ===")
    logger.info("Proyecto: %s", project_dir)
    logger.info("Output: %s", output_dir)
    logger.info("Entrypoint: %s", entrypoint)

    python_files = collect_python_files(project_dir)
    if not python_files:
        logger.error("No se encontraron archivos .py en el proyecto.")
        raise ValueError(f"No se encontraron .py en {project_dir}")

    try:
        entry_mod, entry_function = entrypoint.split(":")
    except ValueError:
        logger.error("Formato inválido de entrypoint: %s", entrypoint)
        raise ValueError("El entrypoint debe tener formato modulo:funcion, ej: app:handler")

    logger.info("Módulo de entrada: %s, función: %s", entry_mod, entry_function)

    # Parsear
    modules = parse_files(python_files)

    if entry_mod not in modules:
        logger.error("El módulo de entrypoint '%s' no existe dentro del proyecto.", entry_mod)
        raise ValueError(f"El módulo de entrypoint '{entry_mod}' no existe dentro del proyecto.")

    # Optimizar
    optimized_trees = optimize_project(modules, entry_mod, entry_function)

    # Minificar + escribir archivos
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Escribiendo módulos optimizados en: %s", output_dir)

    for p in python_files:
        mod_name = p.stem
        logger.info("Procesando módulo: %s", mod_name)
        tree = optimized_trees[mod_name]

        minified_tree = minify_module(tree)
        source = to_source(minified_tree)

        out_name = f"{mod_name}_ma.py"
        out_path = output_dir / out_name
        out_path.write_text(source, encoding="utf-8")

        logger.info("Archivo generado: %s", out_path)

    logger.info("=== Ejecución minimal_app finalizada correctamente ===")


def main():
    # Configuración básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Minimiza y optimiza un proyecto Python usando AST."
    )

    parser.add_argument(
        "project_dir",
        help="Ruta a la carpeta del proyecto que contiene los .py",
    )

    parser.add_argument(
        "-e", "--entrypoint",
        required=True,
        help="Entry point en formato modulo:funcion, ej: app:handler",
    )

    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Directorio de salida donde se escribirán los módulos _ma.py",
    )

    args = parser.parse_args()

    run(Path(args.project_dir), args.entrypoint, Path(args.output))


if __name__ == "__main__":
    main()
