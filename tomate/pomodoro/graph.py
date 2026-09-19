from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Annotated, get_args, get_origin, get_type_hints

_INJECTED = object()
type Injected[T] = Annotated[T, _INJECTED]


class MissingProviderError(KeyError):
    """A service key could not be resolved from a graph."""

    def __init__(self, key: type[object], path: tuple[type[object], ...]) -> None:
        super().__init__(key, path)
        self.key = key
        self.path = path

    def __str__(self) -> str:
        return f"No provider for {_key_name(self.key)} (resolution path: {_path_name(self.path)})"


class DependencyCycleError(RuntimeError):
    """Resolving a service would recursively resolve itself."""

    def __init__(self, path: tuple[type[object], ...]) -> None:
        super().__init__(f"Dependency cycle: {_path_name(path)}")
        self.path = path


class Graph:
    """Lazily resolves explicitly registered singleton services."""

    def __init__(self) -> None:
        self._providers: dict[type[object], Callable[[], object]] = {}
        self._singletons: dict[type[object], object] = {}
        self._resolving: list[type[object]] = []

    def register_factory[T](self, key: type[T], factory: Callable[..., T]) -> None:
        """Register ``factory`` as the singleton provider for ``key``.

        Replacing a provider never replaces an already resolved singleton.
        """

        self._providers[key] = lambda: self._call_factory(factory)

    def register_instance[T](self, key: type[T], instance: T) -> None:
        """Register ``instance`` as the singleton provider for ``key``."""

        self._providers[key] = lambda: instance

    def resolve[T](self, key: type[T]) -> T:
        """Resolve the singleton registered for ``key``."""

        if key in self._singletons:
            return self._singletons[key]  # ty: ignore[invalid-return-type]

        if key in self._resolving:
            start = self._resolving.index(key)
            raise DependencyCycleError(tuple(self._resolving[start:] + [key]))

        provider = self._providers.get(key)
        if provider is None:
            raise MissingProviderError(key, tuple(self._resolving + [key]))

        self._resolving.append(key)
        try:
            instance = provider()
            self._singletons[key] = instance
            return instance  # ty: ignore[invalid-return-type]
        finally:
            self._resolving.pop()

    def _call_factory[T](self, factory: Callable[..., T]) -> T:
        target = factory.__init__ if inspect.isclass(factory) else factory
        hints = get_type_hints(target, include_extras=True)
        arguments: dict[str, object] = {}

        for parameter in inspect.signature(factory).parameters.values():
            annotation = hints.get(parameter.name)
            if get_origin(annotation) is not Injected:
                continue

            dependency = get_args(annotation)
            if len(dependency) != 1 or not isinstance(dependency[0], type):
                raise TypeError(f"Injected dependency for {parameter.name} must be a class or Protocol key")

            if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
                raise TypeError(f"Injected dependency {parameter.name} cannot be positional-only")

            arguments[parameter.name] = self.resolve(dependency[0])

        return factory(**arguments)


def _key_name(key: type[object]) -> str:
    return getattr(key, "__qualname__", repr(key))


def _path_name(path: tuple[type[object], ...]) -> str:
    return " -> ".join(_key_name(key) for key in path)
