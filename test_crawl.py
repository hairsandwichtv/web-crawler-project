import unittest
from crawl import (
    extract_page_data,
    get_first_paragraph_from_html,
    get_heading_from_html,
    get_images_from_html,
    get_urls_from_html,
    normalize_url,
)


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

class TestGetHeadingFromHTML(unittest.TestCase):
    def test_h1_basic(self):
        html = "<html><body><h1>Welcome to Boot.dev</h1></body></html>"
        self.assertEqual(get_heading_from_html(html), "Welcome to Boot.dev")

    def test_h2_fallback(self):
        html = "<html><body><p>Intro</p><h2>A Subheading</h2></body></html>"
        self.assertEqual(get_heading_from_html(html), "A Subheading")

    def test_h1_preferred_over_h2(self):
        html = "<html><body><h2>Second</h2><h1>First</h1></body></html>"
        self.assertEqual(get_heading_from_html(html), "First")

    def test_no_heading(self):
        html = "<html><body><p>Just a paragraph</p></body></html>"
        self.assertEqual(get_heading_from_html(html), "")

    def test_empty_html(self):
        self.assertEqual(get_heading_from_html(""), "")

    def test_first_h1_when_multiple(self):
        html = "<html><body><h1>One</h1><h1>Two</h1></body></html>"
        self.assertEqual(get_heading_from_html(html), "One")

    def test_first_h2_when_multiple(self):
        html = "<html><body><h2>Alpha</h2><h2>Beta</h2></body></html>"
        self.assertEqual(get_heading_from_html(html), "Alpha")

    def test_strips_whitespace(self):
        html = "<html><body><h1>\n   Padded Heading   \n</h1></body></html>"
        self.assertEqual(get_heading_from_html(html), "Padded Heading")

    def test_nested_tags_in_heading(self):
        html = "<html><body><h1>Hello <b>World</b></h1></body></html>"
        self.assertEqual(get_heading_from_html(html), "Hello World")

    def test_empty_heading_tag(self):
        html = "<html><body><h1></h1></body></html>"
        self.assertEqual(get_heading_from_html(html), "")

    def test_heading_with_attributes(self):
        html = '<html><body><h1 class="title" id="main">Styled</h1></body></html>'
        self.assertEqual(get_heading_from_html(html), "Styled")


class TestGetFirstParagraphFromHTML(unittest.TestCase):
    def test_basic(self):
        html = "<html><body><p>First paragraph.</p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(html), "First paragraph.")

    def test_main_priority(self):
        html = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        self.assertEqual(get_first_paragraph_from_html(html), "Main paragraph.")

    def test_first_of_multiple(self):
        html = "<html><body><p>One</p><p>Two</p><p>Three</p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(html), "One")

    def test_first_of_multiple_inside_main(self):
        html = """<html><body><main>
            <p>Alpha</p>
            <p>Beta</p>
        </main></body></html>"""
        self.assertEqual(get_first_paragraph_from_html(html), "Alpha")

    def test_no_paragraph(self):
        html = "<html><body><h1>Only a heading</h1></body></html>"
        self.assertEqual(get_first_paragraph_from_html(html), "")

    def test_empty_html(self):
        self.assertEqual(get_first_paragraph_from_html(""), "")

    def test_main_without_paragraph_falls_back(self):
        html = """<html><body>
            <p>Outside paragraph.</p>
            <main><h2>No paragraph in here</h2></main>
        </body></html>"""
        self.assertEqual(get_first_paragraph_from_html(html), "Outside paragraph.")

    def test_nested_paragraph_in_main(self):
        html = """<html><body><main>
            <div><section><p>Deeply nested.</p></section></div>
        </main></body></html>"""
        self.assertEqual(get_first_paragraph_from_html(html), "Deeply nested.")

    def test_nested_tags_in_paragraph(self):
        html = "<html><body><p>Visit <a href='/x'>this link</a> now</p></body></html>"
        self.assertEqual(
            get_first_paragraph_from_html(html), "Visit this link now"
        )

    def test_strips_whitespace(self):
        html = "<html><body><p>\n   Padded text   \n</p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(html), "Padded text")

    def test_empty_paragraph_tag(self):
        html = "<html><body><p></p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(html), "")

