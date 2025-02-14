import aiohttp
import asyncio
import json
import os
from typing import List, Dict

from typing import List, Optional
from pydantic import BaseModel, Field

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(SCRIPT_DIR, "cache")



class Datasource(BaseModel):
    sourcename: Optional[str] = None
    attribution: Optional[str] = None
    license: Optional[str] = None
    url: Optional[str] = None


class Timezone(BaseModel):
    name: Optional[str] = None
    offset_STD: Optional[str] = None
    offset_STD_seconds: Optional[int] = None
    offset_DST: Optional[str] = None
    offset_DST_seconds: Optional[int] = None
    abbreviation_STD: Optional[str] = None
    abbreviation_DST: Optional[str] = None


class Rank(BaseModel):
    importance: Optional[float] = None
    popularity: Optional[float] = None
    confidence: Optional[float] = None
    confidence_city_level: Optional[float] = None
    confidence_street_level: Optional[float] = None
    confidence_building_level: Optional[float] = None
    match_type: Optional[str] = None


class Properties(BaseModel):
    datasource: Optional[Datasource] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    street: Optional[str] = None
    housenumber: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    state_code: Optional[str] = None
    result_type: Optional[str] = None
    formatted: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    category: Optional[str] = None
    timezone: Optional[Timezone] = None
    plus_code: Optional[str] = None
    plus_code_short: Optional[str] = None
    rank: Optional[Rank] = None
    place_id: Optional[str] = None


class Geometry(BaseModel):
    type: Optional[str] = None
    coordinates: Optional[List[float]] = None


class ParsedQuery(BaseModel):
    housenumber: Optional[str] = None
    street: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    expected_type: Optional[str] = None


class Query(BaseModel):
    text: Optional[str] = None
    parsed: Optional[ParsedQuery] = None


class Feature(BaseModel):
    type: Optional[str] = None
    properties: Optional[Properties] = None
    geometry: Optional[Geometry] = None
    bbox: Optional[List[float]] = None


class GeocodingResponse(BaseModel):
    requested_address: Optional[str] = None
    type: Optional[str] = None
    features: Optional[List[Feature]] = None
    query: Optional[Query] = None


async def geocode_address(address: str, session: aiohttp.ClientSession) -> GeocodingResponse:
    # Create cache directory if it doesn't exist
    os.makedirs(STORAGE_DIR, exist_ok=True)
    # Create cache filename from address
    cache_file = os.path.join(STORAGE_DIR, f"{address.replace(' ', '_')}.json")
    # Check if cached result exists
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            return GeocodingResponse(**cached_data)

    # API endpoint and parameters
    base_url = "https://api.geoapify.com/v1/geocode/search"
    api_key = "8923fefc90c24aa1bbe6bb22b302d39b"
    
    params = {
        "text": address,
        "lang": "en",
        "filter": "countrycode:us",
        "apiKey": api_key
    }

    # Headers matching the PowerShell request
    headers = {
        "authority": "api.geoapify.com",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.geoapify.com",
        "priority": "u=1, i",
        "referer": "https://www.geoapify.com/",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    async with session.get(base_url, params=params, headers=headers) as response:
        json_data = await response.json()
        json_data['requested_address'] = address
        model = GeocodingResponse(**json_data)
        model.features[0].properties.formatted = model.features[0].properties.formatted.replace(', United States of America', '')
        # Save the result to the cache
        with open(cache_file, 'w') as f:
            json.dump(model.model_dump(), f, indent=2)
        return model

async def geocode_addresses_async(addresses: List[str]) -> Dict[str, GeocodingResponse]:
    async with aiohttp.ClientSession() as session:
        tasks = [geocode_address(address, session) for address in addresses]
        task_results = await asyncio.gather(*tasks)
        # Convert list of results into a dictionary keyed by requested address
        return {result.requested_address: result for result in task_results}


def geocode_addresses(addresses: List[str]) -> Dict[str, GeocodingResponse]:
    resp = asyncio.run(geocode_addresses_async(addresses)) 
    return resp

async def main():
    # Example addresses
    addresses = [
        "4433 W WEDGE DR FAYETTEVILLE, AR 72704",
        "123 Main St, New York, NY 10001",
        "1600 Pennsylvania Avenue NW, Washington, DC 20500"
    ]
    
    results = await geocode_addresses_async(addresses)
    for result in results:
        print(f"\nResults for {result['requested_address']}:")
        print(result['result'])

if __name__ == "__main__":
    addresses = [
        "4433 W WEDGE DR FAYETTEVILLE, AR 72704",
        "123 Main St, New York, NY 10001",
        "1600 Pennsylvania Avenue NW, Washington, DC 20500"
    ]

    resp : Dict[str, GeocodingResponse] = geocode_addresses(addresses) 
    geocoding_response = resp['4433 W WEDGE DR FAYETTEVILLE, AR 72704']
    print(json.dumps(geocoding_response.model_dump(), indent=2))