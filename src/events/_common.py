import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Collection
from typing import Iterator, ParamSpec, TypeAlias, TypeVar


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


__all__ = [
    "Delegate",
    "void",
]


void: TypeAlias = object | None
"""
Specifies a return type for a method that does not return a value.

Python does not provide a void type, which is a useful feature in callbacks,
and is clearly different from `None`.

Comparison with TypeScript:

```ts
function foo(): void {}
```
```py
<==> def foo() -> None: pass
```
```ts
let bar: () => void;
```
```py
<==> bar: Callable[[], Any]
```
"""


P = ParamSpec("P")
T = TypeVar("T")


class Delegate(Collection[Callable[P, T]], ABC):
    """
    Represents a multicast delegate that can have more than one element in its invocation list.

    Type Args:
        **P: Parameter specification.
        T: Return type.
    """

    __slots__ = ["__invocation_list"]

    def __init__(self, *values: Callable[P, T]) -> None:
        """
        Initializes a new instance of the `Delegate` class.

        Args:
            *values ((**P) -> T): Delegate invocation list.
        """

        self.__invocation_list = [*values]

    def get_invocation_list(self) -> list[Callable[P, T]]:
        """
        Returns a copy of the invocation list of this multicast delegate, in invocation order.

        Returns:
            list[(**P) -> T]: A list of callable objects.
        """

        return [*self.__invocation_list]

    def __iadd__(self, value: Callable[P, T], /) -> Self:
        """
        Appends the callable object to the invocation list.

        Args:
            value ((**P) -> T): A callable object.

        Returns:
            Self: This delegate.
        """

        self.__invocation_list.append(value)
        return self

    def __isub__(self, value: Callable[P, T], /) -> Self:
        """
        Removes the last occurrence of the callable object from the invocation list.

        Args:
            value ((**P) -> T): A callable object

        Returns:
            Self: This delegate.
        """

        for i in range(len(self.__invocation_list) - 1, -1, -1):
            if self.__invocation_list[i] == value:
                del self.__invocation_list[i]
                break
        return self

    @abstractmethod
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Invokes the callable objects in the invocation list in the order.

        Raises:
            NotImplementedError: Derived classes must provide the implementation.

        Returns:
            T: The return value.
        """

        raise NotImplementedError

    def __contains__(self, x: object, /) -> bool:
        """
        Returns whether the specified object is a callable object in the invocation list.

        Args:
            obj (object): An object.

        Returns:
            bool: `True` if the object is in the invocation list, `False` otherwise.
        """

        return x in self.__invocation_list

    def __iter__(self) -> Iterator[Callable[P, T]]:
        """
        Returns an iterator of the invocation list.

        Yields:
            ((**P) -> T): A callable object from the invocation list.
        """

        yield from self.__invocation_list

    def __len__(self) -> int:
        """
        Returns the number of items in the invocation list.

        Returns:
            int: The length of the invocation list.
        """

        return len(self.__invocation_list)
