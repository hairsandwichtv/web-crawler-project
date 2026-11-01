import aiohttp
import asyncio
import requests
from typing import TypedDict
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup, Tag

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    h_tag = soup.find("h1") or soup.find("h2")

    return h_tag.get_text().strip() if isinstance(h_tag, Tag) else ""

def normalize_url(url):
    parts = urlsplit(url)
    normalized = parts.netloc + parts.path
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    p_tag = None
    main = soup.find("main")
    if isinstance(main, Tag):
        p_tag = main.find("p")

    if not isinstance(p_tag, Tag):
        p_tag = soup.find("p")

    return p_tag.get_text().strip() if isinstance(p_tag, Tag) else ""

def get_urls_from_html(html: str, base_url: str) -> list[str]:
    urls = []
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a")

    for anchor in anchors:
        if not isinstance(anchor, Tag):
            continue
        href = anchor.get("href")
        if isinstance(href, str) and href:
            try:
                absolute_url = urljoin(base_url, href)
                urls.append(absolute_url)
            except Exception as e:
                print(f"{str(e)}: {href}")

    return urls


def get_images_from_html(html: str, base_url: str) -> list[str]:
    image_urls = []
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")

    for img in images:
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src:
            try:
                absolute_url = urljoin(base_url, src)
                image_urls.append(absolute_url)
            except Exception as e:
                print(f"{str(e)}: {src}")

    return image_urls


def extract_page_data(html: str, page_url: str) -> PageData:
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }


def get_html(url):
    headers = {"User-Agent": "BootCrawler/1.0"}
    resp = requests.get(url, headers=headers)

    if resp.status_code >= 400:
        raise Exception(f"HTTP error {resp.status_code}: {resp.reason}")

    content_type = resp.headers.get("content-type", "")
    if not content_type.startswith("text/html"):
        raise Exception(f"non-HTML content-type: {content_type}")

    return resp.text


def crawl_page(base_url, current_url=None, page_data=None):
    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}

    if urlsplit(base_url).netloc != urlsplit(current_url).netloc:
        return page_data

    normalized = normalize_url(current_url)
    if normalized in page_data:
        return page_data

    print(f"crawling: {current_url}")

    try:
        html = get_html(current_url)
    except Exception as e:
        print(f"  skipping: {e}")
        return page_data

    page_data[normalized] = extract_page_data(html, current_url)

    for url in page_data[normalized]["outgoing_links"]:
        crawl_page(base_url, url, page_data)

    return page_data


class AsyncCrawler:
    def __init__(self, base_url, max_concurrency=3, max_pages=10):
        self.base_url = base_url
        self.base_domain = urlsplit(base_url).netloc
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        async with self.lock:
            if self.should_stop:
                return False

            if normalized_url in self.visited:
                return False

            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False

            self.visited.add(normalized_url)
            return True

    async def get_html(self, url):
        headers = {"User-Agent": "BootCrawler/1.0"}
        async with self.session.get(url, headers=headers) as resp:
            if resp.status >= 400:
                raise Exception(f"HTTP error {resp.status}: {resp.reason}")

            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("text/html"):
                raise Exception(f"non-HTML content-type: {content_type}")

            return await resp.text()

    async def crawl_page(self, current_url=None):
        if self.should_stop:
            return

        if current_url is None:
            current_url = self.base_url

        if urlsplit(current_url).netloc != self.base_domain:
            return

        normalized = normalize_url(current_url)
        if not await self.add_page_visit(normalized):
            return

        async with self.semaphore:
            print(f"crawling: {current_url}")
            try:
                html = await self.get_html(current_url)
            except Exception as e:
                print(f"  skipping: {e}")
                return
            data = extract_page_data(html, current_url)

        async with self.lock:
            self.page_data[normalized] = data

        if self.should_stop:
            return

        tasks = []
        for url in data["outgoing_links"]:
            task = asyncio.create_task(self.crawl_page(url))
            self.all_tasks.add(task)
            tasks.append(task)

        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                self.all_tasks.discard(task)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url, max_concurrency=3, max_pages=10):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
