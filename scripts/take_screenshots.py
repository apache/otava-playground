#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Automated screenshot capture for documentation."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright


SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "_static" / "screenshots"
BASE_URL = "http://localhost:8100"


def take_screenshot(page, filename: str, generator: str = None, params: dict = None,
                    enable_ma: bool = False, enable_boundary: bool = False):
    """Take a full-page screenshot with specified settings."""

    # Navigate fresh each time to reset state
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(0.5)  # Wait for chart to render

    # Select generator if specified
    if generator:
        page.select_option("#generator-select", generator)
        page.wait_for_load_state("networkidle")
        time.sleep(0.3)

    # Set parameters if specified
    if params:
        for param_name, value in params.items():
            # Find the input by label text
            inputs = page.query_selector_all(f"input")
            for inp in inputs:
                parent = inp.query_selector("xpath=..")
                if parent:
                    label = parent.query_selector("label")
                    if label and param_name.lower() in label.text_content().lower():
                        inp.fill(str(value))
                        break
            # Also try by aria-label or name
            try:
                page.fill(f"[aria-label*='{param_name}' i]", str(value))
            except:
                pass
            try:
                page.get_by_role("spinbutton", name=param_name).fill(str(value))
            except:
                pass

    # Enable/disable analysis methods
    ma_checkbox = page.locator("#run-ma-checkbox")
    boundary_checkbox = page.locator("#run-boundary-checkbox")

    if enable_ma and not ma_checkbox.is_checked():
        ma_checkbox.click()
    elif not enable_ma and ma_checkbox.is_checked():
        ma_checkbox.click()

    if enable_boundary and not boundary_checkbox.is_checked():
        boundary_checkbox.click()
    elif not enable_boundary and boundary_checkbox.is_checked():
        boundary_checkbox.click()

    # Click Analyse button
    page.click("#generate-btn")
    page.wait_for_load_state("networkidle")
    time.sleep(1)  # Wait for analysis and chart update

    # Take full page screenshot
    filepath = SCREENSHOTS_DIR / filename
    page.screenshot(path=str(filepath), full_page=True)
    print(f"Saved: {filepath}")


def main():
    """Take all documentation screenshots."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # Try Firefox first (often has better rendering)
        try:
            browser = p.firefox.launch(headless=True)
            print("Using Firefox")
        except:
            browser = p.chromium.launch(headless=True)
            print("Using Chromium")

        page = browser.new_page(viewport={"width": 1920, "height": 1200})

        # 1. Step Function with sigma=2
        print("\n1. Step Function sigma=2...")
        take_screenshot(
            page, "step-function-sigma-2.png",
            generator="step_function",
            params={"Sigma": 2}
        )

        # 2. Step Function with sigma=15
        print("\n2. Step Function sigma=15...")
        take_screenshot(
            page, "step-function-sigma-15.png",
            generator="step_function",
            params={"Sigma": 15}
        )

        # 3. Variance Change
        print("\n3. Variance Change...")
        take_screenshot(
            page, "variance-change.png",
            generator="variance_change"
        )

        # 4. Multiple Changes
        print("\n4. Multiple Changes...")
        take_screenshot(
            page, "multiple-changes.png",
            generator="multiple_changes"
        )

        # 5. Banding
        print("\n5. Banding...")
        take_screenshot(
            page, "banding.png",
            generator="banding"
        )

        # 6. Single Outlier
        print("\n6. Single Outlier...")
        take_screenshot(
            page, "single-outlier.png",
            generator="single_outlier"
        )

        # 7. Phase Change
        print("\n7. Phase Change...")
        take_screenshot(
            page, "phase-change.png",
            generator="phase_change"
        )

        # 8. All analysis methods (noisy)
        print("\n8. All analysis methods...")
        take_screenshot(
            page, "all-analysis-noisy.png",
            generator="step_function",
            params={"Sigma": 10},
            enable_ma=True,
            enable_boundary=True
        )

        # 9. Otava analysis only
        print("\n9. Otava analysis only...")
        take_screenshot(
            page, "otava-analysis-only.png",
            generator="step_function",
            params={"Sigma": 5},
            enable_ma=False,
            enable_boundary=False
        )

        browser.close()
        print("\nAll screenshots complete!")


if __name__ == "__main__":
    main()
