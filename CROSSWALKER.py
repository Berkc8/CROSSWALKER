"""
Solves 5x5 New York Times Mini Crossword Puzzle, using the clues provided by the puzzle itself.
Uses specialized modules to get candidates from four different sources, which are: Wikipedia,
WordNet, Merriam-Webster and Encyclopedia.com.  

@GROUP_MEMBERS: Berk Çiçek, Berk Takıt, Özge Kılınç, Zeynep Başak Eken
"""


from modules import EncyclopediaSearch
from modules import WikiSearch
from modules import MerriamSearch
from modules import WordnetSearch
from scrape_puzzle import CrosswordDisplay
from collections import defaultdict
import numpy as np
import re
from nltk.corpus import stopwords
import time
import spacy
import functools
import enchant

nlp = spacy.load('en_core_web_lg')


class Clue:
    def __init__(self, clue, startPos, heading, length, id):
        self.clue = clue
        self.startPos = startPos
        self.heading = heading  # (0,1) for across (1,0) for down
        self.length = length
        self.candidates = set()
        self.backup = set()
        self.id = id
        self.answer = ""
        self.constraints = []
        self.letter_positions = []
        self.clue_type = None
        for i in range(length):
            self.letter_positions.append(
                (startPos[0] + i * heading[0], startPos[1] + i * heading[1]))

    def addConstraints(self, clue):
        """
            Adds constraints according to the letter positions.

        """
        for i, pos in enumerate(clue.letter_positions):
            if pos in self.letter_positions:
                self.constraints.append(
                    ((self.id, clue.id), (self.letter_positions.index(pos), i)))
                return ((self.id, clue.id), (self.letter_positions.index(pos), i))
        return None


