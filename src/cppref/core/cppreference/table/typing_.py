from collections import deque

type RowSpec = deque[str]
type RowText = deque[str]
type TabInfo = tuple[list[RowSpec], list[RowText]]
