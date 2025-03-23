# Booking.com Hotel Scraper

This Python script scrapes hotel data from Booking.com, collecting 10,000 records with a distribution of 15% Malaysia hotels (1,500) and 85% non-Malaysia hotels (8,500) from popular countries (United States, United Kingdom, Spain, and Dubai).

## Features
- Scrapes hotel details including name, description, price, and image URL
- Maintains a 15% Malaysia / 85% non-Malaysia distribution
- Non-Malaysia breakdown:
  - United States: 30% (2,550 hotels)
  - United Kingdom: 25% (2,125 hotels)
  - Spain: 25% (2,125 hotels)
  - Dubai: 20% (1,700 hotels)
- Implements random delays (2-5 seconds) to prevent blocking
- Saves data in JSON format with the following structure:
```json
[
  {
    "bookingDescription": "Hotel description here",
    "bookingName": "Hotel Name",
    "bookingPrice": 100,
    "isMalaysia": true,
    "image": "https://image-url.com"
  },
  ...
]