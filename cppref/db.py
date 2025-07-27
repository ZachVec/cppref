import sqlite3
from pathlib import Path
from typing import Literal, Optional

Source = Literal["cppreference", "cplusplus"]


class DBManager:
    """
    tables
    cplusplus.com              cppreference.com
    cplusplus.com_keywords     cppreference.com_keywords

    # CREATE TABLE IF NOT EXISTS "cplusplus.com" (id INTEGER NOT NULL PRIMARY KEY, title VARCHAR(255) NOT NULL UNIQUE, url VARCHAR(255) NOT NULL UNIQUE);
    # CREATE TABLE IF NOT EXISTS "cplusplus.com_keywords" (id INTEGER NOT NULL, keyword VARCHAR(255), FOREIGN KEY(id) REFERENCES "cplusplus.com"(id));

    CREATE TABLE IF NOT EXISTS "cppreference.com" (id INTEGER NOT NULL PRIMARY KEY, title VARCHAR(255) NOT NULL UNIQUE, url VARCHAR(255) NOT NULL UNIQUE);
    CREATE TABLE IF NOT EXISTS "cppreference.com_keywords" (id INTEGER NOT NULL, keyword VARCHAR(255), FOREIGN KEY(id) REFERENCES "cppreference.com"(id));

    cppreference:
        id 主键
        title  标题
        url  url

    cppreference_keywords:
        id  外键
        keyword 一些同名词


    'SELECT t1.title, t2.keyword, t1.url '
    'FROM "%s" AS t1 '
    'JOIN "%s_keywords" AS t2 '
    'ON t1.id = t2.id'
    'WHERE t2.keyword LIKE ? ORDER BY t2.keyword'
    """

    def __init__(self, path: Path) -> None:
        self._filepath = str(path)

    def get_keywords(
        self, source: Source, limit: Optional[int] = None
    ) -> list[tuple[int, str]]:
        query = ["SELECT id, keyword", f'FROM "{source}.com_keywords"']
        if limit is not None:
            query.append(f"LIMIT {limit}")
        with sqlite3.connect(self._filepath) as conn:
            cursor = conn.cursor()
            return cursor.execute(" ".join(query)).fetchall()

    def get_url(
        self,
        source: Source,
        pkey: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[tuple[int, str, str]]:
        """Get url information from source.

        Args:
            source: cppreference or cplusplus
            pkey: primary key
            limit: number of requested result

        Returns:
            list of (id, title, url) pairs
        """
        query = ["SELECT id, title, url", f'FROM "{source}.com"']
        if pkey is not None:
            query.append(f"WHERE id={pkey}")
        if limit is not None:
            query.append(f"LIMIT {limit}")
        with sqlite3.connect(self._filepath) as conn:
            cursor = conn.cursor()
            return cursor.execute(" ".join(query)).fetchall()

    def set_url(self, source: Source, *urls: tuple[int, str]):
        with sqlite3.connect(self._filepath) as conn:
            cursor = conn.cursor()
            for pkey, url in urls:
                query: list[str] = [
                    f'UPDATE "{source}.com"',
                    f'SET url="{url}"WHERE id={pkey}',
                ]
                cursor.execute(" ".join(query))
            conn.commit()


if __name__ == "__main__":
    db = DBManager(Path("resources/index.db").absolute())
    _id, title, url = db.get_url("cppreference", 35)[0]
    print(f'("{_id}", "{title}",  "{url}")')
