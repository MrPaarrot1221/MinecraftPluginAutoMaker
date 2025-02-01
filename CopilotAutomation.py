import pyautogui
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import win32gui
import win32con
from selenium.webdriver.chrome.options import Options
import psutil
import re
import win32com.client
import win32process
from datetime import datetime, UTC
import os
import subprocess
import win32api
from win32com.client import Dispatch
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import keyboard
import sys
import traceback
from datetime import timezone
from ai_manager import AIConversationManager

class CopilotAutomation:
    def __init__(self):
        self.browser = None
        self.current_window = None
        self.setup_complete = False
        self.keyboard_listener = None
        self.username = "MrPaarrot1221"
        self.project_name = "custommiraclesplugin"  # Default project name
        self.project_info = {}
        self.temp_file_path = None

    def set_project_name(self, project_name: str) -> str:
        """Set the project name and update project info"""
        if project_name and isinstance(project_name, str):
            self.project_name = project_name
            # Update project info dictionary
            if not self.project_info:
                self.project_info = {}
            self.project_info['project_name'] = self.project_name
        return self.project_name

    def get_project_info(self) -> dict:
        """Get current project information"""
        if not self.project_info:
            self.project_info = {
                'project_name': self.project_name,
                'username': self.username,
                'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
        return self.project_info


    @staticmethod
    def is_chrome_running_with_debugging():
        """Check if Chrome is already running with remote debugging enabled"""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['name'] == 'chrome.exe' and proc.info['cmdline']:
                    if '--remote-debugging-port=9222' in proc.info['cmdline']:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    @staticmethod
    def setup_chrome_debugging():
        """Setup Chrome with remote debugging enabled"""
        try:
            if CopilotAutomation.is_chrome_running_with_debugging():
                print("Chrome already running with debugging enabled")
                return True
                
            print("\nChrome needs to be started with remote debugging enabled.")
            print("Please close all Chrome windows and press Enter to continue...")
            input()
            
            os.system("taskkill /f /im chrome.exe")
            time.sleep(2)
            
            debug_dir = os.path.join(os.getenv('TEMP'), 'chrome_debug_profile')
            os.makedirs(debug_dir, exist_ok=True)
            
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
                    
            if not chrome_path:
                print("Chrome not found in standard locations. Please enter Chrome path:")
                chrome_path = input().strip('"')
            
            subprocess.Popen([
                chrome_path,
                '--remote-debugging-port=9222',
                f'--user-data-dir={debug_dir}',
                'https://github.com/copilot'
            ])
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"Error setting up Chrome: {e}")
            return False

    def debug_log(self, message):
        """Print debug messages if debug_mode is enabled"""
        if self.debug_mode:
            print(f"[DEBUG] {message}")

    def setup_browser(self):
        """Initialize the browser instance by connecting to existing Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            try:
                self.browser = webdriver.Chrome(options=chrome_options)
                print("Successfully connected to existing Chrome instance")
                
                print(f"Active window title: {win32gui.GetWindowText(win32gui.GetForegroundWindow())}")
                
                chrome_windows = []
                def enum_handler(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd) and 'chrome' in win32gui.GetWindowText(hwnd).lower():
                        windows.append(hwnd)
                win32gui.EnumWindows(enum_handler, chrome_windows)
                
                print(f"Chrome windows found: {[win32gui.GetWindowText(hwnd) for hwnd in chrome_windows]}")
                
                current_url = self.browser.current_url
                self.debug_log(f"Current URL: {current_url}")
                
                if "github.com/copilot" not in current_url:
                    print("Navigating to GitHub Copilot...")
                    self.browser.get("https://github.com/copilot")
                    time.sleep(5)
                
            except Exception as e:
                print(f"Could not connect to existing Chrome. Starting new instance. Error: {e}")
                self.browser = webdriver.Chrome()
                self.browser.get("https://github.com/copilot")
                time.sleep(5)
            
            return self.find_copilot_tab()
            
        except Exception as e:
            print(f"Error setting up browser: {e}")
            raise

    def find_copilot_tab(self):
        if not self.browser:
            return False
            
        try:
            handles = self.browser.window_handles
            print(f"\nFound {len(handles)} browser tabs")
            
            for handle in handles:
                self.browser.switch_to.window(handle)
                current_url = self.browser.current_url
                print(f"\nChecking tab:")
                print(f"URL: {current_url}")
                print(f"Title: {self.browser.title}")
                
                if "github.com/copilot" in current_url:
                    print(f"✓ Found Copilot tab!")
                    return True
                    
                print("✗ Not a Copilot tab")
            
            print("\nNo Copilot tab found. Opening Copilot...")
            self.browser.get("https://github.com/copilot")
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"\nError finding Copilot tab: {e}")
            return False

    def find_copilot_window(self):
        try:
            if not self.browser:
                return False

            try:
                self.browser.switch_to.window(self.browser.current_window_handle)
                print("Switched to browser window using Selenium")
            except Exception as e:
                print(f"Error switching window with Selenium: {e}")

            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if 'chrome' in window_text.lower() and 'copilot' in window_text.lower():
                        windows.append(hwnd)
                return True

            chrome_windows = []
            win32gui.EnumWindows(enum_windows_callback, chrome_windows)

            if chrome_windows:
                hwnd = chrome_windows[0]
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.5)

                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys('%')
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.5)

                    win32api.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
                    time.sleep(0.5)

                    print(f"Successfully focused Chrome window: {win32gui.GetWindowText(hwnd)}")
                    return True

                except Exception as e:
                    print(f"Failed to focus window using Win32 API: {e}")
                    try:
                        pyautogui.FAILSAFE = False
                        window_title = win32gui.GetWindowText(hwnd)
                        pyautogui.getWindowsWithTitle(window_title)[0].activate()
                        print(f"Successfully focused window using pyautogui")
                        return True
                    except Exception as e:
                        print(f"Failed to focus window using pyautogui: {e}")

            try:
                os.system(f'powershell "(New-Object -ComObject Shell.Application).Windows() | Where-Object {{$_.LocationName -like \'*Copilot*\'}} | ForEach-Object {{$_.Activate()}}"')
                time.sleep(1)
                return True
            except Exception as e:
                print(f"Failed to focus window using PowerShell: {e}")

            print("No suitable Chrome windows found")
            return False

        except Exception as e:
            print(f"Error in find_copilot_window: {e}")
            return False

    def find_chat_input(self):
        """Find the chat input element using basic Selenium methods"""
        max_retries = 3
        selectors = [
            "#copilot-chat-textarea",
            "textarea[placeholder='Ask Copilot']",
            "textarea"
        ]
        
        for attempt in range(max_retries):
            try:
                print(f"\nAttempt {attempt + 1} to find chat input...")
                
                for selector in selectors:
                    try:
                        print(f"Trying selector: {selector}")
                        input_element = WebDriverWait(self.browser, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        
                        if input_element and input_element.is_displayed():
                            print(f"Found element with selector: {selector}")
                            input_element.click()
                            print("Successfully focused input element")
                            return input_element
                            
                    except Exception as e:
                        print(f"Failed with selector {selector}: {str(e)}")
                        continue
                
                # If still not found and not last attempt, refresh the page
                if attempt < max_retries - 1:
                    print("Refreshing page...")
                    self.browser.refresh()
                    time.sleep(5)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(3)
        
        raise Exception("Could not find chat input element after all attempts")

    def wait_for_page_load(self):
        """Wait for the page to be fully loaded"""
        try:
            WebDriverWait(self.browser, 20).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error waiting for page load: {e}")
            return False
        
    def send_prompt_to_chat(self, input_field, prompt: str) -> bool:
        """Send a prompt to Copilot chat and wait for the complete response"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Refresh the input field element with extended wait time
                input_field = WebDriverWait(self.browser, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#copilot-chat-textarea"))
                )
                
                # Ensure element is visible and interactable
                WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#copilot-chat-textarea"))
                )
                
                # Clear existing text using multiple methods
                input_field.clear()
                self.browser.execute_script("arguments[0].value = '';", input_field)
                time.sleep(0.5)
                
                # Focus the element using JavaScript
                self.browser.execute_script("arguments[0].focus();", input_field)
                time.sleep(0.5)
                
                # Send the entire prompt at once using JavaScript
                self.browser.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', {
                        bubbles: true,
                        cancelable: true,
                    }));
                """, input_field, prompt)
                time.sleep(1)

                # Get initial response count
                initial_responses = len(self.browser.find_elements(By.CSS_SELECTOR, ".markdown-body"))
                
                # Click send button
                try:
                    send_button = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send message']"))
                    )
                    send_button.click()
                except Exception as e:
                    print(f"Send button click failed, trying Enter key: {e}")
                    input_field.send_keys(Keys.RETURN)
                
                # Wait for response with improved handling
                def response_complete(driver):
                    try:
                        current_responses = len(driver.find_elements(By.CSS_SELECTOR, ".markdown-body"))
                        loading_elements = len(driver.find_elements(By.CSS_SELECTOR, ".copilot-loading"))
                        return current_responses > initial_responses and loading_elements == 0
                    except:
                        return False
                
                # Wait up to 60 seconds for complete response
                WebDriverWait(self.browser, 60).until(response_complete)
                time.sleep(2)
                
                return True
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1} failed. Retrying... Error: {str(e)}")
                    time.sleep(2)
                    continue
                else:
                    print(f"All attempts failed. Last error: {str(e)}")
                    return False
        
        return False
    
    def ensure_single_chat_session(self):
        """Ensure we're using a single chat session"""
        try:
            # Check if we have multiple chat windows open
            chat_windows = self.browser.find_elements(By.CSS_SELECTOR, ".chat-window")  # Adjust selector as needed
            
            if len(chat_windows) > 1:
                print("Multiple chat windows detected, consolidating...")
                
                # Click the first chat window to make it active
                chat_windows[0].click()
                time.sleep(1)
                
                # Look for any close buttons on other chat windows
                close_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button[aria-label='Close chat']")
                for button in close_buttons[1:]:  # Skip the first one to keep one chat open
                    try:
                        button.click()
                        time.sleep(0.5)
                    except:
                        continue
                        
            return True
        except Exception as e:
            print(f"Error managing chat sessions: {e}")
            return False
        
    def process_prompt(self, prompt):
        try:
            # Ensure we're using a single chat session
            self.ensure_single_chat_session()
            
            # Find chat input
            input_field = self.find_chat_input()
            if not input_field:
                print("Could not find chat input")
                return False
                
            # Send the prompt
            return self.send_prompt_to_chat(input_field, prompt)
            
        except Exception as e:
            print(f"Error processing prompt: {e}")
            return False

    def handle_code_implementation(self, project_info: dict) -> bool:
        """Handle the code implementation response from Copilot"""
        try:
            # Wait for the response to be fully loaded
            time.sleep(2)  # Give time for the response to complete
            
            # Find all markdown body elements (responses)
            responses = self.browser.find_elements(By.CSS_SELECTOR, ".markdown-body")
            
            if not responses:
                print("No response found from Copilot")
                return False
                
            # Get the latest response
            latest_response = responses[-1]
            
            # Check if we got a meaningful response
            if not latest_response.text.strip():
                print("Empty response from Copilot")
                return False
                
            print("\nResponse received from Copilot")
            return True
                
        except Exception as e:
            print(f"Error handling code implementation: {str(e)}")
            return False
    
    def _switch_to_copilot_tab(self) -> bool:
            """Switch to Copilot tab with improved reliability"""
            try:
                # First try to use existing tab
                if self.current_window:
                    try:
                        self.browser.switch_to.window(self.current_window)
                        if "copilot" in self.browser.current_url.lower():
                            return True
                    except:
                        pass  # If failed, continue to find or create new tab
                
                # Look for existing Copilot tab
                for handle in self.browser.window_handles:
                    try:
                        self.browser.switch_to.window(handle)
                        if "copilot" in self.browser.current_url.lower():
                            self.current_window = handle
                            return True
                    except:
                        continue
                
                # If no tab found, create new one
                self.browser.execute_script("window.open('https://github.com/features/copilot/chat', '_blank');")
                time.sleep(2)
                self.current_window = self.browser.window_handles[-1]
                self.browser.switch_to.window(self.current_window)
                
                # Wait for chat to load
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#copilot-chat-textarea"))
                )
                
                return True
                
            except Exception as e:
                print(f"Error switching to Copilot tab: {e}")
                return False

    def get_user_input(self):
        print("\n=== Project Setup ===")
        print("What kind of project would you like to create?")
        print("Examples: Java Console App, Python Script, Web Application")
        project_type = input("Project type: ").strip()
        
        print("\nPlease enter your project requirements:")
        print("Be as specific as possible about what you want the program to do.")
        requirements = input("Requirements: ").strip()
        
        return project_type, requirements
    
    def generate_copilot_prompt(self, project_type, requirements):
        prompt = f"""I need help creating a {project_type}. Here are the requirements:

{requirements}

Please provide:
1. The complete code implementation
2. Instructions for setting up the development environment
3. Any necessary dependencies
4. Brief explanation of how the code works

Please make sure the code is well-documented and follows best practices."""
        return prompt

    def main_loop(self):
        """Main automation loop with IDE integration and AI manager"""
        try:
            # Print session info with UTC time
            current_time = datetime.now(timezone.utc)
            formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\nCurrent Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {formatted_time}")
            print(f"Current User's Login: {self.username}")

            # Get project name
            project_name = input("\nEnter the IntelliJ project name (default: custommiraclesplugin): ").strip()
            if project_name:
                self.set_project_name(project_name)
            else:
                self.set_project_name("custommiraclesplugin")
                
            # Get project requirements
            print("\n=== Project Setup ===")
            print("Please describe your complete project requirements.")
            print("Be as specific as possible about what you want the final program to do.")
            requirements = input("\nProject requirements: ").strip()
            
            if not requirements:
                print("Error: Project requirements cannot be empty")
                return
                
            # Initialize browser and find existing tabs
            print("\nLooking for existing Chrome instances...")
            try:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                
                self.browser = webdriver.Chrome(options=chrome_options)
                print("Connected to existing Chrome instance")
                
                # Check all existing tabs
                print("\nChecking existing tabs...")
                existing_tabs = self.browser.window_handles
                copilot_tab = None
                chatgpt_tab = None
                
                # Look for any valid ChatGPT URL
                for tab in existing_tabs:
                    try:
                        self.browser.switch_to.window(tab)
                        current_url = self.browser.current_url.lower()
                        print(f"Checking tab: {current_url}")
                        
                        # Accept both chat.openai.com and chatgpt.com as valid URLs
                        if "chatgpt.com" in current_url or "chat.openai.com" in current_url:
                            print("Found existing ChatGPT tab")
                            chatgpt_tab = tab
                        elif "github.com/features/copilot" in current_url or "copilot" in current_url:
                            print("Found existing Copilot tab")
                            copilot_tab = tab
                                
                    except Exception as e:
                        print(f"Error checking tab: {e}")
                        continue

                # Handle Copilot tab
                if not copilot_tab:
                    print("Opening new Copilot tab...")
                    self.browser.execute_script("window.open('https://github.com/features/copilot', '_blank');")
                    time.sleep(2)
                    copilot_tab = self.browser.window_handles[-1]

                # Store Copilot tab reference
                self.current_window = copilot_tab

                # Handle ChatGPT tab
                if not chatgpt_tab:
                    print("No existing ChatGPT tab found")
                    print("Would you like to:")
                    print("1. Open ChatGPT in a new tab")
                    print("2. Continue without ChatGPT (limited functionality)")
                    choice = input("\nEnter your choice (1-2): ").strip()
                    
                    if choice == "1":
                        # Switch to Copilot tab first
                        self.browser.switch_to.window(copilot_tab)
                        print("Opening new ChatGPT tab...")
                        # Try chatgpt.com first, but allow fallback to chat.openai.com
                        self.browser.execute_script("window.open('https://chatgpt.com', '_blank');")
                        time.sleep(2)
                        chatgpt_tab = self.browser.window_handles[-1]
                        
                        # Switch to ChatGPT tab and verify access
                        self.browser.switch_to.window(chatgpt_tab)
                        time.sleep(2)
                        current_url = self.browser.current_url.lower()
                        
                        if "auth" in current_url or "login" in current_url:
                            print("\nPlease log in to ChatGPT:")
                            print("1. Complete the login process in the browser")
                            print("2. Wait for the chat interface to load")
                            print("3. Press Enter to continue")
                            input("\nPress Enter after logging in...")
                else:
                    # Verify existing ChatGPT tab
                    self.browser.switch_to.window(chatgpt_tab)
                    current_url = self.browser.current_url.lower()
                    if "auth" in current_url or "login" in current_url:
                        print("\nExisting ChatGPT tab requires login")
                        print("Please log in and press Enter to continue")
                        input()
                
                # Switch back to Copilot tab
                self.browser.switch_to.window(copilot_tab)
                print("\nReady to proceed with automation")
                
                # Initialize AI manager
                try:
                    print("\nInitializing AI Conversation Manager...")
                    ai_manager = AIConversationManager()
                    ai_manager.copilot_automation = self
                    print("AI Manager initialized successfully")
                except Exception as e:
                    print(f"Error initializing AI manager: {e}")
                    return

                # Analyze requirements
                print("\nAnalyzing requirements...")
                sections = ai_manager.analyze_requirements(requirements)
                
                if not sections:
                    print("Failed to break down requirements into sections")
                    return
                
                # Now that setup is complete, enable pause functionality
                print("\nSetup complete! Enabling pause functionality...")
                self.setup_complete = True

                
                # Run implementation
                try:
                    print("\n=== Starting Implementation ===")
                    ai_manager.run(self)
                except Exception as e:
                    print(f"\nError during implementation: {e}")
                    print("\nDetailed error trace:")
                    print(traceback.format_exc())
                
            except Exception as e:
                print(f"Error initializing browser: {e}")
                print("Full error trace:")
                print(traceback.format_exc())
                return
                
        except Exception as e:
            print(f"\nAn error occurred in main loop: {str(e)}")
            print("Full error trace:")
            print(traceback.format_exc())
            
        finally:
            # Cleanup
            print("\n=== Cleaning Up ===")
            try:
                if self.keyboard_listener:
                    keyboard.unhook_all()  # Remove keyboard listener
                if hasattr(self, 'browser') and self.browser:
                    print("Closing browser...")
                    self.browser.quit()
            except Exception as e:
                print(f"Error during cleanup: {e}")
            
            # Print end time with UTC
            end_time = datetime.now(timezone.utc)
            formatted_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            print("\n=== Session Complete ===")
            print(f"End Time (UTC - YYYY-MM-DD HH:MM:SS): {formatted_end_time}")

if __name__ == "__main__":
    print("=== Copilot Automation Tool ===")
    current_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {current_time}")
    print(f"Current User's Login: MrPaarrot1221")
    input("Press Enter when ready...")
    
    if CopilotAutomation.setup_chrome_debugging():
        time.sleep(5)  # Give Chrome time to start
        automation = CopilotAutomation()
        automation.main_loop()
    else:
        print("Failed to set up Chrome debugging. Please try running as administrator.")