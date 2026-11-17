from importlib.metadata import PackageNotFoundError, version

from ._pygfnff import GFNFF, SOLVENTS, gfnff

try:
    __version__ = version("pygfnff")
except PackageNotFoundError:  # running from a source tree
    __version__ = "unknown"

__all__ = ["GFNFF", "SOLVENTS", "__version__", "gfnff"]
