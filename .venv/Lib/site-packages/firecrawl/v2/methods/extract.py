from typing import Any, Dict, List, Optional
import time

from ..types import ExtractResponse, ScrapeOptions
from ..types import AgentOptions
from ..utils.http_client import HttpClient
from ..utils.validation import prepare_scrape_options
from ..utils.error_handler import handle_response_error


def _prepare_extract_request(
    urls: Optional[List[str]],
    *,
    prompt: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    allow_external_links: Optional[bool] = None,
    enable_web_search: Optional[bool] = None,
    show_sources: Optional[bool] = None,
    scrape_options: Optional[ScrapeOptions] = None,
    ignore_invalid_urls: Optional[bool] = None,
    integration: Optional[str] = None,
    agent: Optional[AgentOptions] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if urls is not None:
        body["urls"] = urls
    if prompt is not None:
        body["prompt"] = prompt
    if schema is not None:
        body["schema"] = schema
    if system_prompt is not None:
        body["systemPrompt"] = system_prompt
    if allow_external_links is not None:
        body["allowExternalLinks"] = allow_external_links
    if enable_web_search is not None:
        body["enableWebSearch"] = enable_web_search
    if show_sources is not None:
        body["showSources"] = show_sources
    if ignore_invalid_urls is not None:
        body["ignoreInvalidURLs"] = ignore_invalid_urls
    if scrape_options is not None:
        prepared = prepare_scrape_options(scrape_options)
        if prepared:
            body["scrapeOptions"] = prepared
    if integration is not None and str(integration).strip():
        body["integration"] = str(integration).strip()
    if agent is not None:
        try:
            body["agent"] = agent.model_dump(exclude_none=True)  # type: ignore[attr-defined]
        except AttributeError:
            body["agent"] = agent  # fallback
    return body


def start_extract(
    client: HttpClient,
    urls: Optional[List[str]],
    *,
    prompt: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    allow_external_links: Optional[bool] = None,
    enable_web_search: Optional[bool] = None,
    show_sources: Optional[bool] = None,
    scrape_options: Optional[ScrapeOptions] = None,
    ignore_invalid_urls: Optional[bool] = None,
    integration: Optional[str] = None,
    agent: Optional[AgentOptions] = None,
) -> ExtractResponse:
    body = _prepare_extract_request(
        urls,
        prompt=prompt,
        schema=schema,
        system_prompt=system_prompt,
        allow_external_links=allow_external_links,
        enable_web_search=enable_web_search,
        show_sources=show_sources,
        scrape_options=scrape_options,
        ignore_invalid_urls=ignore_invalid_urls,
        integration=integration,
        agent=agent,
    )
    resp = client.post("/v2/extract", body)
    if not resp.ok:
        handle_response_error(resp, "extract")
    return ExtractResponse(**resp.json())


def get_extract_status(client: HttpClient, job_id: str) -> ExtractResponse:
    resp = client.get(f"/v2/extract/{job_id}")
    if not resp.ok:
        handle_response_error(resp, "extract-status")
    return ExtractResponse(**resp.json())


def wait_extract(
    client: HttpClient,
    job_id: str,
    *,
    poll_interval: int = 2,
    timeout: Optional[int] = None,
) -> ExtractResponse:
    start_ts = time.time()
    while True:
        status = get_extract_status(client, job_id)
        if status.status in ("completed", "failed", "cancelled"):
            return status
        if timeout is not None and (time.time() - start_ts) > timeout:
            return status
        time.sleep(max(1, poll_interval))


def extract(
    client: HttpClient,
    urls: Optional[List[str]],
    *,
    prompt: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    allow_external_links: Optional[bool] = None,
    enable_web_search: Optional[bool] = None,
    show_sources: Optional[bool] = None,
    scrape_options: Optional[ScrapeOptions] = None,
    ignore_invalid_urls: Optional[bool] = None,
    poll_interval: int = 2,
    timeout: Optional[int] = None,
    integration: Optional[str] = None,
    agent: Optional[AgentOptions] = None,
) -> ExtractResponse:
    started = start_extract(
        client,
        urls,
        prompt=prompt,
        schema=schema,
        system_prompt=system_prompt,
        allow_external_links=allow_external_links,
        enable_web_search=enable_web_search,
        show_sources=show_sources,
        scrape_options=scrape_options,
        ignore_invalid_urls=ignore_invalid_urls,
        integration=integration,
        agent=agent,
    )
    job_id = getattr(started, "id", None)
    if not job_id:
        return started
    return wait_extract(client, job_id, poll_interval=poll_interval, timeout=timeout)