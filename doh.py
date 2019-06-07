import asyncio
import json
from collections import defaultdict

import aiohttp
import click


async def fetch_json(url: str, params: dict, session: aiohttp.ClientSession):
    try:
        async with session.get(f"https://{url}", params=params) as resp:
            answer = await resp.json(content_type=None)
    except aiohttp.ClientConnectorError:
        answer = {"Answer": ["Connector Error"]}
    except json.JSONDecodeError:
        answer = {"Answer": ["JSON Decode Error"]}
    return url, answer


def formated_output(ans):
    answer = defaultdict(list)
    try:
        for a in ans["Answer"]:
            answer[a["name"]].append(a["data"])
        for k, v in answer.items():
            print(f"  {k}")
            for data in v:
                print(f"    {data}")
    except TypeError:
        for a in ans["Answer"]:
            print(f"  {a}")
    except KeyError:
        print(ans)


async def aio_dns(name, record_type="AAAA", protocol="json"):
    params = {"name": name, "type": record_type}
    if protocol == "json":
        headers = {"accept": "application/dns-json"}
    if protocol == "wireformat":
        headers = {"accept": "application/dns-message"}
        raise NotImplementedError
    else:
        raise NotImplementedError
    with open("server_list.json", "r") as fp:
        server_list = json.load(fp)
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = list(fetch_json(url, params, session) for url in server_list)
        for f in asyncio.as_completed(tasks):
            url, ans = await f
            print(url)
            formated_output(ans)


@click.command()
@click.argument("name")
@click.argument("record_type", default="A")
@click.argument("protocol", default="json")
def main(name: str, record_type: str, protocol: str):
    asyncio.run(aio_dns(name, record_type, protocol))


if __name__ == "__main__":
    main()
