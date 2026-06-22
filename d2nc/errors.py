"""Typed errors for the d2nc spike (all caught at the CLI boundary)."""


class D2ncError(Exception):
    """Base class for expected, user-facing d2nc failures."""


class DispatchError(D2ncError):
    """No viable backend, or an impossible explicit backend choice."""


class InputError(D2ncError):
    """The supplied path is not a usable Bruker .d directory."""


class LocalJobError(D2ncError):
    """The in-process local conversion failed."""


class CloudJobError(D2ncError):
    """The cloud (ECS) conversion failed."""