class TestGetURLsFromHTML(unittest.TestCase):
    def test_absolute(self):
        base = "https://crawler-test.com"
        html = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        self.assertEqual(get_urls_from_html(html, base), ["https://crawler-test.com"])

    def test_relative(self):
        base = "https://crawler-test.com"
        html = '<html><body><a href="/about">About</a></body></html>'
        self.assertEqual(
            get_urls_from_html(html, base), ["https://crawler-test.com/about"]
        )

    def test_relative_without_leading_slash(self):
        base = "https://crawler-test.com"
        html = '<html><body><a href="contact">Contact</a></body></html>'
        self.assertEqual(
            get_urls_from_html(html, base), ["https://crawler-test.com/contact"]
        )

    def test_both_absolute_and_relative(self):
        base = "https://crawler-test.com"
        html = """<html><body>
            <a href="/one">One</a>
            <a href="https://other-site.com/two">Two</a>
        </body></html>"""
        self.assertEqual(
            get_urls_from_html(html, base),
            ["https://crawler-test.com/one", "https://other-site.com/two"],
        )

    def test_multiple_links_in_order(self):
        base = "https://crawler-test.com"
        html = """<html><body>
            <a href="/alpha">Alpha</a>
            <a href="/beta">Beta</a>
            <a href="/gamma">Gamma</a>
        </body></html>"""
        self.assertEqual(
            get_urls_from_html(html, base),
            [
                "https://crawler-test.com/alpha",
                "https://crawler-test.com/beta",
                "https://crawler-test.com/gamma",
            ],
        )

    def test_nested_anchors_found(self):
        base = "https://crawler-test.com"
        html = """<html><body>
            <main><div><section>
                <a href="/deep">Deep link</a>
            </section></div></main>
        </body></html>"""
        self.assertEqual(
            get_urls_from_html(html, base), ["https://crawler-test.com/deep"]
        )

    def test_no_anchors(self):
        base = "https://crawler-test.com"
        html = "<html><body><p>No links here</p></body></html>"
        self.assertEqual(get_urls_from_html(html, base), [])

    def test_empty_html(self):
        self.assertEqual(get_urls_from_html("", "https://crawler-test.com"), [])

    def test_anchor_without_href_skipped(self):
        base = "https://crawler-test.com"
        html = '<html><body><a>No href</a><a href="/real">Real</a></body></html>'
        self.assertEqual(
            get_urls_from_html(html, base), ["https://crawler-test.com/real"]
        )

    def test_base_url_with_trailing_slash(self):
        base = "https://crawler-test.com/"
        html = '<html><body><a href="/page">Page</a></body></html>'
        self.assertEqual(
            get_urls_from_html(html, base), ["https://crawler-test.com/page"]
        )

    def test_duplicate_urls_kept(self):
        base = "https://crawler-test.com"
        html = '<html><body><a href="/same">A</a><a href="/same">B</a></body></html>'
        self.assertEqual(
            get_urls_from_html(html, base),
            ["https://crawler-test.com/same", "https://crawler-test.com/same"],
        )

