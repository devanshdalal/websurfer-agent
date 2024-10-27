import os.path

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
    storage_state = 's4.json'
    wd = "images/2024-09-11_16-42-24"
    controller = web_controller.WebController(p, wd=wd,
                                              storage_state=storage_state) if os.path.isfile(
        storage_state) else web_controller.WebController(p, wd=wd)
    print("Starting...")
    controller.goto("https://devanshdalal2jira.atlassian.net/jira/servicedesk/projects/ST/queues/custom/1")
    s = controller.elements_summaries()
    # controller.page.context.storage_state(path=storage_state)
    # controller.click("Philips Battery Powered SkinProtect")
    controller.close()
    print("Done")


# Main execution block.
with sync_playwright() as p:
    # f1(p)
    f2(p)
    print("Done")
