# 標準ライブラリ
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Self, Literal
from abc import abstractmethod, ABC
import copy


@dataclass
class Cond(ABC):
    pass

    def __mul__(self, other: Cond) -> AllSelectorCond:
        if not isinstance(other, Cond):
            TypeError("演算子 '*' はCond同士のみ可能です。")
        print(id(self))
        self = self.copy()
        print(id(self))
        other = other.copy()
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
        print(id(self))
        self = self.copy()
        print(id(self))
        other = other.copy()
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

    @property
    def xpath(self) -> str:
        if isinstance(self, AllSelectorCond):
            all_selector = self
        else:
            all_selector = AllSelectorCond()
            and_selector = AndSelector()
            and_selector.append(self)
            all_selector.append(and_selector)

        xpath_maker = XpathMaker()
        xpath = xpath_maker.get_xpath(all_selector.and_selector_list)
        return xpath

    def copy(self) -> Cond:
        """
        自身のインスタンスをコピーする
        これを介せずにcond1 + cond2とかをすると、cond1やcond2が別の値になってしまう
        """
        cond = copy.deepcopy(self)
        return cond


@dataclass
class TagCond(Cond):
    name: str

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise TypeError("タグ名はstrで頼むぅ")


@dataclass
class LocatorCond(Cond):
    name: str
    value: str
    match: Literal["equals", "contains", "startswith", "endswith"] = "equals"

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise TypeError("ロケータ名はstrで頼むぅ")
        if not isinstance(self.value, str):
            raise TypeError("ロケータ値はstrで頼むぅ")
        if not isinstance(self.match, str):
            raise TypeError("ロケータの一致タイプはstrで頼むぅ")


@dataclass
class TextCond(Cond):
    value: str
    match: Literal["equals", "contains"] = "equals"

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("テキスト値はstrで頼むぅ")
        if not isinstance(self.match, str):
            raise TypeError("テキストの一致タイプはstrで頼むぅ")


@dataclass
class AndSelector:
    """AND同士の部分"""

    tag: TagCond | None = None
    locators: list[LocatorCond] = field(default_factory=list)
    texts: list[TextCond] = field(default_factory=list)

    def append(self, cond: TagCond | LocatorCond | TextCond):
        if isinstance(cond, TagCond):
            if cond is None:
                return
            if not self.tag is None and cond.name != self.tag.name:
                raise ValueError(f"タグ条件: {cond.name}と{self.tag.name}は共存できません。")
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
        self.and_selector_list.append(and_selector)

    def get_map_and_append(self, cond: TagCond | LocatorCond | TextCond) -> list[AndSelector]:
        base_and_selector_list = []
        for and_selector in self.and_selector_list:
            and_selector.append(cond)
            base_and_selector_list.append(and_selector)
        return base_and_selector_list

    def mul(self, cond: Cond):
        """積結合。全てorが最前に来る形で格納。"""
        if isinstance(cond, AllSelectorCond):
            # (A1 or A2 or .. or An) and (B1 or B2 or .. or Bn) ⇔ or(i:1→n)or(j:1→n)(Ai and Bj)
            base_and_selector_list = []
            # for Bi in (B1, B2, .., Bn):
            for other_and_selector in cond.and_selector_list:
                # タグ
                and_selector_list = self.get_map_and_append(other_and_selector.tag)
                base_and_selector_list += and_selector_list
                # ロケータ
                for locator in other_and_selector.locators:
                    and_selector_list = self.get_map_and_append(locator)
                    base_and_selector_list += and_selector_list
                # テキスト
                for text in other_and_selector.texts:
                    and_selector_list = self.get_map_and_append(text)
                    base_and_selector_list += and_selector_list
            self.and_selector_list = base_and_selector_list
            return
        # (A1 or A2 or .. or An) and B ⇔ (A1 and B) or (A2 and B) or .. or (An and B)
        self.and_selector_list = self.get_map_and_append(cond)

    def add(self, cond: Cond):
        """和結合。全てorが最前に来る形で格納。"""
        if isinstance(cond, AllSelectorCond):
            # (A1 or A2 or .. or An) or (B1 or B2 or .. or Bn) ⇔ A1 or A2 or .. or An or B1 or B2 or .. or Bn
            self.and_selector_list += cond.and_selector_list
            return
        # (A1 or A2 or .. or An) or B ⇔ A1 or A2 or .. or An or B
        and_selector = AndSelector()
        and_selector.append(cond)
        self.append(and_selector)


class XpathMaker:
    def get_xpath(self, and_selector_list: list[AndSelector]) -> str:
        and_xpath_list = []
        for and_selector in and_selector_list:
            and_xpath = self.get_and_xpath(and_selector)
            and_xpath_list.append(and_xpath)
        xpath = " | ".join(and_xpath_list)
        return xpath

    def get_and_xpath(self, and_selector: AndSelector) -> str:
        tag_xpath = self.get_tag_xpath(and_selector.tag)
        parts = []
        for locator in and_selector.locators:
            locator_xpath = self.get_locator_xpath(locator)
            parts.append(locator_xpath)
        for text in and_selector.texts:
            text_xpath = self.get_text_xpath(text)
            parts.append(text_xpath)

        if parts.__len__() == 0:
            return tag_xpath
        return f"{tag_xpath}[{' and '.join(parts)}]"

    def get_tag_xpath(self, tag: TagCond | None) -> str:
        if tag is None:
            tag_xpath = ".//*"
        else:
            tag_xpath = f".//{tag.name}"
        return tag_xpath

    def get_locator_xpath(self, locator: LocatorCond) -> str:
        attr_name = f"@{locator.name}"
        quote_value = self.quote_value(locator.value)

        if locator.match == "equals":
            return f"{attr_name} = {quote_value}"
        if locator.match == "contains":
            return f"contains({attr_name}, {quote_value})"
        if locator.match == "startswith":
            return f"starts-with({attr_name}, {quote_value})"
        if locator.match == "endswith":
            # XPath 1.0 に ends-with は無いので substring で頑張る
            n = len(quote_value)
            # substring(@attr, string-length(@attr) - (n-1)) = 'xxx'
            return f"substring({attr_name}, string-length({attr_name}) - {n - 1}) = {quote_value}"

    def get_text_xpath(self, text: TextCond) -> str:
        quote_value = self.quote_value(text.value)
        if text.match == "equals":
            return f"normalize-space() = {quote_value}"
        if text.match == "contains":
            return f"contains(normalize-space(), {quote_value})"

    def quote_value(self, value: str) -> str:
        """
        XPath の文字列リテラルを安全に生成する。
        - シングルクォートだけ含む場合: "..." で囲む
        - ダブルクォートだけ含む場合: '...' で囲む
        - 両方含む場合: concat('...', '"', '...') 形式を使う
        """
        # クォート系なし or "だけ
        if "'" not in value:
            return f"'{value}'"
        # 'だけ
        if '"' not in value:
            return f'"{value}"'

        # クォート系全部入り
        # シングルクォートで split して、間に "'" を挟んで concat を組み立てる
        parts = value.split("'")
        concat_parts: list[str] = []
        for i, part in enumerate(parts):
            if part:
                concat_parts.append(f"'{part}'")
            if i != parts.__len__() - 1:
                # シングルクォート文字そのもの
                concat_parts.append('"\'"')
        return f"concat({', '.join(concat_parts)})"
