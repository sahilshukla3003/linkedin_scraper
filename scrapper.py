from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time
import random
from fake_useragent import UserAgent
import re


class LinkedInScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        chrome_options = Options()
        
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={ua.random}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--log-level=3')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
    
    def login(self):
        """Login to LinkedIn"""
        try:
            print("Logging into LinkedIn...")
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(random.uniform(2, 4))
            
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            time.sleep(1)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            time.sleep(1)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(random.uniform(5, 7))
            
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("✓ Successfully logged in\n")
                return True
            else:
                print("⚠ Login may require verification\n")
                return False
        except Exception as e:
            print(f"✗ Login failed: {str(e)}\n")
            return False
    
    def extract_text_safe(self, selectors):
        """Try multiple selectors and return first match"""
        for selector_type, selector in selectors:
            try:
                if selector_type == "xpath":
                    element = self.driver.find_element(By.XPATH, selector)
                elif selector_type == "css":
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                text = element.text.strip()
                if text:
                    return text
            except:
                continue
        return ""
    
    def extract_company_from_headline(self, headline):
        """Enhanced company extraction with multiple pattern matching strategies"""
        if not headline:
            return ""
        
        # Strategy 1: "at Company" or "@ Company" pattern
        at_patterns = [
            r'\bat\s+([^|•\n,.;]+?)(?:\s*[|•/;]|$)',
            r'@\s*([^|•\n,.;]+?)(?:\s*[|•/;]|$)',
        ]
        
        for pattern in at_patterns:
            match = re.search(pattern, headline, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                return self.clean_company_name(company)
        
        # Strategy 2: "of Company" pattern
        of_pattern = r'(?:CEO|CTO|CFO|Founder|President|Director|Head)\s+of\s+([A-Z][^,\n|;]+?)(?:[,|;.]|$)'
        match = re.search(of_pattern, headline, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            return self.clean_company_name(company)
        
        # Strategy 3: Position + comma + Company
        comma_pattern = r'(?:Chair|CEO|CTO|CFO|President|Director|Founder|Co-Founder|Partner|Engineer|Manager|Lead),\s*([A-Z][^,\n]+?)(?:\s+and\s+|[,;.]|$)'
        match = re.search(comma_pattern, headline)
        if match:
            company = match.group(1).strip()
            return self.clean_company_name(company)
        
        # Strategy 4: Co-Founder format
        if re.search(r'(?:Co-)?Founder', headline, re.IGNORECASE):
            founder_pattern = r'(?:Co-)?Founder[,\s]+([A-Z][^.\n|;]+?)(?:[,;.]|$)'
            match = re.search(founder_pattern, headline)
            if match:
                companies_text = match.group(1).strip()
                first_company = companies_text.split(',')[0].strip()
                first_company = re.sub(r'\s+(?:and|&)\s+.*', '', first_company)
                return self.clean_company_name(first_company)
        
        # Strategy 5: Known company database
        known_companies = [
            'Microsoft', 'Google', 'Apple', 'Amazon', 'Meta', 'Facebook',
            'LinkedIn', 'Tesla', 'PayPal', 'Netflix', 'Oracle', 'IBM',
            'Intel', 'Cisco', 'Adobe', 'Salesforce', 'Uber', 'Airbnb',
            'Spotify', 'Snapchat', 'Zoom', 'Shopify', 'HubSpot', 'Canva',
            'Gates Foundation', 'NetApp', 'Superhuman', 'Wing Venture Capital',
            'Amazon Music', 'GEEK performance food', 'Qualcomm', 'Dropbox',
            'Stripe', 'Pinterest', 'Reddit', 'Twitch', 'Discord', 'Figma'
        ]
        
        for company in known_companies:
            if re.search(r'\b' + re.escape(company) + r'\b', headline, re.IGNORECASE):
                return company
        
        return ""
    
    def clean_company_name(self, company):
        """Clean up extracted company name"""
        if not company:
            return ""
        
        company = re.sub(r'[,\.\)]+$', '', company).strip()
        company = re.sub(r'\s+(?:Inc\.?|Corp\.?|Ltd\.?|LLC)$', '', company, flags=re.IGNORECASE)
        
        if len(company) > 50:
            company = company[:50].rsplit(' ', 1)[0]
        
        return company.strip()
    
    def scrape_profile(self, profile_url):
        """Scrape only reliable public profile data"""
        try:
            print(f"Scraping: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 5))
            
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(2)
            
            profile_data = {
                'url': profile_url,
                'name': '',
                'headline': '',
                'location': '',
                'company': ''
            }
            
            # Extract name
            name_selectors = [
                ("xpath", "//h1[contains(@class, 'text-heading-xlarge')]"),
                ("xpath", "//h1[contains(@class, 'inline')]"),
                ("css", "h1.text-heading-xlarge")
            ]
            profile_data['name'] = self.extract_text_safe(name_selectors)
            
            # Extract headline
            headline_selectors = [
                ("xpath", "//div[contains(@class, 'text-body-medium') and contains(@class, 'break-words')]"),
                ("css", "div.text-body-medium.break-words")
            ]
            profile_data['headline'] = self.extract_text_safe(headline_selectors)
            
            # Extract location
            location_selectors = [
                ("xpath", "//span[contains(@class, 'text-body-small') and contains(@class, 'inline')]"),
                ("css", "span.text-body-small.inline")
            ]
            profile_data['location'] = self.extract_text_safe(location_selectors)
            
            # Extract company
            if profile_data['headline']:
                profile_data['company'] = self.extract_company_from_headline(profile_data['headline'])
            
            # Print results
            print(f"  ✓ Name: {profile_data['name']}")
            print(f"  ✓ Company: {profile_data['company'] if profile_data['company'] else '(not found)'}")
            print(f"  ✓ Location: {profile_data['location']}")
            print()
            
            return profile_data
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}\n")
            return None
    
    def scrape_multiple_profiles(self, profile_urls, output_file='linkedin_profiles.json'):
        """Scrape multiple profiles and save to JSON"""
        results = []
        
        print(f"Starting to scrape {len(profile_urls)} profiles...\n")
        print("="*60)
        
        for idx, url in enumerate(profile_urls, 1):
            print(f"[{idx}/{len(profile_urls)}] ", end="")
            
            profile_data = self.scrape_profile(url)
            
            if profile_data and profile_data['name']:
                results.append(profile_data)
            
            if idx < len(profile_urls):
                delay = random.uniform(5, 8)
                print(f"Waiting {delay:.1f}s...\n")
                time.sleep(delay)
        
        # Save to JSON
        if results:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print("="*60)
            print(f"✓ SUCCESS: Saved {len(results)} profiles to {output_file}")
            print("="*60)
            
            print("\nSUMMARY:")
            print(f"  Total scraped: {len(results)}/{len(profile_urls)}")
            print(f"  With names: {sum(1 for p in results if p['name'])}")
            print(f"  With companies: {sum(1 for p in results if p['company'])}")
            print(f"  With locations: {sum(1 for p in results if p['location'])}")
            print(f"  Success rate: {sum(1 for p in results if p['company']) / len(results) * 100:.1f}%")
            
            print("\nFULL DATA:")
            print("-" * 60)
            for i, p in enumerate(results, 1):
                print(f"{i}. {p['name']}")
                print(f"   Company: {p['company'] if p['company'] else 'N/A'}")
                print(f"   Location: {p['location']}")
                print()
        else:
            print("\n✗ No profiles were successfully scraped")
        
        return results
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


def main():
    # 20 VERIFIED LinkedIn profile URLs with accessible public data
    profile_urls = [
        # 
        'https://www.linkedin.com/in/satyanadella/',          
        'https://www.linkedin.com/in/jeffweiner08/',          
        'https://www.linkedin.com/in/williamhgates/',         
        'https://www.linkedin.com/in/reidhoffman/',           
        'https://www.linkedin.com/in/brianchesky/',           
        'https://www.linkedin.com/in/gkumar/',                
        'https://www.linkedin.com/in/harsh-singhal/',         
        'https://www.linkedin.com/in/rahulvohra/',            
        'https://www.linkedin.com/in/tanayjaipuria/',         
        'https://www.linkedin.com/in/adammosseri/',
        'https://www.linkedin.com/in/joshelman/',
        'https://www.linkedin.com/in/chamath/',
        'https://www.linkedin.com/in/naval/',
        'https://www.linkedin.com/in/paulgraham/',            
        'https://www.linkedin.com/in/pmarca/',
        'https://www.linkedin.com/in/shreyas-doshi/',       
        'https://www.linkedin.com/in/lenny-rachitsky/',     
        'https://www.linkedin.com/in/gergely-orosz/',         
        'https://www.linkedin.com/in/wes-kao/',               
        'https://www.linkedin.com/in/hiten-shah/',            
    ]
    
    # Credentials
    EMAIL = 'sahilshula454@gmail.com'
    PASSWORD = 'Sahil@123'
    
    print("\n" + "="*60)
    print("LINKEDIN PROFILE SCRAPER - Verified Profiles")
    print("="*60 + "\n")
    
    scraper = LinkedInScraper(EMAIL, PASSWORD)
    
    try:
        if scraper.login():
            scraper.scrape_multiple_profiles(profile_urls)
        else:
            print("Login failed - cannot proceed")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        scraper.close()
        print("\nBrowser closed.")


if __name__ == '__main__':
    main()
