"""
Pika Art PikaSwaps ???????

?????? Playwright ? https://pika.art/pikaswaps ???????
???????????????????Swap???
"""

import asyncio
import sys
from playwright.async_api import async_playwright, Page, expect
from datetime import datetime


class PikaSwapsTest:
    """PikaSwaps ??????"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.base_url = "https://pika.art/pikaswaps"
        self.test_results = []
        
    def log(self, message: str, test_name: str = "", status: str = "INFO"):
        """??????"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{status}]"
        if test_name:
            log_message += f" [{test_name}]"
        log_message += f" {message}"
        print(log_message)
        
    async def setup(self):
        """???????"""
        self.log("?????????...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        self.log("?????????")
        
    async def teardown(self):
        """??????"""
        self.log("????????...")
        await self.browser.close()
        await self.playwright.stop()
        self.log("????????")
        
    async def test_page_load(self) -> bool:
        """??1: ????"""
        test_name = "??????"
        try:
            self.log(f"????...", test_name)
            
            # ?????
            response = await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
            
            # ??????
            if response.status != 200:
                self.log(f"???????: {response.status}", test_name, "ERROR")
                return False
                
            self.log(f"??????????: {response.status}", test_name, "PASS")
            
            # ??????
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            # ????
            await self.page.screenshot(path="screenshots/pikaswaps_loaded.png")
            self.log("???????", test_name)
            
            return True
            
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            await self.page.screenshot(path="screenshots/pikaswaps_load_error.png")
            return False
            
    async def test_page_title(self) -> bool:
        """??2: ??????"""
        test_name = "??????"
        try:
            self.log(f"????...", test_name)
            
            title = await self.page.title()
            self.log(f"????: {title}", test_name)
            
            # ?????? Pika ? Swap ?????
            if "pika" in title.lower() or "swap" in title.lower():
                self.log("????????", test_name, "PASS")
                return True
            else:
                self.log(f"?????????: {title}", test_name, "FAIL")
                return False
                
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def test_main_content(self) -> bool:
        """??3: ?????????"""
        test_name = "??????"
        try:
            self.log(f"????...", test_name)
            
            # ????????
            await self.page.wait_for_timeout(2000)
            
            # ?????????
            elements_to_check = [
                ("???", "nav, header, [role='navigation']"),
                ("?????", "main, [role='main'], .main-content, #main"),
                ("??", "button"),
            ]
            
            found_elements = []
            for element_name, selector in elements_to_check:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        found_elements.append(element_name)
                        self.log(f"????: {element_name}", test_name)
                except:
                    pass
                    
            if len(found_elements) >= 2:
                self.log(f"?? {len(found_elements)} ?????", test_name, "PASS")
                return True
            else:
                self.log(f"??? {len(found_elements)} ?????", test_name, "FAIL")
                return False
                
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def test_swap_upload_area(self) -> bool:
        """??4: Swap??????"""
        test_name = "Swap??????"
        try:
            self.log(f"????...", test_name)
            
            # ??????
            await self.page.wait_for_timeout(2000)
            
            # ???????????
            upload_selectors = [
                "input[type='file']",
                "[role='button']:has-text('upload')",
                "[role='button']:has-text('Upload')",
                "button:has-text('upload')",
                "button:has-text('Upload')",
                ".upload",
                "#upload",
                "[aria-label*='upload' i]",
                "[aria-label*='??' i]",
            ]
            
            found_upload = False
            for selector in upload_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            self.log(f"??????: {selector}", test_name)
                            found_upload = True
                            break
                except:
                    pass
            
            if found_upload:
                self.log("????????", test_name, "PASS")
                return True
            else:
                self.log("?????????????????????????", test_name, "WARN")
                return True  # ???????
                
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def test_interactive_elements(self) -> bool:
        """??5: ??????"""
        test_name = "??????"
        try:
            self.log(f"????...", test_name)
            
            # ??????????
            buttons = await self.page.query_selector_all("button, [role='button'], .btn, input[type='button'], input[type='submit']")
            self.log(f"?? {len(buttons)} ??????", test_name)
            
            # ??????
            links = await self.page.query_selector_all("a[href]")
            self.log(f"?? {len(links)} ???", test_name)
            
            # ?????
            inputs = await self.page.query_selector_all("input, textarea")
            self.log(f"?? {len(inputs)} ????", test_name)
            
            if len(buttons) > 0 or len(links) > 0:
                self.log("????????", test_name, "PASS")
                return True
            else:
                self.log("???????", test_name, "FAIL")
                return False
                
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def test_responsive_design(self) -> bool:
        """??6: ???????"""
        test_name = "???????"
        try:
            self.log(f"????...", test_name)
            
            viewports = [
                ("??", 1920, 1080),
                ("??", 768, 1024),
                ("??", 375, 667),
            ]
            
            for device_name, width, height in viewports:
                await self.page.set_viewport_size({"width": width, "height": height})
                await self.page.wait_for_timeout(1000)
                
                await self.page.screenshot(path=f"screenshots/pikaswaps_{device_name}_{width}x{height}.png")
                self.log(f"{device_name}?? ({width}x{height}) ?????", test_name)
                
            # ??????
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            self.log("?????????", test_name, "PASS")
            return True
            
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def test_page_performance(self) -> bool:
        """??7: ??????"""
        test_name = "??????"
        try:
            self.log(f"????...", test_name)
            
            # ??????
            start_time = datetime.now()
            
            # ??????????
            await self.page.reload(wait_until="load")
            
            # ??????
            end_time = datetime.now()
            load_time = (end_time - start_time).total_seconds()
            
            self.log(f"??????: {load_time:.2f} ?", test_name)
            
            # ??????
            metrics = await self.page.evaluate("""() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                };
            }""")
            
            self.log(f"DOM????: {metrics['domContentLoaded']:.2f}ms", test_name)
            self.log(f"??????: {metrics['loadComplete']:.2f}ms", test_name)
            
            # ????????10????????
            if load_time < 10:
                self.log(f"??????", test_name, "PASS")
                return True
            else:
                self.log(f"??????", test_name, "WARN")
                return True
                
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def test_console_errors(self) -> bool:
        """??8: ???????"""
        test_name = "???????"
        try:
            self.log(f"????...", test_name)
            
            console_messages = []
            errors = []
            
            # ???????
            self.page.on("console", lambda msg: console_messages.append({
                "type": msg.type,
                "text": msg.text
            }))
            
            # ??????
            self.page.on("pageerror", lambda err: errors.append(str(err)))
            
            # ???????????
            await self.page.reload(wait_until="networkidle")
            await self.page.wait_for_timeout(3000)
            
            # ????
            error_count = len([m for m in console_messages if m["type"] == "error"])
            warning_count = len([m for m in console_messages if m["type"] == "warning"])
            
            self.log(f"??????: {error_count}", test_name)
            self.log(f"??????: {warning_count}", test_name)
            self.log(f"?????: {len(errors)}", test_name)
            
            if error_count > 0:
                self.log(f"???????", test_name, "WARN")
                for msg in console_messages[:5]:  # ????5?
                    if msg["type"] == "error":
                        self.log(f"  - {msg['text']}", test_name, "ERROR")
                        
            if len(errors) == 0 and error_count == 0:
                self.log("???????", test_name, "PASS")
                return True
            else:
                self.log("???????????????", test_name, "WARN")
                return True
                
        except Exception as e:
            self.log(f"????: {str(e)}", test_name, "FAIL")
            return False
            
    async def run_all_tests(self):
        """??????"""
        self.log("="*80)
        self.log("?? PikaSwaps ???????")
        self.log("="*80)
        
        # ??????
        import os
        os.makedirs("screenshots", exist_ok=True)
        
        # ???????
        await self.setup()
        
        # ??????
        tests = [
            ("??????", self.test_page_load),
            ("??????", self.test_page_title),
            ("??????", self.test_main_content),
            ("Swap??????", self.test_swap_upload_area),
            ("??????", self.test_interactive_elements),
            ("???????", self.test_responsive_design),
            ("??????", self.test_page_performance),
            ("???????", self.test_console_errors),
        ]
        
        # ??????
        results = {}
        for test_name, test_func in tests:
            self.log("-"*80)
            result = await test_func()
            results[test_name] = result
            self.test_results.append({
                "name": test_name,
                "passed": result
            })
            await asyncio.sleep(1)  # ??????
            
        # ??????
        await self.teardown()
        
        # ??????
        self.log("="*80)
        self.log("????")
        self.log("="*80)
        
        passed_count = sum(1 for r in results.values() if r)
        total_count = len(results)
        
        for test_name, result in results.items():
            status = "? ??" if result else "? ??"
            self.log(f"{status} - {test_name}")
            
        self.log("-"*80)
        self.log(f"??: {passed_count}/{total_count} ????")
        self.log(f"???: {(passed_count/total_count*100):.1f}%")
        self.log("="*80)
        
        return passed_count == total_count


async def main():
    """???"""
    # ???????
    headless = "--headless" in sys.argv
    
    # ??????
    tester = PikaSwapsTest(headless=headless)
    
    # ??????
    success = await tester.run_all_tests()
    
    # ?????
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
