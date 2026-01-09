#!/usr/bin/env python3
"""
Discover NotebookLM Notebooks
Automatically discovers all notebooks from your Google NotebookLM account
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

from patchright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import BrowserFactory, StealthUtils
from config import STATE_FILE, BROWSER_ARGS, USER_AGENT


class NotebookDiscovery:
    """Discovers notebooks from NotebookLM account"""

    def __init__(self, show_browser: bool = False):
        """Initialize discovery"""
        self.show_browser = show_browser
        self.stealth = StealthUtils()

    def discover(self) -> List[Dict[str, Any]]:
        """
        Discover all notebooks from NotebookLM account

        Returns:
            List of notebooks with name and URL
        """
        print("🔍 Discovering notebooks from your NotebookLM account...")

        # Check if authenticated
        if not STATE_FILE.exists():
            raise RuntimeError(
                "❌ Not authenticated. Please run: python scripts/run.py auth_manager.py setup"
            )

        playwright = None
        context = None
        page = None

        try:
            playwright = sync_playwright().start()

            # Launch using factory (same as auth_manager)
            context = BrowserFactory.launch_persistent_context(
                playwright,
                headless=not self.show_browser
            )

            page = context.new_page()

            try:
                print("  🌐 Navigating to NotebookLM home...")
                page.goto("https://notebooklm.google.com", wait_until="domcontentloaded", timeout=30000)

                # Check if login is needed
                if "accounts.google.com" in page.url:
                    raise RuntimeError("❌ Authentication expired. Please run: python scripts/run.py auth_manager.py reauth")

                # Wait for page to load
                print("  ⏳ Waiting for page to load...")
                time.sleep(3)

                # Click on "我的笔记本" (My Notebooks) tab
                print("  📑 Switching to '我的笔记本' tab...")
                try:
                    # Try to find and click the "我的笔记本" tab
                    my_notebooks_selectors = [
                        'text="我的笔记本"',
                        'button:has-text("我的笔记本")',
                        '[role="tab"]:has-text("我的笔记本")',
                    ]

                    clicked = False
                    for selector in my_notebooks_selectors:
                        try:
                            tab = page.wait_for_selector(selector, timeout=3000)
                            if tab:
                                tab.click()
                                print("    ✓ Switched to 我的笔记本")
                                clicked = True
                                time.sleep(2)
                                break
                        except:
                            continue

                    if not clicked:
                        print("    ⚠️ Could not find '我的笔记本' tab, using current view")

                except Exception as e:
                    print(f"    ⚠️ Error switching tabs: {e}")

                # Scroll down multiple times to load ALL notebooks
                print("  📜 Scrolling to load all notebooks...")
                for i in range(5):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.5)
                    print(f"    Scroll {i+1}/5")

                # Scroll back to top
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)

                # Try multiple selectors to find notebooks
                notebooks = []

                # Method 1: Use project-button class to find notebooks directly
                try:
                    print("  🔍 Searching for notebook cards...")

                    # Find all project buttons
                    project_buttons = page.query_selector_all('.project-button')
                    print(f"    Found {len(project_buttons)} project buttons")

                    for i, button in enumerate(project_buttons):
                        try:
                            # Extract title from project-button-title class
                            title_elem = button.query_selector('.project-button-title')
                            if not title_elem:
                                continue

                            title = title_elem.inner_text().strip()
                            if not title or len(title) < 3:
                                continue

                            print(f"  {i+1}. {title[:60]}")

                            # Click the button to get URL
                            current_url = page.url
                            button.scroll_into_view_if_needed()
                            time.sleep(0.3)

                            button.click(timeout=3000)
                            time.sleep(2)

                            new_url = page.url
                            if new_url != current_url and "/notebook/" in new_url:
                                print(f"     ✓ {new_url}")
                                notebooks.append({
                                    "name": title,
                                    "url": new_url
                                })

                                # Go back
                                page.go_back(wait_until="domcontentloaded")
                                time.sleep(2)
                            else:
                                print(f"     ⚠️ No URL change")

                        except Exception as e:
                            print(f"     ⚠️ Error: {str(e)[:50]}")
                            # Make sure we're back on the list page
                            if "/notebook/" in page.url:
                                page.go_back(wait_until="domcontentloaded")
                                time.sleep(2)

                except Exception as e:
                    print(f"    ⚠️ Project button method failed: {e}")

                # Method 2: Fallback - JavaScript extraction
                if not notebooks:
                    print("  🔄 Trying JavaScript extraction as fallback...")
                        try:
                            href = link.get_attribute("href")
                            if not href or "/notebook/" not in href:
                                continue

                            # Get full URL
                            if href.startswith("/"):
                                url = f"https://notebooklm.google.com{href}"
                            else:
                                url = href

                            # Skip duplicates
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)

                            # Try to get notebook title from various sources
                            title = None

                            # Method 1: Look for aria-label
                            aria_label = link.get_attribute("aria-label")
                            if aria_label:
                                title = aria_label.strip()

                            # Method 2: Try getting text from descendant elements
                            if not title:
                                # Try to find title in child divs/spans
                                title_candidates = link.query_selector_all('div, span, h1, h2, h3, h4')
                                for candidate in title_candidates:
                                    text = candidate.inner_text().strip()
                                    if text and 5 < len(text) < 100 and '\n' not in text:
                                        title = text
                                        break

                            # Method 3: Try getting direct text
                            if not title:
                                text = link.inner_text().strip()
                                lines = [l.strip() for l in text.split('\n') if l.strip()]
                                if lines:
                                    title = lines[0]

                            # Fallback: extract from URL
                            if not title or len(title) > 100:
                                notebook_id = url.split("/notebook/")[-1].split("?")[0]
                                title = f"Notebook {notebook_id[:8]}"

                            notebooks.append({
                                "name": title,
                                "url": url
                            })
                            print(f"    ✓ Found: {title}")

                        except Exception as e:
                            print(f"    ⚠️ Error processing link: {e}")
                            continue

                except Exception as e:
                    print(f"    ⚠️ Method 1 failed: {e}")

                # Method 2: Use JavaScript to extract notebook information
                if not notebooks:
                    print("  🔄 Trying JavaScript extraction method...")

                    try:
                        # Use JavaScript to find all notebook cards and extract their info
                        notebook_data = page.evaluate("""() => {
                            const notebooks = [];
                            const allElements = document.querySelectorAll('*');

                            // Find elements that look like notebook cards
                            // They have a title and "个来源" text
                            const cardElements = [];

                            for (const elem of allElements) {
                                const text = elem.innerText || '';
                                if (text.includes('个来源') && text.split('\\n').length >= 2) {
                                    // This might be a card
                                    const lines = text.split('\\n').filter(l => l.trim());
                                    if (lines.length >= 2) {
                                        const possibleTitle = lines.find(l => !l.includes('个来源') && !l.match(/^\\d{4}年/));
                                        if (possibleTitle && possibleTitle.length > 3 && possibleTitle.length < 150) {
                                            cardElements.push({
                                                element: elem,
                                                title: possibleTitle,
                                                text: text
                                            });
                                        }
                                    }
                                }
                            }

                            // Deduplicate by title
                            const seen = new Set();
                            const unique = [];
                            for (const card of cardElements) {
                                if (!seen.has(card.title)) {
                                    seen.add(card.title);
                                    unique.push(card);
                                }
                            }

                            return unique.map(c => ({ title: c.title, text: c.text }));
                        }""")

                        print(f"  🔍 JavaScript found {len(notebook_data)} unique notebooks")

                        # Now try to click each one
                        for i, nb_info in enumerate(notebook_data):
                            title = nb_info['title']
                            print(f"  {i+1}. {title[:60]}")

                            try:
                                current_url = page.url

                                # Try to find and click element with this title
                                try:
                                    # Find element containing exact title
                                    elements = page.query_selector_all(f'text="{title}"')
                                    if not elements:
                                        # Try partial match
                                        elements = page.query_selector_all(f'text=/{title[:20]}/')

                                    if elements:
                                        # Try clicking first match
                                        elem = elements[0]

                                        # Find parent card (might need to go up a few levels)
                                        clickable = elem
                                        for _ in range(5):
                                            parent = clickable.query_selector('..')
                                            if parent:
                                                clickable = parent
                                            else:
                                                break

                                        clickable.scroll_into_view_if_needed()
                                        time.sleep(0.3)
                                        clickable.click(timeout=2000)
                                        time.sleep(1.5)

                                        new_url = page.url
                                        if new_url != current_url and "/notebook/" in new_url:
                                            print(f"     ✓ {new_url}")
                                            notebooks.append({
                                                "name": title,
                                                "url": new_url
                                            })

                                            # Go back
                                            page.go_back(wait_until="domcontentloaded")
                                            time.sleep(1.5)
                                        else:
                                            print(f"     ⚠️ No URL change")
                                except Exception as e:
                                    print(f"     ⚠️ Click error: {str(e)[:40]}")
                                    if "/notebook/" in page.url:
                                        page.go_back(wait_until="domcontentloaded")
                                        time.sleep(1.5)

                            except Exception as e:
                                continue

                    except Exception as e:
                        print(f"    ⚠️ JavaScript method failed: {e}")

                # Method 3: Debug - dump page HTML for analysis
                if not notebooks and self.show_browser:
                    print("  🐛 Dumping page HTML for analysis...")
                    html_content = page.content()
                    with open("/tmp/notebooklm_page.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print("  💡 HTML saved to /tmp/notebooklm_page.html")

                    print("  📸 Taking screenshot for manual inspection...")
                    page.screenshot(path="/tmp/notebooklm_home.png")
                    print("  💡 Screenshot saved to /tmp/notebooklm_home.png")

                    # Try to inspect some elements
                    print("  🔍 Analyzing page structure...")
                    # Look for any clickable cards
                    result = page.evaluate("""() => {
                        // Find all divs and check their structure
                        const allDivs = Array.from(document.querySelectorAll('div'));
                        const info = [];

                        for (const div of allDivs) {
                            const text = div.innerText || '';
                            // Look for elements that might be notebook cards
                            if (text.includes('个来源') && text.length < 200 && text.length > 10) {
                                const classes = div.className;
                                const onclick = div.onclick ? 'has onclick' : 'no onclick';
                                const role = div.getAttribute('role') || 'no role';
                                info.push({
                                    text: text.substring(0, 100),
                                    classes: classes,
                                    onclick: onclick,
                                    role: role,
                                    tagName: div.tagName
                                });
                            }
                        }

                        return info.slice(0, 5);  // First 5 matches
                    }""")

                    for i, elem_info in enumerate(result):
                        print(f"  Card {i+1}:")
                        print(f"    Text: {elem_info['text'][:60]}")
                        print(f"    Classes: {elem_info['classes'][:60] if elem_info['classes'] else 'none'}")
                        print(f"    Role: {elem_info['role']}")
                        print(f"    OnClick: {elem_info['onclick']}")

                if notebooks:
                    print(f"\n✅ Found {len(notebooks)} notebooks!")
                    for i, nb in enumerate(notebooks, 1):
                        print(f"  {i}. {nb['name']}")
                    return notebooks
                else:
                    print("\n⚠️ No notebooks found.")
                    print("  💡 Possible reasons:")
                    print("     - You don't have any notebooks yet")
                    print("     - The page structure changed (please report this)")
                    print("     - Notebooks are still loading")

                    if not self.show_browser:
                        print("\n  💡 Try running with --show-browser to see what's happening:")
                        print("     python scripts/run.py discover_notebooks.py --show-browser")

                    return []

            except Exception as e:
                print(f"\n❌ Error discovering notebooks: {e}")

                if not self.show_browser:
                    print("\n  💡 Try running with --show-browser to debug:")
                    print("     python scripts/run.py discover_notebooks.py --show-browser")

                raise

        finally:
            if page:
                try:
                    page.close()
                except:
                    pass
            if context:
                try:
                    context.close()
                except:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except:
                    pass


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description='Discover NotebookLM notebooks')
    parser.add_argument('--show-browser', action='store_true', help='Show browser window')
    parser.add_argument('--add-all', action='store_true', help='Add all discovered notebooks to library')

    args = parser.parse_args()

    try:
        discovery = NotebookDiscovery(show_browser=args.show_browser)
        notebooks = discovery.discover()

        if not notebooks:
            print("\n📚 No notebooks to add.")
            return

        if args.add_all:
            print("\n📚 Adding notebooks to library...")
            from notebook_manager import NotebookLibrary

            library = NotebookLibrary()

            for nb in notebooks:
                try:
                    # Check if already in library
                    existing = [n for n in library.list_notebooks() if n['url'] == nb['url']]
                    if existing:
                        print(f"  ⏭️  Skipping {nb['name']} (already in library)")
                        continue

                    # Add with minimal info (can be enriched later)
                    library.add_notebook(
                        url=nb['url'],
                        name=nb['name'],
                        description=f"Discovered from NotebookLM account",
                        topics=["discovered"]
                    )
                    print(f"  ✅ Added: {nb['name']}")

                except Exception as e:
                    print(f"  ❌ Failed to add {nb['name']}: {e}")

            print("\n✅ Done! Use 'python scripts/run.py notebook_manager.py list' to see your library")
        else:
            print("\n💡 To add these notebooks to your library, run:")
            print("   python scripts/run.py discover_notebooks.py --add-all")

    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
