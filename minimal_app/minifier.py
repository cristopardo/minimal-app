# minimal_app/minifier.py
from __future__ import annotations

import ast
import logging

logger = logging.getLogger(__name__)


class DocstringRemover(ast.NodeTransformer):
    """
    Elimina docstrings a nivel de módulo, clase y funciones
    (primer statement tipo Expr con Constant str).
    """

    def __init__(self):
        super().__init__()
        self.removed_count = 0

    def _strip_docstring(self, body):
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            if isinstance(body[0].value.value, str):
                self.removed_count += 1
                logger.debug("Docstring eliminado")
                return body[1:]
        return body

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring(node.body)
        return node


def minify_module(tree: ast.Module) -> ast.Module:
    """
    Aplica transformaciones para "minificar" el árbol:
    - quita docstrings
    - comentarios y espacios innecesarios ya se pierden con ast.unparse
    """
    logger.info("Iniciando minificación de módulo")
    remover = DocstringRemover()
    tree = remover.visit(tree)
    ast.fix_missing_locations(tree)
    logger.info("Minificación completada. Docstrings eliminados: %d", remover.removed_count)
    return tree


def to_source(tree: ast.Module) -> str:
    """
    Convierte el AST en código fuente.
    """
    logger.debug("Convirtiendo AST a código fuente (ast.unparse)")
    return ast.unparse(tree)
