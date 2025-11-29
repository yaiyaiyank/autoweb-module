from selenium.webdriver.common.by import By

INPUTABLE_TAG_NAME_LIST = ["input", "textarea"]
FRAME_TAG_NAME_LIST = ["iframe"]
SELECT_TAG_NAME_LIST = ["select"]
LOCATOR_DICT = {
    "id": By.ID,
    "name": By.NAME,
    "tag": By.TAG_NAME,
    "xpath": By.XPATH,
    "css": By.CSS_SELECTOR,
    "link": By.LINK_TEXT,
    "plink": By.PARTIAL_LINK_TEXT,
    "class": By.CLASS_NAME,
}
