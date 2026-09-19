from typing import Protocol

import pytest

from tomate.pomodoro.graph import (
    DependencyCycleError,
    Graph,
    Injected,
    MissingProviderError,
)


class Repository(Protocol):
    def load(self) -> str: ...


class InMemoryRepository:
    def load(self) -> str:
        return "loaded"


class Service:
    def __init__(self, repository: Injected[Repository]):
        self.repository = repository


class DirectCycle:
    def __init__(self, dependency: Injected["DirectCycle"]):
        self.dependency = dependency


class IndirectFirst:
    def __init__(self, dependency: Injected["IndirectSecond"]):
        self.dependency = dependency


class IndirectSecond:
    def __init__(self, dependency: Injected[IndirectFirst]):
        self.dependency = dependency


def test_resolves_a_factory_and_its_protocol_dependency_once():
    graph = Graph()
    graph.register_factory(Repository, InMemoryRepository)
    graph.register_factory(Service, Service)

    service = graph.resolve(Service)

    assert isinstance(service.repository, InMemoryRepository)
    assert graph.resolve(Service) is service
    assert graph.resolve(Repository) is service.repository


def test_only_injected_parameters_are_resolved():
    class RequiresOrdinaryArgument:
        def __init__(self, value: str):
            self.value = value

    graph = Graph()
    graph.register_instance(str, "not injected")
    graph.register_factory(RequiresOrdinaryArgument, RequiresOrdinaryArgument)

    with pytest.raises(TypeError, match="value"):
        graph.resolve(RequiresOrdinaryArgument)


def test_replacing_provider_keeps_resolved_singletons_and_dependants():
    class Dependency:
        pass

    class FirstDependency(Dependency):
        pass

    class ReplacementDependency(Dependency):
        pass

    class Dependant:
        def __init__(self, dependency: Injected[Dependency]):
            self.dependency = dependency

    graph = Graph()
    graph.register_factory(Dependency, FirstDependency)
    graph.register_factory(Dependant, Dependant)
    dependant = graph.resolve(Dependant)

    graph.register_factory(Dependency, ReplacementDependency)

    assert graph.resolve(Dependency) is dependant.dependency
    assert graph.resolve(Dependant) is dependant


def test_missing_provider_includes_the_key_and_full_resolution_path():
    class Missing:
        pass

    class NeedsMissing:
        def __init__(self, missing: Injected[Missing]):
            self.missing = missing

    graph = Graph()
    graph.register_factory(NeedsMissing, NeedsMissing)

    with pytest.raises(MissingProviderError) as error:
        graph.resolve(NeedsMissing)

    assert error.value.key is Missing
    assert error.value.path == (NeedsMissing, Missing)


def test_direct_dependency_cycle_includes_the_complete_cycle():
    graph = Graph()
    graph.register_factory(DirectCycle, DirectCycle)

    with pytest.raises(DependencyCycleError) as error:
        graph.resolve(DirectCycle)

    assert error.value.path == (DirectCycle, DirectCycle)


def test_indirect_dependency_cycle_includes_the_complete_cycle():
    graph = Graph()
    graph.register_factory(IndirectFirst, IndirectFirst)
    graph.register_factory(IndirectSecond, IndirectSecond)

    with pytest.raises(DependencyCycleError) as error:
        graph.resolve(IndirectFirst)

    assert error.value.path == (IndirectFirst, IndirectSecond, IndirectFirst)
