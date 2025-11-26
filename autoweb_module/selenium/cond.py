# 標準ライブラリ
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Self, Literal
from abc import abstractmethod


# class Cond:
#     @abstractmethod
#     def get_xpath_attr(self) -> str:
#         pass

#     def __mul__(self, other: Self) -> Self:
#         return AND(self, other)

#     def __add__(self, other: Self) -> Self:
#         return OR(self, other)

# class CondBool:
#     pass

# @dataclass
# class AND(CondBool):
#     cond1: Cond
#     cond2: Cond

# @dataclass
# class OR(CondBool):
#     cond1: Cond
#     cond2: Cond


@dataclass
class Cond:
    pass

    def __mul__(self, other: Cond) -> AllSelectorCond:
        if not isinstance(other, Cond):
            TypeError("演算子 '*' はCond同士のみ可能です。")
        # AllSelector * Cond(AllSelector含む)
        if isinstance(self, AllSelectorCond):
            self.mul(other)
            return self
        # Cond(AllSelectorでない) * AllSelector
        if isinstance(other, AllSelectorCond):
            other.mul(self)
            return other
        # Cond(AllSelectorでない) * Cond(AllSelectorでない) 最初はこれ
        and_selector = AndSelector()
        and_selector.append(self)
        and_selector.append(other)
        all_selector = AllSelectorCond()
        all_selector.append(and_selector)
        return all_selector

    def __add__(self, other: Cond) -> AllSelectorCond:
        if not isinstance(other, Cond):
            TypeError("演算子 '+' はCond同士のみ可能です。")
        # AllSelector + Cond(AllSelector含む)
        if isinstance(self, AllSelectorCond):
            self.add(other)
            return self
        # Cond(AllSelectorでない) + AllSelector
        if isinstance(other, AllSelectorCond):
            other.add(self)
            return other
        # Cond(AllSelectorでない) + Cond(AllSelectorでない) 最初はこれ
        all_selector = AllSelectorCond()
        and_selector1 = AndSelector()
        and_selector1.append(self)
        all_selector.append(and_selector1)
        and_selector2 = AndSelector()
        and_selector2.append(other)
        all_selector.append(and_selector2)
        return all_selector


@dataclass
class TagCond(Cond):
    name: str


@dataclass
class LocatorCond(Cond):
    name: str
    value: str
    match: Literal["equals", "contains", "startswith", "endswith"] = "equals"


@dataclass
class TextCond(Cond):
    value: str
    match: Literal["equals", "contains"] = "equals"


@dataclass
class AndSelector:
    """AND同士の部分"""

    tag: TagCond | None = None
    locators: list[LocatorCond] = field(default_factory=list)
    texts: list[TextCond] = field(default_factory=list)

    def append(self, cond: Cond):
        if isinstance(cond, TagCond):
            if not cond is None and cond.name != self.tag.name:
                raise ValueError(f"タグ条件: {cond.name}と{self.tag.name}")
            self.tag = cond
        if isinstance(cond, LocatorCond):
            self.locators.append(cond)
        if isinstance(cond, TextCond):
            self.texts.append(cond)


@dataclass
class AllSelectorCond(Cond):
    """Cond結合時の姿"""

    and_selector_list: list[AndSelector] = field(default_factory=list)

    def append(self, and_selector: AndSelector):
        pass

    def mul(self, cond: Cond):
        if isinstance(cond, AllSelectorCond):
            # (A1 or A2 or .. or An) and (B1 or B2 or .. or Bn) ⇔ 全A, Bの組み合わせのor(書きたくない)
            # 2x2の場合で(A or B) and (C or D) ⇔ (A and (C or D)) or (B and (C or D)) ⇔ (A and C) or (A and D) or (B and C) or (B and D)
            return
        # (A1 or A2 or .. or An) and B ⇔ (A1 and B) or (A2 and B) or .. or (An and B)

    def add(self, cond: Cond):
        if isinstance(cond, AllSelectorCond):
            # (A1 or A2 or .. or An) or (B1 or B2 or .. or Bn) ⇔ A1 or A2 or .. or An or B1 or B2 or .. or Bn
            self.and_selector_list += cond.and_selector_list
            return
        # (A1 or A2 or .. or An) or B ⇔ A1 or A2 or .. or An or B
        and_selector = AndSelector()
        and_selector.append(cond)
        self.and_selector_list.append(and_selector)
