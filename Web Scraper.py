import requests
from bs4 import BeautifulSoup, SoupStrainer
from collections import Counter
import re, string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

'''
    Python 3.8.6
        -Requests library
        -BeautifulSoup4 Library and SoupStrainer
        -Collections Library (Counter Data Type)
        -NLTK
        -re
        -string

'''

#Import stopwords list and punkt to tokenize words
#NOTE: the "download" functions are only required on first run and will throw warnings in all runs after
nltk.download('stopwords')
nltk.download('punkt')
stopWords = set(stopwords.words('english'))

while (True):
    '''

    Ask for correct link for program to scrape

    '''
    try:
        URL = input("Enter your Wikipedia link here: ").strip()
        page = requests.get(URL)
        break
    except:
        print("This is not a valid link! Try again.")
        continue

soup = BeautifulSoup(page.content, "html.parser")

#Extract and print title of article
title = soup.find(id="firstHeading")
print("\nArticle Title: " + title.string)

#Soup result objects used to parse html
content = soup.find("div", {"class":"mw-parser-output"})
links = content.find_all(['a','h1','h2','h3','h4','h5','h6'])
headers = content.find_all(f'h{i}' for i in range(1,7))
parserContent = content.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul'])


'''
#Checks for table of contents and collects data if it is present
#If it is not present, tocPresent will be marked False and no
#TOC related methods will be run
'''
tocPresent = True
try:
    tocContents = content.find("div", {"class":"toc"})
    toc = tocContents.find_all('a')
except:
    tocPresent = False
    
#Menu that will be displayed to user once program finishes executing
menuDisplay = []

def initHeaders():
    '''

    Returns list of header numbers in order of [firstDigit, secondDigit, thirdDigit]

    '''
    menuDisplay.insert(0, "\t0 Intro Section ")
    return [0, 1, 1, 2]

def getTrailingTag(headerLevel, contentCounter):
    '''

    Returns the "decimal" tag for each header label on the menu

    Ex: 1.x.x

    Function returns x.x
    
    '''
    
    if(headerLevel == 2):
        decimal = ""
        contentCounter[1] = 1
    elif(headerLevel == 3):
        decimal = "." + str(contentCounter[1])
        contentCounter[2] = 1
    else:
        decimal = "." + str(contentCounter[1]) + "." + str(contentCounter[2])
    return decimal

def incrementCounter(level, contentCounter):
    '''

    Function increments the contentCounter to accurately track which
    header/subheader the program is on
    
    '''
    
    if(contentCounter[3] >= level):
        contentCounter[level-2] += 1

def indentLevel(level):
    '''

    Function returns the indention level based on the header level

    Ex: one \t for header 2 (h2) and two \t\t for header 3 (h3)
    
    '''
    
    return "\t" * (level - 1)

def getLineFormat(tag, contentCounter):
    '''

    Function is used to simplify finding the header level and
    formats the numerical system for the menu display  

    '''
    
    level = int(tag[1])
    incrementCounter(level, contentCounter)
    indent = indentLevel(level)
    decimal = getTrailingTag(level, contentCounter)
    counter = str(contentCounter[0])
    contentCounter[3] = level
    return indent + str(counter) + decimal + " "

def getDisplayHeader(element, counter):
    '''

    Returns header level format + numerical system for labeling
    headers + header name

    '''
    
    lineFormat = getLineFormat(element.name, counter)
    elementFormat = element.text.strip().replace("[edit]", "")
    return lineFormat + elementFormat

def getHeaders(element, initContentCount):
    '''

    If the given element is a header, add that element to
    the header list in the menu display

    '''
    
    if (element.name in ['h2', 'h3', 'h4', 'h5', 'h6']):
        menuDisplay.append(getDisplayHeader(element, initContentCount))

def findKeywords(frequenciesList, element, excludeList):
    '''

    Given a section of the text, this function adds all
    words that are not considered "stop words" to a Counter
    that is later used to find the most frequent words

    '''
    
    try:
        alpha = list(element.get_text())
    except:
        alpha = list((" ".join(element)))
    alpha = ''.join(ch for ch in alpha if ch not in excludeList)
    alpha = alpha.lower()
    allWords = word_tokenize(alpha)
    keywords = [word.replace("edit", "") for word in allWords if not word.replace("edit", "") in stopWords]
    frequenciesList.append(Counter(keywords))
    
