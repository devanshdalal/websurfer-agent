import re

from playwright.sync_api import Playwright

from utils import timer, similar


class WebController:
    def __init__(self, playwright: Playwright):
        self._browser = playwright.chromium.launch(headless=False)
        self._page = self._browser.new_page()

    def navigate(self, url):
        self._page.goto(url, wait_until='domcontentloaded')
        self.__capture()

    def down(self):
        self._page.mouse.wheel(delta_x=0, delta_y=720)

    @timer
    def click(self, link_text):
        link_text = similar(link_text, self._link_texts)
        link_text = re.sub('[^a-zA-Z0-9 ]', '', link_text)
        partial, exact = None, None
        elements = self._page.query_selector_all("""[gpt-link-text]""")
        for e in elements:
            attribute_val = e.evaluate("""el => el.getAttribute('gpt-link-text')""");
            if link_text in attribute_val:
                partial = e
            if link_text == attribute_val:
                exact = e
        if (exact is not None):
            print('Clicking on exact link text:', link_text)
            exact.click()
        elif (partial is not None):
            print('Clicking on partial link text:', link_text)
            partial.click()
        else:
            print("Failed to find link text:", link_text)
            return
        self.__capture()

    @timer
    def __capture(self):
        self.__highlight_links()
        self._page.screenshot(path="screenshot.jpeg", full_page=False, quality=20, type='jpeg', timeout=100000)
        print("Screenshot taken")

    @timer
    def __highlight_links(self):
        self._page.evaluate(
            """
            () => {
                document.querySelectorAll('[gpt-link-text]').forEach(e => {
                    e.removeAttribute("gpt-link-text");
                });
            }
            """
        )
        elements = self._page.query_selector_all("""a, button, input, textarea, [role=button], [role=treeitem]""")
        elements = list(filter(lambda x: x.text_content(), elements))
        print('Found', len(elements), 'elements.')
        self._link_texts = list(map(lambda x: x.text_content(), elements))
        print(' '.join(map(lambda x: "\"" + x + "\"", self._link_texts)))
        for e in elements:
            if not e.text_content():
                continue
            self._page.evaluate(
                """
                e => {
                    function isElementVisible(el) {
                        if (!el) return false; // Element does not exist

                        function isStyleVisible(el) {
                            const style = window.getComputedStyle(el);
                            return style.width !== '0' &&
                                   style.height !== '0' &&
                                   style.opacity !== '0' &&
                                   style.display !== 'none' &&
                                   style.visibility !== 'hidden';
                        }

                        function isElementInViewport(el) {
                            const rect = el.getBoundingClientRect();
                            return (
                            rect.top >= 0 &&
                            rect.left >= 0 &&
                            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                            );
                        }

                        // Check if the element is visible style-wise
                        if (!isStyleVisible(el)) {
                            return false;
                        }

                        // Traverse up the DOM and check if any ancestor element is hidden
                        let parent = el;
                        while (parent) {
                            if (!isStyleVisible(parent)) {
                            return false;
                            }
                            parent = parent.parentElement;
                        }

                        // Finally, check if the element is within the viewport
                        return isElementInViewport(el);
                    }

                    e.style.border = "1px solid red";

                    const position = e.getBoundingClientRect();

                    if( position.width > 5 && position.height > 5 && isElementVisible(e) ) {
                        const link_text = e.textContent.replace(/[^a-zA-Z0-9 ]/g, '');
                        e.setAttribute( "gpt-link-text", link_text );
                    }
                }
                """,
                e
            )
