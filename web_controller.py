import base64
import os
import re
import subprocess

from playwright.sync_api import Playwright

from dom_utils import JSQ_GPT_ATTR_REMOVE, JSQ_ENHANCE_INPUT, JSQ_ENHANCE_LINK
from utils import timer, equals


class WebController:
    def __init__(self, playwright: Playwright, wd: str):
        self._browser = playwright.chromium.launch(headless=False)
        self._context = self._browser.new_context(
            record_video_dir="videos")
        self._page = self._browser.new_page()
        self._cdp = self._context.new_cdp_session(self._page)
        self._wd = wd
        self._index_number = 0
        self._screenshot_path = os.path.join(self._wd, "screenshot.jpeg")

    def goto(self, url):
        self._page.goto(url, wait_until='domcontentloaded')
        self.__quick_capture()

    def down(self):
        self._page.keyboard.press("PageDown")
        self.__quick_capture()

    def click(self, link_text):
        matching_link_text = re.sub('[^a-zA-Z0-9 ]', '', link_text)
        partial, exact = None, None
        elements = self._page.query_selector_all("""[gpt-link-text]""")
        for e in elements:
            attribute_val = e.evaluate("""el => el.getAttribute('gpt-link-text')""");
            if matching_link_text in attribute_val:
                partial = e
            if matching_link_text == attribute_val:
                exact = e
        if exact is not None:
            exact.click()
        elif partial is not None:
            print('Clicking on partial link text:', matching_link_text)
            partial.click()
        else:
            # Try to click by text
            self.try_click_by_text(link_text)
        self.__quick_capture()

    @timer
    def try_click_by_text(self, link_text):
        elements = self._page.query_selector_all("""*""")
        print('try_click_by_text found', len(elements), 'elements.')
        for e in elements:
            if e.is_hidden() or e.is_disabled() or e.is_enabled() is False or e.is_visible() is False:
                continue
            print('Checking element:', e.text_content())
            if equals(e.get_attribute("placeholder"), link_text) or equals(e.text_content(), link_text):
                e.click()
                return
            if e.text_content() is not None and link_text == e.text_content():
                print("Found element with text_content:", e.text_content())
        print("Failed to find link text:", link_text)

    def type_input(self, placeholder, text):
        input_boxes = self._page.query_selector_all("""input""")
        print('fill_input found', len(input_boxes), 'elements.')
        search_box = None
        for e in input_boxes:
            if equals(e.get_attribute("placeholder"), text) or equals(e.text_content(), text):
                search_box = e
                break
        if search_box is None:
            print("Failed to find input box with placeholder:", placeholder)
            return False
        search_box.type(text=text, delay=300)
        search_box.dispatch_event('click')
        search_box.press('Enter')
        self.__quick_capture()
        return True

    def close(self):
        self._context.close()
        self._browser.close()

    @timer
    def __quick_capture(self):
        self.__enhance_for_next_screenshot()
        b64_str = self._cdp.send("Page.captureScreenshot", {"quality": 40, "format": "jpeg"})["data"]
        b64_bytes = b64_str.encode("ascii")
        binary = base64.decodebytes(b64_bytes)
        with open(self._screenshot_path, "wb") as binary_file:
            binary_file.write(binary)

    def __enhance_for_next_screenshot(self):
        if os.path.isfile(self._screenshot_path):
            subprocess.call(["mv", "-f", self._screenshot_path,
                             os.path.join(self._wd, "screenshot-" + ("%02d" % self._index_number) + ".jpeg")])
        self._index_number += 1
        self._page.wait_for_load_state()
        self.__highlight_links()
        self.__highlight_input()

    def __highlight_links(self):
        self._page.evaluate(JSQ_GPT_ATTR_REMOVE)
        elements = self._page.query_selector_all(
            """a, button, [role=button], [role=treeitem], input, textarea""")
        elements = list(filter(lambda x: x.text_content(), elements))
        print('In __highlight_links found', len(elements), 'elements.')
        for e in elements:
            if e.is_hidden() or e.is_disabled() or not e.text_content():
                continue
            self._page.evaluate(JSQ_ENHANCE_LINK, e)

    def __highlight_input(self):
        elements = self._page.query_selector_all("""
        input[type = "text"]""")
        print('In __highlight_input found', len(elements), 'elements.')
        for e in elements:
            self._page.evaluate(JSQ_ENHANCE_INPUT, e)
