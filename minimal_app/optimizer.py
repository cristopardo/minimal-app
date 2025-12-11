# minimal_app/optimizer.py
from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from typing import Dict, Set, Tuple, List

from .parser import ModuleInfo

logger = logging.getLogger(__name__)

# Identificadores de nodos en el grafo
FuncId = Tuple[str, str]           # ("func", module_name, func_name)
ClassId = Tuple[str, str]          # ("class", module_name, class_name)
MethodId = Tuple[str, str, str]    # ("meth", module_name, class_name, method_name)


@dataclass
class ProjectIndex:
    functions: Dict[Tuple[str, str], ast.FunctionDef]          # (mod, name)
    classes: Dict[Tuple[str, str], ast.ClassDef]               # (mod, name)
    methods: Dict[Tuple[str, str, str], ast.FunctionDef]       # (mod, cls, name)


def build_index(modules: Dict[str, ModuleInfo]) -> ProjectIndex:
    logger.info("Construyendo índice de proyecto (funciones, clases, métodos)")
    functions: Dict[Tuple[str, str], ast.FunctionDef] = {}
    classes: Dict[Tuple[str, str], ast.ClassDef] = {}
    methods: Dict[Tuple[str, str, str], ast.FunctionDef] = {}

    for mod_name, info in modules.items():
        logger.debug("Indexando módulo: %s", mod_name)
        for node in info.tree.body:
            if isinstance(node, ast.FunctionDef):
                functions[(mod_name, node.name)] = node
                logger.debug("Función registrada: %s.%s", mod_name, node.name)
            elif isinstance(node, ast.ClassDef):
                classes[(mod_name, node.name)] = node
                logger.debug("Clase registrada: %s.%s", mod_name, node.name)
                for stmt in node.body:
                    if isinstance(stmt, ast.FunctionDef):
                        methods[(mod_name, node.name, stmt.name)] = stmt
                        logger.debug(
                            "Método registrado: %s.%s.%s",
                            mod_name,
                            node.name,
                            stmt.name,
                        )

    logger.info(
        "Índice construido. Funciones=%d, Clases=%d, Métodos=%d",
        len(functions),
        len(classes),
        len(methods),
    )
    return ProjectIndex(functions=functions, classes=classes, methods=methods)


def build_call_graph(modules: Dict[str, ModuleInfo], index: ProjectIndex):
    """
    Grafo de alcance muy simple: de cada función/método a otros símbolos
    a los que hace referencia por llamadas o atributos.
    """
    logger.info("Construyendo grafo de llamadas/citas")
    graph: Dict[Tuple, Set[Tuple]] = {}

    def add_edge(src, dst):
        if src not in graph:
            graph[src] = set()
        graph[src].add(dst)
        logger.debug("Arista añadida: %s -> %s", src, dst)

    class CallerVisitor(ast.NodeVisitor):
        def __init__(self, current_node_id):
            self.current_node_id = current_node_id

        def visit_Call(self, node: ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
                logger.debug("Call detectado a nombre simple: %s", name)

                for (mod, fname), _ in index.functions.items():
                    if fname == name:
                        add_edge(self.current_node_id, ("func", mod, fname))

                for (mod, cname), _ in index.classes.items():
                    if cname == name:
                        add_edge(self.current_node_id, ("class", mod, cname))

            elif isinstance(node.func, ast.Attribute):
                attr_name = node.func.attr
                logger.debug("Call detectado a atributo: .%s()", attr_name)

                for (mod, cls, mname), _ in index.methods.items():
                    if mname == attr_name:
                        add_edge(self.current_node_id, ("meth", mod, cls, mname))

            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute):
            attr_name = node.attr
            logger.debug("Uso de atributo detectado: .%s", attr_name)

            for (mod, cls, mname), _ in index.methods.items():
                if mname == attr_name:
                    add_edge(self.current_node_id, ("meth", mod, cls, mname))
            self.generic_visit(node)

    # Recorremos todas las funciones y métodos para construir las aristas
    for (mod, fname), fnode in index.functions.items():
        node_id = ("func", mod, fname)
        graph.setdefault(node_id, set())
        logger.debug("Visitando cuerpo de función para grafo: %s.%s", mod, fname)
        CallerVisitor(node_id).visit(fnode)

    for (mod, cls, mname), mnode in index.methods.items():
        node_id = ("meth", mod, cls, mname)
        graph.setdefault(node_id, set())
        logger.debug("Visitando cuerpo de método para grafo: %s.%s.%s", mod, cls, mname)
        CallerVisitor(node_id).visit(mnode)

    # Opcional: conectamos clases con sus __init__ para conservarlos juntos
    for (mod, cname), _ in index.classes.items():
        class_id = ("class", mod, cname)
        graph.setdefault(class_id, set())
        init = index.methods.get((mod, cname, "__init__"))
        if init is not None:
            logger.debug("Conectando clase %s.%s con su __init__", mod, cname)
            graph[class_id].add(("meth", mod, cname, "__init__"))

    logger.info("Grafo construido. Nodos=%d", len(graph))
    return graph


