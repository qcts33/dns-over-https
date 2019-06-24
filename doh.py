import asyncio
import json

import aiohttp
import click
import dns.message
import dns.name
import dns.rdatatype


def get_trace_config():
    async def on_request_start(session, trace_config_ctx, params):
        trace_config_ctx.trace_request_ctx["start"] = asyncio.get_running_loop().time()

    async def on_request_end(session, trace_config_ctx, params):
        trace_config_ctx.trace_request_ctx["end"] = asyncio.get_running_loop().time()

    trace_config = aiohttp.TraceConfig()
    trace_config.on_connection_create_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)
    return trace_config


async def fetch_wireformat(url, query, session):
    try:
        trace = dict()
        async with session.post(
            f"https://{url}/dns-query", data=query, trace_request_ctx=trace
        ) as resp:
            wire = await resp.read()
        response = dns.message.from_wire(wire)
    except aiohttp.ServerTimeoutError:
        response = "ServerTimeoutError"
    except dns.message.ShortHeader:
        response = "ShortHeader"
    except dns.name.BadLabelType:
        response = "BadLabelType"
    finally:
        elapsed = trace.get("end", float("inf")) - trace["start"]
    return url, response, elapsed


def format_message(response):
    try:
        for answer in response.answer:
            print(answer)
    except AttributeError:
        print(response)


async def aio_wire(name, server_list, record_type="AAAA"):
    headers = {
        "accept": "application/dns-message",
        "content-type": "application/dns-message",
    }
    query = dns.message.make_query(qname=name, rdtype=record_type).to_wire()
    timeout = aiohttp.ClientTimeout(sock_connect=5)
    trace_config = get_trace_config()
    async with aiohttp.ClientSession(
        headers=headers, timeout=timeout, trace_configs=[trace_config]
    ) as session:
        tasks = list(
            fetch_wireformat(url=url, query=query, session=session)
            for url in server_list
        )
        for f in asyncio.as_completed(tasks):
            url, ans, elapsed = await f
            click.secho(f"{url} {elapsed:.3f}", fg="green")
            format_message(ans)


async def fetch_json(url: str, query: dict, session: aiohttp.ClientSession):
    try:
        trace = dict()
        async with session.get(
            f"https://{url}/dns-query", params=query, trace_request_ctx=trace
        ) as resp:
            answer = await resp.json(content_type=None)
    except aiohttp.ClientConnectorError:
        answer = "ClientConnectorError"
    except json.JSONDecodeError:
        answer = "JSONDecodeError"
    except aiohttp.ServerTimeoutError:
        answer = "ServerTimeoutError"
    finally:
        elapsed = trace.get("end", float("inf")) - trace["start"]
    return url, answer, elapsed


def formated_output(ans: dict):
    try:
        answer = ans.get("Answer", [])
        for a in answer:
            a["rdtype"] = dns.rdatatype.to_text(a["type"])
            print("{name} {TTL} {rdtype} {data}".format(**a))
    except AttributeError:
        print(ans)


async def aio_json(name, server_list, record_type="AAAA"):
    query = {"name": name, "type": record_type}
    headers = {"accept": "application/dns-json"}
    timeout = aiohttp.ClientTimeout(sock_connect=5)
    trace_config = get_trace_config()
    async with aiohttp.ClientSession(
        headers=headers, timeout=timeout, trace_configs=[trace_config]
    ) as session:
        tasks = list(
            fetch_json(url=url, query=query, session=session) for url in server_list
        )
        for f in asyncio.as_completed(tasks):
            url, ans, elapsed = await f
            click.secho(f"{url} {elapsed:.3f}", fg="green")
            formated_output(ans)


@click.command()
@click.argument("name")
@click.argument("record_type", default="A")
@click.argument("protocol", default="wire")
def main(name: str, record_type: str, protocol: str):
    with open("server_list.txt", "r") as fp:
        server_list = list(s.strip() for s in fp)
    if protocol == "json":
        asyncio.run(aio_json(name, server_list, record_type))
    elif protocol == "wire":
        asyncio.run(aio_wire(name, server_list, record_type))


if __name__ == "__main__":
    main()
