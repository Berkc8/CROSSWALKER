"""
Scrapes today's NYT mini-crossword from the website and creates an image file
that has the clues and the answers, prints a timestamp with the GROUP_NAME
in the bottom right corner of the grid. Can also write the clue || answer pairs
to a text file for future reference.
"""

import requests
import math
import textwrap
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import numpy as np
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

# Timestamp options
GROUP_NAME = 'CROSSWALKER'
TIME = datetime.datetime.now()
TIMESTAMP = TIME.strftime("%d %b %y, %H:%M")

# Change IMG_SAVE_PATH to where you want to save the crossword image
IMG_FILE_NAME = "{}-crossword.png".format(
    TIME.strftime("%d_%m_%Y"))
IMG_SAVE_PATH = f"E:\Bilkent\CS 461\Project\Demo 2 Last Last\\{IMG_FILE_NAME}"

# Change IMG_SAVE_PATH to where you want to save the crossword data
DATA_FILE_NAME = "crossword_data.txt"
DATA_SAVE_PATH = f"E:\Bilkent\CS 461\Project\Demo 2 Last Last\\{DATA_FILE_NAME}"

# This can be changed to wayback machine links to scrape older crosswords
URL = "https://www.nytimes.com/crosswords/game/mini"

X_OFF = 50      # Used for padding between edge of image and crossword grid
Y_OFF = 50      # Used for padding between edge of image and crossword grid
CELL_LEN = 50   # Side length of a single cell in the grid


