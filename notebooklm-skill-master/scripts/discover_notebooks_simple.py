#!/usr/bin/env python3
"""
Simple NotebookLM Notebook Discovery
Uses project-button class to find and extract notebooks
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

from patchright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from browser_utils import BrowserFactory
from config import STATE_FILE


def discover_notebooks(show_browser: bool = False) -> List[Dict[str, Any]]:
    """Discover all notebooks from NotebookLM account"""

    if not STATE_FILE.exists():
        raise RuntimeError(
            "❌ Not authenticated. Please run: python scripts/run.py auth_manager.py setup"
        )

    print("🔍 Discovering notebooks from your NotebookLM account...")

    playwright = None
    context = None
    page = None
    notebooks = []

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=not show_browser)
        page = context.new_page()

        # Navigate to NotebookLM
        print("  🌐 Navigating to NotebookLM...")
        page.goto("https://notebooklm.google.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # Switch to "我的笔记本" tab
        print("  📑 Switching to '我的笔记本' tab...")
        try:
            tab = page.wait_for_selector('text="我的笔记本"', timeout=5000)
            if tab:
                tab.click()
                print("    ✓ Switched")
                time.sleep(2)
        except:
            print("    ⚠️ Using current view")

        # Wait for content to load
        print("  ⏳ Waiting for notebooks to fully load...")
        try:
            page.wait_for_selector('.project-button-card', timeout=10000)
            print("    ✓ Cards loaded")
        except:
            print("    ⚠️ Timeout waiting for cards, trying anyway")

        # Scroll to load all notebooks
        print("  📜 Scrolling to load all notebooks...")
        for i in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)

        # Debug: check what's actually on the page
        if show_browser:
            card_count = page.evaluate("document.querySelectorAll('.project-button-card').length")
            button_count = page.evaluate("document.querySelectorAll('.project-button').length")
            print(f"  🐛 Debug: {card_count} cards, {button_count} buttons on page")

        # Extract notebook data using JavaScript (no clicking needed!)
        print("  🔍 Extracting notebook data...")

        notebook_data = page.evaluate("""() => {
            const notebooks = [];
            const cards = document.querySelectorAll('.project-button-card');
            const debug = [];

            for (const card of cards) {
                try {
                    debug.push('processing card');
                    // Get title - try multiple selectors
                    let titleElem = card.querySelector('.project-button-title');
                    if (!titleElem) {
                        // Try other possible selectors
                        titleElem = card.querySelector('[class*="title"]');
                    }
                    if (!titleElem) {
                        // Try just getting all text
                        const text = card.innerText || card.textContent || '';
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                        const title = lines.find(l => l.length > 3 && l.length < 100 && !l.includes('个来源'));
                        if (title) {
                            notebooks.push({title: title, method: 'text-parse'});
                        }
                        continue;
                    }

                    const title = titleElem.innerText.trim();
                    if (!title || title.length < 3) continue;

                    // Try to find notebook ID from parent elements or click handlers
                    const button = card.querySelector('.project-button');
                    if (!button) continue;

                    // Check for onclick attribute or data attributes
                    const onclick = button.getAttribute('onclick') || '';
                    const dataId = button.getAttribute('data-notebook-id') ||
                                   button.getAttribute('data-project-id') || '';

                    // Also check parent button wrapper
                    let notebookId = dataId;

                    // Try to get from parent chain
                    let parent = card;
                    for (let i = 0; i < 10; i++) {
                        parent = parent.parentElement;
                        if (!parent) break;

                        const id = parent.getAttribute('data-notebook-id') ||
                                   parent.getAttribute('data-project-id') ||
                                   parent.getAttribute('data-id') || '';
                        if (id) {
                            notebookId = id;
                            break;
                        }
                    }

                    notebooks.push({
                        title: title,
                        onclick: onclick.substring(0, 200),
                        notebookId: notebookId,
                        html: card.innerHTML.substring(0, 500)
                    });

                } catch (e) {
                    debug.push('error: ' + e.message);
                }
            }

            return {notebooks: notebooks, debug: debug, cardCount: cards.length};
        }""")

        # Handle new return format
        if isinstance(notebook_data, dict):
            print(f"    🐛 Debug: {notebook_data.get('debug', [])[:5]}")
            print(f"    🐛 Card count: {notebook_data.get('cardCount', 0)}")
            actual_notebooks = notebook_data.get('notebooks', [])
        else:
            actual_notebooks = notebook_data

        print(f"    Found {len(actual_notebooks)} notebooks with titles")

        # For now, let's just try clicking one by one with a fresh query each time
        print("  🔍 Getting URLs by clicking (one at a time)...")

        for i in range(len(actual_notebooks)):
            try:
                nb = actual_notebooks[i]
                title = nb['title']
                print(f"  {i+1}. {title[:70]}")

                # Fresh query each time to avoid stale elements
                cards = page.query_selector_all('.project-button-card')
                if i >= len(cards):
                    print(f"     ⚠️ Card index out of range")
                    continue

                card = cards[i]
                current_url = page.url

                # Click
                try:
                    card.click(timeout=2000, force=True)  # Force click even if obscured
                    time.sleep(2.5)

                    new_url = page.url
                    if "/notebook/" in new_url and new_url != current_url:
                        print(f"     ✓ {new_url[:70]}...")
                        notebooks.append({"name": title, "url": new_url})

                        # Go back
                        page.go_back(wait_until="domcontentloaded")
                        time.sleep(2)
                    else:
                        print(f"     ⚠️ No navigation")

                except Exception as click_err:
                    print(f"     ⚠️ Click failed: {str(click_err)[:40]}")

            except Exception as e:
                print(f"     ⚠️ Error: {str(e)[:40]}")
                # Make sure we're back
                if "/notebook/" in page.url:
                    page.go_back(wait_until="domcontentloaded")
                    time.sleep(2)

        return notebooks

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--show-browser', action='store_true')
    parser.add_argument('--add-all', action='store_true')
    args = parser.parse_args()

    try:
        notebooks = discover_notebooks(show_browser=args.show_browser)

        if notebooks:
            print(f"\n✅ Found {len(notebooks)} notebooks!")
            for i, nb in enumerate(notebooks, 1):
                print(f"  {i}. {nb['name']}")

            if args.add_all:
                from notebook_manager import NotebookLibrary
                library = NotebookLibrary()

                for nb in notebooks:
                    try:
                        # Check if exists
                        existing = [n for n in library.list_notebooks() if n['url'] == nb['url']]
                        if existing:
                            print(f"  ⏭️  Skipping {nb['name']} (already exists)")
                            continue

                        library.add_notebook(
                            url=nb['url'],
                            name=nb['name'],
                            description=f"Auto-discovered from NotebookLM",
                            topics=["auto-discovered"]
                        )
                        print(f"  ✅ Added: {nb['name']}")
                    except Exception as e:
                        print(f"  ❌ Failed to add {nb['name']}: {e}")
        else:
            print("\n⚠️ No notebooks found")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
