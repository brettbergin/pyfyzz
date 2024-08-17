#!/usr/bin/env python3


class ExampleMath:
    def __init__(self) -> None:
        pass

    def example_add(self, a: int, b: int) -> int:
        return int(a + b)

    def example_subtract(self, x: int, y: int) -> int:
        # Verifies parameters types to defend from type confusion.
        if not isinstance(x, int) or not isinstance(y, int):
            return None
        return int(x - y)