def dfs_reachable(graph, start_nodes: List[Tuple]) -> Set[Tuple]:
    logger.info("Iniciando DFS de reachability desde %d nodo(s) de entrada", len(start_nodes))
    visited: Set[Tuple] = set()
    stack: List[Tuple] = list(start_nodes)

    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        logger.debug("Nodo alcanzado: %s", node)
        for nxt in graph.get(node, ()):
            if nxt not in visited:
                stack.append(nxt)

    logger.info("DFS completado. Nodos alcanzables: %d", len(visited))
    return visited


def prune_modules(
    modules: Dict[str, ModuleInfo],
    index: ProjectIndex,
    reachable: Set[Tuple],
) -> Dict[str, ast.Module]:
    """
    Devuelve nuevos árboles AST por módulo, eliminando funciones/clases/métodos
    que no están en 'reachable'.
    """
    logger.info("Iniciando poda de módulos a partir de nodos alcanzables")

    class Pruner(ast.NodeTransformer):
        def __init__(self, mod_name: str):
            super().__init__()
            self.mod_name = mod_name
            self.removed_funcs = 0
            self.removed_classes = 0
            self.removed_methods = 0

        def visit_FunctionDef(self, node: ast.FunctionDef):
            node_id = ("func", self.mod_name, node.name)
            if node_id not in reachable:
                self.removed_funcs += 1
                logger.debug("Poda función no alcanzable: %s.%s", self.mod_name, node.name)
                return None
            return self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef):
            class_id = ("class", self.mod_name, node.name)

            methods_ids = [
                ("meth", self.mod_name, node.name, stmt.name)
                for stmt in node.body
                if isinstance(stmt, ast.FunctionDef)
            ]
            keep_class = (
                class_id in reachable
                or any(mid in reachable for mid in methods_ids)
            )
            if not keep_class:
                self.removed_classes += 1
                logger.debug("Poda clase no alcanzable: %s.%s", self.mod_name, node.name)
                return None

            new_body = []
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef):
                    mid = ("meth", self.mod_name, node.name, stmt.name)
                    if mid in reachable:
                        new_body.append(self.generic_visit(stmt))
                    else:
                        self.removed_methods += 1
                        logger.debug(
                            "Poda método no alcanzable: %s.%s.%s",
                            self.mod_name,
                            node.name,
                            stmt.name,
                        )
                else:
                    new_body.append(self.generic_visit(stmt))
            node.body = new_body
            return node

    new_trees: Dict[str, ast.Module] = {}
    for mod_name, info in modules.items():
        logger.info("Podando módulo: %s", mod_name)
        pruner = Pruner(mod_name)
        new_tree = pruner.visit(info.tree)
        ast.fix_missing_locations(new_tree)

        logger.info(
            "Poda en módulo %s completada. Funciones removidas=%d, Clases removidas=%d, Métodos removidos=%d",
            mod_name,
            pruner.removed_funcs,
            pruner.removed_classes,
            pruner.removed_methods,
        )
        new_trees[mod_name] = new_tree  # type: ignore[arg-type]

    logger.info("Poda de todos los módulos completada")
    return new_trees


def optimize_project(
    modules: Dict[str, ModuleInfo],
    entry_module: str,
    entry_function: str = "handler",
) -> Dict[str, ast.Module]:
    """
    Orquesta:
    - índice de funciones/clases/métodos
    - grafo de llamadas
    - DFS desde entrypoint
    - poda de nodos inalcanzables
    """
    logger.info(
        "Optimizando proyecto. Entry module=%s, entry function=%s",
        entry_module,
        entry_function,
    )

    index = build_index(modules)
    graph = build_call_graph(modules, index)

    entry_id = ("func", entry_module, entry_function)
    if entry_id not in graph:
        logger.warning(
            "El entrypoint %s no tiene nodo explícito en el grafo. Se continuará igual.",
            entry_id,
        )

    reachable = dfs_reachable(graph, [entry_id])
    new_trees = prune_modules(modules, index, reachable)

    logger.info("Optimización de proyecto completada")
    return new_trees
