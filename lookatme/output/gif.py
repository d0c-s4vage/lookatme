"""
Output formatter for gifs of lookatme slides, as they would appear in the
terminal
"""


import copy
import glob
import os
import re
import subprocess
import tempfile
from typing import Dict, List, Tuple


from lookatme.output.base import BaseOutputFormat, MissingExtraDependencyError


try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
except:
    raise MissingExtraDependencyError


import lookatme.config as config
from lookatme.output.base import BaseOutputFormat
from lookatme.output.html_raw import HtmlRawScreenshotOutputFormat
from lookatme.pres import Presentation


class GifOutputFormat(BaseOutputFormat):
    NAME = "gif"
    DEFAULT_OPTIONS = copy.deepcopy(HtmlRawScreenshotOutputFormat.DEFAULT_OPTIONS)
    REQUIRED_BINARIES = ["convert"]

    def do_format_pres(self, pres: Presentation, output_path: str):
        """ """
        fwd_options = {}
        fwd_options.update(self._curr_options or {})

        for opt_name in self.DEFAULT_OPTIONS.keys():
            html_raw_name = HtmlRawScreenshotOutputFormat.NAME
            fwd_options[f"{html_raw_name}.{opt_name}"] = self.opt(opt_name)

        with tempfile.TemporaryDirectory(prefix="lookatme-") as tmpd:
            html_formatter = HtmlRawScreenshotOutputFormat()
            html_formatter.format_pres(pres, tmpd, fwd_options)

            screen_infos = self._get_frame_infos(tmpd)
            pngs = self._html_files_to_pngs(tmpd, screen_infos)
            self._pngs_to_gif(output_path, tmpd, screen_infos, pngs)

    def _get_frame_infos(self, tmpd: str) -> List[Tuple[Dict, str]]:
        screen_files = glob.glob(os.path.join(tmpd, "screen*.html"))
        screen_infos = []
        for screen_file in screen_files:
            screen_file_noext, _ = os.path.splitext(os.path.basename(screen_file))

            info = dict(
                re.findall(
                    r"(?:^|_)(?P<attr>[a-zA-Z]+):(?P<val>[^_\.]*)", screen_file_noext
                )
            )
            screen_infos.append((info, screen_file))

        screen_infos.sort(key=lambda x: int(x[0]["screen"]))
        return screen_infos

    def _html_files_to_pngs(self, tmpd: str, screen_infos: List[Tuple[Dict, str]]):
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_argument("window-size=1200x800")
        driver = webdriver.Chrome(options=options)

        pngs = []
        self.log.info("Converting html files to pngs")
        for _, screen_file in screen_infos:
            load_url = "file://" + os.path.join(tmpd, screen_file)
            driver.get(load_url)
            slide_raw = driver.find_element(By.CLASS_NAME, "slide-raw")

            screenshot_path = screen_file.replace(".html", ".png")
            slide_raw.screenshot(screenshot_path)
            pngs.append(screenshot_path)

        return pngs

    def _pngs_to_gif(self, output_path, tmpd: str, screen_infos, pngs):
        convert_cmd = [
            "convert",
            "-font",
            os.path.join(
                tmpd, "static", "fonts", "DejaVu", "DejaVu Sans Mono for Powerline.ttf"
            ),
        ]

        for idx, screenshot in enumerate(pngs):
            delay = 75

            screen_info, screen_file = screen_infos[idx]
            delay = int(screen_info["delay"]) // 10

            convert_cmd += ["-delay", str(delay), screenshot]

        convert_cmd += ["-loop", "0", output_path]

        self.log.info("Converting png files to final gif")
        proc = subprocess.Popen(
            convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        stdout, _ = proc.communicate()

        if proc.returncode != 0:
            config.get_log().warn("Error running convert:\n\n" + stdout.decode())
