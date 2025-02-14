from property_records.tools import query_and_extract_property_search_data, EXTRACTED_PROPS_CSV  
from geo_search.tools import geocode_addresses

import json




if __name__ == "__main__":
    property_records = query_and_extract_property_search_data()
    addresses = [record.mail_address for record in property_records]
    geocoding_responses = geocode_addresses(addresses)

    for record in property_records:
        address = record.mail_address
        geocoding_response = geocoding_responses[record.mail_address]
        if geocoding_response.features[0].properties.rank.confidence != 1:
            print(f"Owner: {record.owner}")
            print(f"Address: {address}")
            print(f"FormattedAddress: {geocoding_response.features[0].properties.formatted}")
            print(f"Confidence: {geocoding_response.features[0].properties.rank.confidence}")
            print('---------------------------------------------------------------------------------------')

