import aiohttp
import pytest
import dns.message

from doh import fetch_json, fetch_wireformat


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


@pytest.mark.asyncio
async def test_fetch_wireformat():
    query = dns.message.make_query(qname="example.com", rdtype="A").to_wire()
    headers = {
        "accept": "application/dns-message",
        "content-type": "application/dns-message",
    }
    timeout = aiohttp.ClientTimeout(sock_connect=5)
    url = "dns.233py.com/dns-query"
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        u, ans = await fetch_wireformat(url=url, query=query, session=session)
    for a in ans.answer:
        if a.rdtype == 1:
            data = a.items
            answer = data[0].to_text()
    assert answer == "93.184.216.34"
