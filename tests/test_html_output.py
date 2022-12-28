"""
Test the output of converting a slide deck to html
"""


from functools import wraps
import inspect
from pathlib import Path
from six.moves import StringIO  # type: ignore
import yaml
from typing import Dict


import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By


from lookatme.pres import Presentation


from tests.utils import create_style, setup_lookatme


DRIVER_CACHE: Dict[str, webdriver.Chrome] = {}


@pytest.fixture(scope="module")
def driver_cache():
    yield DRIVER_CACHE
    for _, driver in DRIVER_CACHE.items():
        driver.quit()


def selenium_for_slide(markdown: str, style: Dict, complete: bool = False):
    markdown = inspect.cleandoc(markdown)

    def outer(fn):
        full_style = create_style(style, complete=complete)
        embedded_style_markdown = "---\n{}\n---\n{}".format(
            yaml.dump({"styles": full_style}),
            markdown,
        )
        fn.style = full_style

        def inner(driver_cache, tmpdir, mocker):
            _ = driver_cache

            setup_lookatme(tmpdir, mocker, style=full_style)
            input_stream = StringIO(embedded_style_markdown)
            pres = Presentation(input_stream)
            pres.to_html(str(tmpdir))

            cache_key = str((markdown, style, complete))
            if cache_key not in DRIVER_CACHE:
                options = webdriver.ChromeOptions()
                options.add_argument("headless")
                options.add_argument("window-size=1200x600")
                driver = webdriver.Chrome(options=options)
                load_url = "file://" + str(tmpdir / "index.html")
                driver.get(load_url)
                DRIVER_CACHE[cache_key] = driver

            driver = DRIVER_CACHE[cache_key]
            driver.refresh()

            return fn(tmpdir, driver, full_style)

        return inner

    return outer


def go_to_slide(driver, slide_number):
    nav_item = driver.find_element(
        By.XPATH, "//li[@data-slide-idx={}]".format(slide_number - 1)
    )
    nav_item.click()
    assert driver.find_element(By.CLASS_NAME, "nav-active") == nav_item


BASIC_MARKDOWN = r"""
    # Category 1: First Slide

    Content 1

    # Category 1: Second Slide

    Content 2

    # Category 2: Third Slide

    Content 3

    {long_content}
""".format(
    long_content="A<br/>" * 100,
)


DEFAULT_STYLES = {
    "headings": {
        "default": {
            "prefix": ">> ",
        },
        "1": {
            "prefix": ">> ",
        },
    },
    "scrollbar": {
        "slider": {
            "fill": "X",
            "top_chars": ["X"],
            "bottom_chars": ["X"],
        },
        "gutter": {
            "fill": ".",
        },
    },
}


@selenium_for_slide(BASIC_MARKDOWN, DEFAULT_STYLES)
def test_custom_slider_chars(output_dir: Path, driver: webdriver.Chrome, style: Dict):
    body = driver.find_element(By.CSS_SELECTOR, "body")
    assert "X" not in body.text

    go_to_slide(driver, 3)
    assert "X" in body.text


@selenium_for_slide(BASIC_MARKDOWN, DEFAULT_STYLES)
def test_nav_classes(output_dir: Path, driver: webdriver.Chrome, style: Dict):
    body = driver.find_element(By.CSS_SELECTOR, "body")
    nav = driver.find_element(By.CLASS_NAME, "nav")
    visible = nav.text
    assert ">> Category 1" in visible
    assert ">> Category 2" in visible
    assert ">> Category 1: First Slide" not in visible

    active_nav_texts = [
        "First Slide",
        "Second Slide",
        "Third Slide",
    ]

    # move forward through the slides
    for active_text in active_nav_texts:
        active_navs = nav.find_elements(By.CLASS_NAME, "nav-active")
        assert len(active_navs) == 1
        assert active_navs[0].text == active_text

        # next slide
        body.send_keys("j")

    # move backward through the slides
    for active_text in reversed(active_nav_texts):
        active_navs = nav.find_elements(By.CLASS_NAME, "nav-active")
        assert len(active_navs) == 1
        assert active_navs[0].text == active_text

        # previous slide
        body.send_keys("k")


@selenium_for_slide(BASIC_MARKDOWN, DEFAULT_STYLES)
def test_slide_advancing(output_dir: Path, driver: webdriver.Chrome, style: Dict):
    body = driver.find_element(By.CSS_SELECTOR, "body")

    visible = body.text
    # should be in left nav
    assert "Category 1" in visible
    assert "Category 2" in visible
    assert "First Slide" in visible
    assert "Second Slide" in visible

    # first slide contents should be visible
    assert "Content 1" in visible
    assert "slide 1 / 3" in visible

    # second slide should *NOT* be visible
    assert "Content 2" not in visible
    assert "slide 2 / 3" not in visible

    body.send_keys("j")

    visible = body.text
    # first slide contents should be visible
    assert "Content 1" not in visible
    assert "slide 1 / 3" not in visible

    # second slide should *NOT* be visible
    assert "Content 2" in visible
    assert "slide 2 / 3" in visible

    # now go back
    body.send_keys("k")

    visible = body.text
    # first slide contents should be visible
    assert "Content 1" in visible
    assert "slide 1 / 3" in visible

    # second slide should *NOT* be visible
    assert "Content 2" not in visible
    assert "slide 2 / 3" not in visible
