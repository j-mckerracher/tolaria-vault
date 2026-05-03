import os

import requests

from bs4 import BeautifulSoup

import re

  

# ==============================================================================

# --- Configuration ---

# ==============================================================================

  

# Set the directory where the text files will be saved.

# The script will create this folder if it doesn't exist.

#

# Example for Windows: "C:\\Users\\YourUser\\Documents\\PurdueDocs"

# Example for macOS/Linux: "/home/youruser/documents/purdue_docs"

OUTPUT_DIR = "purdue_rcac_docs"

  

# Add or remove pages to scrape here.

# The key is the category name (which will be used for the filename)

# and the value is the full URL of the document.

URLS_TO_SCRAPE = {

    "Basics of SLURM jobs": "https://www.rcac.purdue.edu/knowledge/gilbreth/run/slurm-basics",

    "Example jobs": "https://www.rcac.purdue.edu/knowledge/gilbreth/run/job-examples",

    "Python": "https://www.rcac.purdue.edu/knowledge/gilbreth/run/python",

}

  

# ==============================================================================

# --- End of Configuration ---

# ==============================================================================

  

def generate_filename(name):

    """

    Cleans a string to be used as a valid filename.

    - Removes characters that are not letters, numbers, whitespace, or hyphens.

    - Converts the string to lowercase.

    - Replaces spaces and hyphens with a single underscore.

    - Appends the '.txt' extension.

    """

    # Remove invalid characters, keeping alphanumeric, whitespace, and hyphens

    name = re.sub(r'[^\w\s-]', '', name).strip().lower()

    # Replace one or more whitespace characters or hyphens with a single underscore

    name = re.sub(r'[-\s]+', '_', name)

    return f"{name}.txt"

  
  

def scrape_and_save(urls, output_dir):

    """

    Scrapes the content from a dictionary of URLs and saves it to text files.

  

    Args:

        urls (dict): A dictionary where keys are category names and values are URLs.

        output_dir (str): The path to the directory where files will be saved.

    """

    # --- 1. Create the output directory ---

    # The script will create the specified directory if it doesn't already exist.

    try:

        if not os.path.exists(output_dir):

            os.makedirs(output_dir)

            print(f"Successfully created directory: {output_dir}")

    except OSError as e:

        print(f"Error: Could not create directory {output_dir}. Reason: {e}")

        return # Exit if we can't create the directory

  

    # --- 2. Loop through URLs and process each page ---

    for category, url in urls.items():

        try:

            print("\n" + "-"*50)

            print(f"Processing category: '{category}'")

            print(f"Fetching content from: {url}")

  

            # --- Fetch the HTML content with a reasonable timeout ---

            response = requests.get(url, timeout=15)

            # Raise an HTTPError for bad responses (like 404 Not Found or 500 Server Error)

            response.raise_for_status()

  

            # --- Parse the HTML using BeautifulSoup ---

            soup = BeautifulSoup(response.content, 'html.parser')

  

            # --- Extract the main content area ---

            # From inspecting the site, the main article is within a <div id="content">

            # which contains an <article> tag.

            content_area = soup.find('div', id='content')

            if not content_area or not content_area.find('article'):

                print(f"Warning: Could not find the main article content for '{category}'. Skipping.")

                continue

  

            # Get all text from the article, using newlines to separate elements

            article_text = content_area.find('article').get_text(separator='\n\n', strip=True)

  

            # --- Generate a clean filename and define the full save path ---

            filename = generate_filename(category)

            filepath = os.path.join(output_dir, filename)

  

            # --- Save the extracted text to a file using UTF-8 encoding ---

            with open(filepath, 'w', encoding='utf-8') as f:

                f.write(f"Source URL: {url}\n")

                f.write("="*80 + "\n\n")

                f.write(article_text)

  

            print(f"Successfully saved content to: {filepath}")

  

        except requests.exceptions.RequestException as e:

            print(f"Error: Could not fetch the URL {url}. Please check the URL and your connection. Details: {e}")

        except Exception as e:

            print(f"An unexpected error occurred while processing {url}. Details: {e}")

  

# --- Main execution block ---

# This ensures the script runs only when executed directly (not when imported)

if __name__ == "__main__":

    scrape_and_save(URLS_TO_SCRAPE, OUTPUT_DIR)

    print("\n" + "="*50)

    print("Script finished.")

    print(f"All requested files have been saved in the '{os.path.abspath(OUTPUT_DIR)}' directory.")

    print("="*50)