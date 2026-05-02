from dataclasses import dataclass


@dataclass
class InitialQNA:
    answer: str
    title: str
    category: str
    content: str