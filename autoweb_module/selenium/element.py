# 標準ライブラリ
from pathlib import Path
from dataclasses import dataclass, field
from typing import Self, Literal

# 外部ライブラリ
# element系
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


# 例外系
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# 待機系
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# その他
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.alert import Alert
from bs4 import BeautifulSoup

# 自作ライブラリ
import time_module
from autoweb_module.selenium.const import LOCATOR_DICT, INPUTABLE_TAG_NAME_LIST, FRAME_TAG_NAME_LIST
from autoweb_module.exceptions import DifferenceTagError, NotWebElementError


@dataclass
class Element(time_module.MutableWaitTimeAttrClass):
    elem: WebDriver | WebElement
    _wait_time: int | float | time_module.MutableWaitTime
    debug_mode: bool

    def __post_init__(self):
        # WebDriverを取得
        if not isinstance(self.elem, WebDriver | WebElement):
            raise TypeError(f"elem is WebDriver | WebElement. not {type(self.elem)}")
        if isinstance(self.elem, WebDriver):
            self.driver = self.elem
        if isinstance(self.elem, WebElement):
            self.driver = self.elem.parent
        self.wait_time = self._wait_time

    def _get_new_element(
        self,
        elem: WebDriver | WebElement | None = None,
        wait_time: time_module.MutableWaitTime | None = None,
        debug_mode: bool | None = None,
    ) -> Self:
        """ここで新規Elementを生成。wait_timeなどのイミュータブルはある"""
        if elem is None:
            elem = self.elem
        if wait_time is None:
            _wait_time = self._wait_time
        if debug_mode is None:
            debug_mode = self.debug_mode

        element = self.__class__(elem=elem, _wait_time=_wait_time, debug_mode=debug_mode)
        return element

    # ---------------find_elem系---------------
    def find_elem(
        self,
        locator: Literal["id", "name", "tag", "xpath", "css", "link", "plink", "class"],
        attr: str,
        wait_time: int | float | None = None,
    ):
        """seleniumのfind_elemnetメソッドのラッパー"""
        by = LOCATOR_DICT[locator]

        elem = self._base_find_elem(locator, attr, wait_time)
        if elem is None:
            self.elem.find_element(by, attr)  # raise: NoSuchElementException

    def find_elems(
        self,
        locator: Literal["id", "name", "tag", "xpath", "css", "link", "plink", "class"],
        attr: str,
        wait_time: int | float | None = None,
    ):
        """seleniumのfind_elemnetsメソッドのラッパー"""
        pass  # TODO

    def _base_find_elem(self, locator: str, attr: str, wait_time: int | float | None) -> WebElement | None:
        by = LOCATOR_DICT[locator]
        wait_time = self._get_temp_wait_time(wait_time)
        if wait_time == 0:
            elem = None
        else:
            wait = WebDriverWait(self.driver, wait_time)
            elem = wait.until(EC.visibility_of_element_located((by, attr)))  # raise: TimeoutException
        return elem

    def to_driver_elem(self) -> Self:
        return self._get_new_element(elem=self.driver)

    @property
    def parent(self) -> Self:
        pass

    @property
    def children(self) -> list[Self]:
        pass

    # ---------------status系---------------
    @property
    def is_web_driver(self) -> bool:
        return isinstance(self.driver, WebDriver)

    @property
    def is_web_element(self) -> bool:
        return isinstance(self.driver, WebElement)

    @property
    def is_inputable(self) -> bool:
        if self.is_web_driver:
            return False
        return self.tag_name in INPUTABLE_TAG_NAME_LIST

    @property
    def is_iframe(self) -> bool:
        if self.is_web_driver:
            return False
        return self.tag_name in FRAME_TAG_NAME_LIST

    def __repr__(self) -> str:
        # VSCodeの表示で数秒以上かかるとエラーになるし、ブラウザ側に影響があるかもしれないので詳細表示しない
        return self._status(detail=False)

    @property
    def status(self) -> str:
        """elemのステータス"""
        return self._status(detail=True)

    def _status(self, detail: bool) -> str:
        # detailがTrueかつdebug_modeがTrueのときにやる
        status = ""
        status += f"type: {self.elem.__class__.__name__}"
        # driverならここまで
        if self.is_web_driver:
            return status
        self.elem

    @property
    def text(self):
        return self.elem.text

    @property
    def tag_name(self):
        return self.elem.tag_name

    @property
    def current_url(self):
        return self.driver.current_url

    def attr(self, name) -> str | None:
        if self.is_web_driver:
            return None
        return self.elem.get_attribute(name)

    @property
    def value(self):
        if not self.is_inputable:
            raise DifferenceTagError(
                f"valueが取得できるWebElementのタグは{' or '.join(INPUTABLE_TAG_NAME_LIST)}です。{self.elem.tag_name}は非対応です。"
            )
        return self.attr("value")

    @property
    def exists(self):
        # driverはまあ存在しているでしょうってことで
        if self.is_web_driver:
            return True
        try:
            # 適当なプロパティを1つ読む（tag_name / is_enabled / text など）
            _ = self.elem.tag_name
            return True
        except StaleElementReferenceException:
            # DOMから削除されていて「古い参照」になっている
            return False

    def wait_not_exists(self, wait_time: int | float | None = None):
        if self.is_web_driver:
            raise NotWebElementError("WebDriverは待つとかの次元じゃないです。")
        wait_time = self._get_temp_wait_time(wait_time)
        # なんでseleniumは存在判定機能がないのに存在しなくなるまで待つ機能はあるねん
        WebDriverWait(self.driver, wait_time).until(EC.staleness_of(self.elem))

    # ---------------操作系---------------

    def click(self, mode: Literal["javascript", "normal"] = "javascript"):
        """クリックする。"""
        match mode:
            case "javascript":
                # 基本これでいい。画面外でもクリックしてくれる。
                self.driver.execute_script("arguments[0].click();", self.elem)
            case "normal":
                # selectタグの要素だとjavascriptのクリックで反応しないのでこっちだが、selectならselectメソッドを推奨します。
                # selectタグ以外の要素で必要な時が来るかもしれない
                self.elem.click()

    def clear(self):
        if not self.is_inputable:
            raise DifferenceTagError(
                f"clearできるWebElementのタグは{' or '.join(INPUTABLE_TAG_NAME_LIST)}です。{self.elem.tag_name}は非対応です。"
            )
        # elem.clear()が聞かない時があるのでこっち
        for _ in time_module.WaitTry(self.wait_time):
            self.elem.send_keys(Keys.CONTROL + "a")
            self.elem.send_keys(Keys.BACK_SPACE)
            if self.value == "":
                break
        else:
            raise TimeoutException

    def send_keys(self, clear: bool = False):
        if not self.is_inputable:
            raise DifferenceTagError(
                f"send_keysできるWebElementのタグは{' or '.join(INPUTABLE_TAG_NAME_LIST)}です。{self.elem.tag_name}は非対応です。"
            )
        if clear:
            self.clear()

    def back(self):
        """ブラウザバック"""
        self.driver.back()

    def scroll(self):
        # その要素が見える位置までスクロール
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", self.elem)

    def alert_accept(self):
        """アラートを承認"""
        # アラートにスイッチ
        alert = Alert(self.driver)
        # アラートを承認
        alert.accept()

    def switch_frame(self):
        if not self.is_iframe:
            raise DifferenceTagError(
                f"frame切り替えはできるWebElementのタグは{' or '.join(FRAME_TAG_NAME_LIST)}です。{self.elem.tag_name}は非対応です。"
            )
        self.driver.switch_to.frame(self.elem)

    def return_frame(self):
        self.driver.switch_to.default_content()

    def close(self):
        """タブを閉じる。ただし現在は閉じたあとのdriverのwindowの移動をサポートしていない"""
        self.driver.close()

    def perform(self):
        """マウスをその要素の上に移動（ホバー）"""
        if self.is_web_driver:
            raise NotWebElementError
        actions = ActionChains(self.driver)
        actions.move_to_element(self.elem).perform()

    # ---------------その他---------------
    def save_ss(self, file_path: Path | str):
        """マウスをその要素の上に移動（ホバー）"""
        self.driver.save_screenshot(file_path)

    def save_html(self, file_path: Path | str):
        """マウスをその要素の上に移動（ホバー）"""
        file_path = Path(file_path)
        if file_path.suffix != ".html":
            raise ValueError("HTMLを保存できるファイルの拡張子は「.html」だぇ")
        # WebDriverの場合はページ全体のHTML
        if self.is_web_driver:
            html = self.driver.page_source
        # WebElementの場合はそのElement以下のHTML
        else:
            html = self.elem.get_attribute("outerHTML")

        soup = BeautifulSoup(html, "html.parser")
        pretty = soup.prettify()
        file_path.write_text(pretty, encoding="utf-8")


