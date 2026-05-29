"""Hinagpis / SadBoy CodeX language implementation.

This file is the canonical project basis. It keeps the original SadBoy token
names from the first lexer (`KUNG`, `WHATIF`, `DAGDAG`, `BAWAS`, etc.) and
extends that foundation into a full language pipeline:

lexer -> parser -> AST -> semantic analyzer -> optimizer -> interpreter.
"""

import argparse
import sys

INTEGER = "INTEGER"; FLOAT = "FLOAT"; STRING = "STRING"; IDENTIFIER = "IDENTIFIER"

# Original project token names/values are preserved.
# English keywords are accepted as aliases, but token output uses these names.
IF = "KUNG"; ELSE = "WHATIF"; WHILE = "HABANG"; FOR = "PARA"; FUNC = "GAWA"; RETURN = "BALIKAN"
TRUE = "NOCAP"; FALSE = "CAP"; NULL = "WALA"; IN = "SA"; AND = "AT"; OR = "O"; NOT = "HINDI"
PLUS = "DAGDAG"; MINUS = "BAWAS"; MUL = "DAMAY"; DIV = "HATI"; FD = "TAPIK"; MOD = "NATIRA"; EXP = "LALIM"
EQ = "EQ"; NEQ = "NEQ"; LT = "LT"; GT = "GT"; LTE = "LTE"; GTE = "GTE"; ASSIGN = "ASSIGN"
LPAREN = "LPAREN"; RPAREN = "RPAREN"; LBRACE = "LBRACE"; RBRACE = "RBRACE"
LBRACKET = "LBRACKET"; RBRACKET = "RBRACKET"; COLON = "COLON"; SEMICOLON = "SEMICOLON"
COMMA = "COMMA"; DOT = "DOT"; NEWLINE = "NEWLINE"; EOF = "EOF"; COMMENT = "COMMENT"

KEYWORDS = {
    "if": IF, "else": ELSE, "while": WHILE, "for": FOR, "func": FUNC, "return": RETURN,
    "true": TRUE, "false": FALSE, "null": NULL, "in": IN, "and": AND, "or": OR, "not": NOT,
    "kung": IF, "o_else": ELSE, "habang": WHILE, "para": FOR, "gawa": FUNC, "balikan": RETURN,
    "nocap": TRUE, "cap": FALSE, "walang": NULL, "wala": NULL, "sa": IN, "at": AND, "o": OR,
    "hindi": NOT,
}
LITERAL_TYPES = (INTEGER, FLOAT, STRING, TRUE, FALSE, NULL)


class CodeXError(Exception):
    phase = "CodeX"
    def __init__(self, message, line=None, column=None):
        self.message = message; self.line = line; self.column = column
        loc = "" if line is None else " at line {0}, column {1}".format(line, column)
        super().__init__("{0} error{1}: {2}".format(self.phase, loc, message))


class LexerError(CodeXError): phase = "Lexer"
class ParseError(CodeXError): phase = "Parser"
class SemanticError(CodeXError): phase = "Semantic"
class RuntimeCodeXError(CodeXError): phase = "Runtime"


class Token:
    def __init__(self, type, value, line=1, column=1):
        self.type = type; self.value = value; self.line = line; self.column = column
    def __str__(self): return "Token({0}, {1!r})".format(self.type, self.value)
    def __repr__(self): return self.__str__()


