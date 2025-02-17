from bs4 import BeautifulSoup
import csv
import re
import os
import requests
import json
from typing import List
from pydantic import BaseModel, Field
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(SCRIPT_DIR, "search_data")
COOKIES_FILE = os.path.join(STORAGE_DIR, "cookies.json")
EXTRACTED_PROPS_CSV = os.path.join(STORAGE_DIR, "extracted_properties.csv")
EXTRACTED_PROPS_JSON = os.path.join(STORAGE_DIR, "extracted_properties.json")
EXTRACTED_PROPS_JSON_CLEAN = os.path.join(STORAGE_DIR, "extracted_properties_clean.json")
EXTRACTED_PROPS_HTML = os.path.join(STORAGE_DIR, "result.html")


class PropertyRecord(BaseModel):
    """Represents a property record with associated details."""
    address: Optional[str] = Field(None, description="Street address of the property")
    mail_address: Optional[str] = Field(None, alias="Mail Address", description="Mailing address for the property owner")
    owner: Optional[str] = Field(None, alias="Owner", description="Name of the property owner")
    subdivision: Optional[str] = Field(None, alias="Sub", description="Subdivision name")
    city: Optional[str] = Field(None, alias="City", description="City where the property is located")
    assessed_value: Optional[str] = Field(None, alias="Assessed Value", description="Assessed value of the property")
    str_location: Optional[str] = Field(None, alias="S-T-R", description="Section-Township-Range location")
    block_lot: Optional[str] = Field(None, alias="Block / Lot", description="Block and lot numbers")
    acres: Optional[str] = Field(None, alias="Acres", description="Property size in acres")
    legal: Optional[str] = Field(None, alias="Legal", description="Legal description of the property")

    class Config:
        populate_by_name = True
        json_encoders = {
            # Add any custom encoders if needed
        } 


# Create search data directory if it doesn't exist
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)


def clean_text(text):
    """Clean and normalize text fields"""
    if text is None:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_properties(html_file):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Find all property sections
    properties = []
    
    # First find all divs that might contain property information
    property_sections = soup.find_all('div', {'class': ['col-sm-6', 'col-sm-12']})
    
    current_property = {}
    
    for section in property_sections:
        # Process all dl elements within this section
        dl_elements = section.find_all('dl', class_='dl-horizontal')
        if not dl_elements:
            continue
            
        # Extract data from each dl element
        for dl in dl_elements:
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')
            
            for dt, dd in zip(dt_elements, dd_elements):
                key = clean_text(dt.text.replace(':', ''))
                value = clean_text(dd.text)
                if key:  # Include empty values but require a key
                    current_property[key] = value
        
        # If we find a Legal field, it's the end of a property record
        if any(dt.text.strip() == 'Legal:' for dt in section.find_all('dt')):
            if current_property:
                # Make sure we have all possible fields, even if empty
                expected_fields = ['Address', 'Mail Address', 'Owner', 'Sub', 'City', 
                                 'Assessed Value', 'S-T-R', 'Block / Lot', 'Acres', 'Legal']
                for field in expected_fields:
                    if field not in current_property:
                        current_property[field] = ''
                
                properties.append(current_property.copy())
                current_property = {}

    return properties

def save_to_json(properties, output_file):
    if not properties:
        print("No properties found to save")
        return

    # Use a fixed set of fields in a specific order
    fieldnames = ['Address', 'Mail Address', 'Owner', 'Sub', 'City', 
                 'Assessed Value', 'S-T-R', 'Block / Lot', 'Acres', 'Legal']
    
    # Add any additional fields we found that weren't in our expected list
    additional_fields = set()
    for prop in properties:
        additional_fields.update(set(prop.keys()) - set(fieldnames))
    fieldnames.extend(sorted(list(additional_fields)))

    print(f"Fields being saved: {', '.join(fieldnames)}")
    print(f"Sample of first property data: {properties[0] if properties else 'No properties found'}")


    # Convert properties to PropertyRecord objects
    property_records = []
    for prop in properties:
        try:
            record = PropertyRecord(**prop)
            property_records.append(record)
        except Exception as e:
            print(f"Error converting property to PropertyRecord: {e}")
            continue

    # Convert PropertyRecord objects back to dictionaries for JSON serialization
    properties = [record.model_dump(by_alias=True) for record in property_records]

    # Write to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(properties, f, indent=2)

