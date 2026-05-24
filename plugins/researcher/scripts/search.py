"""Unified search CLI for Exa and Brave Search APIs.

Run inside the project venv:
    plugins/researcher/.venv/bin/python plugins/researcher/scripts/search.py ...

See SKILL.md / agents/researcher.md for venv setup. Dependencies are tracked
in scripts/requirements.txt (Renovate-managed). Brave has no official Python
SDK; requests is used for their REST API directly.

Subcommands:
    check-keys                          Validate EXA_API_KEY / BRAVE_API_KEY
    exa --query STR [...]               Exa search (see --help for full flags)
    brave --query STR [...]             Brave web/news search
    parallel --query STR [...]          Exa + Brave concurrently

All subcommands output JSON to stdout; errors go to stderr.
Exit code: 0 on success, 1 on error or missing required key.
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(value: Optional[str]) -> Optional[str]:
    """Remove HTML tags from Brave snippets (e.g. <strong>foo</strong> → foo)."""
    if not value:
        return value
    return _HTML_TAG_RE.sub("", value)

EXA_API_KEY = os.environ.get("EXA_API_KEY", "")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BRAVE_BASE_URL = "https://api.search.brave.com/res/v1"


# ---------------------------------------------------------------------------
# check-keys
# ---------------------------------------------------------------------------

def check_keys_cmd(_args) -> int:
    exa_ok = bool(EXA_API_KEY)
    brave_ok = bool(BRAVE_API_KEY)
    status = {
        "exa": "ok" if exa_ok else "missing",
        "brave": "ok" if brave_ok else "missing",
    }
    json.dump(status, sys.stdout)
    sys.stdout.write("\n")

    if not exa_ok and not brave_ok:
        print(
            "ERROR: Neither EXA_API_KEY nor BRAVE_API_KEY is set. At least one is required.\n"
            "  EXA_API_KEY   — https://exa.ai/\n"
            "  BRAVE_API_KEY — https://brave.com/search/api/\n"
            "Set them in your shell environment or in ~/.claude/settings.json under \"env\".",
            file=sys.stderr,
        )
        return 1
    return 0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _split_csv(value: Optional[str]) -> Optional[list[str]]:
    """Split a comma-separated string into a list; None passes through."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _single_item_list(value: Optional[str]) -> Optional[list[str]]:
    """Wrap a single string in a list (Exa include_text/exclude_text accept 1-item arrays only)."""
    if not value:
        return None
    return [value]


def _build_contents(
    *,
    no_text: bool,
    text_max_chars: Optional[int],
    verbosity: Optional[str],
    highlights: bool,
    highlights_query: Optional[str],
    summary: bool,
    summary_query: Optional[str],
    livecrawl_max_age_hours: Optional[int],
    subpages: Optional[int],
    subpage_target: Optional[list[str]],
):
    """Build the `contents` parameter for Exa search/get_contents.

    Returns False to skip all content fetching, or a dict configuration.
    """
    if no_text and not highlights and not summary:
        return False

    contents: dict = {}

    if not no_text:
        text_cfg: dict = {}
        if text_max_chars is not None:
            text_cfg["maxCharacters"] = text_max_chars
        if verbosity:
            text_cfg["verbosity"] = verbosity
        contents["text"] = text_cfg or True

    if highlights:
        hl_cfg: dict = {}
        if highlights_query:
            hl_cfg["query"] = highlights_query
        contents["highlights"] = hl_cfg or True

    if summary:
        sum_cfg: dict = {}
        if summary_query:
            sum_cfg["query"] = summary_query
        contents["summary"] = sum_cfg or True

    if livecrawl_max_age_hours is not None:
        contents["max_age_hours"] = livecrawl_max_age_hours

    if subpages is not None:
        contents["subpages"] = subpages

    if subpage_target:
        contents["subpage_target"] = subpage_target if len(subpage_target) > 1 else subpage_target[0]

    return contents


# ---------------------------------------------------------------------------
# exa
# ---------------------------------------------------------------------------

