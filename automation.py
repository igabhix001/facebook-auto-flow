import os
import time
import random
import string
import logging
import requests
import traceback
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import names
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FacebookSignupAutomation:
    """Class to handle Facebook signup automation"""
    
    def __init__(self):
        """Initialize the automation with browser setup"""
        logger.info("Initializing FacebookSignupAutomation")
        self.driver = None
        try:
            # Create screenshots directory if it doesn't exist
            self.screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
            os.makedirs(self.screenshots_dir, exist_ok=True)
            
            self.setup_browser()
            self.captcha_api_key = os.getenv('CAPTCHA_API_KEY')
            self.captcha_service_url = os.getenv('CAPTCHA_SERVICE_URL', 'https://2captcha.com/in.php')
            self.max_retries = 3
            self.facebook_signup_url = "https://www.facebook.com/signup"
            logger.info("FacebookSignupAutomation initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing FacebookSignupAutomation: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def setup_browser(self):
        """Set up the browser with appropriate options"""
        logger.info("Setting up browser")
        try:
            chrome_options = Options()
            
            # Add arguments to mimic human behavior and avoid detection
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
            ]
            
            chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Disable save password and other notifications
            chrome_options.add_experimental_option("prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,  # Block notifications
                "profile.default_content_setting_values.popups": 2  # Block popups
            })
            
            # Uncomment the following line for headless mode in production
            # chrome_options.add_argument("--headless")
            
            # Use the specific ChromeDriver that was downloaded
            logger.info("Using the downloaded ChromeDriver")
            chrome_driver_path = r"C:\Users\abhir\Downloads\facebook Auto-flow\chromedriver_win32\chromedriver.exe"
            
            if os.path.exists(chrome_driver_path):
                logger.info(f"ChromeDriver found at {chrome_driver_path}")
                service = Service(executable_path=chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome WebDriver created successfully")
            else:
                logger.error(f"ChromeDriver not found at {chrome_driver_path}")
                raise Exception(f"ChromeDriver not found at {chrome_driver_path}")
            
            # Set window size
            self.driver.set_window_size(1366, 768)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            })
            
            logger.info("Browser setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up browser: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def take_screenshot(self, name_prefix):
        """Take a screenshot and save it to the screenshots directory"""
        try:
            screenshot_path = os.path.join(self.screenshots_dir, f"{name_prefix}_{int(time.time())}.png")
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    def dismiss_popups(self):
        """Dismiss any browser popups like save password dialogs"""
        try:
            # Press Escape key to dismiss most browser dialogs
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            logger.info("Sent ESC key to dismiss any popups")
            
            # Try to find and click "Not now" or "Cancel" buttons for common dialogs
            dismiss_buttons_xpaths = [
                "//button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(text(), 'No thanks')]",
                "//button[contains(text(), 'Never')]",
                "//button[contains(text(), 'Close')]"
            ]
            
            for xpath in dismiss_buttons_xpaths:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    if buttons:
                        buttons[0].click()
                        logger.info(f"Clicked dismiss button: {xpath}")
                        time.sleep(0.5)  # Short delay after clicking
                except Exception as e:
                    logger.debug(f"No popup button found for xpath {xpath}: {str(e)}")
        
        except Exception as e:
            logger.warning(f"Error dismissing popups: {str(e)}")
    
    def wait_for_page_changes(self, timeout=30):
        """Wait for the page to finish loading or changing"""
        try:
            # Wait for document.readyState to be 'complete'
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait a bit more for any AJAX requests to complete
            time.sleep(1)
            
            # Try to detect if page is still loading by checking for loading indicators
            try:
                loading_indicators = self.driver.find_elements(By.XPATH, 
                    "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(@class, 'progress')]")
                
                if loading_indicators:
                    # If loading indicators are found, wait for them to disappear
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        loading_indicators = self.driver.find_elements(By.XPATH, 
                            "//*[contains(@class, 'loading') or contains(@class, 'spinner') or contains(@class, 'progress')]")
                        
                        if not loading_indicators or not any(indicator.is_displayed() for indicator in loading_indicators):
                            break
                        
                        time.sleep(0.5)
            except Exception as e:
                logger.debug(f"Error checking for loading indicators: {str(e)}")
            
            logger.info("Page finished loading")
            return True
        
        except Exception as e:
            logger.warning(f"Error waiting for page changes: {str(e)}")
            return False
    
    def generate_random_name(self):
        """Generate a random first name"""
        return names.get_first_name()
    
    def generate_random_surname(self):
        """Generate a random surname"""
        return names.get_last_name()
    
    def generate_random_dob(self):
        """Generate a random date of birth for someone between 18-65 years old"""
        today = datetime.now()
        min_age = 18
        max_age = 65
        
        # Calculate date range
        max_date = today - timedelta(days=min_age*365)
        min_date = today - timedelta(days=max_age*365)
        
        # Generate random date in range
        days_range = (max_date - min_date).days
        random_days = random.randint(0, days_range)
        random_date = min_date + timedelta(days=random_days)
        
        return {
            'day': random_date.day,
            'month': random_date.month,
            'year': random_date.year
        }
    
    def generate_random_password(self, length=12):
        """Generate a strong random password"""
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*'
        
        # Ensure at least one character from each set
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special)
        ]
        
        # Fill the rest of the password
        remaining_length = length - len(password)
        all_chars = lowercase + uppercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(remaining_length))
        
        # Shuffle the password
        random.shuffle(password)
        
        # Convert list to string
        return ''.join(password)
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add a random delay to simulate human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def solve_captcha(self, captcha_element):
        """Solve captcha using third-party service"""
        if not self.captcha_api_key:
            logger.error("Captcha API key not found in environment variables")
            return None
        
        try:
            # Take screenshot of captcha element
            captcha_path = os.path.join(self.screenshots_dir, "captcha.png")
            captcha_element.screenshot(captcha_path)
            
            # Send captcha to solving service
            with open(captcha_path, "rb") as f:
                files = {"file": f}
                data = {
                    "key": self.captcha_api_key,
                    "method": "post"
                }
                response = requests.post(self.captcha_service_url, files=files, data=data)
            
            if "OK|" in response.text:
                captcha_id = response.text.split("|")[1]
                
                # Wait for solution
                for _ in range(30):  # Try for 30 seconds
                    time.sleep(1)
                    solution_response = requests.get(
                        f"https://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={captcha_id}"
                    )
                    if "OK|" in solution_response.text:
                        return solution_response.text.split("|")[1]
            
            logger.error(f"Failed to solve captcha: {response.text}")
            return None
        
        except Exception as e:
            logger.error(f"Error solving captcha: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        finally:
            # Clean up
            if os.path.exists(captcha_path):
                os.remove(captcha_path)
    
    def fill_signup_form(self, phone_number):
        """Fill the Facebook signup form with random data and the provided phone number"""
        try:
            # Generate random data
            first_name = self.generate_random_name()
            surname = self.generate_random_surname()
            dob = self.generate_random_dob()
            password = self.generate_random_password()
            gender = random.choice(["Male", "Female"])
            
            logger.info(f"Generated data - Name: {first_name} {surname}, DOB: {dob['day']}/{dob['month']}/{dob['year']}, Gender: {gender}")
            
            # Fill first name
            logger.info("Filling first name field")
            first_name_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "firstname"))
            )
            first_name_field.clear()
            first_name_field.send_keys(first_name)
            self.random_delay()
            
            # Fill surname
            logger.info("Filling surname field")
            surname_field = self.driver.find_element(By.NAME, "lastname")
            surname_field.clear()
            surname_field.send_keys(surname)
            self.random_delay()
            
            # Fill mobile number or email
            logger.info(f"Filling mobile number field with {phone_number}")
            mobile_field = self.driver.find_element(By.NAME, "reg_email__")
            mobile_field.clear()
            mobile_field.send_keys(phone_number)
            self.random_delay()
            
            # Fill password
            logger.info("Filling password field")
            password_field = self.driver.find_element(By.NAME, "reg_passwd__")
            password_field.clear()
            password_field.send_keys(password)
            self.random_delay()
            
            # Select birthday
            logger.info(f"Selecting birthday: {dob['day']}/{dob['month']}/{dob['year']}")
            day_select = Select(self.driver.find_element(By.NAME, "birthday_day"))
            day_select.select_by_value(str(dob['day']))
            self.random_delay()
            
            month_select = Select(self.driver.find_element(By.NAME, "birthday_month"))
            month_select.select_by_value(str(dob['month']))
            self.random_delay()
            
            year_select = Select(self.driver.find_element(By.NAME, "birthday_year"))
            year_select.select_by_value(str(dob['year']))
            self.random_delay()
            
            # Select gender
            logger.info(f"Selecting gender: {gender}")
            if gender == "Male":
                self.driver.find_element(By.XPATH, "//input[@name='sex' and @value='2']").click()
            else:
                self.driver.find_element(By.XPATH, "//input[@name='sex' and @value='1']").click()
            
            self.random_delay()
            
            # Check for captcha
            try:
                captcha_element = self.driver.find_element(By.CLASS_NAME, "captcha_image")
                logger.info("Captcha detected, attempting to solve...")
                
                captcha_solution = self.solve_captcha(captcha_element)
                if captcha_solution:
                    captcha_input = self.driver.find_element(By.NAME, "captcha_response")
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_solution)
                    logger.info("Captcha solution entered")
                else:
                    logger.error("Failed to solve captcha")
                    return {
                        "status": "Failed",
                        "error": "Captcha solving failed"
                    }
            except NoSuchElementException:
                logger.info("No captcha detected")
            
            # Take screenshot before clicking signup
            self.take_screenshot("before_signup")
            
            # Store the current URL before clicking
            before_url = self.driver.current_url
            logger.info(f"URL before clicking signup: {before_url}")
            
            # Click signup button
            logger.info("Clicking signup button")
            signup_button = self.driver.find_element(By.NAME, "websubmit")
            signup_button.click()
            
            # SIMPLIFIED APPROACH: Wait a fixed amount of time, then check what happened
            logger.info("Waiting 10 seconds after clicking signup button...")
            time.sleep(10)
            
            # Take screenshot after waiting
            self.take_screenshot("after_signup_wait")
            
            # Get current URL and page source
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            logger.info(f"URL after signup: {current_url}")
            
            # Check if URL changed
            if current_url != before_url:
                logger.info("URL changed after signup")
                
                # Check if we're on an OTP page
                otp_indicators = [
                    "Enter the confirmation code",
                    "Let us know if this mobile number belongs to you",
                    "Enter the code in the SMS sent to",
                    "FB-",
                    "Send SMS Again",
                    "Update Contact Info",
                    "confirmation code",
                    "verification code"
                ]
                
                for indicator in otp_indicators:
                    if indicator in page_source:
                        logger.info(f"OTP indicator found: {indicator}")
                        return {
                            "status": "OTP Sent",
                            "message": f"OTP page detected: {indicator}",
                            "url": current_url
                        }
                
                # If URL changed but not to OTP page, consider it a success
                logger.info("URL changed but not to OTP page, considering as success")
                return {
                    "status": "Success",
                    "message": "Signup completed, redirected to new page",
                    "url": current_url
                }
            
            # Wait longer for OTP page or error messages to appear (up to 30 seconds total)
            logger.info("Waiting for OTP page or visible error messages to appear...")
            max_wait_time = 30  # Maximum wait time in seconds
            start_time = time.time()
            otp_found = False
            error_found = False
            error_text = ""
            otp_text = ""
            
            while time.time() - start_time < max_wait_time and not (otp_found or error_found):
                try:
                    # Take a screenshot every few seconds
                    if int(time.time() - start_time) % 6 == 0:
                        self.take_screenshot(f"waiting_for_result_{int(time.time() - start_time)}")
                    
                    # Get current page source and URL
                    current_url = self.driver.current_url
                    page_source = self.driver.page_source
                    
                    # Check for OTP indicators
                    otp_indicators = [
                        "Enter the confirmation code",
                        "Let us know if this mobile number belongs to you",
                        "Enter the code in the SMS sent to",
                        "FB-",
                        "Send SMS Again",
                        "Update Contact Info",
                        "confirmation code",
                        "verification code"
                    ]
                    
                    for indicator in otp_indicators:
                        if indicator in page_source:
                            logger.info(f"OTP indicator found after waiting: {indicator}")
                            otp_found = True
                            otp_text = indicator
                            break
                    
                    # If OTP found, break out of the loop
                    if otp_found:
                        break
                    
                    # Check for common error message elements
                    error_xpath_patterns = [
                        "//div[@id='reg_error_inner']",
                        "//*[contains(@class, 'error') and string-length(text()) > 0]",
                        "//*[contains(@role, 'alert') and string-length(text()) > 0]",
                        "//div[contains(@class, 'notification') and string-length(text()) > 0]",
                        "//div[contains(text(), 'error') or contains(text(), 'Error')]"
                    ]
                    
                    for xpath in error_xpath_patterns:
                        error_elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in error_elements:
                            if element.is_displayed() and element.text and len(element.text.strip()) > 0:
                                error_text = element.text.strip()
                                logger.info(f"Found visible error text: {error_text}")
                                error_found = True
                                break
                        
                        if error_found:
                            break
                    
                    # If no result found yet, wait a bit and check again
                    if not (otp_found or error_found):
                        time.sleep(2)
                
                except Exception as e:
                    logger.warning(f"Error while checking for OTP or error messages: {str(e)}")
                    time.sleep(2)
            
            # If we found OTP page
            if otp_found:
                logger.info(f"OTP page detected after waiting: {otp_text}")
                self.take_screenshot("otp_detected")
                return {
                    "status": "OTP Sent",
                    "message": f"OTP page detected after waiting: {otp_text}",
                    "url": current_url
                }
            
            # If we found an error message
            if error_found and error_text:
                logger.info(f"Error message detected after waiting: {error_text}")
                self.take_screenshot("error_detected")
                return {
                    "status": "Failed",
                    "error": error_text,
                    "url": current_url
                }
            
            # Check for "Find Account" popup
            if "Find Your Account" in page_source or "Find Account" in page_source:
                logger.info("Find Account popup detected")
                
                # Try to click "Create New Account" button
                try:
                    create_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Create New Account')] | //button[contains(text(), 'Create New Account')]")
                    if create_buttons:
                        logger.info("Clicking Create New Account button")
                        create_buttons[0].click()
                        time.sleep(5)
                        
                        # Check again for OTP page after clicking
                        current_url = self.driver.current_url
                        page_source = self.driver.page_source
                        
                        for indicator in otp_indicators:
                            if indicator in page_source:
                                logger.info(f"OTP indicator found after clicking Create New Account: {indicator}")
                                return {
                                    "status": "OTP Sent",
                                    "message": f"OTP page detected after clicking Create New Account: {indicator}",
                                    "url": current_url
                                }
                        
                        return {
                            "status": "Success",
                            "message": "Created new account after Find Account popup",
                            "url": current_url
                        }
                except Exception as e:
                    logger.warning(f"Error clicking Create New Account button: {str(e)}")
                
                return {
                    "status": "Failed",
                    "error": "Phone number already exists",
                    "url": current_url
                }
            
            # FALLBACK: If we can't determine what happened, check if we're still on the signup page
            if "signup" in current_url:
                logger.info("Still on signup page, checking for any visible feedback")
                
                # Look for any feedback elements
                try:
                    feedback_elements = self.driver.find_elements(By.XPATH, 
                        "//*[contains(@class, 'feedback') or contains(@class, 'message') or contains(@class, 'notification')]")
                    
                    if feedback_elements:
                        feedback_text = feedback_elements[0].text
                        logger.info(f"Feedback message found: {feedback_text}")
                        self.take_screenshot("feedback_detected")
                        return {
                            "status": "Feedback",
                            "message": feedback_text,
                            "url": current_url
                        }
                except Exception as e:
                    logger.warning(f"Error checking for feedback elements: {str(e)}")
                
                logger.warning("Still on signup page but no feedback found, may indicate form validation issues")
                self.take_screenshot("possible_validation_issue")
                return {
                    "status": "Validation Issue",
                    "error": "Form may have validation issues preventing submission",
                    "url": current_url
                }
            else:
                # We've been redirected somewhere, but not to an OTP page
                logger.info(f"Redirected to a new page: {current_url}")
                
                # Check if we're on a success page
                success_indicators = ["welcome", "home", "feed", "checkpoint", "confirm"]
                if any(indicator in current_url.lower() for indicator in success_indicators):
                    logger.info("Redirected to what appears to be a success page")
                    self.take_screenshot("success_page")
                    return {
                        "status": "Success",
                        "message": "Account created successfully or additional verification needed",
                        "url": current_url
                    }
                
                # If we can't determine the outcome
                logger.warning("Redirected to an unknown page")
                self.take_screenshot("unknown_redirect")
                return {
                    "status": "Unknown",
                    "message": "Redirected to an unknown page",
                    "url": current_url
                }
        
        except Exception as e:
            logger.error(f"Error filling signup form: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Take screenshot on error
            self.take_screenshot("error_filling_form")
            
            return {
                "status": "Failed",
                "error": str(e)
            }
    
    def check_signup_result(self):
        """Check if signup was successful (OTP sent) or if there was an error"""
        try:
            # Get current URL to help determine state
            current_url = self.driver.current_url
            logger.info(f"Current URL after signup: {current_url}")
            
            # Check for OTP confirmation page - use multiple detection methods with exact text patterns
            try:
                # Method 1: Check for OTP input field with explicit wait
                try:
                    otp_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'code_') or contains(@name, 'code') or contains(@placeholder, 'code')]"))
                    )
                    logger.info("OTP input field detected")
                    self.take_screenshot("otp_page_detected")
                    return {
                        "status": "OTP Sent",
                        "url": current_url
                    }
                except TimeoutException:
                    logger.info("No OTP input field detected with explicit wait")
                
                # Method 2: Check for EXACT text patterns indicating OTP was sent
                otp_text_patterns = [
                    "Enter the confirmation code from the text message",
                    "Let us know if this mobile number belongs to you",
                    "Enter the code in the SMS sent to",
                    "FB-",
                    "Send SMS Again",
                    "Update Contact Info",
                    "confirmation code",
                    "sent you a code",
                    "enter the code"
                ]
                
                page_source = self.driver.page_source
                for pattern in otp_text_patterns:
                    if pattern in page_source:
                        logger.info(f"OTP text pattern detected: '{pattern}'")
                        self.take_screenshot("otp_text_detected")
                        return {
                            "status": "OTP Sent",
                            "url": current_url
                        }
                
                # Method 3: Look for elements containing these phrases
                for pattern in otp_text_patterns:
                    try:
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
                        if elements:
                            logger.info(f"OTP element with text '{pattern}' found")
                            self.take_screenshot("otp_element_detected")
                            return {
                                "status": "OTP Sent",
                                "url": current_url
                            }
                    except Exception as e:
                        logger.debug(f"Error searching for OTP text pattern '{pattern}': {str(e)}")
                
                logger.info("No OTP text patterns detected")
            except Exception as e:
                logger.warning(f"Error checking for OTP elements: {str(e)}")
            
            # Check for error messages with explicit wait
            try:
                # First try to find error elements by class or role
                try:
                    error_element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'alert') or contains(@role, 'alert')]"))
                    )
                    error_text = error_element.text
                    logger.info(f"Error element found with text: {error_text}")
                    self.take_screenshot("error_detected")
                    return {
                        "status": "Failed",
                        "error": error_text,
                        "url": current_url
                    }
                except TimeoutException:
                    logger.info("No error elements found by class or role")
                
                # Check for common error text patterns
                error_patterns = [
                    "phone number you entered isn't valid",
                    "already been taken",
                    "Please try again later",
                    "suspicious activity",
                    "Something went wrong",
                    "error",
                    "invalid",
                    "try again",
                    "cannot",
                    "unavailable"
                ]
                
                page_source = self.driver.page_source.lower()
                for error in error_patterns:
                    if error.lower() in page_source:
                        logger.info(f"Error pattern detected: '{error}'")
                        self.take_screenshot("error_pattern_detected")
                        return {
                            "status": "Failed",
                            "error": error,
                            "url": current_url
                        }
                
                # Look for elements containing the word "error"
                try:
                    error_word_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error')]")
                    if error_word_elements:
                        error_text = error_word_elements[0].text
                        logger.info(f"Error word found in element with text: {error_text}")
                        self.take_screenshot("error_word_detected")
                        return {
                            "status": "Failed",
                            "error": error_text,
                            "url": current_url
                        }
                except Exception as e:
                    logger.debug(f"Error searching for error word elements: {str(e)}")
                
                logger.info("No error patterns detected")
            except Exception as e:
                logger.warning(f"Error checking for error elements: {str(e)}")
            
            # Check if we're still on the signup page or redirected elsewhere
            if "signup" in current_url:
                logger.info("Still on signup page, checking for any visible feedback")
                
                # Look for any feedback elements
                try:
                    feedback_elements = self.driver.find_elements(By.XPATH, 
                        "//*[contains(@class, 'feedback') or contains(@class, 'message') or contains(@class, 'notification')]")
                    
                    if feedback_elements:
                        feedback_text = feedback_elements[0].text
                        logger.info(f"Feedback message found: {feedback_text}")
                        self.take_screenshot("feedback_detected")
                        return {
                            "status": "Feedback",
                            "message": feedback_text,
                            "url": current_url
                        }
                except Exception as e:
                    logger.warning(f"Error checking for feedback elements: {str(e)}")
                
                logger.warning("Still on signup page but no feedback found, may indicate form validation issues")
                self.take_screenshot("possible_validation_issue")
                return {
                    "status": "Validation Issue",
                    "error": "Form may have validation issues preventing submission",
                    "url": current_url
                }
            else:
                # We've been redirected somewhere, but not to an OTP page
                logger.info(f"Redirected to a new page: {current_url}")
                
                # Check if we're on a success page
                success_indicators = ["welcome", "home", "feed", "checkpoint", "confirm"]
                if any(indicator in current_url.lower() for indicator in success_indicators):
                    logger.info("Redirected to what appears to be a success page")
                    self.take_screenshot("success_page")
                    return {
                        "status": "Success",
                        "message": "Account created successfully or additional verification needed",
                        "url": current_url
                    }
                
                # If we can't determine the outcome
                logger.warning("Redirected to an unknown page")
                self.take_screenshot("unknown_redirect")
                return {
                    "status": "Unknown",
                    "message": "Redirected to an unknown page",
                    "url": current_url
                }
        
        except Exception as e:
            logger.error(f"Error checking signup result: {str(e)}")
            logger.error(traceback.format_exc())
            self.take_screenshot("error_checking_result")
            return {
                "status": "Error",
                "error": str(e)
            }
    
    def process_phone_number(self, phone_number):
        """Process a single phone number with retries"""
        logger.info(f"Processing phone number: {phone_number}")
        
        # First, clear browser data to start fresh
        self.clear_browser_data()
        
        try:
            logger.info(f"Attempting to process phone number {phone_number}")
            
            # Navigate to Facebook signup page
            logger.info(f"Navigating to {self.facebook_signup_url}")
            self.driver.get(self.facebook_signup_url)
            
            # Wait for page to load
            logger.info("Waiting for page to load")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "firstname"))
            )
            
            # Fill form and submit
            logger.info("Filling signup form")
            result = self.fill_signup_form(phone_number)
            
            # Log the result for debugging
            logger.info(f"Signup result: {result}")
            
            # Return the result immediately without retrying
            return result
            
        except Exception as e:
            logger.error(f"Error processing phone number {phone_number}: {str(e)}")
            logger.error(traceback.format_exc())
            self.take_screenshot(f"error_processing_{phone_number}")
            
            return {
                "status": "Failed",
                "error": str(e)
            }
    
    def clear_browser_data(self):
        """Clear cookies, local storage, and session storage to start fresh"""
        try:
            logger.info("Clearing browser data...")
            
            # Clear cookies
            self.driver.delete_all_cookies()
            logger.info("Cookies cleared")
            
            # Clear localStorage and sessionStorage
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            logger.info("Local storage and session storage cleared")
            
            # Execute JavaScript to clear any Facebook-specific storage
            self.driver.execute_script("""
                try {
                    // Clear any FB-specific storage
                    for (let key in window) {
                        if (key.includes('FB') || key.includes('facebook')) {
                            window[key] = undefined;
                        }
                    }
                } catch (e) {
                    // Ignore errors
                }
            """)
            
            return True
        except Exception as e:
            logger.error(f"Error clearing browser data: {str(e)}")
            return False
    
    def close(self):
        """Close the browser and clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
            logger.error(traceback.format_exc())