def get_and_save_cookies():
    url = "https://www.actdatascout.com/RealProperty/Arkansas/Washington"
    
    headers = {
        "authority": "www.actdatascout.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.actdatascout.com",
        "priority": "u=0, i",
        "referer": "https://www.actdatascout.com/RealProperty",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }
    
    # Make the request
    session = requests.Session()
    response = session.get(url, headers=headers)
    
    # Get all cookies from the session
    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
    
    # Get directory of current script
    
    # Save cookies to file
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies_dict, f, indent=4)
    
    print(f"Cookies have been saved to {COOKIES_FILE}")
    print(f"Number of cookies saved: {len(cookies_dict)}")


def send_property_search_query():
    url = "https://www.actdatascout.com/RealProperty/AdvancedSearch"
    
    # Set up cookies
    cookies = {
        "__stripe_mid": "cb3e3bd3-fe5f-44c7-bf5f-ef1ae4225e4e69ae98",
        "_gid": "GA1.2.2029724246.1739477352",
        "ASP.NET_SessionId": "heej1s0tqdjmthcmoildehpi",
        "__RequestVerificationToken": "9EiupuysIMtswPhGIuTleruL_ask1Leyoh8Od_yqOnw1x3XyQC1c4wptqfPd7DmAk00Gq8fSv4EcdmVpO8riMO7lzcWTr1Mh3Dlhqt4AH4w1",
        "ACTAPPAuthCookie": "hKp5qJLmhQ0RWGkIdzTK01s_yYa2McX5GuKG6QnpSh5O3i7lz8MifYQMDCTosWz0u9bT9P0XIe9MABF3VSoxju6qznL5w4_Cw13GPI8h0sBmfJKrRup5QZJgkxfnPhjBYwa8T2C1BzL0rXtGe_qcVsSy6LD6XwCVIyGmJy_2x0RrSYreIaCpBzQhGiBzHRapZMWFscqk0ekZKT5FXgeEolsyfMQTwvo43eHdXyEGuvwoC5ynJ3r6zlZ1lw806_A9CvCD5K9HJLAo28eR2N0BF-Caw1aYrQS9CniUcgaN9108v-meRqSwZ77OHgfDOxAyKDP5qeQwZGy_TC3Z8xrZPAtnYIyKXPOpTWrryU-EIEMpkNDVnMdSFtYIMdPti4obcmLXerxY_3GH5XCDfIBmte0oHE9Y-jYA4laQha7MVOTPMP7P01KtPDvcdtiRcXNATnR32IqOymED_up3RwP6RGX6KlJSTii700OhZYHDUTM",
        "__stripe_sid": "2014990f-bede-4523-8c58-26986fbb9596a594e6",
        "_gat": "1",
        "_ga": "GA1.1.715823118.1712930545",
        "_ga_4P8D81HTWS": "GS1.1.1739488971.5.1.1739489175.22.0.0"
    }

    
    with open(COOKIES_FILE, 'r') as f:
        saved_cookies = json.load(f)
    
    # Merge saved cookies with existing cookies
    cookies.update(saved_cookies)


    headers = {
        "authority": "www.actdatascout.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.actdatascout.com",
        "priority": "u=0, i",
        "referer": "https://www.actdatascout.com/RealProperty",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }
    
    data = {
        "CountyId": "5143",
        "Vendor": "ACT",
        "PropertyType": "0",
        "ImprovedVacant": "0",
        "IncludeExempt": ["true", "false"],
        "IncludePublicService": ["true", "false"],
        "IncludeVoids": ["true", "false"],
        "ParcelNumber": "",
        "Rpid": "",
        "LastName": "",
        "UseContainsLastNameSearch": "false",
        "FirstName": "",
        "FullName": "",
        "Subdivision": "CROSS KEYS S/D PH I",
        "MinTotalAcres": "",
        "MaxTotalAcres": "",
        "MinTimberAcres": "",
        "MaxTimberAcres": "",
        "StreetNumber": "",
        "StreetDirection": "",
        "StreetName": "",
        "StreetNameMatchType": "false",
        "City": "",
        "Section": "",
        "Township": "",
        "Range": "",
        "Lot": "",
        "Block": "",
        "Legal": "",
        "MinTransferDate": "",
        "MaxTransferDate": "",
        "ExcludePostSales": ["true", "false"],
        "MinSalePrice": "",
        "MaxSalePrice": "",
        "Grantee": "",
        "Book": "",
        "Page": "",
        "WarrantyDeedsOnly": "false",
        "LandSalesOnly": "false",
        "OwnerAddress": "",
        "OwnerCity": "",
        "OwnerState": "",
        "OwnerZipCode": "",
        "ResMinLivingArea": "",
        "ResMaxLivingArea": "",
        "ResMinAge": "",
        "ResMaxAge": "",
        "ResBasement": "",
        "ResFoundation": "",
        "ResFireplace": "",
        "ResConstruction": "",
        "ResOccupancy": "",
        "ResRoofCover": "",
        "ResFullBaths": "",
        "ResHalfBaths": "",
        "ResHeatAir": "",
        "CommMinFloorArea": "",
        "CommMaxFloorArea": "",
        "CommOccupancy": "",
        "CommBusinessName": "",
        "CommMinStories": "",
        "CommMinEffectiveAge": "",
        "CommMaxEffectiveAge": "",
        "CommMinNumberUnits": "",
        "CommMaxNumberUnits": ""
    }

    # Send POST request
    response = requests.post(
        url,
        headers=headers,
        cookies=cookies,
        data=data,
        allow_redirects=True
    )
    
    # Save the response to file in script directory
    with open(EXTRACTED_PROPS_HTML, 'w', encoding='utf-8') as f:
        f.write(response.text)
    # Save the response to a file
    return response



