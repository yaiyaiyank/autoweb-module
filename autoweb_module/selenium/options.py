# 標準ライブラリ
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Literal

from selenium.webdriver.common import options as _options
from selenium.webdriver.common import service as _service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


@dataclass
class OptionsComposer(ABC):
    options: _options.ArgOptions = None
    service: _service.Service = None
    prefs: dict = field(default_factory=dict)

    def main(self, download_folder: Path | None, **kwargs: dict) -> WebDriver:
        self.set_common_setting()
        self.set_setting(download_folder, **kwargs)
        return self.get_driver()

    def set_common_setting(self):
        self.service.creation_flags = 0x08000000  # ヘッドレスモードで DevTools listening on ws:~~ を表示させない
        self.options.add_argument(
            "--disable-background-networking"
        )  # 拡張機能の更新、セーフブラウジングサービス、アップグレード検出、翻訳、UMAを含む様々なバックグラウンドネットワークサービスを無効にする。
        self.options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )  # navigator.webdriver=false となる設定。確認⇒　driver.execute_script("return navigator.webdriver")

        # self.options.add_argument(
        #     "--disable-features=DownloadBubble,DownloadBubbleV2"
        # )  # `--incognito`を使うとき、ダイアログ(名前を付けて保存)を非表示にする。
        # self.options.add_argument("--kiosk-printing")  # なんかPDF保存関係のオプションだった気がする

    @abstractmethod
    def set_setting(self):
        """そのブラウザ特有の設定"""

    @abstractmethod
    def get_driver(self) -> WebDriver:
        """そのブラウザのdriverを取得"""


@dataclass
class ChromeOptionsComposer(OptionsComposer):
    options: ChromeOptions = field(default_factory=ChromeOptions)
    service: ChromeService = field(default_factory=ChromeService)

    def set_setting(self, download_folder: Path | None, profile_path: Path | None, headless: bool):
        self.options.add_argument("--propagate-iph-for-testing")
        self.options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )  # Chromeは自動テスト ソフトウェア~~を非表示
        # pref系
        self.prefs["credentials_enable_service"] = False  # パスワード保存のポップアップを無効
        if not download_folder is None:
            self.prefs["savefile.default_directory"] = (
                download_folder.__str__()
            )  # ダイアログ(名前を付けて保存)の初期ディレクトリを指定
            self.prefs["download.default_directory"] = download_folder.__str__()  # ダウンロード先を指定
        self.prefs["download.prompt_for_download"] = False  # ダウンロードのpromptを出さないようにする
        self.prefs["download_bubble.partial_view_enabled"] = (
            False  # ダウンロードが完了したときの通知(吹き出し/下部表示)を無効にする。
        )
        if not profile_path is None:
            self.options.add_argument(f"--user-data-dir={profile_path}")
        self.prefs["plugins.always_open_pdf_externally"] = (
            True  # Chromeの内部PDFビューアを使わない(＝URLにアクセスすると直接ダウンロードされる)
        )
        self.options.add_experimental_option("prefs", self.prefs)

    def get_driver(self):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        return driver


@dataclass
class FirefoxOptionsComposer(OptionsComposer):
    options: FirefoxOptions = field(default_factory=FirefoxOptions)
    service: FirefoxService = field(default_factory=FirefoxService)

    def set_setting(self, download_folder: Path | None, profile_path: Path | None, headless: bool):
        pass  # 気が向いたらFirefox対応する

    def get_driver(self):
        driver = webdriver.Firefox(service=self.service, options=self.options)
        return driver
