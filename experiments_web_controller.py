from playwright.sync_api import sync_playwright

import web_controller

# Main execution block.
with sync_playwright() as p:
    controller = web_controller.WebController(p)

    print("Starting...")

    controller.goto("https://www.zomato.com/")

    controller.fill_input("Search for restaurant, cuisine or a dish", "Biryani")

    controller.click("Biryani - Delivery")

    elements = controller._page.query_selector_all("*")
    for e in elements:
        print(e.get_attribute("gpt-link-text"))

    print("Done")