def findFrequent(frequenciesList):
    '''
    
    Find the top 5 most common words and returns text
    showing these common words and also how many times they occur
    in the given section of the text
    
    '''
    
    text = ""
    total = sum(frequenciesList, Counter())
    most = [x for x, _ in Counter(total).most_common(5)]
    for x in range(len(most)):
        occurences = total[most[x]]
        text = text + (", " if (x != 0) else "") + most[x] + " (" + str(occurences) + " times)"
    frequenciesList.clear()
    return text

def addMenuFrequencies(text, lineNumber, backTrack):
    '''

    This function adds the formatted text of frequent word
    descriptions to the menu, appended to the end of the given
    menu line

    Line number is the header line that is currently selected,
    backtrack is the number of subsections that need to be subtracted from
    the index to get the correct line

    '''
    
    menuDisplay[lineNumber-backTrack] = menuDisplay[lineNumber-backTrack] + " - 5 Most Frequent Words: " + text

def findAddHeaderFrequencies(frequenciesList, element, checked, excludeList):
    '''

    This function finds the correct header lines and calls
    addMenuFrequencies to add the given text to show the correct set of frequent words

    '''
    flag = True
    text = findFrequent(frequenciesList)
    for line in range(checked[0], len(menuDisplay)):
        if (element.get_text().strip().replace("[edit]", "") in menuDisplay[line]): 
            addMenuFrequencies(text, line, checked[1])
            checked[0] = line + 1
        elif ("." in menuDisplay[line]):
            checked[1] += 1
        if ("Contents" in menuDisplay[line] and tocPresent):
            tocFrequency(frequenciesList, excludeList, line)
            checked[0] = line + 2
    checked[1] = 1
    
def tocFrequency(frequenciesList, excludeList, line):
    '''

    Separate method to add frequent words from the Table of Contents
    due to the differing html style of the table

    '''
    
    tocWords = []
    for i in toc:
        tocWords.append(i['href'].replace("_", " ").replace("#", ""))
    findKeywords(frequenciesList, tocWords, excludeList)
    text = findFrequent(frequenciesList)
    addMenuFrequencies(text, line, 0)
    

def addSectionCommonWords(frequenciesList, element, checked, excludeList):
    '''

    This function takes in the given element from the website and
    checks whether or not it is a header. If it is, then it appends
    the correct text using findAddHeaderFrequencies. Next, it checks
    if the element is the last element that will be checked on the website.
    If it is, then the edge case (last header) will have the frequent word text
    added
    
    '''

    if (element.name == 'h2'):
        findAddHeaderFrequencies(frequenciesList, element, checked, excludeList)
    elif (element == parserContent[-1]):
        text = findFrequent(frequenciesList)
        addMenuFrequencies(text, -1, 0)

def initFrequencies():
    '''

    Defines initial parameters necessary for the frequency of words
    calculations.

    Returned in the form of [frequency Counters, previously checked header number, exclude (stop word) word list]

    '''
    
    frequencies = []
    checked = [0,1]
    exclude = set(string.punctuation)
    exclude |= set([str(i) for i in range(10)])
    return [frequencies, checked, exclude]

def getFrequentWords(settings, element):
    '''

    This function allows the previous functions that find
    frequent words to be used easily in parseAll. This saves O(n)
    time complexity by using the same for loop to add both header
    descriptions and frequent word descriptions at the same time.

    '''
    
    
    addSectionCommonWords(settings[0], element, settings[1], settings[2])
    findKeywords(settings[0], element, settings[2])

def findLinks():
    '''

    This function finds all links and appends them to the menu section
    of the correct header

    '''
    
    sectionNum = 1
    indent = "\t"
    for element in links:
        if (element.has_attr('href') and element.name == 'a'):
            menuDisplay.insert(sectionNum, indent + element.get('href'))
            sectionNum += 1
        elif (element in headers):
            menuDisplay.insert(sectionNum,"\n")
            for line in range(sectionNum, len(menuDisplay)):
                if (element.get_text().strip().replace("[edit]", "") in menuDisplay[line]):
                    sectionNum = line + 1
                    indent = indentLevel(int(element.name[1]))

def parseAll():
    '''

    Combines header and frequent word calculations to save
    O(n) time complexity. In this case, n = len(parserContent)

    '''
    
    headerList = initHeaders()
    frequencyList = initFrequencies()
    for element in parserContent:
        getHeaders(element, headerList)
        getFrequentWords(frequencyList, element)

#Running program to build menu interface and displaying to console
parseAll()
findLinks()
for line in menuDisplay:
    print(line)
