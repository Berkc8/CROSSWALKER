"""
Finds candidates for a clue via WordNet.
"""

import re
from nltk.corpus import wordnet


def getCandidates(clue, length):
    """
    Takes a clue and returns a set of candidates for that clue using WordNet.
    
    ...

    Parameters
    ----------
    clue : str
    length : int
        length of the related answer.

    Returns
    -------
    candidates : set
        set of candidates obtained via WordNet.
        
    """

    # Skips the fill in the blank clues
    if '___' in clue:
        return {}
    print('\tGetting Wordnet Candidates')
    candidates = set()
    formatted_clue = clue.replace(' ', '_')                               # Filtering the spaces and underscore
    synsets = wordnet.synsets(formatted_clue)                             # Find synonyms
    candidates.update(
        {y for x in synsets for y in x.lemma_names() if len(y) == length})
    for syn in synsets:
        candidates.update(searchWordnet(syn, length, candidates))

    return candidates


def searchWordnet(synset, length, candidates, max_iterations=3, iteration=0):
    """
    Searches for candidates of the given length in WordNet

    Parameters
    ----------
    synset 
    length : int
        length of the required answer.
    candidates : set
        set of candidates for the clue.
    max_iterations : int, optional
        maximum number of iterations. The default is 3.
    iteration : int, optional
        current number of iterations. The default is 0.

    Returns
    -------
    candidates : set
        set of candidates for the clue.

    """
    if synset.lemma_names():
        candidates.update({
            noSpace(lemmaname) for lemmaname in synset.lemma_names() if noSpace(lemmaname) == length
        })
    candidates.update([word for word in (synset.definition()).split(' ')])
    for attr in ['root_hypernyms', 'member_holonyms', 'hyponyms', 'hypernyms']:
        if getattr(synset, attr)():
            for nym in getattr(synset, attr)():
                candidates.update({
                    noSpace(lemma.name()) for lemma in nym.lemmas() if len(noSpace(lemma.name())) == length
                })
                if iteration < max_iterations:
                    candidates.update(searchWordnet(
                        nym, length, candidates, max_iterations, iteration+1))
    return candidates


def noSpace(word):
    """
    Removes spaces.

    """
    return re.sub('_', '', word)
