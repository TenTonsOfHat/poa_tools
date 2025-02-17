import csv
import os
from property_record_tools import query_and_extract_property_search_data 
from geo_search_tools import geocode_addresses

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(SCRIPT_DIR, "addresses.csv")
STORAGE_DIR_V2 = os.path.join(SCRIPT_DIR, "addresses.v2.csv")

def generate_address_csv(geocoding_responses, output_file=None):

    if output_file is None:
        output_file = STORAGE_DIR


    print(f"Writing CSV: {output_file}") 
    # Define the CSV headers
    headers = ["fullname", "Address 1", "Address 2", "City", "State", "Zipcode", "Country"]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        print(f"Processing {len(geocoding_responses)} responses")
        for key, record in geocoding_responses.items():
            if not record.features:
                print(f"No features found for {key}")
                continue
                
            mail_address = record.property_record.mail_address
            props = record.features[0].properties
            owner = record.property_record.owner
            
            # Split address into components

            if "BOX" in mail_address:
                address_parts = mail_address.split(',')
                address1 = address_parts[0].strip() if len(address_parts) > 0 else ""
            else:
                address_parts = props.formatted.split(',')
                address1 = address_parts[0].strip() if len(address_parts) > 0 else ""
            
            # Create row data
            row = {
                "fullname": owner,
                "Address 1": address1,
                "Address 2": "",  # We'll leave this blank as we don't have a specific address line 2
                "City": props.city or "",
                "State": props.state_code or "",
                "Zipcode": props.postcode or "",
                "Country": "USA"  # Since we know these are US addresses
            }
            writer.writerow(row)
            



if __name__ == "__main__":
    property_records = query_and_extract_property_search_data()
    geocoding_responses = geocode_addresses(property_records)
    generate_address_csv(geocoding_responses)
    print("CSV file has been generated successfully!") 