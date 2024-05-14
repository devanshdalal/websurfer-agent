from playwright.sync_api import sync_playwright

import web_controller

# Main execution block.
with sync_playwright() as p:
    controller = web_controller.WebController(p)

    print("Starting...")

    controller.navigate("https://www.smartprix.com")

    controller.click("Mobiles")

    print("Done")