class CrosswordDisplay():
    def drawgrid(self, cell_isfilled, cell_no, d, N) -> None:
        """
            Draws the crossword grid with the filled spaces and clue numbers.

            ...

            Parameters
            ----------
                cell_isfilled: list
                    2D array that shows whether a given cell [i][j] is filled
                cell_no: list
                    2D array that holds the clue_no for cell [i][j]
                    blank string if there is no clue no on that cell
                d: ImageDraw
                    used to draw to the image
                N: int
                    side length of the grid, in # of cells
        """

        # Draw a rectangle slightly larger than the grid
        # to look more like the NYT website grid
        d.rectangle([X_OFF - 2, Y_OFF - 2, X_OFF + 2 + N*CELL_LEN,
                     Y_OFF + 2 + N*CELL_LEN], fill='black')

        # Font used for the clue numbers
        fnt = ImageFont.truetype("arial.ttf", 15)

        # Iterate through every cell and draw, start from (X_OFF,Y_OFF)
        # so the grid is not directly on the side of the image
        xoff = X_OFF
        for c in range(N):
            yoff = Y_OFF
            for r in range(N):
                txt = cell_no[r][c]
                color = 'black' if cell_isfilled[r][c] else 'white'
                d.rectangle([xoff, yoff, xoff + CELL_LEN, yoff + CELL_LEN],
                            fill=color, outline='gray')
                d.text((xoff + 4, yoff + 2), text=txt, fill='black', font=fnt)
                yoff += CELL_LEN
            xoff += CELL_LEN

    def writeclues(self, across_clues, down_clues, d, N) -> None:
        """
            Draws the clues to the side of the grid.

            ...

            Parameters
            ----------
                across_clues: list
                    holds the across clues and their numbers
                cell_no: list
                    holds the down clues and their numbers
                d: ImageDraw
                    used to draw to the image
                N: int
                    side length of the grid, in # of cells
        """

        # Leave one cell length of whitespace between the grid
        # and the clues horizontally, but align vertically
        xoff = X_OFF + CELL_LEN * (N + 1)
        yoff = Y_OFF

        # Fonts for titles and clues, title font should preferrably
        # be the bold version of the clue text font
        title_font = ImageFont.truetype('arialbd.ttf', 15)
        clue_font = ImageFont.truetype('arial.ttf', 15)

        # Print across clues
        d.text((xoff, yoff), text='ACROSS', fill='black', font=title_font)

        for clue in across_clues:
            yoff += 25

            # Split the text into several lines if it is too long
            txt = textwrap.wrap(clue[1], 29)

            d.text((xoff + 15, yoff), text=clue[0],
                   fill=(158, 158, 158), font=title_font)

            d.text((xoff + 40, yoff), text=txt[0],
                   fill=(143, 143, 143), font=clue_font)

            for i in range(1, len(txt)):
                yoff += 20
                d.text((xoff + 40, yoff), text=txt[i],
                       fill=(143, 143, 143), font=clue_font)

        # Print down clues
        xoff += 300
        yoff = Y_OFF
        d.text((xoff, yoff), text='DOWN', fill='black', font=title_font)

        for clue in down_clues:
            yoff += 25

            # Split the text into several lines if it is too long
            txt = textwrap.wrap(clue[1], 29)

            d.text((xoff + 15, yoff), text=clue[0],
                   fill=(158, 158, 158), font=title_font)

            d.text((xoff + 40, yoff), text=txt[0],
                   fill=(143, 143, 143), font=clue_font)

            for i in range(1, len(txt)):
                yoff += 20
                d.text((xoff + 40, yoff), text=txt[i],
                       fill=(143, 143, 143), font=clue_font)

    def drawpredictiongrid(self, predictions) -> None:
        d = self.d
        img = self.img
        cell_isfilled = self.cells
        N = self.N
        cell_no = self.cell_no
        # Draw a rectangle slightly larger than the grid
        # to look more like the NYT website grid
        xoff = X_OFF + CELL_LEN * (N + 1) + 2 * X_OFF + 500
        d.rectangle([xoff - 2, Y_OFF - 2, xoff + 2 + N*CELL_LEN,
                     Y_OFF + 2 + N*CELL_LEN], fill='black')
        # Font used for the clue numbers
        fnt = ImageFont.truetype("arial.ttf", 15)
        letter_font = ImageFont.truetype('arialbd.ttf', 30)

        for c in range(N):
            yoff = Y_OFF
            for r in range(N):
                txt = cell_no[r][c]
                letter = predictions[r][c]
                color = 'black' if cell_isfilled[r][c] else 'white'
                d.rectangle([xoff, yoff, xoff + CELL_LEN, yoff + CELL_LEN],
                            fill=color, outline='gray')
                d.text((xoff + 4, yoff + 2), text=txt, fill='black', font=fnt)
                if letter != "":
                    xpos = xoff + \
                        ((CELL_LEN -
                          letter_font.getmask(letter).getbbox()[2]) // 2)
                    d.text((xpos, yoff + 15), text=letter,
                           fill=(41, 96, 216), font=letter_font)
                yoff += CELL_LEN
            xoff += CELL_LEN

    def timestamp(self, d, N):
        """
            Print the GROUP_NAME, date and time on the right bottom corner of
            the grid.

            ...

            Parameters
            ----------
                d: ImageDraw
                    used to draw to the image
                N: int
                    side length of the grid, in # of cells
        """
        # Fonts for the text, group name is bold
        name_font = ImageFont.truetype('arialbd.ttf', 15)
        time_font = ImageFont.truetype('arial.ttf', 15)

        # Some '''magic''' to align the group name with the right side of the grid.
        # getmask(GROUP_NAME).getbbox()[2] gets the width of the text so that a
        # group name of any length will be aligned properly, assuming the group name
        # text width is not larger than the grid's width.
        xoff = X_OFF + CELL_LEN * \
            (N) - name_font.getmask(GROUP_NAME).getbbox()[2]
        TIME = datetime.datetime.now()
        TIMESTAMP = TIME.strftime("%d %b %y, %H:%M")
        # Y position of the text is some pixels below the grid to look nicer
        yoff = Y_OFF + CELL_LEN * N + 9
        d.text((xoff, yoff), text=GROUP_NAME,
               fill=(150, 150, 159), font=name_font)
        d.text((xoff + 10, yoff + 15), text=TIMESTAMP,
               fill=(143, 143, 143), font=time_font)

    def getanswer_letters(self) -> None:
        """
            Use selenium to simulate button clicks and reveal the answer_letters of the
            puzzle, then use BeautifulSoup to get an array of letters corresponding
            to the answer_letters. The whole answer of the clues is not available in the HTML,
            only the letters that correspond to a cell in the grid are, so we will need
            some processing to turn them into answer strings.

            ...

            This function requires that chromedriver is installed on your system and
            is on the PATH. If you don't have chromedriver, you can download it from:
                https://chromedriver.chromium.org/downloads
        """

        # Create a headless chromedriver instance, so that we can scrape in the
        # background without an annoying browser popping up
        options = Options()
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options)
        #driver = webdriver.Chrome()
        driver.get(URL)

        # time.sleep(2) #Uncomment this line if selenium is giving problems like can't click.
        # This seems to be cause by ads loading maybe?

        # The answer_letters are not in the HTML of the website by default. However
        # once we choose to reveal the answer_letters they are added to the HTML.
        # To do this requires 4 button clicks. In order, we must click:
        #   1. The Play without an account button, identified
        #       by the class name StartModal-underlined--3IDBr
        #   2. The Reveal button which can be selected by its aria-label attribute
        #   3. The Puzzle button, which can be identified by its link text
        #   4. The Reveal button again, this time on the Are you sure? pop-up,
        #       which can be identified by its xpath
        driver.find_element_by_class_name(
            "StartModal-underlined--3IDBr").click()
        driver.find_element_by_css_selector(
            "button[aria-label='reveal']").click()
        driver.find_element_by_link_text("Puzzle").click()
        driver.find_element_by_xpath("//span[.='Reveal']").click()

        # Transfer the HTML data of the page over to BeautifulSoup
        # to get the answer letters and close the selenium webdriver
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        time.sleep(3)
        driver.close()

        # Choose all the answer letter objects from HTML, which are identified
        # by the class name Cell-hidden--3xQI1
        letters = soup.find_all('text', {'class': 'Cell-hidden--3xQI1'})
        return [let.text for let in letters if let.text != '']

    def drawanswer_letters(self, cell_isfilled, answer_letters, d, N) -> None:
        """
            Draw the answer letters on the grid.

            ...

            Parameters
            ----------
                cell_isfilled: list
                    2D array that shows whether a given cell [i][j] is filled
                answer_letters: list
                    array that holds the answer letters
                d: ImageDraw
                    used to draw to the image
                N: int
                    side length of the grid, in # of cells
        """

        # Using a bold font for readability
        txt_font = ImageFont.truetype('arialbd.ttf', 30)

        # Since answer_letters is a 1D array, and we do not hold any values
        # for the filled cells, we should keep a seperate index value
        # for it
        ind = 0

        yoff = Y_OFF
        for j in range(N):
            xoff = X_OFF
            for i in range(N):
                if not cell_isfilled[j][i]:
                    txt = answer_letters[ind]

                    # Again some '''magic''' to place a letter right in the middle
                    # of a cell
                    xpos = xoff + \
                        ((CELL_LEN - txt_font.getmask(txt).getbbox()[2]) // 2)
                    d.text((xpos, yoff + 15), text=txt,
                           fill=(41, 96, 216), font=txt_font)
                    ind += 1
                xoff += CELL_LEN
            yoff += CELL_LEN

    def saveimage(self) -> None:
        """
            Saves the image to path and name specified in FILE_PATH and IMG_FILE_NAME
            This function might seem redundant, but it allows for easier modification
            to save path without worrying about the main function.

            ...

            Parameters
            ----------
                img: Image
                    image to be saved
        """
        self.timestamp(self.d, self.N)
        if self.date:
            self.img.save(
                f"c:\\Users\\Personal\\Desktop\\Y3S2\\CS461\\Project\\Crosswords\\Examples\\{self.date}.png")
        else:
            self.img.save(IMG_SAVE_PATH)
        self.img.show()

    def scrapecrossword(self, data=True, solve=True) -> list:
        """
            Scrapes the website, gets answer_letters, saves image and saves data by default. Flags
            can be set to generate an unsolved image and/or not save data.

            ...

            Parameters
            ----------
                data=True: bool
                    optional parameter, True by default
                    if True the clues and answer_letters will be saved to DATA_SAVE_PATH
                    solve must be True as well for data to be saved
                solve=True: bool
                    optional parameter, True by default
                    if True the image will have the answer_letters on the grid.
                    Must be True for the data to be saved
        """
        self.date = None
        # Use BeautifulSoup to get the HTML data we need
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Get an array of cell objects that has an attribute that tells us whether a cell is painted black
        grid = soup.find_all('rect', {'role': 'cell'})

        # Get clue wrapper, [0] holds across clues [1] holds down clues
        clues = soup.find('section', {'class': 'Layout-clueLists--10_Xl'}
                          ).find_all('div', {'class': 'ClueList-wrapper--3m-kd'})

        # Extract across and down clue HTML objects from the clue wrapper
        across_clues_html, down_clues_html = clues[0].find_all(
            'li', {'class': 'Clue-li--1JoPu'}), clues[1].find_all('li', {'class': 'Clue-li--1JoPu'})

        # Extract the actual clues and numbers from the HTML objects
        across_clues = []
        down_clues = []
        for clue in across_clues_html:
            clue_no = clue.find('span', {'class': 'Clue-label--2IdMY'}).text
            clue_text = clue.find('span', {'class': 'Clue-text--3lZl7'}).text
            across_clues.append([clue_no, clue_text])

        for clue in down_clues_html:
            clue_no = clue.find('span', {'class': 'Clue-label--2IdMY'}).text
            clue_text = clue.find('span', {'class': 'Clue-text--3lZl7'}).text
            down_clues.append([clue_no, clue_text])

        # Create a 2D array that tells us whether a given cell is filled
        # class='Cell-block--1oNaD' is used to indicate a cell is filled
        list_ = [True if c['class'][0] ==
                 'Cell-block--1oNaD' else False for c in grid]
        # N is the length of one side of the crossword grid.
        # It could have just been hardcoded to be 5 but we chose
        # to make it more flexible and work with bigger grids
        N = int(math.sqrt(len(list_)))
        self.N = N
        # Using numpy to convert the 1D list_ into 2D cell_isfilled
        cell_isfilled = np.array(list_).reshape(N, N)
        self.cells = cell_isfilled
        # Create the image we are going to draw on, and the draw object
        self.img = Image.new('RGB', (N * CELL_LEN + 3 * X_OFF + 450 + 2 * X_OFF + N * CELL_LEN + X_OFF,
                                     N * CELL_LEN + 2 * Y_OFF), color='white')
        d = ImageDraw.Draw(self.img)
        self.d = d
        # Rather than scraping for it, we can create the little clue #s on the
        # cells by looking at certain conditions. The numbers always grow left to right, top to bottom.
        # A cell has a clue # if it is not filled AND any of the following are true:
        #   -Cell is on the first row
        #   -Cell is on the first column
        #   -Cell's left neighbor is filled
        #   -Cell's top neighbor is filled
        cell_no = [["" for _ in range(N)] for __ in range(N)]

        clue_no = 1
        for y in range(N):
            for x in range(N):
                isblack = cell_isfilled[y][x]
                if not isblack:
                    if y == 0:
                        cell_no[y][x] = str(clue_no)
                        clue_no += 1
                    elif x == 0:
                        cell_no[y][x] = str(clue_no)
                        clue_no += 1
                    else:
                        left_neighbor = cell_isfilled[y][x - 1]
                        top_neighbor = cell_isfilled[y - 1][x]
                        if left_neighbor or top_neighbor:
                            cell_no[y][x] = str(clue_no)
                            clue_no += 1
        self.cell_no = cell_no
        # Call everything in order to generate the image we want
        self.drawgrid(cell_isfilled, cell_no, d, N)
        if solve or data:
            answer_letters = self.getanswer_letters()
        if solve:
            self.drawanswer_letters(cell_isfilled, answer_letters, d, N)
        self.writeclues(across_clues, down_clues, d, N)
        if data:
            self.savedata([across_clues, down_clues],
                          answer_letters, cell_isfilled, cell_no, N)
        return self.cells, self.across, self.down

    def fromArchive(self, cells, across_clues, down_clues, answers, date):
        self.date = date
        answer_letters = list(''.join(answers))
        list_ = cells
        N = 5
        self.N = N
        # Using numpy to convert the 1D list_ into 2D cell_isfilled
        cell_isfilled = np.array(list_).reshape(N, N)
        self.cells = cell_isfilled
        # Create the image we are going to draw on, and the draw object
        self.img = Image.new('RGB', (N * CELL_LEN + 3 * X_OFF + 450 + 2 * X_OFF + N * CELL_LEN + X_OFF,
                                     N * CELL_LEN + 2 * Y_OFF), color='white')
        d = ImageDraw.Draw(self.img)
        self.d = d

        # Rather than scraping for it, we can create the little clue #s on the
        # cells by looking at certain conditions. The numbers always grow left to right, top to bottom.
        # A cell has a clue # if it is not filled AND any of the following are true:
        #   -Cell is on the first row
        #   -Cell is on the first column
        #   -Cell's left neighbor is filled
        #   -Cell's top neighbor is filled
        cell_no = [["" for _ in range(N)] for __ in range(N)]

        clue_no = 1
        for y in range(N):
            for x in range(N):
                isblack = cell_isfilled[y][x]
                if not isblack:
                    if y == 0:
                        cell_no[y][x] = str(clue_no)
                        clue_no += 1
                    elif x == 0:
                        cell_no[y][x] = str(clue_no)
                        clue_no += 1
                    else:
                        left_neighbor = cell_isfilled[y][x - 1]
                        top_neighbor = cell_isfilled[y - 1][x]
                        if left_neighbor or top_neighbor:
                            cell_no[y][x] = str(clue_no)
                            clue_no += 1
        self.cell_no = cell_no
        # Call everything in order to generate the image we want
        self.drawgrid(cell_isfilled, cell_no, d, N)
        self.drawanswer_letters(cell_isfilled, answer_letters, d, N)
        self.writeclues(across_clues, down_clues, d, N)

    def savedata(self, clues, answer_letters, cell_isfilled, cell_no, N):
        """
            Saves the clues and their corresponding answers to the text file at DATA_SAVE_PATH

            ...

            Parameters
            ----------
                clues: [across, down]
                    a list holding across and down clues, which are also lists
                answer_letters: list
                    letters of answers
                cell_isfilled: list
                    2D array that holds whether a given cell is filled
                cell_no: list
                    2D array holding the clue numbers for given cells, or ''
                N: int
                    side length of the crossword grid
        """

        # We need a numpy array for the operations we have to do next
        # 2D array to hold all letters in the grid, '' if filled black
        answers = np.array([["" for _ in range(N)] for __ in range(N)])

        # Extract across and down clues
        across_clues, down_clues = clues[0], clues[1]

        across_answers = []
        down_answers = []
        ind = 0

        # Create the 2D answers array
        for r in range(N):
            for c in range(N):
                if cell_isfilled[r][c]:
                    answers[r][c] = ""
                else:
                    answers[r][c] = answer_letters[ind]
                    ind += 1

        # Get across answers
        for ans in answers:
            across_answers.append(''.join(ans))

        # Getting the across answers is easy but the down answers are pretty hard because
        # they are not always in the order they appear. To match them with clues we have to
        # get clue no's in the order they appear from left to right first.
        down_answer_nos = [-1 for _ in range(N)]
        for r in range(N):
            for c in range(N):
                if not cell_isfilled[r][c]:
                    if r == 0:
                        down_answer_nos[c] = (int(cell_no[r][c]))
                    else:
                        top_neighbor = cell_isfilled[r - 1][c]
                        if top_neighbor:
                            down_answer_nos[c] = int(cell_no[r][c])

        # Rotate and flip the array so that down answers are the rows now.
        answers = np.rot90(answers)
        answers = np.flipud(answers)

        # Add down_answers in wrong order
        for ans in answers:
            down_answers.append(''.join(ans))

        # Sort the down_answers based on the down_answer_nos to match them correctly with
        # the down clues
        down_answers = [ans for ind, ans in sorted(
            zip(down_answer_nos, down_answers), key=lambda pair: pair[0])]

        # Get existing clue || answer pairs to not add duplicate pairs
        existing = set()
        f = open(DATA_SAVE_PATH, 'r')
        lines = f.readlines()
        for line in lines:
            existing.add(line.strip())
        f.close()

        self.across = [(across_clues[i][1], len(across_answers[i]))
                       for i in range(len(across_clues))]
        self.down = [(down_clues[i][1], len(down_answers[i]))
                     for i in range(len(down_clues))]
        f = open(DATA_SAVE_PATH, 'a')

        # Write all clue || answer pairs to file
        for clue, ans in zip(across_clues, across_answers):
            pair = f"{clue[1]} || {ans}"
            if pair not in existing:
                f.write(f"{clue[1]} || {ans}\n")
        for clue, ans in zip(down_clues, down_answers):
            pair = f"{clue[1]} || {ans}"
            if pair not in existing:
                f.write(f"{clue[1]} || {ans}\n")
        f.close()


def main():
    S = CrosswordDisplay()
    S.scrapecrossword(solve=True, data=True)


if __name__ == "__main__":
    main()
