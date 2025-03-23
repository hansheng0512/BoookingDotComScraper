import requests
from bs4 import BeautifulSoup
import time
import random
import json

# Headers to mimic browser behavior
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}


def get_hotel_data(url, is_malaysia, max_hotels, region_name):
    hotels = []
    page = 0
    base_url = url

    while len(hotels) < max_hotels:
        try:
            # Add pagination offset (25 hotels per page)
            offset = page * 25
            current_url = f"{base_url}&offset={offset}"

            # Send request
            response = requests.get(current_url, headers=headers)
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

                    # Get price
                    price_elem = hotel.find('span', {'data-testid': 'price-and-discounted-price'})
                    price = int(''.join(filter(str.isdigit, price_elem.text))) if price_elem else random.randint(50,
                                                                                                                 500)

                    # Get image
                    image_elem = hotel.find('img', {'data-testid': 'image'})
                    image = image_elem['src'] if image_elem else "https://default-hotel-image.com"

                    hotel_data = {
                        'bookingDescription': description,
                        'bookingName': name,
                        'bookingPrice': price,
                        'isMalaysia': is_malaysia,
                        'image': image
                    }
                    hotels.append(hotel_data)

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

    return hotels[:max_hotels]


def main():
    total_records = 10000
    malaysia_target = int(total_records * 0.15)  # 1,500 hotels
    non_malaysia_target = int(total_records * 0.85)  # 8,500 hotels

    # Malaysia hotels (15%)
    malaysia_url = "https://www.booking.com/searchresults.html?ss=Malaysia&checkin=2025-04-01&checkout=2025-04-02&group_adults=2&no_rooms=1"
    malaysia_hotels = get_hotel_data(malaysia_url, True, malaysia_target, "Malaysia")

    # Non-Malaysia hotels (85%) split across popular countries
    country_targets = {
        "United States": int(non_malaysia_target * 0.3),  # 2,550 hotels
        "United Kingdom": int(non_malaysia_target * 0.25),  # 2,125 hotels
        "Spain": int(non_malaysia_target * 0.25),  # 2,125 hotels
        "Dubai": int(non_malaysia_target * 0.2)  # 1,700 hotels
    }

    non_malaysia_hotels = []
    for country, target in country_targets.items():
        url = f"https://www.booking.com/searchresults.html?ss={country}&checkin=2025-04-01&checkout=2025-04-02&group_adults=2&no_rooms=1"
        country_hotels = get_hotel_data(url, False, target, country)
        non_malaysia_hotels.extend(country_hotels)

    # Combine all hotels
    all_hotels = malaysia_hotels + non_malaysia_hotels

    # Save to JSON file
    with open('hotel_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_hotels, f, ensure_ascii=False, indent=2)

    print(f"Successfully scraped {len(all_hotels)} hotels out of {total_records}")
    print(f"Malaysia hotels: {len(malaysia_hotels)} (15%)")
    print(f"Non-Malaysia hotels: {len(non_malaysia_hotels)} (85%)")
    print("Breakdown of non-Malaysia hotels:")
    for country, target in country_targets.items():
        actual = len([h for h in non_malaysia_hotels if country in h['bookingDescription']])
        print(f"  {country}: {actual}/{target}")


if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import bs4
        import requests
    except ImportError:
        import os

        os.system('pip install requests beautifulsoup4')

    main()