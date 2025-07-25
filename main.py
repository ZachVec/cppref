from pathlib import Path

import requests

from cppref import DocumentProcessor

if __name__ == "__main__":
    ROOT = Path(".").absolute()
    if ROOT.joinpath("vector.html").exists():
        with open("vector.html", "r") as file:
            text = file.read()
    else:
        url = "https://en.cppreference.com/w/cpp/container/vector.html"
        text = requests.get(url).text
        with open("vector.html", "w", encoding="utf-8") as file:
            file.write(text)
    try:
        document = DocumentProcessor(text).process()
    except Exception:
        ...  # save html
    else:
        with open("output.man", "w") as file:
            file.write(document)
