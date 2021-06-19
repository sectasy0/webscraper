#!/usr/bin/env python3

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel
import aiohttp
import asyncio


class ProductParams(BaseModel):
    name: str
    price: str
    diameter: str
    weight: str
    alloy: str
    denomination: str
    edge: str
    producer: str


class Product:
    instances: List[object] = []

    def __init__(self, params: ProductParams):
        self._name: str = params.name
        self._price: str = params.price
        self._diameter: str = params.diameter
        self._weight: str = params.weight
        self._alloy: str = params.alloy
        self._denomination: str = params.denomination
        self._edge: str = params.edge
        self._producer: str = params.producer

        self.__class__.instances.append(self)

    def __iter__(self):
        return iter([self._name, self._price, self._diameter, self._weight,
                     self._alloy, self._denomination, self._edge, self._producer])

    @classmethod
    async def save_to_csv(cls,
                          filename: Optional[str] = 'out.csv',
                          delimiter: Optional[str] = ';'
                          ) -> None:

        columns = ProductParams.__dict__['__fields__'].keys()

        with open(filename, 'w', encoding='utf-8') as csv_file:
            csv_file.write(f'{delimiter}'.join([c for c in columns]) + '\n')

            for instance in cls.instances:
                csv_file.write(f'{delimiter}'.join(
                    [i for i in instance]) + '\n')


headers = {
    'authority': 'www.metalmarket.eu',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9',
}


async def get_product_specs(url: str) -> Dict:

    async with aiohttp.ClientSession() as _session:
        async with _session.get(url, headers=headers) as _response:

            soup2 = BeautifulSoup(await _response.text(), 'html.parser')
            spec_body = soup2.findAll('div', class_='n54117_item_b_sub')
            spec_label = soup2.find(
                'table', class_='n54117_dictionary').findAll('span')

            spec_label = [s.text for s in spec_label if s.text != ':']
            spec_body = [s.text for s in spec_body]

        return dict(zip(spec_label, spec_body))


async def get_products(soup: BeautifulSoup):
    for product in soup.findAll('div', class_='product_wrapper'):
        yield product


async def main():
    url = 'https://www.metalmarket.eu/en/menu/coins/1-ounce-coins-802.html?filter_traits%5B1%5D=367'
    default_value = 'null'

    async with aiohttp.ClientSession() as _session:
        async with _session.get(url, headers=headers) as _response:

            soup = BeautifulSoup(await _response.text(), 'html.parser')
            response_domain = f"https://{str(_response.url).split('/')[2]}"

            async for product in get_products(soup):
                product_name = product.find('a', class_='product-name')

                product_detail = await get_product_specs(f"{response_domain}{product_name.attrs['href']}")

                product_params = {
                    'name': product_name.text,
                    'price': product.find('span', class_='price').text,
                    'diameter': product_detail.get('Diameter', default_value),
                    'weight': product_detail.get('Weight', default_value),
                    'alloy': product_detail.get('Alloy', default_value),
                    'denomination': product_detail.get('Denomination', default_value),
                    'edge': product_detail.get('Edge', default_value),
                    'producer': product_detail.get('Producer', default_value)
                }

                Product(ProductParams(**product_params))

    await Product.save_to_csv()

if __name__ == "__main__":
    atask = asyncio.get_event_loop()
    atask.run_until_complete(main())