@dataclass(frozen=True)
class TagCond:
    name: str  # "span", "input" など


@dataclass(frozen=True)
class AttrCond:
    name: str  # "class", "placeholder" など
    value: str | None = None
    op: str = "equals"  # "equals", "contains", "startswith", "endswith"


@dataclass(frozen=True)
class TextCond:
    text: str
    mode: str = "equals"  # "equals", "contains"


# --- 複合セレクタ ---


@dataclass(frozen=True)
class Selector:
    tag: TagCond | None = None
    attrs: list[AttrCond] = field(default_factory=list)
    text: TextCond | None = None

    # 内部用: イミュータブルなまま新しい Selector を返す
    def _merged(self, **kwargs) -> "Selector":
        data = {
            "tag": self.tag,
            "attrs": list(self.attrs),
            "text": self.text,
        }
        data.update(kwargs)
        return Selector(**data)

    # A * B で AND 結合
    def __mul__(self, other: Self | TagCond | AttrCond | TextCond) -> "Selector":
        if isinstance(other, Selector):
            # セレクタ同士をマージ
            tag = other.tag or self.tag
            attrs = self.attrs + [a for a in other.attrs if a not in self.attrs]
            text = other.text or self.text
            return Selector(tag=tag, attrs=attrs, text=text)

        if isinstance(other, TagCond):
            return self._merged(tag=other)

        if isinstance(other, AttrCond):
            return self._merged(attrs=self.attrs + [other])

        if isinstance(other, TextCond):
            return self._merged(text=other)

        return NotImplemented

    # & でも同じ動作にしておく
    __and__ = __mul__

    # --- 出力: XPath ---

    def to_xpath(self, relative: bool = True) -> str:
        tag_name = self.tag.name if self.tag else "*"
        conditions = []

        for attr in self.attrs:
            if attr.op == "equals":
                conditions.append(f"@{attr.name}='{attr.value}'")
            elif attr.op == "contains":
                conditions.append(f"contains(@{attr.name}, '{attr.value}')")
            elif attr.op == "startswith":
                conditions.append(f"starts-with(@{attr.name}, '{attr.value}')")
            elif attr.op == "endswith":
                # XPath 1.0 には ends-with がないのでエミュレート
                conditions.append(
                    f"substring(@{attr.name}, string-length(@{attr.name}) - string-length('{attr.value}') + 1) = '{attr.value}'"
                )

        if self.text:
            if self.text.mode == "equals":
                conditions.append(f"normalize-space(text())='{self.text.text}'")
            elif self.text.mode == "contains":
                conditions.append(f"contains(normalize-space(.), '{self.text.text}')")

        predicate = ""
        if conditions:
            predicate = "[" + " and ".join(conditions) + "]"

        prefix = ".//" if relative else "//"
        return f"{prefix}{tag_name}{predicate}"

    # --- 出力: CSS セレクタ ---

    def to_css(self) -> str:
        # テキスト条件は CSS では表現しにくいのでエラーに
        if self.text:
            raise ValueError("CSS セレクタでは text 条件はサポートしていません（XPath を使ってください）")

        tag_name = self.tag.name if self.tag else ""
        parts = [tag_name]

        attr_selectors = []
        for attr in self.attrs:
            if attr.name == "class" and attr.op == "equals" and attr.value:
                # "p-input p-component" -> ".p-input.p-component"
                classes = attr.value.split()
                for cls in classes:
                    parts.append(f".{cls}")
            elif attr.op == "equals":
                attr_selectors.append(f"[{attr.name}='{attr.value}']")
            elif attr.op == "contains":
                attr_selectors.append(f"[{attr.name}*='{attr.value}']")
            elif attr.op == "startswith":
                attr_selectors.append(f"[{attr.name}^='{attr.value}']")
            elif attr.op == "endswith":
                attr_selectors.append(f"[{attr.name}$='{attr.value}']")

        return "".join(parts + attr_selectors)