class Lexer:
    def __init__(self, text):
        self.text = (text or "").lstrip("\ufeff"); self.pos = 0; self.line = 1; self.column = 1
        self.current_char = self.text[0] if self.text else None
    def advance(self):
        if self.current_char == "\n": self.line += 1; self.column = 1
        else: self.column += 1
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
    def peek(self, offset=1):
        i = self.pos + offset
        return self.text[i] if i < len(self.text) else None
    def skip_whitespace(self):
        while self.current_char is not None and self.current_char in " \t\r": self.advance()
    def skip_comment(self):
        while self.current_char is not None and self.current_char != "\n": self.advance()
    def read_number(self):
        line, col = self.line, self.column; s = ""
        while self.current_char is not None and self.current_char.isdigit(): s += self.current_char; self.advance()
        if self.current_char == "." and self.peek() is not None and self.peek().isdigit():
            s += self.current_char; self.advance()
            while self.current_char is not None and self.current_char.isdigit(): s += self.current_char; self.advance()
            return Token(FLOAT, float(s), line, col)
        return Token(INTEGER, int(s), line, col)
    def read_string(self, quote):
        line, col = self.line, self.column; out = ""; self.advance()
        esc = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}
        while self.current_char is not None and self.current_char != quote:
            if self.current_char == "\\":
                self.advance()
                if self.current_char is None: raise LexerError("Unterminated escape sequence", line, col)
                out += esc.get(self.current_char, self.current_char); self.advance()
            else:
                out += self.current_char; self.advance()
        if self.current_char != quote: raise LexerError("Unterminated string", line, col)
        self.advance(); return Token(STRING, out, line, col)
    def read_identifier(self):
        line, col = self.line, self.column; s = ""
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == "_"):
            s += self.current_char; self.advance()
        typ = KEYWORDS.get(s, IDENTIFIER)
        if typ == TRUE: return Token(TRUE, True, line, col)
        if typ == FALSE: return Token(FALSE, False, line, col)
        if typ == NULL: return Token(NULL, None, line, col)
        return Token(typ, s, line, col)
    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char in " \t\r": self.skip_whitespace(); continue
            if self.current_char == "#": self.skip_comment(); continue
            if self.current_char == "\n":
                t = Token(NEWLINE, "\n", self.line, self.column); self.advance(); return t
            if self.current_char.isdigit(): return self.read_number()
            if self.current_char in ('"', "'"): return self.read_string(self.current_char)
            if self.current_char.isalpha() or self.current_char == "_": return self.read_identifier()
            line, col = self.line, self.column; two = self.current_char + (self.peek() or "")
            if two in {"==": EQ, "!=": NEQ, "<=": LTE, ">=": GTE, "//": FD}:
                self.advance(); self.advance(); return Token({"==": EQ, "!=": NEQ, "<=": LTE, ">=": GTE, "//": FD}[two], two, line, col)
            singles = {"+": PLUS, "-": MINUS, "*": MUL, "/": DIV, "%": MOD, "^": EXP, "=": ASSIGN,
                       "<": LT, ">": GT, "(": LPAREN, ")": RPAREN, "{": LBRACE, "}": RBRACE,
                       "[": LBRACKET, "]": RBRACKET, ":": COLON, ";": SEMICOLON, ",": COMMA, ".": DOT}
            if self.current_char in singles:
                ch = self.current_char; self.advance(); return Token(singles[ch], ch, line, col)
            raise LexerError("Unexpected character {0!r}".format(self.current_char), line, col)
        return Token(EOF, None, self.line, self.column)
    def tokenize(self):
        out = []
        while True:
            t = self.get_next_token(); out.append(t)
            if t.type == EOF: return out


class Node: pass
class Program(Node):
    def __init__(self, statements): self.statements = statements
class Block(Node):
    def __init__(self, statements): self.statements = statements
class VarAssign(Node):
    def __init__(self, name, value, token): self.name = name; self.value = value; self.token = token
class IndexAssign(Node):
    def __init__(self, target, index, value, token): self.target = target; self.index = index; self.value = value; self.token = token
class ExprStatement(Node):
    def __init__(self, expression): self.expression = expression
class IfStatement(Node):
    def __init__(self, condition, then_block, else_block=None): self.condition = condition; self.then_block = then_block; self.else_block = else_block
class WhileStatement(Node):
    def __init__(self, condition, body): self.condition = condition; self.body = body
class ForStatement(Node):
    def __init__(self, name, iterable, body, token): self.name = name; self.iterable = iterable; self.body = body; self.token = token