def _exa_search(
    *,
    query: str,
    category: Optional[str] = None,
    num_results: int = 10,
    search_type: Optional[str] = None,
    include_domains: Optional[list[str]] = None,
    exclude_domains: Optional[list[str]] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    include_text: Optional[list[str]] = None,
    exclude_text: Optional[list[str]] = None,
    user_location: Optional[str] = None,
    additional_queries: Optional[list[str]] = None,
    contents: Any = None,
) -> dict:
    if not EXA_API_KEY:
        print("ERROR: EXA_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    from exa_py import Exa  # noqa: PLC0415

    client = Exa(EXA_API_KEY)
    kwargs: dict = {"num_results": num_results}
    if category:
        kwargs["category"] = category
    if search_type:
        kwargs["type"] = search_type
    if include_domains:
        kwargs["include_domains"] = include_domains
    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains
    if start_published_date:
        kwargs["start_published_date"] = start_published_date
    if end_published_date:
        kwargs["end_published_date"] = end_published_date
    if start_crawl_date:
        kwargs["start_crawl_date"] = start_crawl_date
    if end_crawl_date:
        kwargs["end_crawl_date"] = end_crawl_date
    if include_text:
        kwargs["include_text"] = include_text
    if exclude_text:
        kwargs["exclude_text"] = exclude_text
    if user_location:
        kwargs["user_location"] = user_location
    if additional_queries:
        kwargs["additional_queries"] = additional_queries
    if contents is not None:
        kwargs["contents"] = contents

    response = client.search(query, **kwargs)

    results = []
    for r in response.results:
        item: dict = {
            "url": r.url,
            "title": r.title,
            "published_date": r.published_date,
            "author": r.author,
            "score": r.score,
        }
        # Text content (may be None if contents=False)
        if getattr(r, "text", None):
            item["text"] = r.text[:3000]
        if getattr(r, "highlights", None):
            item["highlights"] = r.highlights
        if getattr(r, "summary", None):
            item["summary"] = r.summary
        results.append(item)

    return {
        "provider": "exa",
        "query": query,
        "category": category,
        "type": search_type,
        "results": results,
    }


def exa_cmd(args) -> int:
    contents = _build_contents(
        no_text=args.no_text,
        text_max_chars=args.text_max_chars,
        verbosity=args.verbosity,
        highlights=args.highlights,
        highlights_query=args.highlights_query,
        summary=args.summary,
        summary_query=args.summary_query,
        livecrawl_max_age_hours=args.livecrawl_max_age_hours,
        subpages=None,
        subpage_target=None,
    )

    result = _exa_search(
        query=args.query,
        category=args.category,
        num_results=args.num_results,
        search_type=args.type,
        include_domains=_split_csv(args.include_domains),
        exclude_domains=_split_csv(args.exclude_domains),
        start_published_date=args.start_published_date,
        end_published_date=args.end_published_date,
        start_crawl_date=args.start_crawl_date,
        end_crawl_date=args.end_crawl_date,
        include_text=_single_item_list(args.include_text),
        exclude_text=_single_item_list(args.exclude_text),
        user_location=args.user_location,
        additional_queries=_split_csv(args.additional_queries),
        contents=contents,
    )
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# brave
# ---------------------------------------------------------------------------

def _brave_search(
    *,
    query: str,
    search_type: str,
    count: int,
    freshness: Optional[str] = None,
    extra_snippets: bool = False,
    result_filter: Optional[str] = None,
    offset: int = 0,
    country: str = "us",
    search_lang: str = "en",
) -> dict:
    if not BRAVE_API_KEY:
        print("ERROR: BRAVE_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    import requests  # noqa: PLC0415

    endpoint = "news" if search_type == "news" else "web"
    # News API supports up to 50 results; Web API is capped at 20.
    max_count = 50 if endpoint == "news" else 20
    params: dict = {
        "q": query,
        "count": min(count, max_count),
        "country": country,
        "search_lang": search_lang,
        "safesearch": "off",
    }
    if freshness:
        params["freshness"] = freshness
    if extra_snippets:
        params["extra_snippets"] = "true"
    if result_filter and endpoint == "web":
        params["result_filter"] = result_filter
    if offset:
        params["offset"] = offset

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }

    resp = requests.get(
        f"{BRAVE_BASE_URL}/{endpoint}/search",
        headers=headers,
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    if endpoint == "web":
        for r in data.get("web", {}).get("results", []):
            item: dict = {
                "url": r.get("url"),
                "title": _strip_html(r.get("title")),
                "description": _strip_html(r.get("description")),
                "published": r.get("published"),
                "source": r.get("profile", {}).get("name"),
            }
            if extra_snippets and r.get("extra_snippets"):
                item["extra_snippets"] = [_strip_html(s) for s in r["extra_snippets"]]
            results.append(item)
    else:
        for r in data.get("results", []):
            item = {
                "url": r.get("url"),
                "title": _strip_html(r.get("title")),
                "description": _strip_html(r.get("description")),
                "age": r.get("age"),
                "source": r.get("profile", {}).get("name"),
            }
            if extra_snippets and r.get("extra_snippets"):
                item["extra_snippets"] = [_strip_html(s) for s in r["extra_snippets"]]
            results.append(item)

    return {"provider": "brave", "query": query, "type": endpoint, "results": results}


def brave_cmd(args) -> int:
    result = _brave_search(
        query=args.query,
        search_type=args.type,
        count=args.count,
        freshness=args.freshness,
        extra_snippets=args.extra_snippets,
        result_filter=args.result_filter,
        offset=args.offset,
        country=args.country,
        search_lang=args.search_lang,
    )
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# parallel (Exa + Brave concurrently via threads)
# ---------------------------------------------------------------------------

def parallel_cmd(args) -> int:
    callables: dict = {}
    if EXA_API_KEY:
        callables["exa"] = lambda: _exa_search(
            query=args.query,
            category=args.category,
            num_results=args.num_results,
            search_type=args.type,
        )
    if BRAVE_API_KEY:
        callables["brave"] = lambda: _brave_search(
            query=args.query,
            search_type="web",
            count=args.count,
            extra_snippets=args.extra_snippets,
            offset=args.offset,
            country=args.country,
            search_lang=args.search_lang,
        )

    if not callables:
        print(
            "ERROR: Neither EXA_API_KEY nor BRAVE_API_KEY is set.",
            file=sys.stderr,
        )
        return 1

    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=len(callables)) as executor:
        futures = {executor.submit(fn): name for name, fn in callables.items()}
        for future, name in futures.items():
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append({"provider": name, "error": str(exc)})

    output: dict = {"results": results}
    if errors:
        output["errors"] = errors

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 1 if errors and not results else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified search CLI for Exa and Brave Search APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check-keys", help="Validate API key environment variables")

    # ----- exa -----
    exa_p = sub.add_parser("exa", help="Search via Exa API")
    exa_p.add_argument("--query", required=True, help="Search query")
    exa_p.add_argument(
        "--category", default=None,
        help="news | research paper | financial report | company | personal site | people | pdf",
    )
    exa_p.add_argument("--num-results", type=int, default=10, metavar="N")
    exa_p.add_argument(
        "--type", default=None, dest="type",
        choices=["auto", "fast", "instant", "deep-lite", "deep", "deep-reasoning"],
        help="Search algorithm. 'deep' / 'deep-reasoning' for high-quality research; 'fast' / 'instant' for low-latency.",
    )
    exa_p.add_argument("--include-domains", default=None, metavar="CSV",
        help="Comma-separated allow-list (e.g. arxiv.org,sec.gov)")
    exa_p.add_argument("--exclude-domains", default=None, metavar="CSV",
        help="Comma-separated deny-list")
    exa_p.add_argument("--start-published-date", default=None, metavar="YYYY-MM-DD")
    exa_p.add_argument("--end-published-date", default=None, metavar="YYYY-MM-DD")
    exa_p.add_argument("--start-crawl-date", default=None, metavar="YYYY-MM-DD")
    exa_p.add_argument("--end-crawl-date", default=None, metavar="YYYY-MM-DD")
    exa_p.add_argument("--include-text", default=None, metavar="STR",
        help="Text that MUST appear in results (Exa accepts 1-item array only)")
    exa_p.add_argument("--exclude-text", default=None, metavar="STR",
        help="Text that must NOT appear (1-item only; some categories reject this)")
    exa_p.add_argument("--user-location", default=None, metavar="CC",
        help="ISO 2-letter country code (e.g. us, jp) for localized ranking")
    exa_p.add_argument("--additional-queries", default=None, metavar="CSV",
        help="Comma-separated query variations (deep search; max 10)")
    # contents options
    exa_p.add_argument("--no-text", action="store_true",
        help="Skip text content (returns URLs + metadata only)")
    exa_p.add_argument("--text-max-chars", type=int, default=None, metavar="N",
        help="Cap full text per result (default: ~10000 from SDK)")
    exa_p.add_argument("--verbosity", default=None,
        choices=["compact", "standard", "full"],
        help="Text verbosity level")
    exa_p.add_argument("--highlights", action="store_true",
        help="Return extractive highlights (10x more token-efficient than full text)")
    exa_p.add_argument("--highlights-query", default=None, metavar="STR",
        help="Query used to select highlight excerpts")
    exa_p.add_argument("--summary", action="store_true",
        help="Return LLM-generated summary per result")
    exa_p.add_argument("--summary-query", default=None, metavar="STR",
        help="Question that the summary should answer")
    exa_p.add_argument("--livecrawl-max-age-hours", type=int, default=None, metavar="H",
        help="Max age of cached content in hours (0=fresh, -1=cached only)")

    # ----- brave -----
    brave_p = sub.add_parser("brave", help="Search via Brave REST API")
    brave_p.add_argument("--query", required=True, help="Search query")
    brave_p.add_argument("--type", choices=["web", "news"], default="web")
    brave_p.add_argument("--count", type=int, default=10, metavar="N",
        help="Max results: 20 for web, 50 for news")
    brave_p.add_argument(
        "--freshness", default=None,
        help="pd (past day) | pw (past week) | pm (past month) | py (past year)",
    )
    brave_p.add_argument(
        "--extra-snippets", action="store_true",
        help="Include up to 5 additional excerpt alternatives per result",
    )
    brave_p.add_argument(
        "--result-filter", default=None, metavar="TYPES",
        help="Web only — comma-separated: discussions,faq,infobox,news,videos,web,locations",
    )
    brave_p.add_argument("--offset", type=int, default=0, metavar="N",
        help="Pagination offset (0-9)")
    brave_p.add_argument("--country", default="us", metavar="CC",
        help="2-letter country code for result ranking (default: us). e.g. jp, gb, de")
    brave_p.add_argument("--search-lang", default="en", metavar="LANG",
        help="Brave language code (default: en). NOT ISO 639-1 — use jp not ja.")

    # ----- parallel -----
    par_p = sub.add_parser("parallel", help="Search Exa and Brave simultaneously")
    par_p.add_argument("--query", required=True, help="Search query")
    par_p.add_argument("--category", default=None, help="Exa category filter")
    par_p.add_argument("--num-results", type=int, default=10, metavar="N", help="Exa result count")
    par_p.add_argument("--count", type=int, default=10, metavar="N", help="Brave result count")
    par_p.add_argument(
        "--type", default=None, dest="type",
        choices=["auto", "fast", "instant", "deep-lite", "deep", "deep-reasoning"],
        help="Exa search algorithm",
    )
    par_p.add_argument(
        "--extra-snippets", action="store_true",
        help="Brave: include up to 5 additional excerpt alternatives per result",
    )
    par_p.add_argument("--offset", type=int, default=0, metavar="N",
        help="Brave pagination offset (0-9)")
    par_p.add_argument("--country", default="us", metavar="CC",
        help="Brave country code (default: us). e.g. jp")
    par_p.add_argument("--search-lang", default="en", metavar="LANG",
        help="Brave language code (default: en). e.g. jp")

    args = parser.parse_args()

    dispatch = {
        "check-keys": check_keys_cmd,
        "exa": exa_cmd,
        "brave": brave_cmd,
        "parallel": parallel_cmd,
    }

    try:
        sys.exit(dispatch[args.command](args))
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
