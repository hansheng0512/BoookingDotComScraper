import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os

# Headers to mimic browser behavior
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

# Approximate exchange rates to MYR (as of March 2025, for simplicity)
EXCHANGE_RATES = {
    "USD": 4.35,  # United States
    "GBP": 5.80,  # United Kingdom
    "EUR": 4.90,  # Spain, France, Italy, Germany
    "AED": 1.18,  # Dubai (UAE)
    "JPY": 0.032,  # Japan (per 100 JPY)
    "SGD": 3.25,  # Singapore
    "THB": 0.13,  # Thailand
    "INR": 0.052,  # India
    "AUD": 2.95,  # Australia
    "default": 4.35  # Fallback for unlisted currencies (MYR handled separately)
}

def convert_to_myr(price, currency):
    """Convert price to MYR based on currency."""
    if currency == "MYR":
        return max(50, min(130000, int(price)))
    rate = EXCHANGE_RATES.get(currency, EXCHANGE_RATES["default"])
    return max(50, min(130000, int(price * rate)))  # Ensure within RM 50 - RM 130,000

def get_hotel_data(url, max_hotels, region_name, is_malaysia, currency="USD", batch_size=5000, output_dir="hotel_batches"):
    hotels = []
    page = 0
    base_url = url

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    while len(hotels) < max_hotels:
        try:
            # Add pagination offset (25 hotels per page)
            offset = page * 25
            current_url = f"{base_url}&offset={offset}"

            # Send request
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            hotel_cards = soup.find_all('div', {'data-testid': 'property-card'})

            if not hotel_cards:
                print(f"No more hotels found for {region_name}")
                break

            for hotel in hotel_cards:
                if len(hotels) >= max_hotels:
                    break

                try:
                    # Get hotel name
                    name = hotel.find('div', {'data-testid': 'title'}).text.strip()

                    # Get description (if available)
                    description_elem = hotel.find('div', {'data-testid': 'property-card-unit-configuration'})
                    description = description_elem.text.strip() if description_elem else f"{name} is a hotel located in {region_name}"

                    # Get price and convert to MYR
                    price_elem = hotel.find('span', {'data-testid': 'price-and-discounted-price'})
                    if price_elem:
                        price_text = ''.join(filter(str.isdigit, price_elem.text))
                        base_price = int(price_text) if price_text else random.randint(10, 30000)
                        price_myr = convert_to_myr(base_price, currency)
                    else:
                        price_myr = random.randint(50, 130000)  # Random MYR price if unavailable

                    # Get high-resolution image
                    image_elem = hotel.find('img', {'data-testid': 'image'})
                    if image_elem and 'src' in image_elem.attrs:
                        image_url = image_elem['src']
                        if 'max' not in image_url and 'square' not in image_url:
                            image_url = image_url.replace('sz=300', 'sz=1024')  # Attempt 1024px version
                        img_response = requests.head(image_url, headers=headers)
                        image = image_url if 'image' in img_response.headers.get('Content-Type', '') else "https://default-hotel-image.com/high-res.jpg"
                    else:
                        image = "https://default-hotel-image.com/high-res.jpg"

                    hotel_data = {
                        'bookingDescription': description,
                        'bookingName': name,
                        'bookingPrice': f"RM {price_myr:,}",
                        'isMalaysia': is_malaysia,
                        'region': region_name,
                        'image': image
                    }
                    hotels.append(hotel_data)

                    # Save to batch file if batch_size is reached
                    if len(hotels) % batch_size == 0:
                        batch_number = (len(hotels) // batch_size)
                        filename = os.path.join(output_dir, f'hotel_data_batch_{region_name}_{batch_number}.json')
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(hotels[-batch_size:], f, ensure_ascii=False, indent=2)
                        print(f"Saved batch {batch_number} for {region_name} with {batch_size} records to {filename}")

                except Exception as e:
                    print(f"Error processing hotel in {region_name}: {e}")
                    continue

            print(f"Scraped {len(hotels)}/{max_hotels} hotels from {region_name} - Page {page}")

            # Random delay between 2-5 seconds to avoid blocking
            time.sleep(random.uniform(2, 5))
            page += 1

        except Exception as e:
            print(f"Error fetching page from {region_name}: {e}")
            time.sleep(5)  # Longer delay on error
            continue

    # Save any remaining hotels that don't fill a full batch
    if len(hotels) % batch_size != 0:
        batch_number = (len(hotels) // batch_size) + 1
        filename = os.path.join(output_dir, f'hotel_data_batch_{region_name}_{batch_number}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hotels[-(len(hotels) % batch_size):], f, ensure_ascii=False, indent=2)
        print(f"Saved final batch {batch_number} for {region_name} with {len(hotels) % batch_size} records to {filename}")

    return hotels[:max_hotels]

def main():
    total_records = 50000
    batch_size = 5000  # Save 5,000 records per batch

    # Define regions and their targets (50,000 total records)
    region_targets = {
        "Malaysia": 7500,      # 15%
        "United States": 6000, # 12%
        "United Kingdom": 5000, # 10%
        "Spain": 5000,         # 10%
        "Dubai": 4000,         # 8%
        "Japan": 4000,         # 8%
        "Singapore": 3500,     # 7%
        "Thailand": 3500,      # 7%
        "India": 3000,         # 6%
        "France": 3000,        # 6%
        "Italy": 2500,         # 5%
        "Germany": 2500,       # 5%
        "Australia": 2000      # 4%
    }

    # Corresponding currencies for each region
    region_currencies = {
        "Malaysia": "MYR",
        "United States": "USD",
        "United Kingdom": "GBP",
        "Spain": "EUR",
        "Dubai": "AED",
        "Japan": "JPY",
        "Singapore": "SGD",
        "Thailand": "THB",
        "India": "INR",
        "France": "EUR",
        "Italy": "EUR",
        "Germany": "EUR",
        "Australia": "AUD"
    }

    all_hotels = []
    for region, target in region_targets.items():
        url = f"https://www.booking.com/searchresults.html?ss={region}&checkin=2025-04-01&checkout=2025-04-02&group_adults=2&no_rooms=1"
        currency = region_currencies[region]
        is_malaysia = (region == "Malaysia")
        region_hotels = get_hotel_data(url, target, region, is_malaysia, currency, batch_size)
        all_hotels.extend(region_hotels)

    # Save all records to a main JSON file
    main_filename = 'hotel_data_50k.json'
    with open(main_filename, 'w', encoding='utf-8') as f:
        json.dump(all_hotels, f, ensure_ascii=False, indent=2)
    print(f"Saved all {len(all_hotels)} records to {main_filename}")

    # Print summary
    print(f"Successfully scraped {len(all_hotels)} hotels out of {total_records}")
    print("Breakdown by region:")
    for region, target in region_targets.items():
        actual = len([h for h in all_hotels if h['region'] == region])
        print(f"  {region}: {actual}/{target} (Malaysia: {len([h for h in all_hotels if h['region'] == region and h['isMalaysia']])})")
    print(f"Total Malaysia hotels: {len([h for h in all_hotels if h['isMalaysia']])}")
    print(f"Data saved in batches of {batch_size} records in 'hotel_batches' directory and as a single file in {main_filename}")

if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import bs4
        import requests
    except ImportError:
        import os
        os.system('pip install requests beautifulsoup4')

    main()