class TestGetImagesFromHTML(unittest.TestCase):
    def test_relative(self):
        base = "https://crawler-test.com"
        html = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        self.assertEqual(
            get_images_from_html(html, base), ["https://crawler-test.com/logo.png"]
        )

    def test_absolute(self):
        base = "https://crawler-test.com"
        html = '<html><body><img src="https://cdn.example.com/pic.jpg"></body></html>'
        self.assertEqual(
            get_images_from_html(html, base), ["https://cdn.example.com/pic.jpg"]
        )

    def test_relative_without_leading_slash(self):
        base = "https://crawler-test.com"
        html = '<html><body><img src="images/icon.svg"></body></html>'
        self.assertEqual(
            get_images_from_html(html, base),
            ["https://crawler-test.com/images/icon.svg"],
        )

    def test_both_absolute_and_relative(self):
        base = "https://crawler-test.com"
        html = """<html><body>
            <img src="/local.png">
            <img src="https://cdn.example.com/remote.png">
        </body></html>"""
        self.assertEqual(
            get_images_from_html(html, base),
            ["https://crawler-test.com/local.png", "https://cdn.example.com/remote.png"],
        )

    def test_multiple_images_in_order(self):
        base = "https://crawler-test.com"
        html = """<html><body>
            <img src="/one.png">
            <img src="/two.png">
            <img src="/three.png">
        </body></html>"""
        self.assertEqual(
            get_images_from_html(html, base),
            [
                "https://crawler-test.com/one.png",
                "https://crawler-test.com/two.png",
                "https://crawler-test.com/three.png",
            ],
        )

    def test_nested_images_found(self):
        base = "https://crawler-test.com"
        html = """<html><body>
            <main><div><figure>
                <img src="/deep.png">
            </figure></div></main>
        </body></html>"""
        self.assertEqual(
            get_images_from_html(html, base), ["https://crawler-test.com/deep.png"]
        )

    def test_img_without_src_skipped(self):
        base = "https://crawler-test.com"
        html = '<html><body><img alt="broken"><img src="/real.png"></body></html>'
        self.assertEqual(
            get_images_from_html(html, base), ["https://crawler-test.com/real.png"]
        )

    def test_no_images(self):
        base = "https://crawler-test.com"
        html = "<html><body><p>No images here</p></body></html>"
        self.assertEqual(get_images_from_html(html, base), [])

    def test_empty_html(self):
        self.assertEqual(get_images_from_html("", "https://crawler-test.com"), [])

    def test_base_url_with_trailing_slash(self):
        base = "https://crawler-test.com/"
        html = '<html><body><img src="/banner.jpg"></body></html>'
        self.assertEqual(
            get_images_from_html(html, base), ["https://crawler-test.com/banner.jpg"]
        )

    def test_img_with_extra_attributes(self):
        base = "https://crawler-test.com"
        html = '<html><body><img src="/x.png" alt="X" width="100" class="hero"></body></html>'
        self.assertEqual(
            get_images_from_html(html, base), ["https://crawler-test.com/x.png"]
        )

class TestExtractPageData(unittest.TestCase):
    def test_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(extract_page_data(input_body, input_url), expected)

    def test_empty_html(self):
        input_url = "https://crawler-test.com"
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        }
        self.assertEqual(extract_page_data("", input_url), expected)

    def test_url_is_page_url_not_base(self):
        input_url = "https://crawler-test.com/blog/post"
        input_body = "<html><body><h1>Post</h1></body></html>"
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["url"], "https://crawler-test.com/blog/post")

    def test_h2_fallback_heading(self):
        input_url = "https://crawler-test.com"
        input_body = "<html><body><h2>Fallback Heading</h2></body></html>"
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["heading"], "Fallback Heading")

    def test_main_paragraph_preferred(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main><p>Main paragraph.</p></main>
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["first_paragraph"], "Main paragraph.")

    def test_multiple_links_and_images(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Gallery</h1>
            <p>Some pictures.</p>
            <a href="/one">One</a>
            <a href="https://other-site.com/two">Two</a>
            <img src="/a.png">
            <img src="https://cdn.example.com/b.png">
        </body></html>"""
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Gallery",
            "first_paragraph": "Some pictures.",
            "outgoing_links": [
                "https://crawler-test.com/one",
                "https://other-site.com/two",
            ],
            "image_urls": [
                "https://crawler-test.com/a.png",
                "https://cdn.example.com/b.png",
            ],
        }
        self.assertEqual(extract_page_data(input_body, input_url), expected)

    def test_relative_urls_resolved_against_page_url(self):
        input_url = "https://crawler-test.com/blog/"
        input_body = '<html><body><a href="post">Post</a></body></html>'
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(
            actual["outgoing_links"], ["https://crawler-test.com/blog/post"]
        )

    def test_all_keys_present(self):
        actual = extract_page_data("<html></html>", "https://crawler-test.com")
        self.assertEqual(
            set(actual.keys()),
            {"url", "heading", "first_paragraph", "outgoing_links", "image_urls"},
        )

    def test_missing_pieces_have_empty_defaults(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/only-a-link">Link</a></body></html>'
        actual = extract_page_data(input_body, input_url)
        self.assertEqual(actual["heading"], "")
        self.assertEqual(actual["first_paragraph"], "")
        self.assertEqual(actual["image_urls"], [])
        self.assertEqual(actual["outgoing_links"], ["https://crawler-test.com/only-a-link"])


if __name__ == "__main__":
    unittest.main()
