from playwright.sync_api import sync_playwright

import web_controller

# Main execution block.
with sync_playwright() as p:
    controller = web_controller.WebController(p)

    print("Starting...")

    controller.goto("https://www.zomato.com/")

    controller.type_input("Search for restaurant, cuisine or a dish", "Biryani")

    controller.click("Biryani - Delivery")
    print("Clicked on Biryani - Delivery")

    # print(controller._page.video.path())
    controller.close()

    print("Done")
