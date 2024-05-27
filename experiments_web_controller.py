from playwright.sync_api import sync_playwright, PlaywrightContextManager

import web_controller


def f1(p: PlaywrightContextManager):
    controller = web_controller.WebController(p, "images/2024-05-22_16-45-33")

    print("Starting...")

    controller.goto("https://semantic-ui.com/modules/dropdown.html")

    controller.try_click_by_text("Gender")

    controller.try_click_by_text("Male")

    # print(controller._page.video.path())
    controller.close()

    print("Done")


def f2(p: PlaywrightContextManager):
    controller = web_controller.WebController(p, "images/2024-05-22_16-45-33")
    print("Starting...")
    controller.goto("https://element-plus.org/en-US/component/checkbox.html")
    controller.try_click_by_text("Guangzhou")
    controller.close()
    print("Done")


# Main execution block.
with sync_playwright() as p:
    # f1(p)
    f2(p)
    print("Done")
