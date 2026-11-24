"""Browser regression checks. Run: python -m unittest discover -s tests -v

Install Playwright and its browser first:
  python -m pip install playwright
  python -m playwright install chromium
Set GHOSTWEB_BROWSER_CHANNEL=chrome to use an installed Chrome instead.
Set GHOSTWEB_SCREENSHOTS to a directory to save desktop/mobile previews.
"""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT))
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            channel=os.environ.get("GHOSTWEB_BROWSER_CHANNEL") or None
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 1000}, reduced_motion="reduce"
        )
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.goto(self.url, wait_until="networkidle")
        self.page.evaluate("document.fonts.ready")

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], "Unexpected JavaScript errors")

    def test_tabs_click_and_keyboard(self):
        for tab in self.page.locator(".tab").all():
            tab.click()
            expect(tab).to_have_attribute("aria-selected", "true")
            panel_id = tab.get_attribute("aria-controls")
            expect(self.page.locator(f"#{panel_id}")).to_be_visible()
            self.assertEqual(self.page.locator(".panel:visible").count(), 1)
        self.page.locator("#t-seo").press("Home")
        expect(self.page.locator("#t-li")).to_be_focused()
        self.page.locator("#t-li").press("ArrowLeft")
        expect(self.page.locator("#t-seo")).to_be_focused()
        self.page.locator("#t-seo").press("End")
        expect(self.page.locator("#t-seo")).to_have_attribute("aria-selected", "true")

    def test_name_propagates_to_all_previews(self):
        self.page.locator("#nameField").fill("Ada Lovelace")
        for target in ["liName", "mailFrom", "vName"]:
            expect(self.page.locator(f"#{target}")).to_have_text("Ada Lovelace")
        expect(self.page.locator("#liAvatar")).to_have_text("AL")
        expect(self.page.locator("#blogMeta")).to_contain_text("By Ada Lovelace")
        expect(self.page.locator("#artMeta")).to_contain_text("By Ada Lovelace")

    def test_seo_and_answer_preview(self):
        self.page.locator("#t-seo").click()
        self.page.locator("#kwInput").fill("standing desk")
        self.page.locator("#brandInput").fill("Acme")
        expect(self.page.locator("#serpTitle")).to_have_text("Standing Desk that lasts | Acme")
        expect(self.page.locator("#seoOutline")).to_contain_text("standing desk")
        self.page.locator("#viewAi").click()
        expect(self.page.locator("#viewAi")).to_have_attribute("aria-pressed", "true")
        expect(self.page.locator("#engineOut .answer")).to_contain_text("Acme")
        self.page.locator("#viewSearch").click()
        expect(self.page.locator("#engineOut .serp-title")).to_contain_text("Standing Desk")
        # User-provided values stay text, not executable markup.
        self.page.locator("#kwInput").fill('<img src=x onerror="alert(1)">')
        self.assertEqual(self.page.locator("#seoOutline img, #engineOut img").count(), 0)

    def test_tone_controls(self):
        for index, phrase in [(0, "prices"), (1, "reporting feature"), (2, "scoping calls")]:
            self.page.locator(f'[data-p="{index}"]').click()
            expect(self.page.locator("#voiceText")).to_contain_text(phrase)
        for index in range(3):
            slider = self.page.locator(f"#s{index}")
            slider.fill("2")
        expect(self.page.locator("#lab0")).to_have_text("Literary")
        expect(self.page.locator("#lab1")).to_have_text("Blunt")
        expect(self.page.locator("#lab2")).to_have_text("Full")
        expect(self.page.locator("#voiceCombo")).to_have_text("2 / 2 / 2")
        self.assertGreater(int(self.page.locator("#vWords").text_content()), 50)
        expect(self.page.locator("#vWords")).to_have_attribute("aria-label", "79")

    def test_restored_logo_and_consistent_typography(self):
        serif = self.page.locator("h1").evaluate("el => getComputedStyle(el).fontFamily")
        for selector in ["body", "h2", "h3", ".draft-body", ".voice-text"]:
            self.assertEqual(self.page.locator(selector).first.evaluate(
                "el => getComputedStyle(el).fontFamily"
            ), serif)
        mono = self.page.locator(".logo").first.evaluate("el => getComputedStyle(el).fontFamily")
        self.assertIn("Space Mono", mono)
        for selector in [".btn", ".nav-links", ".tab"]:
            self.assertEqual(self.page.locator(selector).first.evaluate(
                "el => getComputedStyle(el).fontFamily"
            ), mono)
        caret = self.page.locator(".logo .mk-caret").first
        self.assertEqual(caret.evaluate("el => getComputedStyle(el).animationName"), "none")
        self.page.emulate_media(reduced_motion="no-preference")
        self.assertEqual(caret.evaluate("el => getComputedStyle(el).animationName"), "blink")
        self.assertEqual(caret.evaluate("el => getComputedStyle(el).animationDuration"), "1.2s")

    def test_reading_index_navigation_and_keyboard(self):
        expect(self.page.locator("#readingIndex")).not_to_be_visible()
        self.page.locator('#navLinks [data-goto="quality"]').click()
        toggle = self.page.locator("#readingToggle")
        expect(toggle).to_be_visible()
        toggle.click()
        expect(toggle).to_have_attribute("aria-expanded", "true")
        chapters = self.page.locator("#readingChapters button")
        self.assertEqual(chapters.count(), 7)
        expect(self.page.locator('#readingChapters [data-goto="quality"]')).to_have_attribute(
            "aria-current", "location"
        )
        toggle.press("ArrowDown")
        expect(chapters.first).to_be_focused()
        chapters.first.press("End")
        expect(chapters.last).to_be_focused()
        chapters.last.press("Escape")
        expect(toggle).to_be_focused()
        expect(toggle).to_have_attribute("aria-expanded", "false")
        toggle.click()
        self.page.locator('#readingChapters [data-goto="pricing"]').click()
        expect(toggle).to_have_attribute("aria-expanded", "false")
        self.assertLess(abs(self.page.locator("#pricing").bounding_box()["y"] - 96), 3)
        self.page.locator("#fName").focus()
        expect(self.page.locator("#readingIndex")).not_to_be_visible()

    def test_process_player_manual_selection(self):
        self.page.locator("#process").scroll_into_view_if_needed()
        player = self.page.locator("#processPlayer")
        expect(player).to_have_attribute("data-playing", "false")
        buttons = self.page.locator(".process-seek")
        for i, name in enumerate(["Talk", "Sample", "Decide", "Work"]):
            buttons.nth(i).click()
            expect(buttons.nth(i)).to_have_attribute("aria-current", "step")
            expect(self.page.locator("#processPlayerLabel")).to_have_text(name)
            self.assertEqual(self.page.locator(".step.is-current").count(), 1)
            self.assertEqual(self.page.locator(".step:visible").count(), 4)
        buttons.last.press("Home")
        expect(buttons.first).to_be_focused()
        buttons.first.press("ArrowRight")
        expect(buttons.nth(1)).to_be_focused()
        expect(self.page.locator("#processPlayerLabel")).to_have_text("Sample")

    def test_process_player_play_pause_and_auto_advance(self):
        self.page.locator("#process").scroll_into_view_if_needed()
        control = self.page.locator("#processControl")
        control.click()
        expect(self.page.locator("#processPlayer")).to_have_attribute("data-playing", "true")
        expect(control).to_have_attribute("aria-label", "Pause process walkthrough")
        expect(self.page.locator("#processPlayerLabel")).to_have_text("Sample", timeout=6000)
        control.click()
        expect(self.page.locator("#processPlayer")).to_have_attribute("data-playing", "false")
        expect(control).to_have_attribute("aria-label", "Play process walkthrough")
        control.click()
        self.page.locator("#start").scroll_into_view_if_needed()
        expect(self.page.locator("#processPlayer")).to_have_attribute("data-playing", "false")
        self.page.locator("#process").scroll_into_view_if_needed()
        self.page.locator(".process-seek").last.click()
        control.click()
        expect(control).to_have_attribute("aria-label", "Replay process walkthrough", timeout=6000)
        control.click()
        expect(self.page.locator("#processPlayerLabel")).to_have_text("Talk")
        expect(self.page.locator("#processPlayer")).to_have_attribute("data-playing", "true")

    def test_rolling_counters_keep_accessible_values(self):
        for counter in self.page.locator(".score-top b").all():
            expect(counter).to_have_attribute("aria-label", counter.text_content())
            self.assertEqual(counter.inner_text(), counter.text_content())
            self.assertGreater(counter.locator(".rolling-digit").count(), 0)
        self.page.locator("#tone").scroll_into_view_if_needed()
        self.page.emulate_media(reduced_motion="no-preference")
        count = self.page.locator("#vWords")
        count.scroll_into_view_if_needed()
        expect(count).to_have_attribute("data-counter-visible", "true")
        self.page.locator("#s2").fill("2")
        expect(count).to_have_attribute("aria-label", count.text_content())
        self.page.locator("#s2").fill("0")
        expect(count).to_have_attribute("aria-label", count.text_content())
        expect(count.locator(".roll-down").first).to_be_attached()

    def test_faq_accessibility_and_keyboard(self):
        questions = self.page.locator(".faq-q")
        for question in questions.all():
            question.click()
            expect(question).to_have_attribute("aria-expanded", "true")
            answer = self.page.locator(f'#{question.get_attribute("aria-controls")}')
            expect(answer).to_have_attribute("aria-hidden", "false")
            self.assertGreater(answer.bounding_box()["height"], 30)
            question.click()
            expect(answer).to_have_attribute("aria-hidden", "true")
        questions.first.focus()
        questions.first.press("ArrowDown")
        expect(questions.nth(1)).to_be_focused()

    def test_form_existing_validation_and_confirmation(self):
        self.page.locator("#sendBtn").click()
        for error in ["eName", "eEmail", "ePick"]:
            expect(self.page.locator(f"#{error}")).to_be_visible()
        self.page.locator("#fName").fill("Ada Lovelace")
        self.page.locator("#fEmail").fill("ada@example.com")
        self.page.locator('#pickWrap label').first.click()
        self.page.locator("#fMsg").fill("A short writing sample.")
        expect(self.page.locator("#msgCount")).to_have_text("4 words")
        self.page.locator("#sendBtn").click()
        expect(self.page.locator("#sentMsg")).to_contain_text("Thanks Ada.")
        expect(self.page.locator("#sendBtn")).to_have_text("Sent")

    def test_mobile_menu(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        burger = self.page.locator("#burger")
        burger.click()
        expect(self.page.locator("#mobileMenu")).to_be_visible()
        burger.press("Escape")
        expect(burger).to_have_attribute("aria-expanded", "false")
        expect(burger).to_be_focused()
        burger.click()
        self.page.locator('#mobileMenu [data-goto="pricing"]').click()
        expect(burger).to_have_attribute("aria-expanded", "false")
        self.assertLess(abs(self.page.locator("#pricing").bounding_box()["y"] - 96), 3)
        burger.click()
        self.page.set_viewport_size({"width": 1440, "height": 1000})
        expect(self.page.locator("#mobileMenu")).not_to_be_visible()

    def test_section_rail_and_skip_link(self):
        rail_button = self.page.locator('#sectionRail [data-goto="quality"]')
        rail_button.click()
        expect(rail_button).to_have_attribute("aria-current", "location")
        expect(self.page.locator('#navLinks [data-goto="quality"]')).to_have_attribute(
            "aria-current", "location"
        )
        self.page.locator(".skip").focus()
        self.page.locator(".skip").press("Enter")
        expect(self.page.locator("#main")).to_be_focused()

    def test_responsive_layout_and_previews(self):
        for width in [320, 360, 390, 620, 768, 900, 1024, 1280, 1440, 1920]:
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 1000})
                self.page.evaluate("window.scrollTo(0, 0)")
                overflow = self.page.evaluate(
                    "document.documentElement.scrollWidth > window.innerWidth"
                )
                self.assertFalse(overflow, f"Horizontal page overflow at {width}px")
                for selector in ["#heroTitle", ".draft", ".form-card"]:
                    box = self.page.locator(selector).bounding_box()
                    self.assertGreaterEqual(box["x"], -2)
                    self.assertLessEqual(box["x"] + box["width"], width + 2)
        directory = os.environ.get("GHOSTWEB_SCREENSHOTS")
        if directory:
            output = Path(directory)
            output.mkdir(parents=True, exist_ok=True)
            for label, width in [("desktop", 1440), ("mobile", 390)]:
                self.page.set_viewport_size({"width": width, "height": 1000})
                self.page.evaluate("window.scrollTo(0, 0)")
                self.page.screenshot(path=str(output / f"{label}.png"), full_page=True)

    def test_no_javascript_content_is_readable(self):
        context = self.browser.new_context(java_script_enabled=False)
        try:
            page = context.new_page()
            page.goto(self.url)
            expect(page.locator("#servicesTitle")).to_be_visible()
            self.assertEqual(page.locator(".rv").first.evaluate(
                "el => getComputedStyle(el).opacity"
            ), "1")
        finally:
            context.close()

    def test_default_motion_finishes_typing(self):
        context = self.browser.new_context(reduced_motion="no-preference")
        try:
            page = context.new_page()
            page.goto(self.url)
            expect(page.locator("#typeTarget")).to_contain_text(
                "The price was never the problem.", timeout=20000
            )
            expect(page.locator("#draftWords")).to_have_text("31 words")
        finally:
            context.close()


if __name__ == "__main__":
    unittest.main()