class FunctionDef(Node):
    def __init__(self, name, params, body, token): self.name = name; self.params = params; self.body = body; self.token = token
class ReturnStatement(Node):
    def __init__(self, value, token): self.value = value; self.token = token
class Literal(Node):
    def __init__(self, value, token): self.value = value; self.token = token
class Variable(Node):
    def __init__(self, name, token): self.name = name; self.token = token
class ListLiteral(Node):
    def __init__(self, elements, token): self.elements = elements; self.token = token
class IndexExpression(Node):
    def __init__(self, target, index, token): self.target = target; self.index = index; self.token = token
class UnaryOp(Node):
    def __init__(self, op, operand, token): self.op = op; self.operand = operand; self.token = token
class BinaryOp(Node):
    def __init__(self, left, op, right, token): self.left = left; self.op = op; self.right = right; self.token = token
class Call(Node):
    def __init__(self, callee, args, token): self.callee = callee; self.args = args; self.token = token


class Parser:
    """Recursive-descent parser that validates syntax and builds an AST."""
    def __init__(self, lexer_or_tokens):
        self.tokens = lexer_or_tokens.tokenize() if isinstance(lexer_or_tokens, Lexer) else lexer_or_tokens
        self.pos = 0; self.current_token = self.tokens[0]
    def advance(self):
        if self.pos < len(self.tokens) - 1: self.pos += 1; self.current_token = self.tokens[self.pos]
        return self.current_token
    def match(self, *types):
        if self.current_token.type in types:
            t = self.current_token; self.advance(); return t
        return None
    def expect(self, typ, msg=None):
        if self.current_token.type == typ:
            t = self.current_token; self.advance(); return t
        raise ParseError(msg or "Expected {0}, got {1}".format(typ, self.current_token.type), self.current_token.line, self.current_token.column)
    def skip_separators(self):
        while self.current_token.type in (NEWLINE, SEMICOLON): self.advance()
    def parse(self):
        stmts = []; self.skip_separators()
        while self.current_token.type != EOF:
            stmts.append(self.statement()); self.skip_separators()
        return Program(stmts)
    def statement(self):
        if self.current_token.type == IF: return self.if_statement()
        if self.current_token.type == WHILE: return self.while_statement()
        if self.current_token.type == FOR: return self.for_statement()
        if self.current_token.type == FUNC: return self.function_def()
        if self.current_token.type == RETURN: return self.return_statement()
        return self.simple_statement()
    def simple_statement(self):
        expr = self.expression()
        if self.current_token.type == ASSIGN:
            tok = self.current_token; self.advance(); value = self.expression()
            if isinstance(expr, Variable): return VarAssign(expr.name, value, tok)
            if isinstance(expr, IndexExpression): return IndexAssign(expr.target, expr.index, value, tok)
            raise ParseError("Invalid assignment target", tok.line, tok.column)
        return ExprStatement(expr)
    def block(self):
        self.expect(LBRACE, "Expected '{' to start a block"); stmts = []; self.skip_separators()
        while self.current_token.type not in (RBRACE, EOF):
            stmts.append(self.statement()); self.skip_separators()
        self.expect(RBRACE, "Expected '}' to close a block"); return Block(stmts)
    def if_statement(self):
        self.expect(IF); self.expect(LPAREN, "Expected '(' after if")
        cond = self.expression(); self.expect(RPAREN, "Expected ')' after if condition")
        then = self.block(); self.skip_separators(); other = None
        if self.match(ELSE): other = Block([self.if_statement()]) if self.current_token.type == IF else self.block()
        return IfStatement(cond, then, other)
    def while_statement(self):
        self.expect(WHILE); self.expect(LPAREN, "Expected '(' after while")
        cond = self.expression(); self.expect(RPAREN, "Expected ')' after while condition")
        return WhileStatement(cond, self.block())
    def for_statement(self):
        tok = self.expect(FOR); name = self.expect(IDENTIFIER, "Expected loop variable after for").value
        self.expect(IN, "Expected 'in' after loop variable"); iterable = self.expression()
        return ForStatement(name, iterable, self.block(), tok)
    def function_def(self):
        tok = self.expect(FUNC); name = self.expect(IDENTIFIER, "Expected function name").value
        self.expect(LPAREN, "Expected '(' after function name"); params = []
        if self.current_token.type != RPAREN:
            params.append(self.expect(IDENTIFIER, "Expected parameter name").value)
            while self.match(COMMA): params.append(self.expect(IDENTIFIER, "Expected parameter name after ','").value)
        self.expect(RPAREN, "Expected ')' after parameters"); return FunctionDef(name, params, self.block(), tok)
    def return_statement(self):
        tok = self.expect(RETURN)
        if self.current_token.type in (NEWLINE, SEMICOLON, RBRACE, EOF): return ReturnStatement(Literal(None, tok), tok)
        return ReturnStatement(self.expression(), tok)
    def expression(self): return self.or_expr()
    def or_expr(self):
        node = self.and_expr()
        while self.current_token.type == OR:
            tok = self.current_token; self.advance(); node = BinaryOp(node, OR, self.and_expr(), tok)
        return node
    def and_expr(self):
        node = self.equality()
        while self.current_token.type == AND:
            tok = self.current_token; self.advance(); node = BinaryOp(node, AND, self.equality(), tok)
        return node
    def equality(self):
        node = self.comparison()
        while self.current_token.type in (EQ, NEQ):
            tok = self.current_token; self.advance(); node = BinaryOp(node, tok.type, self.comparison(), tok)
        return node
    def comparison(self):
        node = self.term()
        while self.current_token.type in (LT, GT, LTE, GTE):
            tok = self.current_token; self.advance(); node = BinaryOp(node, tok.type, self.term(), tok)
        return node
    def term(self):
        node = self.factor()
        while self.current_token.type in (PLUS, MINUS):
            tok = self.current_token; self.advance(); node = BinaryOp(node, tok.type, self.factor(), tok)
        return node
    def factor(self):
        node = self.power()
        while self.current_token.type in (MUL, DIV, FD, MOD):
            tok = self.current_token; self.advance(); node = BinaryOp(node, tok.type, self.power(), tok)
        return node
    def power(self):
        node = self.unary()
        if self.current_token.type == EXP:
            tok = self.current_token; self.advance(); node = BinaryOp(node, EXP, self.power(), tok)
        return node
    def unary(self):
        if self.current_token.type in (MINUS, NOT):
            tok = self.current_token; self.advance(); return UnaryOp(tok.type, self.unary(), tok)
        return self.call()
    def call(self):
        node = self.primary()
        while True:
            if self.current_token.type == LPAREN:
                tok = self.current_token; self.advance(); args = []
                if self.current_token.type != RPAREN:
                    args.append(self.expression())
                    while self.match(COMMA): args.append(self.expression())
                self.expect(RPAREN, "Expected ')' after arguments"); node = Call(node, args, tok)
            elif self.current_token.type == LBRACKET:
                tok = self.current_token; self.advance(); idx = self.expression()
                self.expect(RBRACKET, "Expected ']' after index"); node = IndexExpression(node, idx, tok)
            else: return node
    def primary(self):
        tok = self.current_token
        if tok.type in LITERAL_TYPES: self.advance(); return Literal(tok.value, tok)
        if tok.type == IDENTIFIER: self.advance(); return Variable(tok.value, tok)
        if tok.type == LPAREN:
            self.advance(); expr = self.expression(); self.expect(RPAREN, "Expected ')' after expression"); return expr
        if tok.type == LBRACKET:
            self.advance(); elems = []
            if self.current_token.type != RBRACKET:
                elems.append(self.expression())
                while self.match(COMMA): elems.append(self.expression())
            self.expect(RBRACKET, "Expected ']' after list literal"); return ListLiteral(elems, tok)
        raise ParseError("Expected expression, got {0}".format(tok.type), tok.line, tok.column)


