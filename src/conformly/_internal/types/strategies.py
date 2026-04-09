from typing import Literal

CaseStrategy = Literal["first", "random"] | str
CasesStrategy = Literal["first", "random", "all", "all_violations"] | str
