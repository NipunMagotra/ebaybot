import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
from urllib.parse import urlencode
from datetime import datetime

class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        # More realistic headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.selected_fields = []
        self.debug_mode = False
        
    def get_user_preferences(self):
        """Interactive menu to get user preferences"""
        print("\n" + "="*60)
        print("         EBAY SCRAPER - CONFIGURATION")
        print("="*60)
        
        # Available fields
        available_fields = {
            '1': ('title', 'Product Title'),
            '2': ('price', 'Price'),
            '3': ('condition', 'Condition (New/Used)'),
            '4': ('shipping', 'Shipping Cost/Info'),
            '5': ('location', 'Seller Location'),
            '6': ('url', 'Product URL'),
            '7': ('image_url', 'Image URL'),
            '8': ('sold_count', 'Items Sold'),
        }
        
        # Step 1: Select fields
        print("\nSTEP 1: SELECT DATA FIELDS TO SCRAPE")
        print("-" * 60)
        print("Available fields:")
        for key, (field, description) in available_fields.items():
            print(f"  {key}. {description}")
        print("  0. Select ALL fields")
        
        while True:
            choice = input("\nEnter field numbers separated by commas (e.g., 1,2,3) or 0 for all: ").strip()
            
            if choice == '0':
                self.selected_fields = [field for field, _ in available_fields.values()]
                break
            else:
                try:
                    choices = [c.strip() for c in choice.split(',')]
                    self.selected_fields = [available_fields[c][0] for c in choices if c in available_fields]
                    if self.selected_fields:
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except (KeyError, ValueError):
                    print("Invalid input. Please enter valid numbers.")
        
        print(f"\n✓ Selected fields: {', '.join(self.selected_fields)}")
        
        # Step 2: Search query
        print("\n" + "-" * 60)
        print("STEP 2: SEARCH QUERY")
        print("-" * 60)
        search_query = input("Enter your search term (e.g., 'laptop', 'iphone 15'): ").strip()
        
        # Step 3: Price range
        print("\n" + "-" * 60)
        print("STEP 3: PRICE RANGE (Optional)")
        print("-" * 60)
        min_price = input("Enter minimum price (press Enter to skip): ").strip()
        max_price = input("Enter maximum price (press Enter to skip): ").strip()
        
        min_price = float(min_price) if min_price else None
        max_price = float(max_price) if max_price else None
        
        # Step 4: Condition filter
        print("\n" + "-" * 60)
        print("STEP 4: CONDITION FILTER (Optional)")
        print("-" * 60)
        print("1. All conditions")
        print("2. New only")
        print("3. Used only")
        condition_choice = input("Enter your choice (1-3): ").strip()
        
        condition_filter = {
            '1': None,
            '2': 'new',
            '3': 'used'
        }.get(condition_choice, None)
        
        # Step 5: Sort by
        print("\n" + "-" * 60)
        print("STEP 5: SORT RESULTS BY")
        print("-" * 60)
        print("1. Best Match")
        print("2. Price: Lowest First")
        print("3. Price: Highest First")
        print("4. Newest Listings")
        sort_choice = input("Enter your choice (1-4): ").strip()
        
        sort_by = {
            '1': 'best_match',
            '2': 'price_low',
            '3': 'price_high',
            '4': 'newest'
        }.get(sort_choice, 'best_match')
        
        # Step 6: Number of pages
        print("\n" + "-" * 60)
        print("STEP 6: NUMBER OF PAGES")
        print("-" * 60)
        max_pages = input("How many pages to scrape? (1-5, default 2): ").strip()
        max_pages = int(max_pages) if max_pages.isdigit() and 1 <= int(max_pages) <= 5 else 2
        
        # Step 7: Export format
        print("\n" + "-" * 60)
        print("STEP 7: EXPORT FORMAT")
        print("-" * 60)
        print("1. CSV")
        print("2. JSON")
        print("3. Both")
        export_choice = input("Enter your choice (1-3): ").strip()
        
        export_format = {
            '1': 'csv',
            '2': 'json',
            '3': 'both'
        }.get(export_choice, 'csv')
        
        # Step 8: Debug mode
        print("\n" + "-" * 60)
        debug = input("Enable debug mode? (y/n, default n): ").strip().lower()
        self.debug_mode = debug == 'y'
        
        print("\n" + "="*60)
        print("         CONFIGURATION COMPLETE!")
        print("="*60)
        
        return {
            'query': search_query,
            'min_price': min_price,
            'max_price': max_price,
            'condition': condition_filter,
            'sort_by': sort_by,
            'max_pages': max_pages,
            'export_format': export_format
        }
    
    def search(self, query, max_pages=3, sort_by='best_match', min_price=None, max_price=None):
        """Search eBay for products"""
        sort_options = {
            'best_match': 12,
            'price_low': 15,
            'price_high': 16,
            'newest': 10
        }
        
        params = {
            '_nkw': query,
            '_sop': sort_options.get(sort_by, 12),
            '_ipg': 60
        }
        
        # Add price range to search
        if min_price:
            params['_udlo'] = min_price
        if max_price:
            params['_udhi'] = max_price
        
        all_products = []
        
        for page in range(1, max_pages + 1):
            params['_pgn'] = page
            url = f"{self.base_url}?{urlencode(params)}"
            
            if self.debug_mode:
                print(f"\nDebug: URL = {url}")
            
            print(f"Scraping page {page}/{max_pages}...", end=' ')
            products = self._scrape_page(url)
            all_products.extend(products)
            print(f"✓ Found {len(products)} items")
            
            if len(products) == 0 and page == 1:
                print("\n⚠️  WARNING: No products found. Possible reasons:")
                print("   - eBay is blocking the request")
                print("   - The search query returned no results")
                print("   - eBay has changed their HTML structure")
                print("   - You may need to use a VPN or proxy")
                
                if self.debug_mode:
                    print("\nTrying to diagnose the issue...")
                    self._diagnose_issue(url)
                break
            
            # Be nice to eBay's servers
            time.sleep(random.uniform(2, 4))
        
        return all_products
    
    def _diagnose_issue(self, url):
        """Diagnose why scraping might be failing"""
        try:
            response = self.session.get(url, timeout=15)
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response Length: {len(response.content)} bytes")
            
            if response.status_code == 403:
                print("❌ 403 Forbidden - eBay is blocking your requests")
                print("   Solutions: Use proxy, VPN, or eBay's official API")
            elif response.status_code == 429:
                print("❌ 429 Too Many Requests - You're being rate limited")
                print("   Solution: Wait a few minutes and try again")
            
            # Check if we got a CAPTCHA page
            if 'captcha' in response.text.lower() or 'robot' in response.text.lower():
                print("❌ CAPTCHA detected - eBay thinks you're a bot")
                print("   Solutions: Use proxy, reduce request frequency, or use API")
            
            # Save HTML for inspection
            with open('debug_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\n✓ Saved response to 'debug_response.html' for inspection")
            
        except Exception as e:
            print(f"❌ Error during diagnosis: {e}")
    
    def _scrape_page(self, url):
        """Scrape a single search results page with improved selectors"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Try multiple selectors as eBay's HTML can vary
            items = soup.find_all('li', {'class': 's-item'})
            
            if not items:
                # Try alternative selector
                items = soup.find_all('div', {'class': 's-item__wrapper'})
            
            if self.debug_mode:
                print(f"\nDebug: Found {len(items)} item containers")
            
            for idx, item in enumerate(items):
                product = self._extract_product_data(item)
                if product:
                    products.append(product)
                elif self.debug_mode and idx < 3:
                    print(f"Debug: Failed to extract data from item {idx}")
            
            return products
            
        except requests.RequestException as e:
            print(f"\n❌ Network Error: {e}")
            return []
        except Exception as e:
            print(f"\n❌ Unexpected Error: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return []
    
    def _extract_product_data(self, item):
        """Extract only selected fields from a product listing"""
        try:
            product = {}
            
            # Title - try multiple selectors
            if 'title' in self.selected_fields:
                title_elem = (item.find('span', {'role': 'heading'}) or 
                             item.find('div', {'class': 's-item__title'}) or
                             item.find('h3', {'class': 's-item__title'}))
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # Skip sponsored/header items
                    if title in ['Shop on eBay', 'New Listing', '']:
                        return None
                    product['title'] = title
                else:
                    if self.debug_mode:
                        print("Debug: Could not find title")
                    return None
            
            # Price
            if 'price' in self.selected_fields:
                price_elem = item.find('span', {'class': 's-item__price'})
                product['price'] = price_elem.get_text(strip=True) if price_elem else 'N/A'
            
            # Condition
            if 'condition' in self.selected_fields:
                condition_elem = (item.find('span', {'class': 'SECONDARY_INFO'}) or
                                item.find('span', string=lambda x: x and ('New' in x or 'Used' in x or 'Pre-Owned' in x)))
                product['condition'] = condition_elem.get_text(strip=True) if condition_elem else 'N/A'
            
            # Shipping
            if 'shipping' in self.selected_fields:
                shipping_elem = (item.find('span', {'class': 's-item__shipping'}) or
                               item.find('span', {'class': 's-item__logisticsCost'}))
                product['shipping'] = shipping_elem.get_text(strip=True) if shipping_elem else 'N/A'
            
            # URL
            if 'url' in self.selected_fields:
                a_tag = item.find('a', {'class': 's-item__link'})
                product['url'] = a_tag['href'] if a_tag and 'href' in a_tag.attrs else 'N/A'
            
            # Location
            if 'location' in self.selected_fields:
                location_elem = (item.find('span', {'class': 's-item__location'}) or
                               item.find('span', {'class': 's-item__itemLocation'}))
                product['location'] = location_elem.get_text(strip=True) if location_elem else 'N/A'
            
            # Image URL
            if 'image_url' in self.selected_fields:
                img_tag = item.find('img')
                if img_tag:
                    product['image_url'] = img_tag.get('src', img_tag.get('data-src', 'N/A'))
                else:
                    product['image_url'] = 'N/A'
            
            # Sold count
            if 'sold_count' in self.selected_fields:
                sold_elem = item.find('span', {'class': 's-item__quantitySold'})
                product['sold_count'] = sold_elem.get_text(strip=True) if sold_elem else '0'
            
            product['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return product if len(product) > 1 else None  # Must have more than just timestamp
            
        except Exception as e:
            if self.debug_mode:
                print(f"Debug: Extraction error - {e}")
            return None
    
    def filter_by_condition(self, products, condition):
        """Filter products by condition"""
        if not condition:
            return products
        
        filtered = []
        for product in products:
            prod_condition = product.get('condition', '').lower()
            if condition.lower() in prod_condition:
                filtered.append(product)
        
        return filtered
    
    def save_to_csv(self, products, filename='ebay_products.csv'):
        """Save products to CSV file"""
        if not products:
            print("No products to save")
            return
        
        keys = products[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(products)
        
        print(f"✓ Saved {len(products)} products to {filename}")
    
    def save_to_json(self, products, filename='ebay_products.json'):
        """Save products to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(products)} products to {filename}")
    
    def display_summary(self, products):
        """Display summary of scraped data"""
        print("\n" + "="*60)
        print("         SCRAPING SUMMARY")
        print("="*60)
        print(f"Total products scraped: {len(products)}")
        
        if 'price' in self.selected_fields and products:
            prices = []
            for product in products:
                try:
                    price_str = product.get('price', '').replace('$', '').replace(',', '').replace('£', '').replace('€', '')
                    if 'to' in price_str:
                        price = float(price_str.split('to')[0].strip())
                    else:
                        price = float(price_str)
                    prices.append(price)
                except (ValueError, AttributeError):
                    continue
            
            if prices:
                print(f"Average price: ${sum(prices)/len(prices):.2f}")
                print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
        
        print("="*60 + "\n")