class Scope:
    def __init__(self, parent=None): self.parent = parent; self.names = set()
    def define(self, name): self.names.add(name)
    def contains(self, name): return name in self.names or (self.parent.contains(name) if self.parent else False)


class SemanticAnalyzer:
    """Checks undefined variables/functions, function arity, returns, and basic types."""
    def __init__(self):
        self.scope = Scope(); self.functions = {"print": None, "len": 1, "type": 1, "input": None}
        for n in self.functions: self.scope.define(n)
        self.in_function = 0
    def analyze(self, node): return getattr(self, "visit_" + node.__class__.__name__)(node)
    def visit_Program(self, node):
        for s in node.statements:
            if isinstance(s, FunctionDef): self.scope.define(s.name); self.functions[s.name] = len(s.params)
        for s in node.statements: self.analyze(s)
        return node
    def visit_Block(self, node):
        old = self.scope; self.scope = Scope(old)
        for s in node.statements: self.analyze(s)
        self.scope = old
    def visit_VarAssign(self, node): self.analyze(node.value); self.scope.define(node.name)
    def visit_IndexAssign(self, node): self.analyze(node.target); self.analyze(node.index); self.analyze(node.value)
    def visit_ExprStatement(self, node): self.analyze(node.expression)
    def visit_IfStatement(self, node): self.analyze(node.condition); self.analyze(node.then_block); self.analyze(node.else_block) if node.else_block else None
    def visit_WhileStatement(self, node): self.analyze(node.condition); self.analyze(node.body)
    def visit_ForStatement(self, node):
        self.analyze(node.iterable); old = self.scope; self.scope = Scope(old); self.scope.define(node.name)
        for s in node.body.statements: self.analyze(s)
        self.scope = old
    def visit_FunctionDef(self, node):
        old = self.scope; self.scope = Scope(old)
        for p in node.params: self.scope.define(p)
        self.in_function += 1
        for s in node.body.statements: self.analyze(s)
        self.in_function -= 1; self.scope = old
    def visit_ReturnStatement(self, node):
        if self.in_function == 0: raise SemanticError("return can only be used inside a function", node.token.line, node.token.column)
        self.analyze(node.value)
    def visit_Literal(self, node): return type_name(node.value)
    def visit_Variable(self, node):
        if not self.scope.contains(node.name): raise SemanticError("Undefined variable '{0}'".format(node.name), node.token.line, node.token.column)
    def visit_ListLiteral(self, node):
        for e in node.elements: self.analyze(e)
    def visit_IndexExpression(self, node): self.analyze(node.target); self.analyze(node.index)
    def visit_UnaryOp(self, node):
        self.analyze(node.operand)
        if isinstance(node.operand, Literal) and node.op == MINUS and not is_number(node.operand.value):
            raise SemanticError("Unary '-' requires a number", node.token.line, node.token.column)
    def visit_BinaryOp(self, node):
        self.analyze(node.left); self.analyze(node.right)
        if isinstance(node.left, Literal) and isinstance(node.right, Literal):
            if node.op in (MINUS, MUL, DIV, FD, MOD, EXP, LT, GT, LTE, GTE) and not (is_number(node.left.value) and is_number(node.right.value)):
                raise SemanticError("Operator requires numeric operands", node.token.line, node.token.column)
    def visit_Call(self, node):
        if isinstance(node.callee, Variable):
            name = node.callee.name
            if name not in self.functions and not self.scope.contains(name):
                raise SemanticError("Undefined function '{0}'".format(name), node.callee.token.line, node.callee.token.column)
            arity = self.functions.get(name)
            if arity is not None and arity != len(node.args):
                raise SemanticError("Function '{0}' expects {1} arguments but got {2}".format(name, arity, len(node.args)), node.token.line, node.token.column)
        else: self.analyze(node.callee)
        for a in node.args: self.analyze(a)


