from typing import List, Dict, Optional
import os
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import pyautogui
import pyperclip
from time import sleep
import shutil
import json
import keyboard
import sys

class AIConversationManager:
    def __init__(self):
        self.project_requirements = ""
        self.sections = []
        self.current_section = 0
        self.context = {}
        self.copilot_automation = None
        self.chatgpt_tab = None

        self.project_requirements = ""
        self.sections = []
        self.current_section = 0
        self.context = {}
        self.copilot_automation = None
        self.chatgpt_tab = None
        
        # Add error tracking stats
        self.implementation_stats = {
            'total_errors': 0,
            'errors_by_type': {
                'compilation': 0,
                'runtime': 0,
                'syntax': 0,
                'logic': 0
            },
            'retries': 0
        }

    def merge_main_class_code(self, original_code: str, new_code: str) -> str:
        """
        Merges new code into existing main class, properly placing imports at top
        and adding only necessary code.
        """
        try:
            print("\nStarting main class code merger...")
            
            # Initialize sections to store different parts of code
            new_imports = []
            new_fields = []
            enable_additions = []
            disable_additions = []
            getter_methods = []
            
            current_section = None
            
            # Parse new code additions
            for line in new_code.split('\n'):
                stripped = line.strip()
                
                # Skip empty lines and comment markers
                if not stripped or stripped == '//new code to be added' or stripped.startswith('// Example:'):
                    continue
                    
                # Identify sections
                if '//IMPORTS:' in line:
                    current_section = 'imports'
                    continue
                elif '//ADD FIELDS TO MAIN CLASS:' in line:
                    current_section = 'fields'
                    continue
                elif '//PLACEMENT:' in line:
                    if 'Add to onEnable()' in line:
                        current_section = 'enable'
                    elif 'Add to onDisable()' in line:
                        current_section = 'disable'
                    continue
                elif '//CODE TO ADD:' in line:
                    continue
                    
                # Add lines to appropriate sections
                if stripped and current_section:
                    if current_section == 'imports' and stripped.startswith('import'):
                        new_imports.append(stripped)
                    elif current_section == 'fields' and ';' in stripped:
                        new_fields.append(stripped if stripped.startswith('    ') else '    ' + stripped)
                    elif current_section == 'enable' and ';' in stripped:
                        enable_additions.append(stripped if stripped.startswith('        ') else '        ' + stripped)
                    elif current_section == 'disable' and ';' in stripped:
                        disable_additions.append(stripped if stripped.startswith('        ') else '        ' + stripped)
                    elif stripped.startswith('public') and 'get' in stripped:
                        getter_methods.append(stripped)

            # Split original code into lines
            original_lines = original_code.split('\n')
            merged_lines = []
            
            # Track sections in original code
            in_package = False
            after_package = False
            in_imports = False
            in_class = False
            in_enable = False
            in_disable = False
            imports_added = False
            
            # Process original code line by line
            for i, line in enumerate(original_lines):
                stripped = line.strip()
                
                # Handle package declaration
                if stripped.startswith('package '):
                    merged_lines.append(line)
                    in_package = True
                    after_package = True
                    continue
                    
                # Add imports after package
                if after_package and not imports_added and not stripped.startswith('import'):
                    for imp in sorted(new_imports):
                        if imp not in '\n'.join(original_lines):
                            merged_lines.append(imp)
                    imports_added = True
                
                # Skip if line is an import and we've already added imports
                if stripped.startswith('import') and imports_added:
                    continue
                    
                # Handle class declaration
                if 'class ' in stripped and '{' in stripped:
                    merged_lines.append(line)
                    in_class = True
                    # Add fields right after class declaration
                    for field in new_fields:
                        if field not in '\n'.join(original_lines):
                            merged_lines.append(field)
                    continue
                    
                # Handle onEnable method
                if 'public void onEnable()' in stripped:
                    merged_lines.append(line)
                    in_enable = True
                    continue
                    
                # Handle onDisable method
                if 'public void onDisable()' in stripped:
                    merged_lines.append(line)
                    in_disable = True
                    continue
                    
                # Add new code before closing braces of methods
                if in_enable and '}' in stripped:
                    for enable_line in enable_additions:
                        if enable_line not in '\n'.join(original_lines):
                            merged_lines.append(enable_line)
                    in_enable = False
                elif in_disable and '}' in stripped:
                    for disable_line in disable_additions:
                        if disable_line not in '\n'.join(original_lines):
                            merged_lines.append(disable_line)
                    in_disable = False
                    
                merged_lines.append(line)
                
                # Add getter methods at the end of the class if needed
                if i == len(original_lines) - 1:  # Last line
                    for method in getter_methods:
                        if method not in '\n'.join(original_lines):
                            merged_lines.insert(-1, method)

            # Join lines back together
            merged_code = '\n'.join(merged_lines)
            
            print("Successfully merged code changes")
            return merged_code
            
        except Exception as e:
            print(f"Error in code merger: {e}")
            print(traceback.format_exc())
            return original_code

    def _extract_method_name(self, line: str) -> str:
        """Extract method name from method declaration line"""
        try:
            # Remove annotations if present
            if '@' in line:
                line = line.split('\n')[-1]
            
            # Extract method name
            parts = line.split('(')[0].split()
            return parts[-1]
        except Exception:
            return ""
            
    def _verify_merged_code(self, code: str) -> bool:
        """Verify the merged code structure"""
        try:
            lines = code.split('\n')
            has_package = False
            has_class = False
            brace_count = 0
            
            for line in lines:
                stripped = line.strip()
                
                if stripped.startswith('package '):
                    has_package = True
                elif 'class ' in stripped and '{' in stripped:
                    has_class = True
                
                brace_count += stripped.count('{')
                brace_count -= stripped.count('}')
                
            # Basic verification
            if not has_package:
                print("Warning: No package declaration found")
            if not has_class:
                print("Warning: No class declaration found")
                return False
            if brace_count != 0:
                print("Warning: Unmatched braces in merged code")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error verifying merged code: {e}")
            return False

    def _update_error_stats(self, error_type: str) -> None:
        """Update error tracking statistics"""
        try:
            if error_type.lower() in self.implementation_stats['errors_by_type']:
                self.implementation_stats['errors_by_type'][error_type.lower()] += 1
                self.implementation_stats['total_errors'] += 1
        except Exception as e:
            print(f"Error updating error stats: {e}")


    def perform_initial_checks(self):
        """Perform initial checks and get necessary information from user"""
        print("\n=== Initial Project Setup ===")

        # Get project root directory
        print("\n=== Project Location ===")
        print("Please enter the full path to your project root directory")
        print("Example: C:\\Users\\username\\Documents\\MyPlugins\\myplugin")
        
        while True:
            project_root = input("\nProject root directory: ").strip().replace('"', '')
            
            if not os.path.exists(project_root):
                print(f"\nError: Directory not found: {project_root}")
                print("Options:")
                print("1. Try again")
                print("2. Create this directory")
                print("3. Exit")
                
                choice = input("\nEnter choice (1-3): ").strip()
                if choice == '1':
                    continue
                elif choice == '2':
                    try:
                        os.makedirs(project_root)
                        print(f"\nCreated directory: {project_root}")
                        break
                    except Exception as e:
                        print(f"Error creating directory: {e}")
                        continue
                else:
                    return None
            else:
                print(f"\nFound project directory: {project_root}")
                break

        # Get package name
        while True:
            package_name = input("\nEnter the package name (e.g., com.yourname.plugin): ").strip()
            if package_name and '.' in package_name:
                break
            print("Invalid package name. It should contain at least one dot (e.g., com.example.plugin)")

        # Working Directory Setup
        print("\n=== Working Directory Setup ===")
        print("Where do you want to create/modify your classes?")
        print("1. Enter path relative to project root (e.g., 'src/main/java/com/example/plugin')")
        print("2. Or press Enter to use default 'src/main/java/<package>'")
        
        relative_working_dir = input("\nEnter working directory path: ").strip() or f"src/main/java/{package_name.replace('.', '/')}"
        working_dir = os.path.join(project_root, relative_working_dir)

        # Create working directory if it doesn't exist
        if not os.path.exists(working_dir):
            try:
                os.makedirs(working_dir)
                print(f"\nCreated working directory: {working_dir}")
            except Exception as e:
                print(f"Error creating directory: {e}")
                return None
        else:
            print(f"\nFound existing working directory: {working_dir}")

        # Check if this is a new plugin
        while True:
            is_new = input("\nIs this a new plugin? (yes/no): ").lower().strip()
            if is_new in ['yes', 'no', 'y', 'n']:
                is_new = is_new.startswith('y')
                break
            print("Please answer 'yes' or 'no'")

        # Set up temp directory and file
        temp_dir = os.path.join(os.getenv('TEMP'), 'copilot_automation')
        os.makedirs(temp_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_file_path = os.path.join(temp_dir, f"main_class_{timestamp}.txt")

        main_class_name = None
        main_class_path = None
        existing_main_content = None

        if not is_new:
            while True:
                print("\n=== Main Class Location ===")
                print("Where is your main class located? (relative to project root)")
                print("Examples:")
                print("1. src/main/java/com/example/MainClass.java")
                print("2. src/main/java/plugin/MainClass.java")
                
                relative_path = input("\nEnter main class location: ").strip()
                main_class_path = os.path.join(project_root, relative_path)
                main_class_name = os.path.splitext(os.path.basename(main_class_path))[0]

                if not os.path.exists(main_class_path):
                    print(f"\nWarning: Main class not found: {main_class_path}")
                    print("\nOptions:")
                    print("1. Try a different location")
                    print("2. Create this file")
                    print("3. Start over as a new plugin")
                    print("4. Exit")
                    
                    choice = input("\nEnter choice (1-4): ").strip()
                    if choice == '1':
                        continue
                    elif choice == '2':
                        try:
                            os.makedirs(os.path.dirname(main_class_path), exist_ok=True)
                            with open(main_class_path, 'w') as f:
                                f.write(f"package {package_name};\n\n")
                                f.write("import org.bukkit.plugin.java.JavaPlugin;\n\n")
                                f.write(f"public class {main_class_name} extends JavaPlugin {{\n\n}}")
                            print(f"\nCreated main class at: {main_class_path}")
                            existing_main_content = f"package {package_name};\n\npublic class {main_class_name} extends JavaPlugin {{\n\n}}"
                            
                            # Create temp file
                            with open(self.temp_file_path, 'w') as f:
                                f.write(existing_main_content)
                            print(f"Created temporary copy at: {self.temp_file_path}")
                            break
                        except Exception as e:
                            print(f"Error creating main class: {e}")
                            continue
                    elif choice == '3':
                        is_new = True
                        break
                    else:
                        return None
                else:
                    try:
                        # Read the existing main class
                        with open(main_class_path, 'r') as f:
                            existing_main_content = f.read()
                        
                        # Create temp file with main class content
                        with open(self.temp_file_path, 'w') as f:
                            f.write(existing_main_content)
                        
                        print(f"\nSuccessfully read existing main class: {main_class_name}")
                        print(f"Location: {main_class_path}")
                        print(f"Temporary copy created at: {self.temp_file_path}")
                        break
                    except Exception as e:
                        print(f"Error reading/copying main class file: {e}")
                        continue

        # Store project info
        self.project_info = {
            'project_root': project_root,
            'package_name': package_name,
            'working_dir': working_dir,
            'is_new_plugin': is_new,
            'main_class_name': main_class_name,
            'main_class_path': main_class_path,
            'existing_main_content': existing_main_content,
            'temp_file': self.temp_file_path
        }

        print("\n=== Initial Setup Complete ===")
        return self.project_info
    

    def compare_and_merge_code(self, copilot_code: str, temp_file_path: str) -> str:
        """Compare Copilot's code with existing main class and merge appropriately"""
        try:
            # Read the original main class from temp file
            with open(temp_file_path, 'r') as f:
                original_code = f.read()

            # Split both codes into lines for comparison
            original_lines = original_code.split('\n')
            copilot_lines = copilot_code.split('\n')

            # Find code blocks marked with "//new code to be added"
            new_code_blocks = []
            current_block = []
            in_new_block = False

            for line in copilot_lines:
                if "//new code to be added" in line:
                    in_new_block = True
                    continue
                elif in_new_block and line.strip():
                    current_block.append(line)
                elif in_new_block and not line.strip():
                    if current_block:
                        new_code_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_new_block = False

            # Add final block if exists
            if current_block:
                new_code_blocks.append('\n'.join(current_block))

            # If no new code blocks found, return original code
            if not new_code_blocks:
                print("No new code blocks found to add")
                return original_code

            # For each new code block, find appropriate method to insert it
            modified_code = original_code
            for block in new_code_blocks:
                # Try to determine the target method from the code block
                method_match = re.search(r'(?:public|private|protected)?\s+\w+\s+(\w+)\s*\(', block)
                if method_match:
                    method_name = method_match.group(1)
                    # Look for this method in original code
                    method_pattern = f"\\s+{method_name}\\s*\\("
                    if re.search(method_pattern, original_code):
                        # Method exists, insert new code before closing brace
                        pattern = f"(\\s+{method_name}\\s*\\([^{{]+{{[^}}]*)(}})"
                        replacement = f"\\1\n    {block}\n    \\2"
                        modified_code = re.sub(pattern, replacement, modified_code)
                    else:
                        # Method doesn't exist, add it before last class brace
                        insert_point = modified_code.rstrip().rfind('}')
                        if insert_point != -1:
                            modified_code = (
                                modified_code[:insert_point] +
                                f"\n    {block}\n" +
                                modified_code[insert_point:]
                            )

            return modified_code

        except Exception as e:
            print(f"Error comparing and merging code: {e}")
            return copilot_code  # Return original Copilot code if comparison fails
    

    def compare_main_class_code(self, existing_code: str, new_code: str) -> List[str]:
        """Compare existing main class with new code to identify additions"""
        existing_lines = set(line.strip() for line in existing_code.split('\n'))
        new_lines = [line.strip() for line in new_code.split('\n')]
        
        # Find new code blocks
        new_code_blocks = []
        current_block = []
        
        for line in new_lines:
            if line and line not in existing_lines:
                current_block.append(line)
            elif current_block:
                if any(line.strip() for line in current_block):  # Only add non-empty blocks
                    new_code_blocks.append('\n'.join(current_block))
                current_block = []
        
        # Add final block if exists
        if current_block and any(line.strip() for line in current_block):
            new_code_blocks.append('\n'.join(current_block))
        
        return new_code_blocks
    

    def modify_copilot_prompt(self, prompt: str, project_info: dict) -> str:
        """Modify Copilot's prompt to include package information"""
        package_info = f"\nUse this for all classes at the top of each class package: {project_info['package_name']}"
            
        if not project_info['is_new_plugin'] and project_info['main_class_name']:
            package_info += f"\nAdd '//new code to be added' comments next to code that should be added to the main class: {project_info['main_class_name']}"
            
        # Add package info after initial requirements but before implementation details
        parts = prompt.split("Please break this down into numbered steps")
        if len(parts) == 2:
            return parts[0] + package_info + "\nPlease break this down into numbered steps" + parts[1]
        return prompt + package_info 
    

    def handle_code_implementation(self, code: str, project_info: dict) -> bool:
        """
        Handle code implementation by modifying the existing class at the specified path
        """
        try:
            print("\nStarting code implementation...")
            
            # Get the exact path and class name from project_info
            main_class_path = project_info.get('main_class_path')
            main_class_name = project_info.get('main_class_name')
            
            if not main_class_path or not os.path.exists(main_class_path):
                print(f"Error: Main class not found at: {main_class_path}")
                return False
                
            print(f"Modifying existing class: {main_class_name}")
            print(f"Location: {main_class_path}")
            
            # First check if this code is for our main class
            if f"// Main class: {main_class_name}" in code or f"class {main_class_name}" in code:
                try:
                    # Read the existing class content
                    with open(main_class_path, 'r', encoding='utf-8') as f:
                        original_code = f.read()
                    
                    # Create backup
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_path = f"{main_class_path}.{timestamp}.bak"
                    shutil.copy2(main_class_path, backup_path)
                    print(f"Created backup at: {backup_path}")
                    
                    # Extract modifications from Copilot's response
                    main_class_mods = []
                    current_section = None
                    
                    for line in code.split('\n'):
                        stripped = line.strip()
                        
                        if not stripped:
                            continue
                            
                        # Identify main class sections
                        if any(marker in stripped for marker in [
                            '//IMPORTS:', 
                            '//ADD FIELDS TO MAIN CLASS:', 
                            '//PLACEMENT:', 
                            '//CODE TO ADD:'
                        ]):
                            current_section = 'main_class'
                            main_class_mods.append(line)
                            continue
                            
                        # Collect code for main class sections
                        if current_section == 'main_class':
                            if '//NEW CLASS:' in stripped:
                                current_section = None
                            else:
                                main_class_mods.append(line)
                    
                    if main_class_mods:
                        # Merge modifications into existing code
                        merged_code = self.merge_main_class_code(original_code, '\n'.join(main_class_mods))
                        
                        if merged_code != original_code:
                            # Write changes back to the original file
                            with open(main_class_path, 'w', encoding='utf-8') as f:
                                f.write(merged_code)
                            print(f"Successfully updated {main_class_name} at: {main_class_path}")
                            
                            # Update temp file if it exists
                            if project_info.get('temp_file'):
                                with open(project_info['temp_file'], 'w', encoding='utf-8') as f:
                                    f.write(merged_code)
                                print("Updated temporary file")
                                
                            return True
                        else:
                            print("No changes needed in main class")
                            return True
                    else:
                        print("No modifications found for main class")
                        return False
                        
                except Exception as e:
                    print(f"Error modifying main class: {e}")
                    print(traceback.format_exc())
                    return False
            else:
                print(f"Warning: Code doesn't match main class name: {main_class_name}")
                return False
                
        except Exception as e:
            print(f"Error in implementation: {e}")
            print(traceback.format_exc())
            return False

    def _verify_file_operation(self, file_path: str, operation: str) -> bool:
        """
        Verify file operations were successful
        """
        if operation == 'write':
            return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        elif operation == 'backup':
            return os.path.exists(file_path)
        return False
        
    def _parse_implementation_steps(self, response: str) -> List[Dict]:
        """Parse the ChatGPT response into implementation steps"""
        try:
            steps = []
            current_step = {}
            lines = response.split('\n')
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                    
                if "What this step implements:" in line:
                    if current_step:
                        steps.append(current_step)
                    current_step = {
                        'title': "Set Up Basic Plugin Structure",
                        'description': stripped.split("What this step implements:")[1].strip()
                    }
                elif "Required Bukkit/Spigot APIs:" in line:
                    current_step['apis'] = stripped.split("Required Bukkit/Spigot APIs:")[1].strip()
                elif "Classes and methods needed:" in line:
                    current_step['classes'] = stripped.split("Classes and methods needed:")[1].strip()
                    
            if current_step:
                steps.append(current_step)
                
            return steps
            
        except Exception as e:
            print(f"Error parsing implementation steps: {e}")
            print(traceback.format_exc())
            return []
        
    def _implement_step(self, step: Dict, project_info: dict) -> bool:
        """Implement a single step"""
        try:
            print(f"\nImplementing step: {step.get('title', 'Unknown Step')}")
            
            # Create implementation prompt
            prompt = self._create_implementation_prompt(step)
            
            # Get implementation from Copilot
            implementation = self._get_copilot_implementation(prompt)
            
            # Process the implementation
            return self._process_implementation(implementation, project_info)
            
        except Exception as e:
            print(f"Error implementing step: {e}")
            print(traceback.format_exc())
            return False
        
    def _handle_main_class_modifications(self, modifications: List[str], project_info: dict) -> bool:
        """Handle modifications to the main class"""
        try:
            print("\nProcessing main class modifications...")
            
            # Read original main class
            with open(project_info['main_class_path'], 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Create backup
            backup_path = project_info['main_class_path'] + '.bak'
            shutil.copy2(project_info['main_class_path'], backup_path)
            print(f"Created backup at: {backup_path}")
            
            # Merge changes
            merged_code = self.merge_main_class_code(original_code, '\n'.join(modifications))
            
            if merged_code != original_code:
                # Write merged code
                with open(project_info['main_class_path'], 'w', encoding='utf-8') as f:
                    f.write(merged_code)
                print("Successfully updated main class")
                return True
            else:
                print("No changes needed in main class")
                return True
                
        except Exception as e:
            print(f"Error handling main class modifications: {e}")
            print(traceback.format_exc())
            return False

    

    def find_chatgpt_tab(self, browser):
        """Find ChatGPT tab or open a new one"""
        print("\nStarting ChatGPT tab search...")
        print(f"Current tabs: {len(browser.window_handles)}")
        
        # First, save the Copilot tab handle
        copilot_tab = browser.current_window_handle
        print(f"Saved Copilot tab handle: {copilot_tab}")
        
        # Define the correct ChatGPT URL
        CHATGPT_URL = 'https://chat.openai.com/'
        
        try:
            # First try: Direct navigation in new tab
            print(f"Opening new tab with ChatGPT ({CHATGPT_URL})...")
            browser.execute_script(f"window.open('{CHATGPT_URL}', '_blank');")
            time.sleep(3)
            
            # Get all window handles
            all_handles = browser.window_handles
            print("Available window handles:", all_handles)
            
            # Switch to the new tab
            new_tab = [h for h in all_handles if h != copilot_tab][0]
            browser.switch_to.window(new_tab)
            
            # Wait for page to load
            time.sleep(5)
            
            # Get current URL
            current_url = browser.current_url.lower()
            print(f"Current URL: {current_url}")
            
            # Check if we're on the correct site
            if "chat.openai.com" in current_url:
                print("Successfully accessed ChatGPT!")
                self.chatgpt_tab = new_tab
                
                # Check for login page
                if "auth" in current_url or "login" in current_url:
                    print("\nChatGPT login required!")
                    print("Please:")
                    print("1. Log in to ChatGPT in the newly opened tab")
                    print("2. Wait for the chat interface to load")
                    print("3. Press Enter here to continue")
                    input("\nPress Enter after logging into ChatGPT...")
                
                # Switch back to Copilot tab
                browser.switch_to.window(copilot_tab)
                return True
                
            else:
                print("Not on ChatGPT. Trying alternative method...")
                
                # Try direct navigation
                try:
                    print(f"Navigating directly to {CHATGPT_URL}")
                    browser.get(CHATGPT_URL)
                    time.sleep(5)
                    
                    current_url = browser.current_url.lower()
                    print(f"New URL after navigation: {current_url}")
                    
                    if "chat.openai.com" in current_url:
                        print("Successfully accessed ChatGPT!")
                        self.chatgpt_tab = browser.current_window_handle
                        
                        # Check for login
                        if "auth" in current_url or "login" in current_url:
                            print("\nChatGPT login required!")
                            print("Please log in and press Enter to continue...")
                            input()
                        
                        # Switch back to Copilot tab
                        browser.switch_to.window(copilot_tab)
                        return True
                except Exception as e:
                    print(f"Direct navigation failed: {str(e)}")
                
                # If we're still not on ChatGPT, try one last method
                try:
                    print("\nTrying final method with new window...")
                    browser.execute_script(f"""
                        var win = window.open('{CHATGPT_URL}', 'chatgpt_window', 
                        'width=800,height=600,left=200,top=200');
                    """)
                    time.sleep(5)
                    
                    # Find the new window
                    all_handles = browser.window_handles
                    new_handles = [h for h in all_handles if h != copilot_tab]
                    
                    if new_handles:
                        browser.switch_to.window(new_handles[-1])
                        current_url = browser.current_url.lower()
                        print(f"Final attempt URL: {current_url}")
                        
                        if "chat.openai.com" in current_url:
                            print("Successfully accessed ChatGPT!")
                            self.chatgpt_tab = browser.current_window_handle
                            
                            # Check for login
                            if "auth" in current_url or "login" in current_url:
                                print("\nChatGPT login required!")
                                print("Please log in and press Enter to continue...")
                                input()
                            
                            # Switch back to Copilot tab
                            browser.switch_to.window(copilot_tab)
                            return True
                except Exception as e:
                    print(f"Final attempt failed: {str(e)}")
                
                # If all methods failed, return to Copilot tab
                browser.switch_to.window(copilot_tab)
                print("All attempts to access ChatGPT failed")
                return False
                
        except Exception as e:
            print(f"Error during ChatGPT tab creation: {str(e)}")
            print("Detailed error:")
            import traceback
            print(traceback.format_exc())
            
            # Make sure we're back on the Copilot tab
            try:
                browser.switch_to.window(copilot_tab)
            except:
                pass
            return False

    def send_to_chatgpt(self, browser, message):
        """Send a message to ChatGPT and get the response"""
        try:
            # Store current tab
            current_tab = browser.current_window_handle
            
            # Switch to ChatGPT tab
            print("Switching to ChatGPT tab...")
            browser.switch_to.window(self.chatgpt_tab)
            time.sleep(2)
            
            print("Looking for input field...")
            input_field = None
            
            # Try multiple selectors
            selectors = [
                "textarea[placeholder*='Send a message']",
                "textarea[placeholder*='Message ChatGPT']",
                "textarea.chatgpt-input",
                "#prompt-textarea"
            ]
            
            for selector in selectors:
                try:
                    input_field = WebDriverWait(browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if input_field:
                        print(f"Found input field using selector: {selector}")
                        break
                except:
                    continue
            
            if not input_field:
                print("Could not find input field!")
                browser.switch_to.window(current_tab)
                return None
            
            # Clear and send message
            print("Sending message to ChatGPT...")
            input_field.clear()
            
            # Send message in chunks to handle long messages
            chunk_size = 100
            message_chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
            
            for chunk in message_chunks:
                input_field.send_keys(chunk)
                time.sleep(0.1)
            
            time.sleep(1)
            input_field.send_keys(Keys.RETURN)
            
            print("Waiting for response...")
            time.sleep(3)
            
            # Wait for response with better detection
            response_selector = ".markdown-content p, .markdown-content pre, .response-message"
            max_retries = 30
            retry_count = 0
            last_response_length = 0
            stable_count = 0
            
            while retry_count < max_retries:
                try:
                    response_elements = browser.find_elements(By.CSS_SELECTOR, response_selector)
                    
                    if response_elements:
                        current_length = sum(len(elem.text) for elem in response_elements)
                        
                        if current_length > 0:
                            if current_length == last_response_length:
                                stable_count += 1
                                if stable_count >= 3:  # Response has been stable for 3 checks
                                    break
                            else:
                                stable_count = 0
                                last_response_length = current_length
                    
                    time.sleep(1)
                    retry_count += 1
                    
                except Exception as e:
                    print(f"Error checking response: {e}")
                    time.sleep(1)
                    retry_count += 1
            
            # Extract response
            print("Extracting response...")
            response_text = ""
            try:
                response_elements = browser.find_elements(By.CSS_SELECTOR, response_selector)
                response_text = "\n".join([elem.text for elem in response_elements if elem.text.strip()])
            except Exception as e:
                print(f"Error extracting response: {e}")
            
            # Switch back to original tab
            browser.switch_to.window(current_tab)
            
            return response_text
            
        except Exception as e:
            print(f"Error in send_to_chatgpt: {e}")
            print("Detailed error:")
            import traceback
            print(traceback.format_exc())
            
            # Make sure we return to the original tab
            try:
                browser.switch_to.window(current_tab)
            except:
                pass
            
            return None

    def _ensure_chrome_running(self):
        """Ensure Chrome is running with debugging enabled"""
        try:
            if not self.copilot_automation or not self.copilot_automation.browser:
                print("\nNo active Chrome instance found. Setting up Chrome...")
                if self.copilot_automation.setup_chrome_debugging():
                    chrome_options = webdriver.ChromeOptions()
                    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                    self.copilot_automation.browser = webdriver.Chrome(options=chrome_options)
                    print("Successfully connected to Chrome")
                    return True
                return False
            return True
        except Exception as e:
            print(f"Error ensuring Chrome is running: {e}")
            return False
        
    def wait_for_complete_response(self, browser) -> str:
        """Wait for complete response from ChatGPT with better completion detection"""
        max_attempts = 60  # 2 minutes maximum wait time
        attempt = 0
        last_response_length = 0
        same_length_count = 0
        generating_stopped = False
        final_wait_started = False
        final_wait_start_time = None
        
        print("\nWaiting for ChatGPT response...")
        
        while attempt < max_attempts:
            try:
                # Check for "Generating" indicator
                generating_indicators = browser.find_elements(By.CSS_SELECTOR, ".text-2xl") + \
                                    browser.find_elements(By.CSS_SELECTOR, "div[class*='generating']") + \
                                    browser.find_elements(By.CSS_SELECTOR, "div[class*='result-streaming']")
                
                is_generating = False
                for indicator in generating_indicators:
                    if indicator.is_displayed() and any(word in indicator.text.lower() for word in ['generating', 'thinking', 'working']):
                        is_generating = True
                        generating_stopped = False
                        final_wait_started = False
                        print("Still generating...", end='\r')
                        break
                
                # If we were generating but now stopped, start final wait timer
                if not is_generating and not generating_stopped:
                    generating_stopped = True
                    final_wait_started = True
                    final_wait_start_time = time.time()
                    print("\nGeneration appears complete, waiting final verification period...")
                
                # Get current response content
                response_elements = []
                selectors = [
                    "div[data-message-author-role='assistant'] div.markdown",
                    ".markdown-content",
                    ".prose",
                    "div.markdown"
                ]
                
                for selector in selectors:
                    elements = browser.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        response_elements.extend(elements)
                
                if response_elements:
                    # Get the last (most recent) response
                    latest_response = response_elements[-1]
                    current_response = latest_response.text.strip()
                    current_length = len(current_response)
                    
                    # If in final wait period, check if content is still changing
                    if final_wait_started:
                        if current_length != last_response_length:
                            # Content changed during final wait, reset timer
                            final_wait_start_time = time.time()
                            print("Content still updating, resetting final wait period...")
                        elif time.time() - final_wait_start_time >= 5:
                            # Content stable for 5 seconds after generation stopped
                            print("\nResponse complete and stable.")
                            return current_response
                    
                    # Update last known length
                    if current_length != last_response_length:
                        print(f"Response length: {current_length} characters", end='\r')
                        last_response_length = current_length
                
                time.sleep(2)
                attempt += 1
                
            except Exception as e:
                print(f"\nError checking response: {e}")
                time.sleep(2)
                attempt += 1
        
        print("\nTimed out waiting for response")
        return None

    def analyze_requirements(self, requirements: str) -> List[Dict]:
        """Break down project requirements using ChatGPT in browser"""
        self.project_requirements = requirements
        
        print("\nDebug: Checking automation initialization...")
        print(f"Copilot automation object exists: {self.copilot_automation is not None}")
        
        if not self.copilot_automation or not self.copilot_automation.browser:
            print("Browser automation not initialized")
            return []
                
        browser = self.copilot_automation.browser
        
        try:
            print("\nAttempting to find ChatGPT tab...")
            
            # Find ChatGPT tab
            print("\nStarting ChatGPT tab search...")
            current_tabs = browser.window_handles
            print(f"Current tabs: {len(current_tabs)}")
            
            chatgpt_tab = None
            for tab in current_tabs:
                try:
                    browser.switch_to.window(tab)
                    current_url = browser.current_url.lower()
                    if "chatgpt.com" in current_url or "chat.openai.com" in current_url:
                        print(f"Found ChatGPT tab at: {current_url}")
                        chatgpt_tab = tab
                        break
                except Exception as e:
                    print(f"Error checking tab: {e}")
                    continue
            
            if not chatgpt_tab:
                print("Could not find ChatGPT tab")
                return []
                        
            # Switch to ChatGPT tab and ensure it's ready
            browser.switch_to.window(chatgpt_tab)
            sleep(2)
            
            # Create the prompt for ChatGPT
            chatgpt_prompt = (
                "I need help breaking down this Minecraft plugin project into numbered implementation steps. "
                "For each step, provide a specific prompt for GitHub Copilot to generate the code.\n\n"
                "IMPORTANT: DO NOT INCLUDE ANY CODE IN YOUR RESPONSE. Only provide step descriptions and Copilot prompts.\n\n"
                f"Project Requirements:\n{requirements}\n\n"
                "Please break this down into numbered steps (1, 2, 3, etc.) where each step includes:\n"
                "1. Step number and title\n"
                "2. What this step implements\n"
                "3. Required Bukkit/Spigot APIs\n"
                "4. Classes and methods needed\n"
                "5. A specific, detailed prompt for GitHub Copilot to generate the code (NO CODE HERE, just the prompt)\n"
                "6. What to test after implementation\n\n"
                "Format each step clearly with numbers and ensure the steps build upon each other logically. "
                "Start with basic plugin setup and progress through more complex features. "
                "Please make sure each step's Copilot prompt is very detailed and specific to get the best code generation.\n\n"
                "IMPORTANT NOTES:\n"
                "- DO NOT include any actual code snippets, class definitions, or method implementations\n"
                "- DO NOT use code blocks (```) in your response\n"
                "- Only describe what needs to be implemented\n"
                "- Save all code generation for GitHub Copilot\n"
            )
            
            print("\nDebug - Prompt content:")
            print(chatgpt_prompt)
            
            # Wait for the page to be fully loaded
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find and wait for the input field
            print("Finding input field...")
            input_field = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#prompt-textarea"))
            )
            
            # Ensure the input field is interactable
            print("Ensuring input field is ready...")
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#prompt-textarea"))
            )
            
            # Clear existing text
            print("Clearing input field...")
            input_field.clear()
            sleep(1)
            
            # Store original clipboard content
            original_clipboard = pyperclip.paste()
            
            try:
                # Copy prompt to clipboard
                print("Copying prompt to clipboard...")
                pyperclip.copy(chatgpt_prompt)
                sleep(1)
                
                # Focus the input field and paste
                print("Pasting prompt...")
                input_field.click()
                sleep(0.5)
                pyautogui.hotkey('ctrl', 'v')
                sleep(1)
                
                # Submit the prompt
                print("Submitting prompt...")
                pyautogui.hotkey('ctrl', 'enter')
                sleep(2)
                
                # Wait for response with improved detection
                print("\nWaiting for ChatGPT response...")
                response_text = self.wait_for_complete_response(browser)
                
                if not response_text:
                    print("Failed to get complete response from ChatGPT")
                    return []

                # Show response preview and validate
                print("\nValidating ChatGPT response...")
                print("\nResponse preview (first 500 characters):")
                print("-" * 80)
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                print("-" * 80)
                
                if not self._validate_chatgpt_response(response_text):
                    print("\nChatGPT response contained code that should be generated by Copilot")
                    print("Options:")
                    print("1. Continue anyway")
                    print("2. Retry with a stronger warning")
                    print("3. Cancel")
                    
                    choice = input("\nEnter choice (1-3): ").strip()
                    if choice == '1':
                        print("Continuing with response...")
                    elif choice == '2':
                        print("Retrying with stronger warning...")
                        # Add stronger warning to prompt
                        chatgpt_prompt = (
                            "IMPORTANT - PREVIOUS RESPONSE CONTAINED CODE. DO NOT INCLUDE ANY CODE!\n\n" +
                            chatgpt_prompt
                        )
                        return self.analyze_requirements(requirements)
                    else:
                        print("Cancelling analysis")
                        return []
                
                # Parse the response into steps
                print("\nParsing ChatGPT response...")
                steps = self._parse_steps(response_text)
                
                if not steps:
                    print("Failed to parse steps from response")
                    return []
                
                # Convert steps into sections
                sections = []
                for step in steps:
                    section = {
                        'requirements': step['copilot_prompt'],
                        'status': 'pending',
                        'code_implemented': False,
                        'user_tested': False,
                        'context': step
                    }
                    sections.append(section)
                
                self.sections = sections
                
                # Print analysis summary
                print("\nProject Analysis:")
                print(f"Breaking down into {len(sections)} implementation steps:")
                for i, section in enumerate(sections, 1):
                    step = section['context']
                    print(f"\nStep {i}: {step['title']}")
                    print(f"Description: {step['description'][:100]}...")
                    if step.get('apis'):
                        print(f"Required APIs: {', '.join(step['apis'])}")
                
                return sections
                
            except Exception as e:
                print(f"Error in analyze_requirements: {e}")
                print("Full error trace:")
                print(traceback.format_exc())
                return []
                
            finally:
                # Restore original clipboard content
                try:
                    pyperclip.copy(original_clipboard)
                except:
                    pass
                
        except Exception as e:
            print(f"Error in analyze_requirements: {e}")
            print("Full error trace:")
            print(traceback.format_exc())
            return []
        
    def _reconnect_browser(self):
        """Attempt to reconnect to Chrome if connection is lost"""
        try:
            print("\nAttempting to reconnect to Chrome...")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            self.copilot_automation.browser = webdriver.Chrome(options=chrome_options)
            print("Successfully reconnected to Chrome")
            return True
        except Exception as e:
            print(f"Error reconnecting to Chrome: {e}")
            return False
        
    def _validate_chatgpt_response(self, response_text: str) -> bool:
        """Check if ChatGPT response contains actual code blocks that should be generated by Copilot"""
        if not response_text:
            return False
                
        # Look for actual code blocks with ```
        code_blocks = re.findall(r'```(?:java|kotlin|xml|yaml|yml)?\s*(.*?)```', response_text, re.DOTALL)
        if code_blocks:
            print("\nWARNING: Found code blocks that should be generated by Copilot")
            return False

        # Look for specific code patterns
        code_patterns = [
            r'public\s+class\s+\w+\s*{.*?}',  # Complete class definitions
            r'@Override\s*public\s+void\s+\w+\s*\(.*?\)\s*{.*?}',  # Complete method definitions
            r'package\s+[\w.]+;\s*import',  # Package and import statements together
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, response_text, re.DOTALL):
                print("\nWARNING: Found code implementation that should be generated by Copilot")
                return False

        # These are okay to mention in descriptions
        allowed_terms = {
            'plugin.yml', 'class', 'extends JavaPlugin', 'implements Listener',
            '@EventHandler', 'public void', 'private', 'protected', 'return',
            'package', 'import', 'org.bukkit'
        }

        return True

        
    def _find_chat_input(self, browser, max_retries=3):
        """Find chat input with retries"""
        for attempt in range(max_retries):
            try:
                print(f"\nAttempting to find chat input (attempt {attempt + 1}/{max_retries})...")
                
                # Try multiple selectors
                selectors = [
                    "#prompt-textarea",
                    "textarea[data-id='root']",
                    "textarea[placeholder*='Send a message']",
                    "textarea[class*='chat']"
                ]
                
                for selector in selectors:
                    try:
                        input_field = WebDriverWait(browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if input_field and input_field.is_displayed():
                            print(f"Found chat input using selector: {selector}")
                            return input_field
                    except:
                        continue
                
                print("No chat input found with current selectors, refreshing page...")
                browser.refresh()
                sleep(3)
                
            except Exception as e:
                print(f"Error finding chat input (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    sleep(2)
                continue
                
        raise Exception("Could not find chat input after multiple attempts")
    

    def _parse_steps(self, response_text: str) -> List[Dict]:
        """Parse the response text into structured steps"""
        try:
            print("\nParsing steps from response...")
            steps = []
            current_step = {}
            lines = response_text.split('\n')
            
            # State tracking
            in_step = False
            current_section = None
            copilot_prompt = []
            
            # Track processed titles to avoid duplicates
            processed_titles = set()
            
            def normalize_title(title: str) -> str:
                """Normalize step title to avoid duplicates"""
                # Remove step numbers and common prefixes
                title = re.sub(r'^(step\s*\d+[\.:]\s*|^\d+[\.:]\s*)', '', title.lower())
                # Remove extra whitespace
                return ' '.join(title.split())
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for main step headers or numbered steps
                if line.lower().startswith(('step ', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    # Extract title
                    if ':' in line:
                        title = line.split(':', 1)[1].strip()
                    else:
                        parts = line.split(' ', 1)
                        title = parts[1] if len(parts) > 1 else line
                    
                    normalized_title = normalize_title(title)
                    
                    # Skip if we've already processed this step
                    if normalized_title in processed_titles:
                        continue
                    
                    # Save previous step if exists
                    if current_step:
                        if copilot_prompt:
                            current_step['copilot_prompt'] = '\n'.join(copilot_prompt)
                        steps.append(current_step)
                    
                    # Start new step
                    processed_titles.add(normalized_title)
                    current_step = {
                        'title': title,
                        'description': '',
                        'apis': [],
                        'classes': [],
                        'copilot_prompt': ''
                    }
                    in_step = True
                    current_section = None
                    copilot_prompt = []
                    print(f"Found step: {title}")
                    continue
                
                if in_step:
                    # Check for section headers
                    lower_line = line.lower()
                    if any(header in lower_line for header in [
                        "what this step implements",
                        "this step implements",
                        "implementation"
                    ]):
                        current_section = "description"
                        continue
                    elif "copilot prompt" in lower_line:
                        current_section = "copilot_prompt"
                        print(f"Found Copilot prompt section in: {current_step['title']}")
                        continue
                    elif any(header in lower_line for header in [
                        "required bukkit/spigot apis",
                        "required apis",
                        "apis needed"
                    ]):
                        current_section = "apis"
                        continue
                    elif "what to test" in lower_line:
                        current_section = "testing"
                        continue
                    
                    # Add content to current section
                    if current_section == "description":
                        if current_step['description']:
                            current_step['description'] += ' ' + line
                        else:
                            current_step['description'] = line
                    elif current_section == "apis":
                        apis = [api.strip() for api in line.split(',')]
                        current_step['apis'].extend(api for api in apis if api)
                    elif current_section == "copilot_prompt":
                        copilot_prompt.append(line)
            
            # Don't forget to add the last step
            if current_step:
                if copilot_prompt:
                    current_step['copilot_prompt'] = '\n'.join(copilot_prompt)
                steps.append(current_step)
            
            print(f"\nSuccessfully parsed {len(steps)} steps")
            for i, step in enumerate(steps, 1):
                print(f"\nStep {i}: {step['title']}")
                print(f"Description: {step['description'][:100]}...")
                print(f"Prompt length: {len(step['copilot_prompt'])} characters")
            
            return steps
            
        except Exception as e:
            print(f"Error parsing steps: {e}")
            print("Full error trace:")
            print(traceback.format_exc())
            return []
        
    def _process_implementation_step(self, step: Dict, step_number: int, total_steps: int):
        """Process a single implementation step with robust error handling"""
        # Get step title from context if available
        title = step.get('context', {}).get('title', f"Step {step_number}")
        
        print(f"\nProcessing step {step_number} of {total_steps}")
        print(f"Title: {title}")
        
        try:
            print("Ensuring ChatGPT tab...")
            self._ensure_chatgpt_tab()
            sleep(1)
            
            print("Finding chat input...")
            input_field = self._find_chat_input_robust()
            if not input_field:
                raise Exception("Could not find chat input after multiple attempts")
            
            print("Preparing implementation prompt...")
            prompt = self._create_implementation_prompt(step)
            
            print("Entering and submitting prompt...")
            success = self._enter_and_submit_prompt(input_field, prompt)
            if not success:
                raise Exception("Failed to enter or submit prompt")
            
            print("Waiting for response...")
            response_text = ""
            last_length = 0
            no_change_count = 0
            max_no_change = 5
            
            while True:
                try:
                    response_elements = self.copilot_automation.browser.find_elements(
                        By.CSS_SELECTOR, 
                        "div[data-message-author-role='assistant'] div.markdown"
                    )
                    
                    if response_elements:
                        current_response = "\n".join([elem.text for elem in response_elements if elem.text])
                        if len(current_response) > last_length:
                            print(f"Response growing: {len(current_response)} characters")
                            last_length = len(current_response)
                            response_text = current_response
                            no_change_count = 0
                        else:
                            no_change_count += 1
                            
                        if no_change_count >= max_no_change and len(response_text) > 100:
                            print("Response appears complete")
                            break
                            
                    sleep(1)
                    
                except Exception as e:
                    print(f"Error while waiting for response: {e}")
                    if not response_text:
                        break
                    sleep(1)
            
            return response_text
            
        except Exception as e:
            print(f"Error processing step: {e}")
            print("Full error trace:")
            print(traceback.format_exc())
            return None

    def _ensure_chatgpt_tab(self):
        """Make sure we're on the ChatGPT tab"""
        try:
            current_url = self.copilot_automation.browser.current_url.lower()
            if "chatgpt.com" not in current_url and "chat.openai.com" not in current_url:
                # Find and switch to ChatGPT tab
                for handle in self.copilot_automation.browser.window_handles:
                    self.copilot_automation.browser.switch_to.window(handle)
                    if "chatgpt.com" in self.copilot_automation.browser.current_url.lower():
                        print("Switched to ChatGPT tab")
                        sleep(1)
                        return True
                raise Exception("ChatGPT tab not found")
            return True
        except Exception as e:
            raise Exception(f"Error ensuring ChatGPT tab: {e}")

    def _find_chat_input_robust(self):
        """Find chat input with multiple methods and retries"""
        browser = self.copilot_automation.browser
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to find chat input (attempt {attempt + 1}/{max_retries})...")
                
                # First ensure we're on the ChatGPT tab
                self._ensure_chatgpt_tab()
                
                # Wait for page to be ready
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Try multiple methods to find the input
                methods = [
                    # Method 1: Default textarea
                    (By.CSS_SELECTOR, "#prompt-textarea"),
                    # Method 2: Any textarea with chat-related attributes
                    (By.CSS_SELECTOR, "textarea[placeholder*='Send a message']"),
                    # Method 3: Any textarea
                    (By.TAG_NAME, "textarea"),
                    # Method 4: Any contenteditable div
                    (By.CSS_SELECTOR, "div[contenteditable='true']")
                ]
                
                for by, selector in methods:
                    try:
                        print(f"Trying selector: {selector}")
                        elements = browser.find_elements(by, selector)
                        
                        for element in elements:
                            if element.is_displayed():
                                try:
                                    # Try to interact with the element
                                    element.click()
                                    element.clear()
                                    print(f"Found and verified chat input using: {selector}")
                                    return element
                                except:
                                    continue
                    except:
                        continue
                
                # If we get here, no method worked - try refreshing
                if attempt < max_retries - 1:
                    print("No input found, refreshing page...")
                    browser.refresh()
                    sleep(3)
                    
            except Exception as e:
                print(f"Error finding chat input (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    sleep(2)
        
        raise Exception("Could not find chat input after multiple attempts")

    def _enter_and_submit_prompt(self, input_field, prompt: str):
        """Enter and submit prompt with multiple methods"""
        try:
            # Method 1: Clipboard paste
            try:
                print("Trying clipboard paste method...")
                pyperclip.copy(prompt)
                sleep(1)
                input_field.click()
                sleep(1)
                pyautogui.hotkey('ctrl', 'v')
                sleep(2)
                
                # Verify text entry
                actual_text = input_field.get_attribute('value') or input_field.text
                if actual_text and len(actual_text) > 10:
                    print("Text entered successfully via clipboard")
                    # Submit with PyAutoGUI
                    pyautogui.hotkey('ctrl', 'enter')
                    sleep(2)
                    return True
            except Exception as e:
                print(f"Clipboard paste failed: {e}")
            
            # Method 2: Selenium send_keys
            try:
                print("Trying Selenium send_keys...")
                input_field.clear()
                input_field.send_keys(prompt)
                sleep(2)
                input_field.send_keys(Keys.CONTROL + Keys.RETURN)
                sleep(2)
                return True
            except Exception as e:
                print(f"Selenium send_keys failed: {e}")
            
            return False
            
        except Exception as e:
            print(f"Error entering prompt: {e}")
            return False

    def _create_implementation_prompt(self, step: Dict) -> str:
        """Create the implementation prompt emphasizing proper code organization"""
        if 'context' in step:
            title = step['context'].get('title', 'Unknown Step')
            description = step['context'].get('description', '')
        else:
            title = "Unknown Step"
            description = ""

        requirements = step.get('requirements', '')
        main_class_name = self.project_info.get('main_class_name', '')

        base_prompt = (
            f"Let's implement step: {title}\n\n"
            f"Description: {description}\n\n"
            "CRITICAL CODE ORGANIZATION RULES:\n"
            "1. Main class should ONLY contain:\n"
            "   - Plugin initialization\n"
            "   - Event listener registration\n"
            "   - Command registration\n"
            "   - Manager/Handler initialization\n"
            "   - Configuration loading/saving\n\n"
            "2. ALL other functionality MUST be in separate classes:\n"
            "   - Commands → Create separate command classes\n"
            "   - Events → Create separate listener classes\n"
            "   - Core logic → Create appropriate manager/handler classes\n"
            "   - Data handling → Create dedicated data classes\n\n"
            "FORMATTING REQUIREMENTS:\n"
            "1. Start with all imports, marked with '//IMPORTS:'\n"
            "2. For main class additions (ONLY registration/initialization!):\n"
            "   //PLACEMENT: Add to onEnable()\n"
            "   //CODE TO ADD:\n"
            "   // Example: register events, commands, load config\n\n"
            "   //PLACEMENT: Add to onDisable()\n"
            "   //CODE TO ADD:\n"
            "   // Example: save data, cleanup resources\n\n"
            "3. For main class fields (ONLY manager/handler instances):\n"
            "   //ADD FIELDS TO MAIN CLASS:\n"
            "   // Example: private final CommandManager commandManager;\n\n"
            "4. For new functionality classes:\n"
            "   //NEW CLASS: [appropriate class name]\n"
            "   // Full implementation of functionality\n\n"
            "EXAMPLES:\n"
            "✓ GOOD - Main Class Content:\n"
            "   - private final TeamManager teamManager;\n"
            "   - getTeamManager() method\n"
            "   - teamManager = new TeamManager(this);\n"
            "   - getServer().getPluginManager().registerEvents(new TeamListener(this), this);\n"
            "   - getCommand(\"team\").setExecutor(new TeamCommand(this));\n\n"
            "✗ BAD - Main Class Content:\n"
            "   - Team creation logic\n"
            "   - Event handling code\n"
            "   - Command execution logic\n"
            "   - Data manipulation\n\n"
            "Remember:\n"
            "- Main class should be as minimal as possible\n"
            "- Create descriptive class names for functionality\n"
            "- Use proper dependency injection\n"
            "- Follow Single Responsibility Principle\n\n"
        )

        if not self.project_info.get('is_new_plugin', True):
            base_prompt += (
                f"IMPORTANT: This is an existing plugin with main class '{main_class_name}'\n"
                "- DO NOT provide complete onEnable/onDisable implementations\n"
                "- Only provide the specific lines to be added\n"
                "- Use proper placement instructions\n\n"
            )

        base_prompt += (
            "Please provide the implementation, following these organization rules exactly.\n"
            "Always create separate classes for functionality.\n"
            "Main class should ONLY contain initialization and registration code.\n\n"
            f"Requirements:\n{requirements}\n\n"
        )

        return base_prompt
    
    def implement_steps(self, project_info: dict) -> None:
        """Implement all steps"""
        print("\n=== Starting Implementation ===\n")
        
        try:
            for i, step in enumerate(self.sections, 1):
                print(f"\nProcessing step {i} of {len(self.sections)}")
                
                # Switch to Copilot tab and ensure chat interface
                print("Switching to Copilot chat interface...")
                if not self._switch_to_copilot_tab():
                    raise Exception("Could not access Copilot chat interface")
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Get the Copilot input field with explicit wait
                        input_field = WebDriverWait(self.copilot_automation.browser, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#copilot-chat-textarea"))
                        )
                        
                        if not input_field:
                            raise Exception("Could not find Copilot chat input")
                        
                        # Create and send the implementation prompt
                        prompt = self._create_implementation_prompt(step)
                        print(f"\nSending implementation prompt to Copilot for step {i}...")
                        
                        if not self.copilot_automation.send_prompt_to_chat(input_field, prompt):
                            raise Exception("Failed to send prompt to Copilot")
                        
                        # Wait for and handle Copilot's response with project info
                        print("Waiting for Copilot's response...")
                        if not self.copilot_automation.handle_code_implementation(project_info):
                            raise Exception("Failed to get implementation from Copilot")
                        
                        print("\nStep implementation successful")
                        
                        # Ask for user confirmation
                        while True:
                            user_input = input("\nDoes this implementation look correct? (yes/no/retry): ").lower()
                            if user_input in ['yes', 'y']:
                                step['status'] = 'complete'
                                break
                            elif user_input in ['no', 'n']:
                                print("\nMoving to next step...")
                                break
                            elif user_input == 'retry':
                                print("\nRetrying step implementation...")
                                continue
                            else:
                                print("Invalid input. Please enter 'yes', 'no', or 'retry'")
                        
                        if step['status'] == 'complete':
                            break
                            
                    except Exception as e:
                        print(f"Error in attempt {attempt + 1}: {e}")
                        if attempt < max_retries - 1:
                            sleep(2)
                            continue
                        else:
                            print("All attempts failed for this step")
                            break
            
            print("\n=== Implementation Complete ===")
            print(f"Processed {len(self.sections)} steps")
            completed = sum(1 for step in self.sections if step['status'] == 'complete')
            print(f"Successfully completed: {completed}/{len(self.sections)} steps")
            
        except Exception as e:
            print(f"Error in implementation process: {e}")
            print("Full error trace:")
            print(traceback.format_exc())

    def _switch_to_copilot_tab(self):
        """Switch to the Copilot tab and ensure we're on the chat interface"""
        try:
            browser = self.copilot_automation.browser
            
            # First try to find existing Copilot tab
            for handle in browser.window_handles:
                browser.switch_to.window(handle)
                current_url = browser.current_url.lower()
                
                if "copilot" in current_url:
                    # Check if we're on the chat interface
                    if not self._ensure_copilot_chat_page():
                        continue
                        
                    print("Successfully switched to Copilot chat interface")
                    sleep(1)
                    return True
                    
            # If we haven't found it, try to open it
            print("Opening new Copilot tab...")
            browser.execute_script("window.open('https://github.com/copilot/chat', '_blank');")
            sleep(2)
            
            # Switch to new tab
            browser.switch_to.window(browser.window_handles[-1])
            
            # Ensure we're on the chat interface
            if self._ensure_copilot_chat_page():
                print("Successfully opened Copilot chat interface")
                return True
                
            raise Exception("Could not access Copilot chat interface")
            
        except Exception as e:
            print(f"Error switching to Copilot tab: {e}")
            return False
        
    def _ensure_copilot_chat_page(self):
        """Ensure we're on the Copilot chat interface page"""
        try:
            browser = self.copilot_automation.browser
            current_url = browser.current_url.lower()
            
            # If we're not on a Copilot page, return False
            if "copilot" not in current_url:
                return False
                
            # Check if we're already on the chat interface
            chat_input = browser.find_elements(By.CSS_SELECTOR, "#copilot-chat-textarea")
            if chat_input:
                return True
                
            # If not, try to navigate to the chat interface
            if "github.com/features/copilot" in current_url:
                # Click the "Try Copilot" or similar button
                try:
                    buttons = browser.find_elements(By.CSS_SELECTOR, "a[href*='copilot/chat']")
                    for button in buttons:
                        if button.is_displayed():
                            button.click()
                            sleep(2)
                            return True
                except:
                    pass
                    
            # Try direct navigation to chat
            browser.get("https://github.com/copilot/chat")
            sleep(3)
            
            # Verify we're on the chat interface
            chat_input = browser.find_elements(By.CSS_SELECTOR, "#copilot-chat-textarea")
            return bool(chat_input)
            
        except Exception as e:
            print(f"Error ensuring Copilot chat page: {e}")
            return False        

    def _get_latest_chatgpt_response(self):
        """Get only the latest response from ChatGPT with better targeting"""
        try:
            browser = self.copilot_automation.browser
            
            # Try multiple selectors to find the latest response
            selectors = [
                # Primary selector for latest response
                "div.group.w-full:last-child div[data-message-author-role='assistant']",
                # Backup selector
                "div[data-message-author-role='assistant']:last-of-type",
                # Another common structure
                ".markdown-content:last-child",
                # Final fallback
                "div.group.w-full:last-child .prose"
            ]
            
            for selector in selectors:
                try:
                    # Wait briefly for the element
                    element = WebDriverWait(browser, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element and element.is_displayed():
                        response_text = element.text.strip()
                        if response_text:
                            return response_text
                except:
                    continue
            
            # If no selectors worked, try finding all responses and getting the last one
            all_responses = browser.find_elements(
                By.CSS_SELECTOR, 
                "div[data-message-author-role='assistant']"
            )
            
            if all_responses:
                return all_responses[-1].text.strip()
                
            return None
            
        except Exception as e:
            print(f"Error getting latest ChatGPT response: {e}")
            return None


    def process_section(self, section_index: int) -> bool:
        """Process a specific section with Copilot"""
        if section_index >= len(self.sections):
            return False
            
        section = self.sections[section_index]
        if section['status'] != 'pending':
            return False
            
        try:
            # Get back to Copilot tab
            for tab in self.copilot_automation.browser.window_handles:
                self.copilot_automation.browser.switch_to.window(tab)
                if "copilot" in self.copilot_automation.browser.current_url.lower():
                    break
            
            # Send implementation prompt to Copilot
            input_element = self.copilot_automation.find_chat_input()
            if not input_element:
                print("Could not find chat input")
                return False
            
            step = section['context']
            print(f"\nImplementing step {step['number']}: {step['title']}")
            
            # Use the specific Copilot prompt from ChatGPT
            prompt = section['requirements']
            if not self.copilot_automation.send_prompt_to_chat(input_element, prompt):
                print("Failed to send prompt to Copilot")
                return False
            
            # Handle code implementation
            if not self.copilot_automation.handle_code_implementation():
                print("Failed to implement code")
                return False
            
            # Update section status
            section['status'] = 'implemented'
            section['code_implemented'] = True
            
            # Request user testing
            print(f"\n{'='*60}")
            print(f"Step {step['number']}: {step['title']} Implementation Complete!")
            print("\nTesting Criteria:")
            for test in step['testing']:
                print(f"- {test}")
            print("\nPlease test the implementation against these criteria.")
            print("Enter 'continue' when testing is complete, or 'retry' if changes are needed.")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"Error processing section {section_index}: {e}")
            return False

    def run(self, copilot_automation) -> None:
        """Main execution loop"""
        try:
            self.copilot_automation = copilot_automation
            
            # Perform initial checks and get project info
            print("\nPerforming initial project checks...")
            project_info = self.perform_initial_checks()
            if not project_info:
                print("Failed to get required project information")
                return
            
            print("\n=== Starting Implementation Process ===")
            
            # Store project info in copilot automation
            copilot_automation.project_info = project_info
            copilot_automation.temp_file_path = project_info.get('temp_file')
            
            # Modify prompts to include package information
            if hasattr(self, 'sections'):
                for section in self.sections:
                    section['requirements'] = self.modify_copilot_prompt(
                        section['requirements'],
                        project_info
                    )
            
            # Call implement_steps with project info
            self.implement_steps(project_info)
            
            print("\n=== Implementation Complete ===")
            
        except Exception as e:
            print(f"Error in run method: {e}")
            print("Full error trace:")
            print(traceback.format_exc())