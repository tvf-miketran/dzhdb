"""
Math Engine v3 — Full Summation Support
========================================
Supports:
  Basic          : + - * /  with precedence, parentheses, unary minus
  Variables      : AB, REVENUE, COST_Q1  (resolved via dict or DB callback)
  Functions      : SUM(a,b,c)  AVG  MIN  MAX  ABS
  Sigma loop     : SIGMA(i, start, end, expr)   — Σ i=start..end of expr
  Conditional    : SUM_IF(cond, true_val, false_val, ...items)
                   IF(cond, true_val, false_val)
  Running total  : CUMSUM(a, b, c, ...)          — returns list
  Product loop   : PRODUCT(i, start, end, expr)  — Π notation
  Comparisons    : > < >= <= == !=  (usable inside IF / SUM_IF)
"""
from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# TOKENS
# ─────────────────────────────────────────────────────────────────────────────

class T:
    NUMBER = "NUMBER"; VAR = "VAR"
    PLUS = "PLUS"; MINUS = "MINUS"; MULTIPLY = "MULTIPLY"; DIVIDE = "DIVIDE"
    LPAREN = "LPAREN"; RPAREN = "RPAREN"; COMMA = "COMMA"
    GT = "GT"; LT = "LT"; GTE = "GTE"; LTE = "LTE"; EQ = "EQ"; NEQ = "NEQ"
    FUNC = "FUNC"; EOF = "EOF"

class Token:
    __slots__ = ("type", "value")
    def __init__(self, t, v): self.type = t; self.value = v
    def __repr__(self): return f"Token({self.type},{self.value!r})"

# Functions that take a loop variable (special parsing)
LOOP_FUNCS  = {"SIGMA", "PRODUCT"}
# Functions resolved normally (args evaluated first)
EAGER_FUNCS = {"SUM", "AVG", "MIN", "MAX", "ABS", "CUMSUM", "SUM_IF", "IF"}
ALL_FUNCS   = LOOP_FUNCS | EAGER_FUNCS


def tokenize(text: str) -> list[Token]:
    tokens = []; i = 0; n = len(text); text = text.strip()
    while i < n:
        ch = text[i]
        if ch == " ": i += 1; continue

        # Numbers
        if ch.isdigit() or (ch == "." and i+1 < n and text[i+1].isdigit()):
            j = i
            while j < n and (text[j].isdigit() or text[j] == "."): j += 1
            tokens.append(Token(T.NUMBER, float(text[i:j]))); i = j; continue

        # Words → function or variable
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"): j += 1
            word = text[i:j].upper()
            tokens.append(Token(T.FUNC if word in ALL_FUNCS else T.VAR, word))
            i = j; continue

        # Two-char operators
        two = text[i:i+2]
        two_map = {">=": T.GTE, "<=": T.LTE, "==": T.EQ, "!=": T.NEQ}
        if two in two_map:
            tokens.append(Token(two_map[two], two)); i += 2; continue

        # Single-char
        one_map = {
            "+": T.PLUS, "-": T.MINUS, "*": T.MULTIPLY, "/": T.DIVIDE,
            "(": T.LPAREN, ")": T.RPAREN, ",": T.COMMA,
            ">": T.GT, "<": T.LT,
        }
        if ch in one_map:
            tokens.append(Token(one_map[ch], ch)); i += 1; continue

        raise ValueError(f"Unexpected character: {ch!r} at position {i}")

    tokens.append(Token(T.EOF, None))
    return tokens


# ─────────────────────────────────────────────────────────────────────────────
# AST NODES
# ─────────────────────────────────────────────────────────────────────────────

class NumNode:
    __slots__ = ("v",)
    def __init__(self, v): self.v = v

class VarNode:
    __slots__ = ("name",)
    def __init__(self, name): self.name = name

class BinOpNode:
    __slots__ = ("l", "op", "r")
    def __init__(self, l, op, r): self.l = l; self.op = op; self.r = r

class NegNode:
    __slots__ = ("o",)
    def __init__(self, o): self.o = o

class CallNode:
    """Eager function: all args are AST nodes, evaluated before calling."""
    __slots__ = ("fn", "args")
    def __init__(self, fn, args): self.fn = fn; self.args = args

class LoopNode:
    """
    SIGMA / PRODUCT: loop variable is bound during evaluation.
      SIGMA(i, 1, 10, i*2)
        var_name = "i"
        start, end = AST nodes
        body = AST node (may reference var_name)
    """
    __slots__ = ("fn", "var_name", "start", "end", "body")
    def __init__(self, fn, var_name, start, end, body):
        self.fn = fn; self.var_name = var_name
        self.start = start; self.end = end; self.body = body


# ─────────────────────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────────────────────

CMP_OPS = {T.GT, T.LT, T.GTE, T.LTE, T.EQ, T.NEQ}

