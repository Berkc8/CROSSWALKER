"""
Finds candidates for a clue via Encyclopedia.com.
"""

import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


def getCandidates(clue):
    """
    Takes a clue and returns a set of candidates for that clue using Encyclopedia.com.
    
    ...

    Parameters
    ----------
    clue : str

    Returns
    -------
    candidates : set
        set of candidates obtained via Encyclopedia.com

    """
    print('\tGetting Encyclopedia Candidates')
    candidates = set()
    formatted_clue = clue.replace(' ', '+')                 # Clues are formatted to certain type
    URL = f'https://www.encyclopedia.com/gsearch?q={formatted_clue}'
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options)              # After chrome options are set driver called
    driver.get(URL)
    soup = BeautifulSoup(driver.page_source, 'html.parser') 
    links = soup.find_all('a', {'class': 'gs-title'})       # Necessary classes are pointed for iteration

    for link in links:
        text = link.text
        text.replace(' | Encyclopedia.com', '')             # Unnecessary string is removed from the title
        candidates.add(text.replace(' ', ''))               # Title text is added to candidate set, removing spaces
        words = re.split('[;:,.\-\% ]', text)               # Words from the title are separated according to the given separators and a list is created
        candidates.update(words)                            # The list containing the words is added to candidates set
    driver.close()
    return candidates
