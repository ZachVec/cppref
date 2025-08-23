from typing import Literal, NamedTuple, Union

type Source = Literal["cppreference", "cplusplus"]

type Format = Literal["html", "man"]

type ConfKey = Literal["db_path", "source"]

type ConfVal = Union[str, Source]


class Record(NamedTuple):
    id: str
    title: str
    url: str

    def __str__(self):
        return f"{self.id:6d} {self.title}"

    @property
    def normalized_name(self):
        return self.title.replace("/", "_")