def main():
    scraper = EbayScraper()
    
    # Get user preferences
    config = scraper.get_user_preferences()
    
    # Start scraping
    print("\n🔍 Starting scrape...\n")
    products = scraper.search(
        query=config['query'],
        max_pages=config['max_pages'],
        sort_by=config['sort_by'],
        min_price=config['min_price'],
        max_price=config['max_price']
    )
    
    # Apply condition filter
    if config['condition'] and products:
        original_count = len(products)
        products = scraper.filter_by_condition(products, config['condition'])
        print(f"\n✓ Filtered from {original_count} to {len(products)} {config['condition']} items")
    
    if not products:
        print("\n⚠️  No products scraped. Check the warnings above.")
        print("\nTroubleshooting tips:")
        print("1. Try a different search term")
        print("2. Run with debug mode enabled")
        print("3. Use a VPN or proxy service")
        print("4. Consider using eBay's official API for reliable scraping")
        return
    
    # Display summary
    scraper.display_summary(products)
    
    # Display sample products
    print("Sample products (first 3):")
    print("-" * 60)
    for i, product in enumerate(products[:3], 1):
        print(f"\n{i}.")
        for key, value in product.items():
            if key != 'scraped_at':
                print(f"  {key}: {value[:100] if isinstance(value, str) and len(value) > 100 else value}")
    
    # Save results
    if config['export_format'] in ['csv', 'both']:
        scraper.save_to_csv(products)
    
    if config['export_format'] in ['json', 'both']:
        scraper.save_to_json(products)
    
    print("\n✅ Scraping complete!")


if __name__ == "__main__":
    main()