def extract_props():
    print(f"Extracting properties from {EXTRACTED_PROPS_HTML}...")
    properties = extract_properties(EXTRACTED_PROPS_HTML)
    print(f"Found {len(properties)} properties")
    print(f"Saving to {EXTRACTED_PROPS_JSON}...")
    save_to_json(properties, EXTRACTED_PROPS_JSON)
    print("Done!")




class PropertyRecord(BaseModel):
    """Represents a property record with associated details."""
    address: Optional[str] = Field(None, alias="Address", description="Street address of the property")
    mail_address: Optional[str] = Field(None, alias="Mail Address", description="Mailing address for the property owner")
    owner: Optional[str] = Field(None, alias="Owner", description="Name of the property owner")
    subdivision: Optional[str] = Field(None, alias="Sub", description="Subdivision name")
    city: Optional[str] = Field(None, alias="City", description="City where the property is located")
    assessed_value: Optional[str] = Field(None, alias="Assessed Value", description="Assessed value of the property")
    str_location: Optional[str] = Field(None, alias="S-T-R", description="Section-Township-Range location")
    block_lot: Optional[str] = Field(None, alias="Block / Lot", description="Block and lot numbers")
    acres: Optional[str] = Field(None, alias="Acres", description="Property size in acres")
    legal: Optional[str] = Field(None, alias="Legal", description="Legal description of the property")

    class Config:
        populate_by_name = True
        json_encoders = {
            # Add any custom encoders if needed
        } 



def load_property_records(path) -> List[PropertyRecord]:

    """Load property records from JSON file and convert to PropertyRecord models"""
    print(f"Loading property records from {path}...")
    
    with open(path, 'r') as f:
        properties_data = json.load(f)
    
    property_records: List[PropertyRecord] = []
    for prop_data in properties_data:
        try:
            record = PropertyRecord(**prop_data)
            property_records.append(record)
        except Exception as e:
            print(f"Error loading property record: {e}")
            continue
    
    print(f"Loaded {len(property_records)} property records")
    return property_records

def load_clean_property_records() -> List[PropertyRecord]:
    clean_property_record()
    return load_property_records(EXTRACTED_PROPS_JSON_CLEAN)

def clean_property_record():
    records = load_property_records(EXTRACTED_PROPS_JSON)
    for record in records:
        if record.address in record.mail_address and 'SPRINGDALE' in record.mail_address:
            record.mail_address = record.mail_address.replace('SPRINGDALE', 'FAYETTEVILLE') 

    # Write updated records back to JSON
    records_dict = [record.model_dump(by_alias=True) for record in records]
    with open(EXTRACTED_PROPS_JSON_CLEAN, 'w') as f:
        json.dump(records_dict, f, indent=2)
    print(f"Updated {len(records)} records in {EXTRACTED_PROPS_JSON_CLEAN}")

def query_and_extract_property_search_data(pull_new_data: bool = False) -> List[PropertyRecord]:
    if pull_new_data:
        get_and_save_cookies()
        response = send_property_search_query()
        print(f"Status code: {response.status_code}")
        print(f"Response saved to result.html") 

    extract_props() 
    clean_property_record()
    return load_property_records(EXTRACTED_PROPS_JSON_CLEAN)

if __name__ == "__main__":
   query_and_extract_property_search_data()
   clean_property_record()
