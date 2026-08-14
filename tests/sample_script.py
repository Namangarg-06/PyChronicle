# Sample script for testing AST parsing

# 1. Simple Assignment
x = 10
name = "PyChronicle"

# 2. Annotated Assignment
age: int = 25
is_active: bool = True

# 3. Tuple/List Unpacking
a, b = 1, 2
[c, d] = [3, 4]
nested_a, (nested_b, nested_c) = 10, (20, 30)

# 4. Augmented Assignment
counter = 0
counter += 1
multiplier = 1
multiplier *= 2

# 5. Attribute Assignment
class Person:
    def __init__(self):
        self.name = "John"
        self.age = 30

# 6. Subscript Assignment
items = [1, 2, 3]
items[0] = 99