class Optimizer:
    """Constant folding, constant branch pruning, and dead-code removal after return."""
    def optimize(self, node): return getattr(self, "visit_" + node.__class__.__name__, lambda n: n)(node)
    def visit_Program(self, node): node.statements = [self.optimize(s) for s in node.statements]; return node
    def visit_Block(self, node):
        out = []
        for s in node.statements:
            out.append(self.optimize(s))
            if isinstance(s, ReturnStatement): break
        node.statements = out; return node
    def visit_VarAssign(self, node): node.value = self.optimize(node.value); return node
    def visit_IndexAssign(self, node): node.target = self.optimize(node.target); node.index = self.optimize(node.index); node.value = self.optimize(node.value); return node
    def visit_ExprStatement(self, node): node.expression = self.optimize(node.expression); return node
    def visit_IfStatement(self, node):
        node.condition = self.optimize(node.condition); node.then_block = self.optimize(node.then_block)
        node.else_block = self.optimize(node.else_block) if node.else_block else None
        if isinstance(node.condition, Literal): return node.then_block if truthy(node.condition.value) else (node.else_block or Block([]))
        return node
    def visit_WhileStatement(self, node): node.condition = self.optimize(node.condition); node.body = self.optimize(node.body); return node
    def visit_ForStatement(self, node): node.iterable = self.optimize(node.iterable); node.body = self.optimize(node.body); return node
    def visit_FunctionDef(self, node): node.body = self.optimize(node.body); return node
    def visit_ReturnStatement(self, node): node.value = self.optimize(node.value); return node
    def visit_ListLiteral(self, node): node.elements = [self.optimize(e) for e in node.elements]; return node
    def visit_IndexExpression(self, node):
        node.target = self.optimize(node.target); node.index = self.optimize(node.index)
        if isinstance(node.target, ListLiteral) and isinstance(node.index, Literal) and isinstance(node.index.value, int):
            try: return node.target.elements[node.index.value]
            except IndexError: pass
        return node
    def visit_UnaryOp(self, node):
        node.operand = self.optimize(node.operand)
        if isinstance(node.operand, Literal):
            try:
                if node.op == MINUS: return Literal(-node.operand.value, node.token)
                if node.op == NOT: return Literal(not truthy(node.operand.value), node.token)
            except Exception: pass
        return node
    def visit_BinaryOp(self, node):
        node.left = self.optimize(node.left); node.right = self.optimize(node.right)
        if isinstance(node.left, Literal) and isinstance(node.right, Literal):
            try: return Literal(apply_binary(node.op, node.left.value, node.right.value, node.token), node.token)
            except Exception: pass
        return node
    def visit_Call(self, node): node.callee = self.optimize(node.callee); node.args = [self.optimize(a) for a in node.args]; return node


