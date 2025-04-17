#!/usr/bin/env python
"""
Script to check and fix .env file issues
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    print("====== Environment File Checker ======")
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check for .env files in current and parent directories
    env_files = []
    for path in [current_dir, os.path.join(current_dir, 'backend')]:
        env_file = os.path.join(path, '.env')
        if os.path.exists(env_file):
            env_files.append(env_file)
            
    if env_files:
        print("\nFound .env files:")
        for file in env_files:
            print(f"- {file}")
    else:
        print("\nNo .env files found in current or backend directories")
    
    # Check for .env.example files
    example_files = []
    for path in [current_dir, os.path.join(current_dir, 'backend')]:
        example_file = os.path.join(path, '.env.example')
        if os.path.exists(example_file):
            example_files.append(example_file)
    
    if example_files:
        print("\nFound .env.example files:")
        for file in example_files:
            print(f"- {file}")
    else:
        print("\nNo .env.example files found")
    
    # Action menu
    while True:
        print("\nOptions:")
        print("1. Create new .env file in current directory")
        print("2. Create new .env file in backend directory")
        print("3. Copy existing .env file to another location")
        print("4. Display contents of an existing .env file")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            create_env_file(current_dir)
        elif choice == "2":
            backend_dir = os.path.join(current_dir, 'backend')
            if not os.path.exists(backend_dir):
                print(f"Backend directory not found: {backend_dir}")
                continue
            create_env_file(backend_dir)
        elif choice == "3":
            copy_env_file()
        elif choice == "4":
            display_env_files()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again")

def create_env_file(directory):
    env_path = os.path.join(directory, '.env')
    
    if os.path.exists(env_path):
        overwrite = input(f".env already exists at {env_path}. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            return
    
    serpapi_key = input("Enter your SERPAPI_API_KEY (leave empty to skip): ")
    anthropic_key = input("Enter your ANTHROPIC_API_KEY (leave empty to skip): ")
    
    with open(env_path, 'w') as f:
        if serpapi_key:
            f.write(f"SERPAPI_API_KEY={serpapi_key}\n")
        if anthropic_key:
            f.write(f"ANTHROPIC_API_KEY={anthropic_key}\n")
    
    print(f"\n✅ Created .env file at {env_path}")

def copy_env_file():
    # Find all .env files
    all_env_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == '.env':
                path = os.path.join(root, file)
                all_env_files.append(path)
    
    if not all_env_files:
        print("No .env files found to copy")
        return
    
    print("\nFound .env files:")
    for i, file in enumerate(all_env_files):
        print(f"{i+1}. {file}")
    
    try:
        source_idx = int(input("\nSelect source file number: ")) - 1
        if source_idx < 0 or source_idx >= len(all_env_files):
            print("Invalid selection")
            return
        
        source_file = all_env_files[source_idx]
        
        # Destination options
        destinations = [os.getcwd(), os.path.join(os.getcwd(), 'backend')]
        
        print("\nDestination options:")
        for i, dest in enumerate(destinations):
            print(f"{i+1}. {dest}")
        
        dest_idx = int(input("\nSelect destination number: ")) - 1
        if dest_idx < 0 or dest_idx >= len(destinations):
            print("Invalid selection")
            return
        
        destination = os.path.join(destinations[dest_idx], '.env')
        
        if os.path.exists(destination) and destination != source_file:
            overwrite = input(f".env already exists at {destination}. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                return
        
        shutil.copy2(source_file, destination)
        print(f"\n✅ Copied {source_file} to {destination}")
        
    except ValueError:
        print("Invalid input, please enter a number")
    except Exception as e:
        print(f"Error copying file: {str(e)}")

def display_env_files():
    # Find all .env files
    all_env_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == '.env':
                path = os.path.join(root, file)
                all_env_files.append(path)
    
    if not all_env_files:
        print("No .env files found")
        return
    
    print("\nFound .env files:")
    for i, file in enumerate(all_env_files):
        print(f"{i+1}. {file}")
    
    try:
        file_idx = int(input("\nSelect file number to display: ")) - 1
        if file_idx < 0 or file_idx >= len(all_env_files):
            print("Invalid selection")
            return
        
        selected_file = all_env_files[file_idx]
        
        print(f"\nContents of {selected_file}:")
        print("-" * 40)
        
        with open(selected_file, 'r') as f:
            lines = f.readlines()
            
            if not lines:
                print("(Empty file)")
            
            for line in lines:
                # Mask API keys in the output
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if "KEY" in key and len(value) > 8:
                        masked_value = f"{value[:4]}...{value[-4:]}"
                        print(f"{key}={masked_value}")
                    else:
                        print(line.strip())
                else:
                    print(line.strip())
        
        print("-" * 40)
        
    except ValueError:
        print("Invalid input, please enter a number")
    except Exception as e:
        print(f"Error displaying file: {str(e)}")

if __name__ == "__main__":
    main() 