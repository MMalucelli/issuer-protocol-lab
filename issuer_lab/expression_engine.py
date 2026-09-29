from __future__ import annotations
import ast, math

FUNCS={
 'sqrt': lambda x: math.sqrt(max(float(x),0.0)),
 'exp': lambda x: math.exp(float(x)),
 'log': lambda x: math.log(max(float(x),1e-15)),
 'abs': abs,
 'min': min,
 'max': max,
 'clamp': lambda x,lo=0.0,hi=1.0: max(float(lo),min(float(hi),float(x))),
}
BIN={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,ast.Div:lambda a,b:a/b,ast.Pow:lambda a,b:a**b}
UN={ast.UAdd:lambda a:a,ast.USub:lambda a:-a}

def evaluate(expr:str, variables:dict[str,float])->float:
    tree=ast.parse(expr,mode='eval')
    def walk(n):
        if isinstance(n,ast.Expression): return walk(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return float(n.value)
        if isinstance(n,ast.Name):
            if n.id not in variables: raise ValueError(f'variável desconhecida: {n.id}')
            try: return float(variables[n.id])
            except (TypeError,ValueError) as exc:
                raise ValueError(f'{n.id} precisa ser numérica; valor recebido: {variables[n.id]!r}') from exc
        if isinstance(n,ast.BinOp) and type(n.op) in BIN:
            a,b=walk(n.left),walk(n.right)
            if isinstance(n.op,ast.Pow) and abs(b)>8: raise ValueError('expoente limitado a ±8')
            return BIN[type(n.op)](a,b)
        if isinstance(n,ast.UnaryOp) and type(n.op) in UN: return UN[type(n.op)](walk(n.operand))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in FUNCS and not n.keywords:
            return float(FUNCS[n.func.id](*[walk(x) for x in n.args]))
        raise ValueError('expressão contém sintaxe não permitida')
    value=float(walk(tree))
    if not math.isfinite(value): raise ValueError('resultado não finito')
    return value

def endpoint_saturation(x:float,kind:str='hyperbolic',shape:float=3.0)->float:
    """Saturation on normalized x∈[0,1], with f(0)=0 and f(1)=1 for every family."""
    x=max(0.0,min(1.0,float(x))); k=max(float(shape),1e-9)
    if kind=='linear': return x
    if kind=='hyperbolic':
        # x/(a+x), normalized by its value at x=1. shape k controls curvature via a=1/k.
        a=1.0/k
        raw=x/(a+x) if x else 0.0
        end=1.0/(a+1.0)
        return raw/end
    if kind=='exponential':
        den=1.0-math.exp(-k)
        return (1.0-math.exp(-k*x))/den if den else x
    if kind=='power': return x**(1.0/k)
    raise ValueError(f'saturação desconhecida: {kind}')

def names_in_expression(expr: str) -> set[str]:
    tree = ast.parse(expr, mode='eval')
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id not in FUNCS}

def evaluate_derived(definitions: dict[str, str], primitives: dict[str, float]) -> dict[str, float]:
    """Resolve derived variables recursively while rejecting dependency cycles."""
    # Keep observed fields in their native types. evaluate() converts only the
    # symbols actually referenced by a numeric expression. This lets the base
    # contain dates, labels and other metadata without breaking unrelated math.
    values = dict(primitives)
    visiting: set[str] = set()
    def resolve(name: str) -> float:
        if name in values:
            return values[name]
        if name not in definitions:
            raise ValueError(f'variável desconhecida: {name}')
        if name in visiting:
            raise ValueError(f'ciclo de dependência envolvendo {name}')
        visiting.add(name)
        deps = names_in_expression(definitions[name])
        env = dict(values)
        for dep in deps:
            env[dep] = resolve(dep)
        value = evaluate(definitions[name], env)
        visiting.remove(name)
        values[name] = value
        return value
    for name in definitions:
        resolve(name)
    return values

def direct_dependents(definitions: dict[str, str], target: str) -> list[str]:
    """Return valid formulas that directly reference target.

    Invalid/stale formulas are deliberately ignored: maintenance actions such
    as deleting a broken variable must remain possible even when the full graph
    cannot be validated.
    """
    out=[]
    for name,expr in definitions.items():
        if name == target: continue
        try: deps=names_in_expression(expr)
        except (SyntaxError,ValueError,TypeError): continue
        if target in deps: out.append(name)
    return out

def dependency_graph(definitions: dict[str, str], primitives: set[str] | None = None) -> dict[str, list[str]]:
    """Return direct dependencies for each derived concept, preserving only symbols."""
    primitive_names = primitives or set()
    graph: dict[str, list[str]] = {}
    for name, expr in definitions.items():
        deps = sorted(names_in_expression(expr))
        unknown = [d for d in deps if d not in definitions and d not in primitive_names]
        if unknown:
            raise ValueError(f'{name} depende de variável desconhecida: {", ".join(unknown)}')
        graph[name] = deps
    # Reuse resolver semantics to detect cycles even when no values are available.
    visiting: set[str] = set(); done: set[str] = set()
    def visit(n: str):
        if n in done or n not in definitions: return
        if n in visiting: raise ValueError(f'ciclo de dependência envolvendo {n}')
        visiting.add(n)
        for d in graph[n]: visit(d)
        visiting.remove(n); done.add(n)
    for n in definitions: visit(n)
    return graph


def dependency_layers(target: str, definitions: dict[str, str], primitives: set[str]) -> list[list[str]]:
    """Layers from target down to its primitive leaves; useful for explanation UIs."""
    graph = dependency_graph(definitions, primitives)
    if target not in definitions and target not in primitives:
        raise ValueError(f'variável desconhecida: {target}')
    layers: list[list[str]] = [[target]]; seen={target}; frontier=[target]
    while frontier:
        nxt=[]
        for n in frontier:
            for d in graph.get(n, []):
                if d not in seen: seen.add(d); nxt.append(d)
        if not nxt: break
        layers.append(nxt); frontier=nxt
    return layers


def explain_dependency(target: str, definitions: dict[str, str], primitives: dict[str, float], descriptions: dict[str,str] | None=None) -> list[dict[str, object]]:
    """Produce a causal calculation trace for one concept, including intermediate values."""
    descriptions = descriptions or {}
    values = evaluate_derived(definitions, primitives)
    graph = dependency_graph(definitions, set(primitives))
    rows=[]; visited=set()
    def walk(name: str, depth: int, parent: str | None):
        if (name,parent) in visited: return
        visited.add((name,parent))
        rows.append({
            'depth': depth, 'name': name, 'parent': parent or '',
            'kind': 'conceito' if name in definitions else 'dado primitivo',
            'value': values[name], 'expression': definitions.get(name, ''),
            'description': descriptions.get(name, ''),
        })
        for dep in graph.get(name, []): walk(dep, depth+1, name)
    walk(target,0,None)
    return rows
