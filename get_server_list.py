import asyncio
import json

import aiohttp
import click


async def get_list():
    url = "https://download.dnscrypt.info/resolvers-list/json/public-resolvers.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response = await resp.text()
    with open("public-resolvers.json", "w") as fp:
        fp.write(response)


def filter_list():
    with open("public-resolvers.json", "r") as fp:
        server_list = json.load(fp)
    names = set(
        server["addrs"][0] for server in server_list if server["proto"] == "DoH"
    )
    names = sorted(names, key=lambda url: tuple(reversed(url.split("."))))
    with open("server_list.text", "w") as fp:
        for url in names:
            print(url, file=fp)


@click.command()
@click.option("--update", is_flag=True)
def main(update):
    if update:
        asyncio.run(get_list())
    filter_list()


if __name__ == "__main__":
    main()
