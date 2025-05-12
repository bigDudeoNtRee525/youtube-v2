import asyncio
from apify import Actor
from playwright.async_api import async_playwright

async def scroll_page(page, max_scrolls=15, pause=1.5):
    for _ in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        await page.wait_for_timeout(pause * 1000)

async def scrape_keyword(page, keyword, results_limit):
    url = f"https://www.youtube.com/results?search_query={keyword.replace(' ', '+')}"
    await page.goto(url)
    await page.wait_for_selector('ytd-toggle-button-renderer', timeout=10000)

    # Click the "Filters" button
    await page.locator('ytd-toggle-button-renderer').click()
    await page.wait_for_selector('ytd-search-filter-renderer', timeout=10000)

    # Click "Last hour"
    filters = page.locator('ytd-search-filter-renderer')
    count = await filters.count()
    for i in range(count):
        text = (await filters.nth(i).inner_text()).lower()
        if 'last hour' in text:
            await filters.nth(i).click()
            break

    await page.wait_for_timeout(2000)
    await scroll_page(page)

    videos = page.locator("ytd-video-renderer")
    count = await videos.count()
    results = []

    for i in range(min(count, results_limit)):
        vid = videos.nth(i)
        title = await vid.locator("#video-title").get_attribute("title")
        href = await vid.locator("#video-title").get_attribute("href")
        channel = await vid.locator("#channel-info a").inner_text()
        meta = vid.locator("#metadata-line span")
        views = await meta.nth(0).inner_text()
        uploaded = await meta.nth(1).inner_text()

        results.append({
            "title": title,
            "url": f"https://www.youtube.com{href}",
            "channel": channel.strip(),
            "views": views.strip(),
            "uploaded": uploaded.strip(),
        })

    return results

async def main():
    async with Actor:
        input_data = await Actor.get_input() or {}
        keywords = input_data.get("keywords", ["top saas tools 2024"])
        results_per_keyword = input_data.get("resultsPerKeyword", 100)

        proxy_url = Actor.apify_proxy.get_url()  # 🔐 Enables Apify Proxy
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_url}
            )
            page = await browser.new_page()

            all_results = []
            for keyword in keywords:
                await Actor.log.info(f"Scraping for: {keyword}")
                res = await scrape_keyword(page, keyword, results_per_keyword)
                all_results.extend(res)

            await Actor.push_data(all_results)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
