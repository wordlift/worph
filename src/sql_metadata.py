from __future__ import annotations

import re

_TABLE_TOKEN_RE = re.compile(
    r"\b(?:FROM|JOIN)\b\s+((?:\"[^\"]+\")|(?:'[^']+')|(?:`[^`]+`)|(?:[A-Za-z_][\w.$]*))",
    flags=re.IGNORECASE,
)


class Parser:
    def __init__(self, sql: str):
        self.sql = sql or ""
        self.tables = self._extract_tables(self.sql)

    @staticmethod
    def _extract_tables(sql: str) -> list[str]:
        seen: list[str] = []
        for match in _TABLE_TOKEN_RE.finditer(sql):
            token = match.group(1).strip()
            if token[:1] in {"'", '"', "`"} and token[-1:] == token[:1]:
                token = token[1:-1]
            if token and token not in seen:
                seen.append(token)
        return seen