class CROSSWALKER:
    def __init__(self):
        self.scraper = CrosswordDisplay()
        self.solution = np.array([["" for _ in range(5)] for __ in range(5)])
        self.constraints = []
        self.sols = []

    def initCandidates(self):
        """
            Initialize candidate lists for all clues.
        
        """
        for id, clue in self.clues.items():
            print(f'Getting candidates for clue {id} : {clue.clue}')
            clue.clue_type, clue_text = self.determineClueType(clue.clue)
            clue.candidates = self.getCandidates(clue)
            print(f'Got {len(clue.candidates)} candidates')

    def getCandidates(self, clue):
        """
            Get Candidates for given clue.

            ...

            Parameters
            ----------
                clue: Clue
                    Clue object to get candidates for

            ...

            Returns
            -------
            candidates: set
                set of all legal candidates
        """

        candidates = set()

        # Don't bother searching for clues of these types as they are nearly impossible to find
        # return an empty set instead so we can ignore it in constraint satisfaction
        if clue.clue_type in ['QuestionMark', 'SquareBrackets', 'ReferClue', 'HumanSpeech']:
            return candidates

        length = clue.length
        clue_text = clue.clue

        # If clue is an abbreviation, we get the best results after formatting it a certain
        # way
        if clue.clue_type == 'Abbreviation':
            clue_text = self.formatAbbr(clue.clue)

        # If the clue is a kindof or single word clue, the answers are most frequently
        # found in the dictionary, thesaurus so no need to get candidates from other
        # sources
        if clue.clue_type in ['SingleWord', 'KindOf']:
            candidates = candidates.union(
                MerriamSearch.getCandidates(clue_text))

        # Get candidates from all sources for all other clue types
        else:
            candidates = candidates.union(EncyclopediaSearch.getCandidates(clue_text), WikiSearch.getCandidates(
                clue_text), WordnetSearch.getCandidates(clue_text, length), MerriamSearch.getCandidates(clue_text))
        candidates = self.cleanCandidates(clue_text, candidates, length)
        return candidates

    def determineClueType(self, clue):
        """
        
            Determines the clue types.
            
            Possible clue types:
            KindOf, SingleWord, QuotationMarks, FillInTheBlanks, CommaIn,
            QuestionMark, HumanSpeech, Abbreviation, SquareBrackets, ReferClue, Other
                
            Parameters
            ----------
            clue: Clue
                clue object to determine the type of
    
            ...
    
            Returns
            -------
            clue_type : str
                type of the clue
            clue : str
                edited version of the clue depending on the clue type

        """

        clue = clue.lower()
        clue_type = ''     

        # KindOf type clues
        # Looks for the phrases given in the phrase_list. If one of them exists in the clue
        # returns 'KindOf' as the clue type.

        phrase_list = ['kind of', 'starter for',
                       'type of', 'suffix with', 'partner of']

        for phrase in phrase_list:
            if phrase in clue.lower():
                clue_type = 'KindOf'
                return clue_type, clue

        # SingleWord type clues
        # Checks if the clue is a single word.

        if ' ' not in clue:
            clue_type = 'SingleWord'
            return clue_type, clue

        # QutotationMarks and HumanSpeech type clues
        # Checks if there are any quotation marks in the clue. Depending on the position of the quotation marks
        # clue type is determined.

        if '\"' in clue and '_' not in clue:
            if clue[0] == clue[-1] == '"':
                clue_type = 'HumanSpeech'
            else:
                clue_type = 'QuotationMarks'
            for char in clue:
                if char == '\"':
                    clue = clue.replace(char, '')
            return clue_type, clue

        # FillInTheBlanks type clues
        # Checks if the clue has a blank space to fill.

        if '_' in clue:
            clue_type = 'FillInTheBlanks'
            return clue_type, clue

        # CommaIn type clues
        # If the clue includes "in" after comma, it only returns the part of the clue
        # before the comma.

        if ", in" in clue:
            index_comma = clue.find(',')
            clue_type = 'CommaIn'
            clue = clue[0:index_comma]
            return clue_type, clue
        
        # QuestionMark type clues
        # Checks if there is a question mark in the clue.
        
        if '?' in clue:
            clue_type = 'QuestionMark'
            return clue_type, clue

        # SquareBrackets type clues
        # Checks if there are square brackets in the clue.

        if '[' in clue:
            clue_type = 'SquareBrackets'
            return clue_type, clue

        # ReferClue type clues
        # Checks if a clue is referenced in the clue.

        if '-across' in clue or '-down' in clue:
            clue_type = 'ReferClue'
            return clue_type, clue

        # Abbreviation type clues
        # Looks for the abbreviations given in the abbreviation_list. If one of them exists in the clue
        # returns 'Abbreviation' as the clue type.

        abbreviation_list = ['abbr.', 'for short',
                             'in brief', 'e.g.', 'etc.', 'i.e.', 'et', 'al.']

        for abbreviation in abbreviation_list:
            if abbreviation in clue.lower():
                clue_type = 'Abbreviation'
                return clue_type, clue

        # Definition type clues
        # If the clue satisfies non of the types above, it is categorized as Other type.

        else:
            clue_type = 'Other'
            clue = clue
            return clue_type, clue

    def initClues(self):
        """
            Initialize all variables we need to solve the puzzle by getting
            the relevant data from scraper.
        """

        print('Scraping crossword...')

        # Get scraped data
        self.cells, across_clues, down_clues = self.scraper.scrapecrossword()

        print('Scraping finished')

        cells = self.cells
        across_pos = []
        down_pos = []

        # Get across answer starting positions
        for i in range(len(cells)):
            for j in range(len(cells[0])):
                if not cells[i][j]:
                    across_pos.append((i, j))
                    break

        # Get down answer starting positions
        for i in range(len(cells)):
            for j in range(len(cells[0])):
                if not cells[i][j]:
                    if i == 0:
                        down_pos.append((i, j))
                    elif cells[i-1][j]:
                        down_pos.append((i, j))
                if len(down_pos) == len(down_clues):
                    break
            if len(down_pos) == len(down_clues):
                break

        # Create Clue objects and add them to a dictionary for easy access
        self.clues = dict()
        for i, clue in enumerate(across_clues):
            self.clues[f'A{i+1}'] = Clue(clue[0],
                                         across_pos.pop(0), (0, 1), clue[1], f'A{i+1}')

        for i, clue in enumerate(down_clues):
            self.clues[f'D{i+1}'] = Clue(clue[0],
                                         down_pos.pop(0), (1, 0), clue[1], f'D{i+1}')

        # Print out the clues
        for clue in self.clues.values():
            print(f'\tClue {clue.id} : {clue.clue} , {clue.length} letters')

        # Add constraints to each clue for every other clue (bruteforce is ok since we have a small number)
        for k1 in self.clues:
            for k2 in self.clues:
                if k1 != k2:
                    constraint = self.clues[k1].addConstraints(self.clues[k2])
                    if constraint:
                        self.constraints.append(constraint)

    def unplural(self, candidates):
        """
            Remove s from ends of candidates to get the 'unplural'ed version
            (singular is not as funny to say) of a word although rarely. This
            is a crude way but it works.

            ...

            Parameters
            ----------
            candidates: set
                candidates to iterate through

            ...

            Returns
            -------
            results: set
                candidates set with singular versions of words added
        """

        results = set()
        for candidate in candidates:
            results.add(candidate)
            if len(candidate) > 0:
                if candidate[-1] == 's':
                    results.add(candidate[:-1])
        return results

    def plural(self, candidates):
        """
            Add s to end of words to try to create plural versions

            ...

            Parameters
            ----------
            candidates: set
                candidates to iterate through

            ...

            Returns
            -------
            results: set
                candidates set with plural versions of words added
        """

        results = set()
        for candidate in candidates:
            results.add(candidate)
            results.add(candidate + 's')
        return results

    def formatAbbr(self, clue):
        """
            Format an abbreviation type clue to get better results when searching
            for candidates.

            ...

            Parameters
            ----------
            clue: str
                clue to format

            ...

            Returns
            -------
            formatted_clue: str
                formatted clue
        """

        words = clue.split(' ')
        formatted_words = []
        for word in words:
            if word not in ['Abbr.', 'e.g.', 'etc.', 'i.e.', 'et', 'al.']:
                formatted_words.append(word)
        return ' '.join(formatted_words)

    def removeClueWords(self, clue, candidates):
        """
            Since a word in the clue can't be in the answer, filter words in clue
            from candidates

            ...

            Parameters
            ----------
            clue: str
                clue string
            candidates: set
                candidates to filter

            ...

            Returns
            -------
            results: set
                filtered candidates
        """

        clue = clue.upper().split(' ')
        results = set()
        for candidate in candidates:
            if candidate in clue:
                continue
            results.add(candidate)
            for word in clue:
                results.add(candidate.replace(word, ''))
        return results

    def fitLength(self, candidates, length):
        """
            Filter out candidates of wrong length

            ...

            Parameters
            ----------
            candidates: set
                candidates to filter
            length: int
                length of the answer

            ...

            Returns
            -------
            results: set
                filtered candidates
        """

        candidates = {word for word in candidates if len(word) == length}
        return candidates

    def removeNonAlphabetic(self, candidates):
        """
            Filter non-alphabetic candidates

            ...

            Parameters
            ----------
            candidates: set
                candidates to filter

            ...

            Returns
            -------
            results: set
                filtered candidates
        """
        regex = re.compile('[^a-zA-Z]')
        candidates = {regex.sub('', word) for word in candidates}
        return candidates

    def removeStopwords(self, candidates):
        """
            Filter stopwords like the, a, or from candidates

            ...

            Parameters
            ----------
            candidates: set
                candidates to filter

            ...

            Returns
            -------
            results: set
                filtered candidates
        """
        return {word.upper() for word in candidates if word.lower() not in stopwords.words('english') + ['list', 'com', 'www']}

    def cleanCandidates(self, clue, candidates, length):
        """
            Apply all filters to candidates to get a clean set

            ...

            Parameters
            ----------
            clue: str
                clue string
            candidates: set
                candidates to filter
            length: int
                length of the answer

            ...

            Returns
            -------
            candidates: set
                filtered candidates
        """

        candidates = self.removeNonAlphabetic(candidates)
        candidates = self.unplural(candidates)
        candidates = self.removeStopwords(candidates)
        candidates = self.removeClueWords(clue, candidates)
        candidates = self.fitLength(candidates, length)
        candidates = self.removeMeaningless(candidates)
        return candidates

    def removeMeaningless(self, candidates):
        """
            Filter out meaningless - ie not in english - dictionary words from
            candidates

            ...

            Parameters
            ----------
            candidates: set
                candidates to filter

            ...

            Returns
            -------
            result: set
                filtered candidates
        """

        d = enchant.Dict('en_US')
        result = set()
        for word in candidates:
            if d.check(word):
                result.add(word)
        return result

    def AC3(self):
        """
            Apply the AC3 algorithm to candidate sets of clues to prune out
            words that do no satisfy constraints so that we can get a result
        """

        # Get all constraints ie arcs
        arcs = self.constraints[:]

        # Iterate while arcs is not empty
        while arcs:

            # Get constraint from arcs
            cur = arcs.pop(0)
            clue1, clue2 = cur[0][0], cur[0][1]
            ind1, ind2 = cur[1][0], cur[1][1]

            # If either of the sides' candidates list is empty, continue
            if self.clues[clue1].candidates == "" or self.clues[clue2].candidates == "":
                continue

            # Revise the left side rule's domain, check if any changes were made
            revised = self.revise(cur)

            # If any changes are made, add all arcs not in the arcs queue
            # where current left clue is on the right of arc
            if revised:
                for arc in self.constraints:
                    if arc[0][1] == clue1 and arc not in arcs:
                        arcs.append(arc)

    def revise(self, arc):
        """
            Revise the domain of the left side rule to leave out any words that do not
            satisfy a constraint for any other word in left side rule's domain

            ...

            Parameters
            ----------
            arc: list
                a constraint containing the relevant information
                ie which clues have the constraint and which indices
                of the answers should be equal

            ...

            Returns
            -------
            revised: set
                filtered domain
        """

        # Get relevant information for constraint
        x, y = self.clues[arc[0][0]], self.clues[arc[0][1]]
        x_domain, y_domain = x.candidates, y.candidates
        lind, rind = arc[1][0], arc[1][1]

        # If either of the domains is empty, no need to check further
        if not x_domain or not y_domain:
            return False

        revised = False
        x_domain_revised = set()

        # Check for every word in x's domain
        for lword in x_domain:
            added = False

            # Check constraint against every word in y's domain
            for rword in y_domain:
                if lword[lind] == rword[rind]:
                    x_domain_revised.add(lword)
                    added = True
            # If no word in y's domain was found st the word in x's domain
            # satisfied the constraint, we removed it from the domain therefore
            # the domain is revised
            if not added:
                revised = True

        # Update x's domain
        x.candidates = x_domain_revised
        return revised

    def solve(self):
        """
            Solve the constraint satisfaction problem by first applying the AC3
            algorithm to the domains of the clues and then applying backtracking.

        """

        # Back-up all candidates
        for clue in self.clues.values():
            clue.backup = clue.candidates

        # Leave one clue out from clues that have candidates
        leave_one = [None] + [self.clues[clue]
                              for clue in self.clues if self.clues[clue].candidates]

        print('Starting solving process...')
        for bye in leave_one:

            # Restore candidates from backups each time
            for clue in self.clues.values():
                clue.candidates = clue.backup

            # Leave out one clue's candidates
            if bye:
                print(f'Not including candidates for rule {bye.id}')
                bye.candidates = set()
            else:
                print('Including all candidates for all rules')

            assigned = set()
            assignment = dict()

            clues = sorted(
                [self.clues[clue] for clue in self.clues if self.clues[clue].candidates], key=lambda e: len(e.candidates))

            # Apply AC3 followed by backtracking
            self.AC3()
            self.backtrack(assigned, assignment, clues)
            print('\n')

        # Sort sols to get the solution where most answers were placed
        self.sols.sort(key=lambda sol: len(sol), reverse=True)

        # Put the solution into a grid that represent the crossword
        grid = self.putIntoGrid(self.sols[0])

        # Fill in the blanks, if any, in the grid
        grid = self.fillBlankSpaces(grid)

        # Create the image for presentation
        self.scraper.drawpredictiongrid(grid)
        self.scraper.saveimage()

    def putIntoGrid(self, sol):
        """
            Put a given solution into a grid that is representative of the
            crossword puzzle

            ...

            Parameters
            ----------
            sol: dict
                clues and corresponding answers

            ...

            Returns
            -------
            grid: list
                grid that is representative of the crossword puzzle solution
        """

        # Create empty grid
        grid = [["" for _ in range(5)] for __ in range(5)]

        for item in sol:
            clue, ans = item
            clue = self.clues[clue]
            x, y = clue.startPos
            h_x, h_y = clue.heading

            # Fill in the grid for the answer of the clue
            for i in range(clue.length):
                grid[x][y] = ans[i]
                x, y = x+h_x, y+h_y
        return grid

    def backtrack(self, assigned, assignment, clues):
        """
            Use backtracking to solve a CSP

            ...

            Parameters
            ----------
            assigned: set
                clues that have an answer assigned
            assignment: dict
                answers for corresponding clues
            clues: list
                clues to be used in the CSP
        """

        if len(assigned) == len(clues):
            # print('Assigned everything we can, adding possible solution')
            self.sols.append(list(assignment.items()))
            return

        cur = self.selectUnassigned(assigned, clues)

        if not cur:
            # print('Backtracking stuck, adding possible solution')
            self.sols.append(list(assignment.items()))
            return

        assigned.add(cur.id)

        for candidate in cur.candidates:

            tmp = ''
            if cur.id in assignment:
                tmp = assignment[cur.id]

            assignment[cur.id] = candidate

            # If consistent, continue with this answer
            if self.isConsistent(assigned, assignment):
                print(f'Assigning {cur.id} : {tmp} -> {candidate}')
                self.backtrack(assigned, assignment, clues)

        # Continue with blank answer for current clue
        self.backtrack(assigned, assignment, clues)

    def fillBlankSpaces(self, grid):
        """
            Try to fill the blank spaces in the grid. Currently only single blank spaces
            can be filled (not consecutive spaces)
            ...

            Parameters
            ----------
            grid: list
                grid that represent the crossword puzzle solution

            ...

            Returns
            -------
            grid: list
                grid with blank spaces filled or not filled

        """

        blanks = []
        d = enchant.Dict('en_US')

        # Create pairs of answers for blank spaces
        for r in range(5):
            for c in range(5):
                if grid[r][c] == "" and not self.cells[r][c]:
                    grid[r][c] = '*'
                    pair = []
                    tmp = ""
                    for y in range(0, 5):
                        if not self.cells[r][y]:
                            tmp += grid[r][y]
                    pair.append(tmp)
                    tmp = ""
                    for x in range(0, 5):
                        if not self.cells[x][c]:
                            tmp += grid[x][c]
                    pair.append(tmp)
                    pair.append((r, c))
                    blanks.append(pair)

        # For each pair try to find a letter to fill the blank that
        # makes both answers meaningful words
        for pair in blanks:
            word1, word2, pos = pair
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if d.check(word1.replace('*', letter)) and d.check(word2.replace('*', letter)):
                    print(f'Found letter for blank at {pos}')
                    grid[pos[0]][pos[1]] = letter
                    break

        # Remove any unfilled blanks that still have the * in them
        for r in range(5):
            for c in range(5):
                if grid[r][c] == '*':
                    grid[r][c] = ''
        return grid

    def selectUnassigned(self, assigned, clues):
        """
            Try to fill the blank spaces in the grid. Currently only single blank spaces
            can be filled (not consecutive spaces)
            ...

            Parameters
            ----------
            assigned: set
                clues that have already been assigned an answer

            clues: list
                clues that may or may not have been assigned an answer

            ...

            Returns
            -------
            clue: Clue
                clue that is to be assigned next

        """

        unassigned = sorted(list({clue.id for clue in clues}.difference(
            assigned)), key=lambda e: self.clues[e].length)
        for free in unassigned:
            if self.clues[free].candidates:
                return self.clues[free]
        return None

    def isConsistent(self, assigned, assignment):
        """
            Check if a given state is consistent ie it satisfies all
            relevant constraints
            ...

            Parameters
            ----------
            assigned: set
                clues that have already been assigned an answer

            assignment: dict
                answers for corresponding clues

            ...

            Returns
            -------
            isConsisten: bool
                whether the given state is consistent

        """

        for id, ans in assignment.items():
            clue = self.clues[id]
            for constraint in clue.constraints:
                rclue = constraint[0][1]
                lind, rind = constraint[1][0], constraint[1][1]
                if rclue in assignment.keys() and ans[lind] != assignment[rclue][rind]:
                    return False
        return True


def main():
    solver = CROSSWALKER()
    solver.initClues()
    solver.initCandidates()
    solver.solve()


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