class ReturnSignal(Exception):
    def __init__(self, value): self.value = value


class Environment:
    def __init__(self, parent=None): self.parent = parent; self.values = {}
    def define(self, name, value): self.values[name] = value
    def contains(self, name):
        return name in self.values or (self.parent.contains(name) if self.parent else False)
    def assign(self, name, value):
        if name in self.values: self.values[name] = value; return
        if self.parent is not None and self.parent.contains(name): self.parent.assign(name, value); return
        self.values[name] = value
    def get(self, name, token=None):
        if name in self.values: return self.values[name]
        if self.parent is not None: return self.parent.get(name, token)
        raise RuntimeCodeXError("Undefined variable '{0}'".format(name), token.line if token else None, token.column if token else None)


class UserFunction:
    def __init__(self, declaration, closure): self.declaration = declaration; self.closure = closure
    def call(self, interpreter, args, token):
        env = Environment(self.closure)
        for name, value in zip(self.declaration.params, args): env.define(name, value)
        try: interpreter.execute_block(self.declaration.body, env)
        except ReturnSignal as signal: return signal.value
        return None
    def __repr__(self): return "<func {0}>".format(self.declaration.name)


class Interpreter:
    """Tree-walking interpreter for CodeX programs."""
    def __init__(self, debug=False):
        self.debug = debug; self.globals = Environment(); self.environment = self.globals; self.output = []; self.install_builtins()
    def install_builtins(self):
        def builtin_print(*args):
            text = " ".join(to_display(a) for a in args); print(text); self.output.append(text); return None
        self.globals.define("print", builtin_print); self.globals.define("len", lambda value: len(value))
        self.globals.define("type", lambda value: type_name(value)); self.globals.define("input", lambda prompt="": input(str(prompt)))
    def run(self, node): return self.visit(node)
    def visit(self, node):
        if self.debug: print("[debug]", node.__class__.__name__)
        return getattr(self, "visit_" + node.__class__.__name__)(node)
    def visit_Program(self, node):
        result = None
        for s in node.statements: result = self.visit(s)
        return result
    def visit_Block(self, node): return self.execute_block(node, Environment(self.environment))
    def execute_block(self, block, env):
        old = self.environment; self.environment = env
        try:
            result = None
            for s in block.statements: result = self.visit(s)
            return result
        finally: self.environment = old
    def visit_VarAssign(self, node):
        value = self.visit(node.value); self.environment.assign(node.name, value); return value
    def visit_IndexAssign(self, node):
        target = self.visit(node.target); index = self.visit(node.index); value = self.visit(node.value)
        try: target[index] = value
        except Exception as exc: raise RuntimeCodeXError("Invalid indexed assignment: {0}".format(exc), node.token.line, node.token.column)
        return value
    def visit_ExprStatement(self, node): return self.visit(node.expression)
    def visit_IfStatement(self, node):
        if truthy(self.visit(node.condition)): return self.visit(node.then_block)
        return self.visit(node.else_block) if node.else_block else None
    def visit_WhileStatement(self, node):
        result = None; guard = 0
        while truthy(self.visit(node.condition)):
            result = self.visit(node.body); guard += 1
            if guard > 1000000: raise RuntimeCodeXError("Possible infinite loop stopped after 1,000,000 iterations")
        return result
    def visit_ForStatement(self, node):
        iterable = self.visit(node.iterable); result = None
        try: iterator = iter(iterable)
        except TypeError: raise RuntimeCodeXError("for loop requires an iterable value", node.token.line, node.token.column)
        for value in iterator:
            env = Environment(self.environment); env.define(node.name, value); result = self.execute_block(node.body, env)
        return result
    def visit_FunctionDef(self, node):
        fn = UserFunction(node, self.environment); self.environment.define(node.name, fn); return fn
    def visit_ReturnStatement(self, node): raise ReturnSignal(self.visit(node.value))
    def visit_Literal(self, node): return node.value
    def visit_Variable(self, node): return self.environment.get(node.name, node.token)
    def visit_ListLiteral(self, node): return [self.visit(e) for e in node.elements]
    def visit_IndexExpression(self, node):
        target = self.visit(node.target); index = self.visit(node.index)
        try: return target[index]
        except Exception as exc: raise RuntimeCodeXError("Invalid index operation: {0}".format(exc), node.token.line, node.token.column)
    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if node.op == MINUS:
            if not is_number(value): raise RuntimeCodeXError("Unary '-' requires a number", node.token.line, node.token.column)
            return -value
        if node.op == NOT: return not truthy(value)
        raise RuntimeCodeXError("Unknown unary operator", node.token.line, node.token.column)
    def visit_BinaryOp(self, node):
        if node.op == AND:
            left = self.visit(node.left); return self.visit(node.right) if truthy(left) else False
        if node.op == OR:
            left = self.visit(node.left); return True if truthy(left) else self.visit(node.right)
        return apply_binary(node.op, self.visit(node.left), self.visit(node.right), node.token)
    def visit_Call(self, node):
        callee = self.visit(node.callee); args = [self.visit(a) for a in node.args]
        if isinstance(callee, UserFunction):
            if len(args) != len(callee.declaration.params):
                raise RuntimeCodeXError("Function expected {0} arguments but got {1}".format(len(callee.declaration.params), len(args)), node.token.line, node.token.column)
            return callee.call(self, args, node.token)
        if callable(callee):
            try: return callee(*args)
            except TypeError as exc: raise RuntimeCodeXError("Invalid function call: {0}".format(exc), node.token.line, node.token.column)
        raise RuntimeCodeXError("Value is not callable", node.token.line, node.token.column)


