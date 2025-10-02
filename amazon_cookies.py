from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def setup_chrome_driver():
    """Set up Chrome driver with options"""
    chrome_options = Options()
    
    # Optional: Add these for better compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Keep browser open until script ends
    chrome_options.add_experimental_option("detach", True)
    
    # You might need to specify the path to chromedriver if it's not in PATH
    # service = Service("/path/to/chromedriver")  # Uncomment and modify if needed
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_amazon_cookies():
    """Main function to fetch Amazon cookies after manual login"""
    
    # Set up the driver
    driver = setup_chrome_driver()
    
    try:
        print("Opening Amazon.ca...")
        driver.get("https://www.amazon.ca")
        
        print("\n" + "="*50)
        print("PLEASE LOG IN TO YOUR AMAZON ACCOUNT")
        print("The script will automatically detect when you're logged in...")
        print("Looking for Your Account link...")
        print("="*50 + "\n")
        
        # Wait for login by detecting the "Your Account" link with the specific pattern
        login_detected = False
        start_time = time.time()
        timeout = 300  # 5 minutes in seconds
        
        # XPath to find <a> element with href containing both patterns
        account_link_xpath = "//a[contains(@href, 'https://www.amazon.ca/') and contains(@href, '=nav_youraccount_btn')]"
        
        print("Waiting for login detection...")
        
        while not login_detected and (time.time() - start_time) < timeout:
            try:
                # Check if the login element is present
                account_elements = driver.find_elements(By.XPATH, account_link_xpath)
                
                if account_elements and account_elements[0].is_displayed():
                    print("Login detected successfully! Found Your Account link.")
                    login_detected = True
                else:
                    # Wait a bit before checking again
                    time.sleep(2)
                    
            except Exception as e:
                # Wait a bit before trying again
                time.sleep(2)
        
        if not login_detected:
            print("Login detection timed out after 5 minutes.")
            proceed = input("\nPress ENTER to continue with cookie capture anyway, or 'q' to quit: ").strip().lower()
            if proceed == 'q':
                return None
        
        # Get all cookies
        selenium_cookies = driver.get_cookies()
        
        # Convert to the required format
        cookies = []
        for cookie in selenium_cookies:
            formatted_cookie = {
                "domain": cookie.get('domain', ''),
                "expirationDate": cookie.get('expiry', None),
                "hostOnly": not cookie.get('domain', '').startswith('.'),
                "httpOnly": cookie.get('httpOnly', False),
                "name": cookie.get('name', ''),
                "path": cookie.get('path', '/'),
                "sameSite": cookie.get('sameSite', None),
                "secure": cookie.get('secure', False),
                "session": cookie.get('expiry') is None,
                "storeId": None,
                "value": cookie.get('value', '')
            }
            cookies.append(formatted_cookie)
        
        print(f"\nFound {len(cookies)} cookies")
        
        # Save cookies to a JSON file in the required format
        with open('amazon_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        print("Cookies saved to 'amazon_cookies.json'")
        
        # Print session cookies (the important ones for maintaining login)
        session_cookies = [cookie for cookie in cookies if 'session' in cookie['name'].lower() or 
                          cookie['name'] in ['at-main', 'sess-at-main', 'x-main', 'session-id', 
                                           'at-acbca', 'sess-at-acbca', 'sst-acbca', 'ubid-acbca', 'x-acbca']]
        
        print(f"\nKey session cookies found: {len(session_cookies)}")
        for cookie in session_cookies:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
        
        return cookies
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    finally:
        # Ask user if they want to close the browser
        close_browser = input("\nDo you want to close the browser? (y/n): ").lower().strip()
        if close_browser == 'y':
            driver.quit()
            print("Browser closed.")
        else:
            print("Browser will remain open.")

def load_cookies_to_session(cookies_file='amazon_cookies.json'):
    """Helper function to load cookies back into a new browser session"""
    driver = setup_chrome_driver()
    
    try:
        # First visit Amazon to set the domain
        driver.get("https://www.amazon.ca")
        
        # Load cookies from file
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        # Add each cookie to the browser (convert back to Selenium format)
        for cookie in cookies:
            try:
                selenium_cookie = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie['path'],
                    'secure': cookie['secure'],
                    'httpOnly': cookie['httpOnly']
                }
                
                # Add expiry if it's not a session cookie
                if not cookie['session'] and cookie['expirationDate']:
                    selenium_cookie['expiry'] = int(cookie['expirationDate'])
                
                # Add sameSite if present
                if cookie['sameSite']:
                    selenium_cookie['sameSite'] = cookie['sameSite']
                
                driver.add_cookie(selenium_cookie)
            except Exception as e:
                print(f"Could not add cookie {cookie['name']}: {e}")
        
        # Refresh the page to apply cookies
        driver.refresh()
        print("Cookies loaded successfully!")
        
        return driver
        
    except Exception as e:
        print(f"Error loading cookies: {e}")
        driver.quit()
        return None

if __name__ == "__main__":
    print("Amazon Cookie Fetcher")
    print("====================")
    
    choice = input("Choose an option:\n1. Fetch new cookies\n2. Load existing cookies\nEnter (1 or 2): ").strip()
    
    if choice == "1":
        cookies = fetch_amazon_cookies()
        if cookies:
            print(f"\nSuccessfully captured {len(cookies)} cookies!")
    
    elif choice == "2":
        try:
            driver = load_cookies_to_session()
            if driver:
                print("Cookies loaded! You should now be logged in.")
                input("Press ENTER to close the browser...")
                driver.quit()
        except FileNotFoundError:
            print("No cookies file found. Please run option 1 first.")
    
    else:
        print("Invalid choice. Please run the script again.")