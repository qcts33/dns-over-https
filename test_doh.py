import aiohttp
import pytest

from doh import fetch_json


@pytest.mark.asyncio
async def test_fetch_json():
    headers = {"accept": "application/dns-json"}
    query = {"name": "example.com", "type": "A"}
    timeout = aiohttp.ClientTimeout(sock_connect=5)
    url = "dns.233py.com/dns-query"
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        u, ans = await fetch_json(url=url, query=query, session=session)
    for a in ans["Answer"]:
        if isinstance(a, dict):
            if a["type"] == 1:
                answer = a["data"]
                break
        else:
            answer = a
            break
    assert answer == "93.184.216.34"
