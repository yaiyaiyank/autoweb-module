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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# その他
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.alert import Alert
from bs4 import BeautifulSoup

# 自作ライブラリ
import time_module
from autoweb_module.selenium.const import (
    LOCATOR_DICT,
    INPUTABLE_TAG_NAME_LIST,
    FRAME_TAG_NAME_LIST,
    SELECT_TAG_NAME_LIST,
)
from autoweb_module.exceptions import DifferenceTagError, NotWebElementError
from autoweb_module.selenium.cond import Cond, TagCond, LocatorCond, TextCond, AllSelectorCond


@dataclass
class Element(time_module.MutableWaitTimeAttrClass):
    elem: WebDriver | WebElement
    _wait_time: int | float | time_module.MutableWaitTime
    debug_mode: bool = False

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
    ) -> Self:
        """seleniumのfind_elemnetメソッドのラッパー"""
        by = LOCATOR_DICT[locator]

        elem = self._find_and_wait_elem(locator, attr, wait_time)
        # wait_timeが0の場合
        if elem is None:
            elem = self.elem.find_element(by, attr)  # raise: NoSuchElementException, StaleElementReferenceException
        return self._get_new_element(elem=elem)

    def find_elems(
        self,
        locator: Literal["id", "name", "tag", "xpath", "css", "link", "plink", "class"],
        attr: str,
        wait_time: int | float | None = None,
    ) -> list[Self]:
        """seleniumのfind_elemnetsメソッドのラッパー"""
        by = LOCATOR_DICT[locator]
        try:
            self._find_and_wait_elem(locator, attr, wait_time)
            # wait_timeが0の場合または待機して要素が1つ以上見つかった場合
            elem_list = self.elem.find_elements(by, attr)
        except TimeoutException:
            # 待機して要素が見つからなかった場合
            elem_list = []

        return [self._get_new_element(elem=elem) for elem in elem_list]

    def find_cond_elem(self, cond: Cond, wait_time: int | float | None = None) -> Self:
        return self.find_elem("xpath", cond.xpath, wait_time=wait_time)

    def find_cond_elems(self, cond: Cond, wait_time: int | float | None = None) -> list[Self]:
        return self.find_elems("xpath", cond.xpath, wait_time=wait_time)

    def find_locator_elem(
        self,
        name: str,
        value: str,
        match: Literal["equals", "contains", "startswith", "endswith"] = "equals",
        wait_time: int | float | None = None,
    ) -> Self:
        locator = LocatorCond(name, value, match)
        return self.find_cond_elem(locator, wait_time=wait_time)

    def find_locator_elems(
        self,
        name: str,
        value: str,
        match: Literal["equals", "contains", "startswith", "endswith"] = "equals",
        wait_time: int | float | None = None,
    ) -> list[Self]:
        locator = LocatorCond(name, value, match)
        return self.find_cond_elems(locator, wait_time=wait_time)

    def find_text_elem(
        self,
        value: str,
        match: Literal["equals", "contains", "startswith", "endswith"] = "equals",
        wait_time: int | float | None = None,
    ) -> Self:
        text = TextCond(value, match)
        return self.find_cond_elem(text, wait_time=wait_time)

    def find_text_elems(
        self,
        value: str,
        match: Literal["equals", "contains", "startswith", "endswith"] = "equals",
        wait_time: int | float | None = None,
    ) -> list[Self]:
        text = TextCond(value, match)
        return self.find_cond_elems(text, wait_time=wait_time)

    def _find_and_wait_elem(self, by: str, attr: str, wait_time: int | float | None) -> WebElement | None:
        wait_time = self._get_temp_wait_time(wait_time)
        if wait_time == 0:
            elem = None
        else:
            wait = WebDriverWait(self.elem, wait_time)
            elem = wait.until(
                EC.presence_of_element_located((by, attr))
            )  # raise: TimeoutException, StaleElementReferenceException
        return elem

    def to_driver_elem(self) -> Self:
        return self._get_new_element(elem=self.driver)

    @property
    def parent(self) -> Self:
        """1つ親"""
        return self.find_elem("xpath", "..", wait_time=0)

    @property
    def children(self) -> list[Self]:
        """1つ子すべて"""
        return self.find_elems("xpath", "./*", wait_time=0)

    # ---------------status系---------------
    @property
    def is_web_driver(self) -> bool:
        return isinstance(self.driver, WebDriver)

    @property
    def is_web_element(self) -> bool:
        return isinstance(self.driver, WebElement)

    @property
    def is_input(self) -> bool:
        if self.is_web_driver:
            return False
        return self.tag_name in INPUTABLE_TAG_NAME_LIST

    @property
    def is_iframe(self) -> bool:
        if self.is_web_driver:
            return False
        return self.tag_name in FRAME_TAG_NAME_LIST

    @property
    def is_select(self) -> bool:
        if self.is_web_driver:
            return False
        return self.tag_name in SELECT_TAG_NAME_LIST

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
        if not self.is_input:
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
        if not self.is_input:
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
        if not self.is_input:
            raise DifferenceTagError(
                f"send_keysできるWebElementのタグは{' or '.join(INPUTABLE_TAG_NAME_LIST)}です。{self.elem.tag_name}は非対応です。"
            )
        if clear:
            self.clear()

    def select(self, value_or_text_or_index: str | int, value_type: Literal["value", "text", "index"] = "value"):
        if not self.is_select:
            raise DifferenceTagError("selectはselectタグ時のみです。")
        select = Select(self.elem)
        if value_type == "value":
            select.select_by_value(value_or_text_or_index.__str__())
        if value_type == "text":
            select.select_by_visible_text(value_or_text_or_index.__str__())
        if value_type == "index":
            select.select_by_index(int(value_or_text_or_index))

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
        """スクショを保存"""
        file_path = Path(file_path)
        if file_path.suffix != ".png":
            raise ValueError("スクショを保存できるファイルの拡張子は「.png」だけです。")
        self.driver.save_screenshot(file_path)

    def save_html(self, file_path: Path | str):
        """そのelemのHTMLを保存"""
        file_path = Path(file_path)
        if file_path.suffix != ".html":
            raise ValueError("HTMLを保存できるファイルの拡張子は「.html」だけです。")

        pretty = self.soup.prettify()
        file_path.write_text(pretty, encoding="utf-8")

    @property
    def soup(self) -> BeautifulSoup:
        """そのelemのHTMLのBeautifulSoupオブジェクト"""
        html = self._get_html()

        soup = BeautifulSoup(html, "html.parser")
        return soup

    def _get_html(self) -> str:
        """elemに応じてhtmlを取得"""
        # WebDriverの場合はページ全体のHTML
        if self.is_web_driver:
            html = self.driver.page_source
        # WebElementの場合はそのElement以下のHTML
        else:
            html = self.attr("outerHTML")

        return html
