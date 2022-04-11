"""
Finds candidates for a clue via Merriam-Webster.
"""

import re
import urllib.request
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def getCandidates(clue):
    """
    Takes a clue and returns a set of candidates for that clue using Merriam-Webster.
    
    ...

    Parameters
    ----------
    clue : str

    Returns
    -------
    candidates : set
        set of candidates obtained via Merriam-Webster.

    """
    if '___' in clue:
        return {}
    print('\tGetting Merriam-Webster Candidates')
    candidates = set()
    formatted_clue = clue.replace(' ', '%20')                            # Clues are formatted to certain type
    candidates = candidates.union(
        getDictionaryCandidates(formatted_clue))                         # Candidates from dictionary called
    candidates = candidates.union(
        getThesaurusCandidates(formatted_clue))                          # Candidates from thesaurus called 
    for word in removeNonAlphabetic(clue):
        if word.lower() not in stopwords.words('english'):               # Candidate list are filtered from stopwords
            candidates = candidates.union(getDictionaryCandidates(word)) # Thesaurus and dictionary candidates are added to the candidate list
            candidates = candidates.union(getThesaurusCandidates(word))
    return candidates


def getDictionaryCandidates(clue):
    """
    Takes a clue and returns a set of candidates for that clue using Merriam-Webster Dictionary.
    
    ...

    Parameters
    ----------
    clue : str

    Returns
    -------
    candidates : set
        set of candidates obtained via Merriam-Webster Dictionary.

    """
    candidates = set()
    URL = f'https://www.merriam-webster.com/dictionary/{clue}'
    try:
        webUrl = urllib.request.urlopen(URL)
        data = webUrl.read()
        soup = BeautifulSoup(data, 'html.parser')
        definitions = soup.find_all('span', {'class': 'dtText'})
        for definition in definitions:
            text = definition.text
            words = re.split('[;:,.\-\% ]', text)  # Words from the text are separated according to the given separators and a list is created
            words.append(text.replace(" ", ""))    # Link text is added to the list, removing spaces
            candidates.update(words)               # The list is added to the candidate set
    except:
        if '%20' in clue:      
            candidates.update(useSelenium(URL))    # If the clue consists of more than one word, useSelenium function is called
        else:
            pass
    return candidates


def getThesaurusCandidates(clue):
    """
    Takes a clue and returns a set of candidates for that clue using Merriam-Webster Thesaurus.
    
    ...

    Parameters
    ----------
    clue : str

    Returns
    -------
    candidates : set
        set of candidates obtained via Merriam-Webster Thesaurus.

    """
    candidates = set()
    URL = f'https://www.merriam-webster.com/thesaurus/{clue}'
    try:
        webUrl = urllib.request.urlopen(URL)
        data = webUrl.read()
        soup = BeautifulSoup(data, 'html.parser')
        lists = soup.find_all('ul', {'class': 'mw-list'})
        items = []

        for ul in lists:
            items.append(ul.find_all('li'))

        for item in items:
            for i in item:
                for link in i.find_all('a'):
                    text = link.text
                    words = re.split('[;:,.\-\% ]', text) # Words from the text are separated according to the given separators and a list is created
                    words.append(text.replace(" ", ""))   # Link text is added to the list, removing spaces
                    candidates.update(words)              # The list is added to the candidate set
    except:
        if '%20' in clue:
            candidates.update(useSelenium(URL))           # If the clue consists of more than one word, useSelenium function is called
        else:
            pass

    return candidates


def useSelenium(URL):
    candidates = set()
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--headless')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    suggestions = soup.find_all('p', {'class': 'spelling-suggestions'})
    for sug in suggestions:
        text = sug.text
        candidates.add(text.replace(' ', ''))  
        words = re.split('[;:,.\-\% ]', text)  
        candidates.update(words)
    return candidates


def removeNonAlphabetic(clue):
    """
    Filters non-alphabetic words from the clue.

    """
    regex = re.compile('[^a-zA-Z]')
    words = {regex.sub('', word) for word in clue.split(' ')}
    return words


def isMeaningful(word):
    """
    Checks whether the candidate word is meaningful or not.
    
    ...

    Parameters
    ----------
    word : str
        candidate word.

    Returns
    -------
    bool
        if there is no Merriam-Webster Dictionary page for the word, returns False.

    """
    URL = f'https://www.merriam-webster.com/dictionary/{word}'
    try:
        webUrl = urllib.request.urlopen(URL)
    except:
        return False
    return True
