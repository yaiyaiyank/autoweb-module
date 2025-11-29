# Web操作自動化モジュール

自分のエコシステム用につくったブラウザなどの自動化モジュール<br>
役立ちそう ∧ 機密情報なし なのでパブリックで公開<br>
自分の環境でplaywrightは動かせませんでしたが...

# install
### 動作環境
* Python 3.13↑
### インストール方法 
uvなら
```bash
uv add git+https://github.com/yaiyaiyank/autoweb-module
```
pipなら
```bash
pip install git+https://github.com/yaiyaiyank/autoweb-module
```

# usage
ブラウザ起動～準備
```python
# TIPS テスト時はipynbでやると実験しやすい。
from autoweb_module import Selenium, TagCond, LocatorCond, TextCond
# ブラウザ起動
url = "https://example.com"
selenium = Selenium()
selenium.launch_browser(url)
# driverをメインで扱う
driver = selenium.driver
```

例: ユーザーID入力
```python
# id属性が"userid"のElement
userid_elem = driver.find_elem("id", "userid") # seleniumライブラリのfind_elementをそのままラッピングしたメソッド
# 属性名=属性値の検索ならfind_locator_elemでもいい。classとかroleみたいな属性名だったらむしろこっちが必須。
# userid_elem = driver.find_locator_elem("id", "userid")
# 1つ親からタグ名がinputであるものを1つ探して「うおｗ」する
userid_elem.parent.find_elem("tag", "input").send_keys("うおｗ")
```

例: 画像リンク取得
```python
# 検索条件: タグ名がa かつ href属性の末尾が".png"
link_elems = driver.find_cond_elems(TagCond("a") * LocatorCond("href", ".png", "endswith"))
# ちなみに、この条件のxpathは以下のようにして取れる。find_cond_elemやfind_cond_elemsではこのxpathを用いて検索している
# cond = TagCond("a") * LocatorCond("href", ".png", "endswith")
# print(cond.xpath) -> ".//a[substring(@href, string-length(@href) - 5) = '.png']"
# id属性が"userid"のElement
link_list = [link_elem.attr("href") for link_elem in link_elems]
```

その他、Elementオブジェクトができること
* existsで存在確認
* save_html(file_path)でそのElement以下のHTMLを保存
* find_text_elemでテキスト条件で検索

とか