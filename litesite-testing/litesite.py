#! /opt/miniconda3/envs/litesite/bin/python

"""Generates a static site for a shallow, blog-like collection of pages.

Assumed site structure:
    index.md            (required)
    *.md                (zero or more files such as privacy.md, license.md,...)
    *.*                 (zero or more files/folders with no .md file)
    cmn/                (required)
       |_ head.html     (required)
       |_ header.html   (required)
       |_ footer.html   (required)
    */                  (zero or more folders holding pages in the collection)   
        |_ index.md     (required)
        |_ *.*          (zero or more files/folders relevant only to index.md,
                        such as in-page images, audio, gps data, ...)

where:
    - the top-level index.md file generates the site home page. 
    - index.md files in a root-level subfolder generate pages in the Collection.
    - .md files with names other than 'index' will be created, but are not 
      part of the Collection.
    - the script will not traverse sub-subfolders; this means it
      will not generate pages for .md files more than one folder deep.
    - cmn/header.html and cmn/footer.html may contain placeholders for 
      prev/home/next style navigation links. The script will use these
      placeholders only in pages in the Collection. All other pages (eg, 
      privacy.md) will use only the home placeholder (if present).
    - the top-level index.md file may contain a TOC placeholder, in which case
      the script will insert a sorted list of all pages in the Collection.
    - the script is blind to all links outside the Collection; specify
      links to other files (eg, privacy.html, style.css) directly in the cmn/ 
      or .md files where you want them. Be sure to use absolute links from
      your root domain in the cmn/ files, such as href="/style.css" if you're
      running this script in the root, or href="/blog/style.css" if you're
      running this script in the blog/ folder of your root domain, etc.

Usage:
    The script starts from the directory you run it in and creates a
    self-contained blog-type site -- so you could run it in multiple
    different folders on your site, creating multiple self-contained
    collections with their own styling and navigation.
"""

import pypandoc as ppd  # markdown --> html conversion
from datetime import date  # to sort pages by date
import os  # to traverse local file structure
import re  # to find and replace nav placeholders
import frontmatter # to parse markdown files including YAML-style frontmatter
from operator import attrgetter  # to efficiently sort list of Page objects


# --- CONSTANTS ---
BASEURL = "https://gbmj.net/litesite-testing" # the URL to this folder
SITENAME = "My Awesome Site"
LANGUAGE = "en" # use the two-letter iso code for your site's language




OS_BASEDIR = os.path.dirname(__file__) # the local filesystem path to this folder
HEADFILE = os.path.join(OS_BASEDIR, 'cmn/head.html')
HEADERFILE = os.path.join(OS_BASEDIR, 'cmn/header.html')
FOOTERFILE = os.path.join(OS_BASEDIR, 'cmn/footer.html')
# to read files relative to current file, use os.path.join(OS_BASEDIR, filename)
# if filename includes relative path elements such as ../, run os.path.normpath afterward to remove unnecessary segments


# Input .md file assumptions:
# - if name is 'index' then window title is folder name with - replaced by space
# - if name is not 'index' then window title is filename with - replaced by space
# - the file contains the following three lines in its YAML-style frontmatter:
#     title: "Title to use as window title in html"
#     date: YYYY-MM-DD
#     blurb: "Short description to use in table of contents."
# - the file might contain other frontmatter, which the script will ignore.



HEAD = open(HEADFILE, "r").read()
HEADER = open(HEADERFILE, "r").read()
FOOTER = open(FOOTERFILE, "r").read()

# --- class definition ---
class Page():
    def __init__(self, title, date):
      self.title = title
      self.date = date

        
    
# --- end class definition ---

# --- define helper functions ---
def nextfile():
   pass
# --- end helper function definitions ---
"""
pages: list[Page()]= []

for f in nextfile():
    # create a new Page from the tags and content 
    pages.append(Page(metadata, content))

for page in pages:
"""   

# --- TESTING ---
titles = []
dates = []
blurbs = []
links = []
alien_quotient = []

# get the next file
fmd = os.path.join(OS_BASEDIR, 'index.md')
fhtml = fmd.replace(".md", ".html")

# create its URL relative to BASEURL
link = BASEURL + '/index.html'

# read in the contents of file f and split into tags and main content
tags, content = frontmatter.parse(open(fmd, "r").read())

# add the navigation and TOC relevant items to the growing lists, 
# for later sorting
titles.append(tags['title'])
dates.append(tags['date'])
blurbs.append(tags['blurb'])
links.append(link)
alien_quotient.append(tags['alien quotient'])
zipped = zip(titles, dates, blurbs, links, alien_quotient)
print(list(zipped))
print(dates[0])
print(alien_quotient[0])


head = (
            HEAD
            .replace("<title></title>", f"<title>{titles[0]}</title>")
            .replace('canonical" href=""', f'canonical" href="{links[0]}"')
        )

body = "\n<main>\n"
body += ppd.convert_text(content, "html", format="md")
body += "\n</main>\n"

html = "<!DOCTYPE html>\n"
html += '<html lang="' + LANGUAGE + '">\n'
html += head
html += "\n\n<body>\n\n"
html += HEADER
html += body
html += FOOTER
html += "\n\n</body>\n\n"
html += "</html>"

# and write out the html file (note we have to use f,
# not self.link, in case the file is named index.html):
with open(fhtml, "w") as outfile:
    outfile.write(html)


# --- end TESTING ---


