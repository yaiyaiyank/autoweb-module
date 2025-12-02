# 標準ライブラリ
from pathlib import Path
from typing import Literal

# 自作モジュール
import download_module
import time_module
from autoweb_module import Element
from autoweb_module.selenium.options import ChromeOptionsComposer, FirefoxOptionsComposer

# 外部ライブラリ
from selenium.webdriver.remote.webdriver import WebDriver


class Selenium:
    def __init__(self, element_class: type = Element):
        # 扱うElementクラスを決定
        if not hasattr(self, "element_class"):
            self.element_class = element_class

        # browser_name

    def launch_browser(
        self,
        start_url: str,
        browser_name: Literal["chrome", "firefox", "tor"] = "chrome",
        default_save_folder: Path | str | None = None,
        debug_mode: bool = False,
        profile_path: Path | str | None = None,
        headless: str | None = None,
        wait_time: int | float | time_module.MutableWaitTime | None = None,
        is_raise_for_no_vpn: bool = False,
    ):
        match browser_name:
            case "chrome":
                options_composer = ChromeOptionsComposer()
            case "firefox":
                raise NotImplementedError("まだfirefoxブラウザ非対応です。")
                options_composer = FirefoxOptionsComposer()
            case "tor":
                raise NotImplementedError("まだtorブラウザ非対応です。")
        if default_save_folder is None:
            default_save_folder = Path(default_save_folder)
        # seleniumライブラリのdriverを起動。これをラップする
        self._driver: WebDriver = options_composer.main(
            default_save_folder, profile_path=profile_path, headless=headless
        )
        self._start(start_url)
        # 待機時間はデフォルト10秒
        if wait_time is None:
            wait_time = 10
        self.driver: Element = self.element_class(
            elem=self._driver, save_folder=default_save_folder, debug_mode=debug_mode, _wait_time=wait_time
        )

    def _start(self, start_url: str):
        self._driver.get(start_url)

    def quit(self):
        try:
            self._driver.quit()
        except Exception:
            pass
