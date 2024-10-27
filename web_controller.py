import base64
import os
import subprocess

from playwright.sync_api import Playwright
from playwright_stealth import stealth_sync

from dom_utils import JSQ_GPT_ATTR_REMOVE, JSQ_DOCUMENT_ENHANCE_LINKS, JSQ_DOCUMENT_ENHANCE_INPUT, \
    JSQ_GET_ELEMENT_ATTRIBUTES
from utils import timer, equals, alpha_numeric, return_on_failure

LABEL_BLACK_LIST = {"src", "class", "style", "id", "data*", "jsname", "href"}
LABEL_BLACK_LIST_REGEX = "(" + ")|(".join(LABEL_BLACK_LIST) + ")"

LABEL_WHITE_LIST = ["alt", "role", "title", "aria-label"]
INPUT_LABEL_WHITE_LIST = ["alt", "type", "title", "aria-label", "placeholder", "name", "value"]


class WebController:
    def __init__(self, playwright: Playwright, wd: str, storage_state=None):
        self._browser = playwright.chromium.launch(headless=False)
        self._context = self._browser.new_context(
            storage_state=storage_state) if storage_state else self._browser.new_context()
        self._page = self._context.new_page()
        stealth_sync(self._page)
        self._cdp = self._context.new_cdp_session(self._page)
        self._wd = wd
        self._index_number = 0
        self._screenshot_path = os.path.join(self._wd, "screenshot.jpeg")
        self._elements = []

    def goto(self, url):
        self._page.goto(url, wait_until="commit")
        self._quick_capture()

    def down(self):
        self._page.keyboard.press("PageDown")
        self._quick_capture()

    @timer
    def elements_summaries(self):
        summaries = []
        self._elements = []

        # Add all anchor elements.
        links = self._page.query_selector_all("a[href]")
        summaries.extend(
            self._construct_summaries(tag='a', nodes=links, label_whitelist=LABEL_WHITE_LIST, do_viewport_check=False))

        # Add all button elements.
        buttons = self._page.query_selector_all("button")
        summaries.extend(self._construct_summaries(tag='button', nodes=buttons, label_whitelist=INPUT_LABEL_WHITE_LIST,
                                                   do_viewport_check=False))

        # Ass all input elements.
        inputs = self._page.query_selector_all("input")
        summaries.extend(
            self._construct_summaries(tag='input', nodes=inputs, label_whitelist=INPUT_LABEL_WHITE_LIST,
                                      do_viewport_check=False))

        return summaries

    def _construct_summaries(self, tag, nodes, label_whitelist, do_viewport_check):
        summaries = []
        for node in nodes:
            skip_node = False
            try:
                if node.is_disabled() or not node.is_visible():
                    skip_node = True
                elif do_viewport_check and not self._is_element_in_viewport(node):
                    skip_node = True
            except:
                skip_node = True
            if skip_node:
                continue
            text = self._text(node)
            # if not text.strip():
            #     continue
            s = self._add_node_and_get_summary(tag, text, node)
            attr = self._get_element_attributes(node, label_whitelist)
            if attr:
                s['attributes'] = attr
            summaries.append(s)
        return summaries

    def _add_node_and_get_summary(self, tag_name, link_text, node):
        index = len(self._elements)
        self._elements.append(node)
        return {'tag': tag_name, 'text': link_text, 'index': str(index)}

    def click(self, link_text=None, link_index=None):
        ret = False
        if link_index:  # Try to click by index
            index = int(link_index)
            if index < len(self._elements):
                link_element = self._elements[index]
                self._click_node(link_element)
            else:
                print("Invalid link index:", link_index, len(self._elements))
                raise ValueError("Invalid link index.")
            ret = True
        if not ret:  # Try to click by text
            for e in self.elements:
                text = self._text(e)
                if equals(text, link_text):
                    e.click()
                    ret = True
                    break
        if not ret:
            matching_link_text = alpha_numeric(link_text)
            # g = self._page.evaluate(JSQ_DOCUMENT_FIND_BY_TEXT, matching_link_text)
            exact = None
            elements = self._page.query_selector_all("""[gpt-link-text]""")
            for e in elements:
                attribute_val = e.evaluate("""el => el.getAttribute('gpt-link-text')""")
                if equals(attribute_val, matching_link_text):
                    exact = e
                    break
            if exact is not None:
                exact.click()
            else:
                # Try to click by text
                # self._page.get_by_text(link_text).click()
                print("Unable to find link text:", link_text)
        self._quick_capture()

    # @timer
    # def try_click_by_text(self, link_text):
    #     elements = self._page.query_selector_all("""*""")
    #     print('try_click_by_text found', len(elements), 'elements.')
    #     for e in elements:
    #         if e.is_hidden() or e.is_disabled() or e.is_enabled() is False or e.is_visible() is False:
    #             continue
    #         print('Checking element:', self._text_content(e))
    #         if equals(e.get_attribute("placeholder"), link_text) or equals(self._text_content(e), link_text):
    #             e.click()
    #             return
    #         if self._text_content(e) is not None and link_text == self._text_content(e):
    #             print("Found element with text_content:", self._text_content(e))
    #     print("Failed to find link text:", link_text)

    def type_input(self, placeholder, text):
        input_boxes = self._page.query_selector_all("""input, textarea""")
        print('fill_input found', len(input_boxes), 'elements.')
        search_box = None
        for e in input_boxes:
            print('Checking element:', self._text(e), e.get_attribute("placeholder"), text)
            if equals(e.get_attribute("placeholder"), placeholder) or equals(self._text(e), placeholder):
                search_box = e
                break
        if search_box is None:
            print("Failed to find input box with placeholder:", placeholder)
            return False
        search_box.type(text=text, delay=50)
        search_box.dispatch_event('click')
        search_box.press('Enter')
        self._quick_capture()
        return True

    def close(self):
        self._context.close()
        self._browser.close()

    @return_on_failure(None)
    def _click_node(self, node):
        # Remove the 'target' attribute if it exists to force the link to open in the same tab
        print("Clicking node:", node.inner_html())
        self._page.evaluate('el => el.removeAttribute("target")', node)
        node.click()

    @timer
    def _quick_capture(self):
        self._enhance_for_next_screenshot()
        b64_str = self._cdp.send("Page.captureScreenshot", {"quality": 40, "format": "jpeg"})["data"]
        b64_bytes = b64_str.encode("ascii")
        binary = base64.decodebytes(b64_bytes)
        with open(self._screenshot_path, "wb") as binary_file:
            binary_file.write(binary)

    @timer
    def _enhance_for_next_screenshot(self):
        if os.path.isfile(self._screenshot_path):
            subprocess.call(["mv", "-f", self._screenshot_path,
                             os.path.join(self._wd, "screenshot-" + ("%02d" % self._index_number) + ".jpeg")])
        self._index_number += 1
        self._page.wait_for_load_state()
        self._highlight_links()
        self._highlight_input()

    def _highlight_links(self):
        self._page.evaluate(JSQ_GPT_ATTR_REMOVE)
        self._page.evaluate(JSQ_DOCUMENT_ENHANCE_LINKS)

    def _highlight_input(self):
        self._page.evaluate(JSQ_DOCUMENT_ENHANCE_INPUT)

    def _get_element_attributes(self, element, label_whitelist):
        return element.evaluate(JSQ_GET_ELEMENT_ATTRIBUTES, label_whitelist)

    def _text(self, node):
        candidates = [lambda x: x.inner_text(),
                      lambda x: x.text_content(), lambda x: x.inner_html()]
        for getter in candidates:
            c = getter(node)
            if c:
                return c
        return ""

    def _is_element_in_viewport(self, element):
        bounding = element.bounding_box()
        if bounding is None:
            return False
        viewport = self._page.viewport_size
        return 0 <= bounding["x"] <= viewport["width"] and 0 <= bounding["y"] <= viewport["height"]

    @property
    def screenshot_path(self):
        return self._screenshot_path

    @property
    def page(self):
        return self._page

    @property
    def elements(self):
        return self._elements
