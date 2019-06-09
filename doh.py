import asyncio
import json

import aiohttp
import click
import dns.message
import dns.rdatatype


async def fetch_wireformat(url, query, session):
    try:
        async with session.post(f"https://{url}", data=query) as resp:
            wire = await resp.read()
        response = dns.message.from_wire(wire)
    except aiohttp.ServerTimeoutError:
        response = dns.message.from_wire(query)
    return url, response


def format_message(response):
    for answer in response.answer:
        print(answer)


async def aio_wire(name, server_list, record_type="AAAA"):
    headers = {
        "accept": "application/dns-message",
        "content-type": "application/dns-message",
    }
    query = dns.message.make_query(qname=name, rdtype=record_type).to_wire()
    timeout = aiohttp.ClientTimeout(sock_connect=5)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        tasks = list(
            fetch_wireformat(url=url, query=query, session=session)
            for url in server_list
        )
        for f in asyncio.as_completed(tasks):
            url, ans = await f
            click.secho(url, fg="green")
            format_message(ans)


async def fetch_json(url: str, query: dict, session: aiohttp.ClientSession):
    try:
        async with session.get(f"https://{url}", params=query) as resp:
            answer = await resp.json(content_type=None)
    except aiohttp.ClientConnectorError:
        answer = {"Answer": ["Connector Error"]}
    except json.JSONDecodeError:
        answer = {"Answer": ["JSON Decode Error"]}
    except aiohttp.ServerTimeoutError:
        answer = {"Answer": ["Timeout Error"]}
    return url, answer


def formated_output(ans: dict):
    answer = ans.get("Answer", [])
    for a in answer:
        if isinstance(a, dict):
            a["rdtype"] = dns.rdatatype.to_text(a["type"])
            print("{name} {TTL} {rdtype} {data}".format(**a))
        else:
            print(a)


async def aio_json(name, server_list, record_type="AAAA"):
    query = {"name": name, "type": record_type}
    headers = {"accept": "application/dns-json"}
    timeout = aiohttp.ClientTimeout(sock_connect=5)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        tasks = list(
            fetch_json(url=url, query=query, session=session) for url in server_list
        )
        for f in asyncio.as_completed(tasks):
            url, ans = await f
            click.secho(url, fg="green")
            formated_output(ans)


@click.command()
@click.argument("name")
@click.argument("record_type", default="A")
@click.argument("protocol", default="json")
def main(name: str, record_type: str, protocol: str):
    with open("server_list.json", "r") as fp:
        server_list = json.load(fp)
    if protocol == "json":
        asyncio.run(aio_json(name, server_list, record_type))
    elif protocol == "wire":
        asyncio.run(aio_wire(name, server_list, record_type))


if __name__ == "__main__":
    main()
