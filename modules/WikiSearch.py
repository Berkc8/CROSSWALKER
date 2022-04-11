"""
Finds candidates for a clue via Wikipedia.
"""

import wikipedia as wiki
import urllib.request
import re
from bs4 import BeautifulSoup


def getCandidates(clue, num_results=20, summaries=5):   
    """
    Takes a clue and searches on Wikipedia. Find summary pages and titles then
    returns set of candidates.

    Parameters
    ----------
    clue : str
    num_results : int, optional
        number of results that will be searched. The default is 20.
    summaries : TYPE, optional
        number of summaries that will be searched. The default is 5.

    Returns
    -------
    candidates : set
        set of candidates obtained via Wikipedia.

    """    
                                                                          # Initialize summarized page count and listed result on per search
    formatted_clue = clue.replace(' ', '+')                               # Clues are formatted to certain type
    candidates = set()
    print('\tGetting Wikipedia Candidates')
    URL = f'https://en.wikipedia.org/w/index.php?search={formatted_clue}' # Set URL for each clue
    try:
        # Setting website link for web scraping 
        webUrl = urllib.request.urlopen(URL)
        data = webUrl.read()
        soup = BeautifulSoup(data, 'html.parser')
        definitions = soup.find_all('div', {'class': 'searchresult'})
        definitions.extend(soup.find_all('span', {'class': 'searchalttitle'}))
        for definition in definitions:
            text = definition.text
            words = re.split('[;:,.\-\% ]', text)                         # Filtering unnecessary characters
            words.append(text.replace(" ", ""))
            candidates.update(words)                                      # Add resulted words to set of candidates
    except:
        pass

    pages = wiki.search(clue, num_results)
    i = 0
    for page in pages:
        candidates.add(page.replace(' ', ''))
        candidates.add(page.replace('-', ''))
        candidates.update([word for word in page.split(' ')])
        if i < summaries:
            i += 1
            candidates.update(getWikiSummary(page))
    return candidates


def getWikiSummary(page, sentences=3):
    """
    Initializes Wikipedia summary search. Returns a list of words existing on the first 3 sentences of a summary by default.

    """
    words = []
    try:
        summary = wiki.summary(page, sentences=sentences)
        words = summary.split(' ')
    except:
        pass
    return words
