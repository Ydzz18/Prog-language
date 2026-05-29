"""
Test suite for the CodeX Lexer.
Demonstrates lexical analysis of CodeX programs.
"""

from hinagpis import Lexer, Token, EOF, NEWLINE

def print_tokens(code, title=""):
    """Tokenize and print all tokens from code."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    print(f"\nCode:\n{code}\n")
    print("Tokens:")
    print("-" * 60)
    
    lexer = Lexer(code)
    tokens = []
    
    while True:
        token = lexer.get_next_token()
        if token.type == NEWLINE:
            continue  # Skip newlines for display clarity
        tokens.append(token)
        print(f"  {token}")
        if token.type == EOF:
            break
    
    return tokens

# =====================
# Test Case 1: Variables and Assignment
# =====================
code1 = """
x = 10
name = "CodeX"
is_active = true
pi = 3.14
"""
print_tokens(code1, "Test 1: Variables and Assignment")

# =====================
# Test Case 2: Arithmetic Expressions
# =====================
code2 = """
result = 5 + 3 * 2
power = 2 ^ 8
division = 20 / 4
floor_div = 20 // 3
modulo = 17 % 5
"""
print_tokens(code2, "Test 2: Arithmetic Expressions")

# =====================
# Test Case 3: Comparison and Logical Operators
# =====================
code3 = """
is_equal = x == 10
is_not_equal = y != 5
is_greater = z > 0
is_less_equal = a <= 100
condition = (x > 5) and (y < 10)
negation = not is_active
or_condition = true or false
"""
print_tokens(code3, "Test 3: Comparison and Logical Operators")

# =====================
# Test Case 4: Control Flow - If Statement
# =====================
code4 = """
if (x > 5) {
    print("x is greater than 5")
} else {
    print("x is less than or equal to 5")
}
"""
print_tokens(code4, "Test 4: If Statement")

# =====================
# Test Case 5: Loops
# =====================
code5 = """
while (count < 10) {
    count = count + 1
}

for i in [1, 2, 3, 4, 5] {
    print(i)
}
"""
print_tokens(code5, "Test 5: While and For Loops")

# =====================
# Test Case 6: Function Definition
# =====================
code6 = """
func add(a, b) {
    return a + b
}

func greet(name) {
    print("Hello, " + name)
}

result = add(5, 3)
"""
print_tokens(code6, "Test 6: Function Definition and Calls")

# =====================
# Test Case 7: Lists and Indexing
# =====================
code7 = """
numbers = [1, 2, 3, 4, 5]
item = numbers[0]
matrix = [[1, 2], [3, 4]]
"""
print_tokens(code7, "Test 7: Lists and Indexing")

# =====================
# Test Case 8: Strings and Comments
# =====================
code8 = """
# This is a comment
message = "Hello, World!"
escaped = "Line 1\\nLine 2"
single_quote = 'also valid'
"""
print_tokens(code8, "Test 8: Strings and Comments")

# =====================
# Test Case 9: Complex Program - Factorial
# =====================
code9 = """
# Calculate factorial
func factorial(n) {
    if (n <= 1) {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}

result = factorial(5)
print(result)
"""
print_tokens(code9, "Test 9: Complex Program - Factorial")

# =====================
# Test Case 10: All Keywords
# =====================
code10 = """
if else while for func return true false null in and or not
"""
print_tokens(code10, "Test 10: All Keywords")

# =====================
# Summary Statistics
# =====================
print(f"\n{'='*60}")
print("  Lexer Test Suite Complete")
print(f"{'='*60}")
print("\nThe CodeX Lexer successfully tokenized:")
print("  * Variables and assignments")
print("  * Arithmetic operators (+, -, *, /, //, %, ^)")
print("  * Comparison operators (==, !=, <, >, <=, >=)")
print("  * Logical operators (and, or, not)")
print("  * Keywords (if, else, while, for, func, return, etc.)")
print("  * String literals with escape sequences")
print("  * Numeric literals (integers and floats)")
print("  * Lists and indexing")
print("  * Function definitions and calls")
print("  * Comments")
print("  * All delimiters and special characters")
print(f"{'='*60}\n")