def is_number(value): return isinstance(value, (int, float)) and not isinstance(value, bool)
def truthy(value): return bool(value)
def type_name(value):
    if value is None: return "null"
    if isinstance(value, bool): return "bool"
    if isinstance(value, int): return "int"
    if isinstance(value, float): return "float"
    if isinstance(value, str): return "string"
    if isinstance(value, list): return "list"
    if isinstance(value, UserFunction): return "function"
    if callable(value): return "builtin"
    return type(value).__name__
def to_display(value):
    if value is None: return "null"
    if value is True: return "true"
    if value is False: return "false"
    return str(value)
def apply_binary(op, left, right, token):
    try:
        if op == PLUS: return left + right
        if op == MINUS: return left - right
        if op == MUL: return left * right
        if op == DIV: return left / right
        if op == FD: return left // right
        if op == MOD: return left % right
        if op == EXP: return left ** right
        if op == EQ: return left == right
        if op == NEQ: return left != right
        if op == LT: return left < right
        if op == GT: return left > right
        if op == LTE: return left <= right
        if op == GTE: return left >= right
        if op == AND: return truthy(left) and truthy(right)
        if op == OR: return truthy(left) or truthy(right)
    except ZeroDivisionError:
        raise RuntimeCodeXError("Division by zero", token.line, token.column)
    except Exception as exc:
        raise RuntimeCodeXError("Invalid operation: {0}".format(exc), token.line, token.column)
    raise RuntimeCodeXError("Unknown binary operator {0}".format(op), token.line, token.column)


