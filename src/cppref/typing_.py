import re
from typing import Literal, NamedTuple, Required, TypedDict, Union

type Source = Literal["cppreference", "cplusplus"]

type Format = Literal["html", "man"]

type ConfKey = Literal["source", "path"]

type ConfVal = Union[str, Source]


class Record(NamedTuple):
    id: int
    title: str
    url: str

    def __str__(self):
        return f"{self.id:6d} {self.title}"

    @property
    def normalized_name(self):
        return self.title.replace("/", "_")

    @staticmethod
    def parse_id(string: str) -> int:
        result = re.search(r"^\s*(\d+).*", string)
        assert result is not None, "Nothing matched"
        return int(result.group(1))


class Configuration(TypedDict):
    source: Required[Source]
    folder: Required[str]