class Parser:
    def __init__(self, tokens):
        self.t = tokens; self.p = 0

    def cur(self): return self.t[self.p]

    def eat(self, tp=None):
        tok = self.t[self.p]
        if tp and tok.type != tp:
            raise SyntaxError(f"Expected {tp}, got {tok.type} ({tok.value!r})")
        self.p += 1; return tok

    def parse(self):
        node = self.comparison(); self.eat(T.EOF); return node

    # comparison sits above expr in precedence
    def comparison(self):
        node = self.expr()
        if self.cur().type in CMP_OPS:
            op = self.eat().value
            node = BinOpNode(node, op, self.expr())
        return node

    def expr(self):
        node = self.term()
        while self.cur().type in (T.PLUS, T.MINUS):
            op = self.eat().value
            node = BinOpNode(node, op, self.term())
        return node

    def term(self):
        node = self.factor()
        while self.cur().type in (T.MULTIPLY, T.DIVIDE):
            op = self.eat().value
            node = BinOpNode(node, op, self.factor())
        return node

    def factor(self):
        tok = self.cur()

        if tok.type == T.MINUS:
            self.eat(); return NegNode(self.factor())

        if tok.type == T.LPAREN:
            self.eat(); node = self.comparison(); self.eat(T.RPAREN); return node

        # Loop functions: SIGMA(i, start, end, body)  PRODUCT(i, start, end, body)
        if tok.type == T.FUNC and tok.value in LOOP_FUNCS:
            fn = self.eat().value
            self.eat(T.LPAREN)
            # first arg must be a plain variable name → loop iterator
            var_tok = self.eat(T.VAR)
            self.eat(T.COMMA)
            start = self.comparison()
            self.eat(T.COMMA)
            end = self.comparison()
            self.eat(T.COMMA)
            body = self.comparison()
            self.eat(T.RPAREN)
            return LoopNode(fn, var_tok.value, start, end, body)

        # Eager functions
        if tok.type == T.FUNC:
            fn = self.eat().value
            self.eat(T.LPAREN)
            args = []
            if self.cur().type != T.RPAREN:
                args.append(self.comparison())
                while self.cur().type == T.COMMA:
                    self.eat(); args.append(self.comparison())
            self.eat(T.RPAREN)
            return CallNode(fn, args)

        if tok.type == T.NUMBER:
            self.eat(); return NumNode(tok.value)

        if tok.type == T.VAR:
            self.eat(); return VarNode(tok.value)

        raise SyntaxError(f"Unexpected token: {tok}")


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATOR
# ─────────────────────────────────────────────────────────────────────────────

_CMP = {">": lambda a,b: a>b, "<": lambda a,b: a<b,
        ">=": lambda a,b: a>=b, "<=": lambda a,b: a<=b,
        "==": lambda a,b: a==b, "!=": lambda a,b: a!=b}

