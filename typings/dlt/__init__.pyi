"""Type stubs for dlt library."""

from types import ModuleType
from typing import Any, Optional, Union

from typing_extensions import Literal

# Basic types
DltResource = Any
DltSource = Any
LoadInfo = Any

WriteDisposition = Union[
    Literal["skip", "append", "replace", "merge"],
    dict[str, Any],
]

class resource:
    """DLT resource decorator."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

class source:
    """DLT source decorator."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

# Pipeline class
class Pipeline:
    """DLT Pipeline class."""

    def run(self, source: DltSource, **kwargs: Any) -> LoadInfo: ...
    loads_ids: list[Any] = ...

def pipeline(
    pipeline_name: str,
    destination: Any = ...,
    dataset_name: Optional[str] = ...,
    **kwargs: Any,
) -> Pipeline: ...
def run(
    source: DltSource,
    destination: Any = ...,
    **kwargs: Any,
) -> LoadInfo: ...

# destinations is a submodule
class _DestinationsModule(ModuleType):
    def postgres(self, **kwargs: Any) -> Any: ...
    def redshift(self, **kwargs: Any) -> Any: ...

destinations: _DestinationsModule

# Configuration
class config:
    """DLT configuration object."""

    ...

# Module-level instances
resource: resource
source: source
config: config