def compile_source(source, optimize=True):
    ast = Parser(Lexer(source)).parse()
    SemanticAnalyzer().analyze(ast)
    return Optimizer().optimize(ast) if optimize else ast
def run_source(source, optimize=True, debug=False): return Interpreter(debug=debug).run(compile_source(source, optimize))
def repl():
    print("CodeX REPL. Type 'exit' to quit.")
    interpreter = Interpreter()
    while True:
        try:
            line = input("codex> ")
            if line.strip() in ("exit", "quit"): break
            result = interpreter.run(compile_source(line, optimize=True))
            if result is not None: print(to_display(result))
        except CodeXError as exc: print(exc)
        except KeyboardInterrupt: print(); break
def main(argv=None):
    p = argparse.ArgumentParser(description="Run CodeX source files.")
    p.add_argument("file", nargs="?", help="Path to a .codex source file")
    p.add_argument("--tokens", action="store_true", help="Print tokens only")
    p.add_argument("--ast", action="store_true", help="Parse and validate only")
    p.add_argument("--no-opt", action="store_true", help="Disable AST optimization")
    p.add_argument("--debug", action="store_true", help="Print interpreter debug trace")
    args = p.parse_args(argv)
    if not args.file: repl(); return 0
    with open(args.file, "r", encoding="utf-8") as f: source = f.read()
    try:
        if args.tokens:
            for token in Lexer(source).tokenize(): print(token)
            return 0
        ast = compile_source(source, optimize=not args.no_opt)
        if args.ast: print("AST parsed, semantically valid, and optimized successfully."); return 0
        Interpreter(debug=args.debug).run(ast); return 0
    except CodeXError as exc:
        print(exc, file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