def evaluate(node, ctx: dict) -> float | list:
    t = type(node)

    if t is NumNode: return node.v

    if t is VarNode:
        name = node.name
        if name not in ctx:
            raise NameError(f"Variable '{name}' not defined. Available: {sorted(ctx)}")
        return ctx[name]

    if t is NegNode:
        return -evaluate(node.o, ctx)

    if t is BinOpNode:
        op = node.op
        # Lazy evaluation for comparisons (return bool as 1/0)
        if op in _CMP:
            return float(_CMP[op](evaluate(node.l, ctx), evaluate(node.r, ctx)))
        l = evaluate(node.l, ctx); r = evaluate(node.r, ctx)
        if op == "+": return l + r
        if op == "-": return l - r
        if op == "*": return l * r
        if op == "/":
            if r == 0: raise ZeroDivisionError("Division by zero")
            return l / r

    if t is CallNode:
        fn = node.fn

        # ── IF(condition, true_val, false_val) ──────────────────────────────
        if fn == "IF":
            if len(node.args) != 3:
                raise ValueError("IF requires exactly 3 arguments: IF(cond, true_val, false_val)")
            cond = evaluate(node.args[0], ctx)
            return evaluate(node.args[1], ctx) if cond else evaluate(node.args[2], ctx)

        # ── SUM_IF(cond_expr, val_expr, var, item1, item2, ...) ─────────────
        # Iterates over items, binds each to `var`, sums val_expr where cond is true
        # Syntax: SUM_IF(i, i > 0, i, -3, 5, -1, 7)
        #           → var=i, cond=i>0, val=i, items=[-3,5,-1,7] → 5+7=12
        if fn == "SUM_IF":
            if len(node.args) < 4:
                raise ValueError(
                    "SUM_IF(var, condition, value_expr, item1, item2, ...)\n"
                    "  e.g. SUM_IF(i, i > 0, i, -3, 5, -1, 7)"
                )
            var_node = node.args[0]
            if not isinstance(var_node, VarNode):
                raise ValueError("SUM_IF first arg must be a variable name")
            var_name  = var_node.name
            cond_node = node.args[1]
            val_node  = node.args[2]
            items     = [evaluate(a, ctx) for a in node.args[3:]]
            total = 0.0
            for item in items:
                local_ctx = {**ctx, var_name: item}
                if evaluate(cond_node, local_ctx):
                    total += evaluate(val_node, local_ctx)
            return total

        # ── CUMSUM(a, b, c, ...) ────────────────────────────────────────────
        if fn == "CUMSUM":
            vals = [evaluate(a, ctx) for a in node.args]
            result = []; running = 0.0
            for v in vals:
                running += v; result.append(running)
            return result          # returns a list!

        # ── Standard functions ───────────────────────────────────────────────
        args = [evaluate(a, ctx) for a in node.args]
        if fn == "SUM": return sum(args)
        if fn == "AVG": return sum(args) / len(args) if args else 0.0
        if fn == "MIN": return min(args)
        if fn == "MAX": return max(args)
        if fn == "ABS": return abs(args[0])
        raise ValueError(f"Unknown function: {fn}")

    # ── Loop nodes: SIGMA and PRODUCT ────────────────────────────────────────
    if t is LoopNode:
        start = int(evaluate(node.start, ctx))
        end   = int(evaluate(node.end,   ctx))

        if node.fn == "SIGMA":
            total = 0.0
            for i in range(start, end + 1):
                total += evaluate(node.body, {**ctx, node.var_name: float(i)})
            return total

        if node.fn == "PRODUCT":
            result = 1.0
            for i in range(start, end + 1):
                result *= evaluate(node.body, {**ctx, node.var_name: float(i)})
            return result

    raise TypeError(f"Unknown node type: {type(node)}")


# ─────────────────────────────────────────────────────────────────────────────
# VARIABLE SCANNER
# ─────────────────────────────────────────────────────────────────────────────

def collect_variables(node, bound: set | None = None) -> set:
    """Return all external variable names (excluding loop iterators)."""
    bound = bound or set()
    t = type(node)
    if t is NumNode:   return set()
    if t is VarNode:   return set() if node.name in bound else {node.name}
    if t is NegNode:   return collect_variables(node.o, bound)
    if t is BinOpNode: return collect_variables(node.l, bound) | collect_variables(node.r, bound)
    if t is CallNode:
        if node.fn == "SUM_IF" and node.args and isinstance(node.args[0], VarNode):
            var_name = node.args[0].name
            new_bound = bound | {var_name}
            result = set()
            for a in node.args[1:]: result |= collect_variables(a, new_bound)
            return result
        result = set()
        for a in node.args: result |= collect_variables(a, bound)
        return result
    if t is LoopNode:
        new_bound = bound | {node.var_name}
        return (collect_variables(node.start, bound) |
                collect_variables(node.end,   bound) |
                collect_variables(node.body,  new_bound))
    return set()


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE  (public API)
# ─────────────────────────────────────────────────────────────────────────────

class MathEngine:
    def __init__(self, context: dict | None = None, query_fn=None):
        self.context  = dict(context or {})
        self.query_fn = query_fn
        self._cache: dict = {}

    def set(self, name, value): self.context[name] = value

    def _build(self, expression: str):
        if expression not in self._cache:
            self._cache[expression] = Parser(tokenize(expression)).parse()
        return self._cache[expression]

    def variables_in(self, expression: str) -> set:
        return collect_variables(self._build(expression))

    def calculate(self, expression: str, extra: dict | None = None):
        ast_node = self._build(expression)
        ctx = {**self.context, **(extra or {})}
        if self.query_fn:
            for v in collect_variables(ast_node):
                if v not in ctx:
                    ctx[v] = self.query_fn(v)
        return evaluate(ast_node, ctx)

    def explain(self, expression: str, extra: dict | None = None) -> str:
        ast_node = self._build(expression)
        needed   = collect_variables(ast_node)
        ctx = {**self.context, **(extra or {})}
        if self.query_fn:
            for v in needed:
                if v not in ctx: ctx[v] = self.query_fn(v)
        result = evaluate(ast_node, ctx)
        lines = [f"  Expression : {expression}",
                 f"  Variables  : {sorted(needed) or '(none)'}"]
        for v in sorted(needed):
            lines.append(f"    {v} = {ctx[v]}")
        if isinstance(result, list):
            lines.append(f"  Result     : {[round(x,4) for x in result]}")
        else:
            disp = int(result) if isinstance(result, float) and result == int(result) else round(result, 6)
            lines.append(f"  Result     : {disp}")
        return "\n".join(lines)

