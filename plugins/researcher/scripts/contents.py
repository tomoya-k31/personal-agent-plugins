"""Exa Get Contents CLI — fetch full content of specific URLs.

Use this AFTER search.py has returned a list of URLs, to pull full text /
highlights / summary for a curated subset. This implements the two-step
pattern recommended by Exa: search with highlights for triage, then
contents for selected pages.

Run inside the project venv:
    plugins/researcher/.venv/bin/python plugins/researcher/scripts/contents.py ...

Usage:
    ... contents.py --urls URL1,URL2,...
    ... contents.py --urls URL1 --highlights --highlights-query "key claims"
    ... contents.py --urls URL1 --summary --summary-query "what is X"
    ... contents.py --urls URL1 --subpages 5 --subpage-target "docs,api"
    ... contents.py --urls URL1 --livecrawl always --livecrawl-timeout 15000

Outputs JSON to stdout; errors to stderr.
Exit code: 0 on success, 1 on error.
"""

import argparse
import json
import os
import sys
from typing import Any, Optional

EXA_API_KEY = os.environ.get("EXA_API_KEY", "")


def _split_csv(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def fetch_contents(
    *,
    urls: list[str],
    no_text: bool = False,
    text_max_chars: Optional[int] = None,
    verbosity: Optional[str] = None,
    highlights: bool = False,
    highlights_query: Optional[str] = None,
    summary: bool = False,
    summary_query: Optional[str] = None,
    subpages: Optional[int] = None,
    subpage_target: Optional[list[str]] = None,
    livecrawl: Optional[str] = None,
    livecrawl_timeout: Optional[int] = None,
    extras_links: Optional[int] = None,
    extras_image_links: Optional[int] = None,
) -> dict:
    if not EXA_API_KEY:
        print("ERROR: EXA_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    from exa_py import Exa  # noqa: PLC0415

    client = Exa(EXA_API_KEY)
    kwargs: dict[str, Any] = {}

    # Default: include text unless --no-text passed. Must pass False
    # explicitly to suppress — get_contents() defaults to returning text.
    if no_text:
        kwargs["text"] = False
    else:
        text_cfg: dict[str, Any] = {}
        if text_max_chars is not None:
            text_cfg["max_characters"] = text_max_chars
        if verbosity:
            text_cfg["verbosity"] = verbosity
        kwargs["text"] = text_cfg or True

    if highlights:
        hl_cfg: dict[str, Any] = {}
        if highlights_query:
            hl_cfg["query"] = highlights_query
        kwargs["highlights"] = hl_cfg or True

    if summary:
        sum_cfg: dict[str, Any] = {}
        if summary_query:
            sum_cfg["query"] = summary_query
        kwargs["summary"] = sum_cfg or True

    if subpages is not None:
        kwargs["subpages"] = subpages
    if subpage_target:
        kwargs["subpage_target"] = subpage_target if len(subpage_target) > 1 else subpage_target[0]

    if livecrawl:
        kwargs["livecrawl"] = livecrawl
    if livecrawl_timeout is not None:
        kwargs["livecrawl_timeout"] = livecrawl_timeout

    extras: dict[str, int] = {}
    if extras_links is not None:
        extras["links"] = extras_links
    if extras_image_links is not None:
        extras["imageLinks"] = extras_image_links
    if extras:
        kwargs["extras"] = extras

    response = client.get_contents(urls, **kwargs)

    results = []
    for r in response.results:
        item: dict = {"url": r.url, "title": getattr(r, "title", None)}
        if getattr(r, "text", None):
            item["text"] = r.text
        if getattr(r, "highlights", None):
            item["highlights"] = r.highlights
        if getattr(r, "summary", None):
            item["summary"] = r.summary
        if getattr(r, "subpages", None):
            item["subpages"] = [
                {"url": s.url, "title": getattr(s, "title", None), "text": getattr(s, "text", None)}
                for s in r.subpages
            ]
        if getattr(r, "extras", None):
            item["extras"] = r.extras
        results.append(item)

    # Surface per-URL failures (the endpoint returns 200 even when individual URLs fail).
    # ContentStatus objects from the SDK aren't directly JSON-serializable, so coerce
    # them into plain dicts.
    statuses_raw = getattr(response, "statuses", None)
    output: dict = {"results": results, "count": len(results)}
    if statuses_raw:
        output["statuses"] = [_coerce(s) for s in statuses_raw]

    return output


def _coerce(obj: Any) -> Any:
    """Best-effort conversion of SDK objects to plain dict/list/scalar."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: _coerce(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_coerce(x) for x in obj]
    return obj


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch full content (text/highlights/summary) for URLs via Exa Get Contents API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--urls", required=True, metavar="CSV",
        help="Comma-separated URLs to fetch")

    # text mode
    parser.add_argument("--no-text", action="store_true",
        help="Skip text content (useful when only summary/highlights wanted)")
    parser.add_argument("--text-max-chars", type=int, default=None, metavar="N",
        help="Cap full text per result")
    parser.add_argument("--verbosity", default=None,
        choices=["compact", "standard", "full"],
        help="Text verbosity level")

    # highlights mode
    parser.add_argument("--highlights", action="store_true",
        help="Return extractive highlights (10x more token-efficient than text)")
    parser.add_argument("--highlights-query", default=None, metavar="STR",
        help="Query used to select highlight excerpts")

    # summary mode
    parser.add_argument("--summary", action="store_true",
        help="Return LLM-generated summary per URL")
    parser.add_argument("--summary-query", default=None, metavar="STR",
        help="Question the summary should answer")

    # subpages
    parser.add_argument("--subpages", type=int, default=None, metavar="N",
        help="Number of linked subpages to fetch (recommended 5-10, max 15)")
    parser.add_argument("--subpage-target", default=None, metavar="CSV",
        help="Comma-separated keywords to prioritize subpages (e.g. docs,api)")

    # livecrawl
    parser.add_argument("--livecrawl", default=None,
        choices=["auto", "always", "fallback", "never"],
        help="Livecrawl strategy. 'always' = fresh fetch; 'never' = cache only")
    parser.add_argument("--livecrawl-timeout", type=int, default=None, metavar="MS",
        help="Livecrawl timeout in ms (default 10000)")

    # extras
    parser.add_argument("--extras-links", type=int, default=None, metavar="N",
        help="Extract N links per page")
    parser.add_argument("--extras-image-links", type=int, default=None, metavar="N",
        help="Extract N image links per page")

    args = parser.parse_args()

    urls = _split_csv(args.urls)
    if not urls:
        print("ERROR: --urls is empty.", file=sys.stderr)
        sys.exit(1)

    try:
        result = fetch_contents(
            urls=urls,
            no_text=args.no_text,
            text_max_chars=args.text_max_chars,
            verbosity=args.verbosity,
            highlights=args.highlights,
            highlights_query=args.highlights_query,
            summary=args.summary,
            summary_query=args.summary_query,
            subpages=args.subpages,
            subpage_target=_split_csv(args.subpage_target),
            livecrawl=args.livecrawl,
            livecrawl_timeout=args.livecrawl_timeout,
            extras_links=args.extras_links,
            extras_image_links=args.extras_image_links,
        )
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
