"""Search provider implementations: DuckDuckGo HTML, Local Browser, Manual fallback."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import html
from html.parser import HTMLParser
import time
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.models.schemas import ManualSearchSubmitRequest, SearchResult


@dataclass(slots=True)
class ProviderResult:
    status: str
    provider: str
    results: list[SearchResult]
    detail: str = ""
    manual_instructions: str | None = None


class SearchProvider:
    name: str

    async def search(self, query: str, num_results: int, safe: bool) -> ProviderResult:  # pragma: no cover - interface
        raise NotImplementedError


class _DuckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.current_title = ""
        self.current_url = ""
        self.pending_snippet = ""
        self.results: list[SearchResult] = []
        self.rank = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = attr.get("class", "")
        if tag == "a" and "result__a" in classes:
            self.in_title = True
            self.current_title = ""
            self.current_url = _normalize_duck_url(attr.get("href", "") or "")
        if tag == "a" and "result__snippet" in classes:
            self.pending_snippet = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_title and self.current_title and self.current_url:
            self.results.append(
                SearchResult(
                    title=self.current_title.strip(),
                    url=self.current_url.strip(),
                    snippet=self.pending_snippet.strip(),
                    source_name="duckduckgo_html",
                    rank=self.rank,
                )
            )
            self.rank += 1
            self.in_title = False
            self.pending_snippet = ""

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.current_title += html.unescape(data)
        elif data.strip() and self.rank > 1:
            # Best-effort snippet extraction for the latest added row.
            self.pending_snippet = (self.pending_snippet + " " + html.unescape(data)).strip()


def _normalize_duck_url(raw: str) -> str:
    if raw.startswith("/l/?"):
        parsed = urlparse(raw)
        query = parse_qs(parsed.query).get("uddg", [])
        if query:
            return unquote(query[0])
    return raw


class DuckDuckGoHtmlProvider(SearchProvider):
    name = "duckduckgo_html"
    _last_call = 0.0

    async def search(self, query: str, num_results: int, safe: bool) -> ProviderResult:
        now = time.time()
        delay = 0.8 - (now - self._last_call)
        if delay > 0:
            await asyncio.sleep(delay)
        self._last_call = time.time()

        safe_param = "1" if safe else "-1"
        data = {"q": query, "kp": safe_param}
        headers = {"User-Agent": "NeroAI/1.0 (Windows; privacy-focused)"}
        url = "https://html.duckduckgo.com/html/"
        last_error = ""
        for _ in range(2):
            try:
                async with httpx.AsyncClient(timeout=12) as client:
                    resp = await client.post(url, data=data, headers=headers, follow_redirects=True)
                if resp.status_code >= 400:
                    last_error = f"HTTP {resp.status_code}"
                    continue
                parser = _DuckParser()
                parser.feed(resp.text)
                if parser.results:
                    return ProviderResult(status="ok", provider=self.name, results=parser.results[:num_results], detail="ok")
                last_error = "No parseable results returned."
            except Exception as exc:
                last_error = str(exc)
        return ProviderResult(
            status="error",
            provider=self.name,
            results=[],
            detail=f"DuckDuckGo search failed: {last_error}",
        )


class LocalBrowserProvider(SearchProvider):
    name = "local_browser"

    def __init__(self, headed: bool = True, engine: str = "chrome") -> None:
        self.headed = headed
        self.engine = engine

    async def search(self, query: str, num_results: int, safe: bool) -> ProviderResult:
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            return ProviderResult(status="error", provider=self.name, results=[], detail=f"Playwright unavailable: {exc}")

        try:
            async with async_playwright() as p:
                browser_type = p.chromium
                launch_channel = "chrome" if self.engine == "chrome" else None
                browser = await browser_type.launch(channel=launch_channel, headless=not self.headed)
                page = await browser.new_page()
                await page.goto("https://duckduckgo.com", timeout=20_000)
                await page.fill("input[name='q']", query)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                body_text = (await page.text_content("body")) or ""
                if "captcha" in body_text.lower() or "robot" in body_text.lower():
                    await browser.close()
                    return ProviderResult(
                        status="error",
                        provider=self.name,
                        results=[],
                        detail="CAPTCHA/bot check detected. Use Manual provider.",
                    )

                links = await page.query_selector_all("a[data-testid='result-title-a'], h2 a")
                results: list[SearchResult] = []
                rank = 1
                for link in links:
                    href = await link.get_attribute("href")
                    title = (await link.inner_text()) or ""
                    if not href or not title.strip():
                        continue
                    results.append(
                        SearchResult(
                            title=title.strip(),
                            url=href.strip(),
                            snippet="",
                            source_name=self.name,
                            rank=rank,
                        )
                    )
                    rank += 1
                    if len(results) >= num_results:
                        break
                await browser.close()
                if not results:
                    return ProviderResult(
                        status="error",
                        provider=self.name,
                        results=[],
                        detail="Could not parse browser results. Use Manual provider.",
                    )
                return ProviderResult(status="ok", provider=self.name, results=results, detail="ok")
        except Exception as exc:
            return ProviderResult(status="error", provider=self.name, results=[], detail=f"Local browser search failed: {exc}")


class ManualFallbackProvider(SearchProvider):
    name = "manual"

    async def search(self, query: str, num_results: int, safe: bool) -> ProviderResult:
        return ProviderResult(
            status="manual_required",
            provider=self.name,
            results=[],
            detail="Manual input required.",
            manual_instructions=(
                "Paste JSON array of {title,url,snippet} OR newline URLs with optional snippet text."
            ),
        )

    def parse_manual(self, payload: ManualSearchSubmitRequest) -> ProviderResult:
        if payload.json_results:
            return ProviderResult(status="ok", provider=self.name, results=payload.json_results, detail="manual_json")

        lines = (payload.pasted_lines or "").splitlines()
        results: list[SearchResult] = []
        rank = 1
        for line in lines:
            row = line.strip()
            if not row:
                continue
            if row.startswith("http://") or row.startswith("https://"):
                results.append(SearchResult(title=row, url=row, snippet="", source_name=self.name, rank=rank))
                rank += 1
                continue
            if "|" in row:
                parts = [x.strip() for x in row.split("|")]
                if len(parts) >= 2 and parts[1].startswith(("http://", "https://")):
                    snippet = parts[2] if len(parts) >= 3 else ""
                    results.append(
                        SearchResult(
                            title=parts[0],
                            url=parts[1],
                            snippet=snippet,
                            source_name=self.name,
                            rank=rank,
                        )
                    )
                    rank += 1
        if not results:
            return ProviderResult(
                status="error",
                provider=self.name,
                results=[],
                detail="Invalid manual input. Provide JSON list or URL lines.",
            )
        return ProviderResult(status="ok", provider=self.name, results=results, detail="manual_text")
