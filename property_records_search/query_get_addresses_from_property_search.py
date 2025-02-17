from property_record_tools import query_and_extract_property_search_data 
from geo_search_tools import geocode_addresses
from generate_address_csv import generate_address_csv

import json
import csv



if __name__ == "__main__":
    property_records = query_and_extract_property_search_data()
    geocoding_responses = geocode_addresses(property_records)
    generate_address_csv(geocoding_responses)

    
   



