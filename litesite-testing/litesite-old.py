#! /opt/miniconda3/envs/litesite/bin/python

"""Mostly unopinionated static site generator
that stitches together common and page-specific
building blocks, making global changes reasonably
painless.

Author:
    Grayson Bray Morris
Created:
    2025-09-26

Usage:
    Edit the code in the bottom section of the file to use your
    specifics (base URL for your site, site name, sort order for
    navigation links, etc). Then run the script in the folder
    where your home page should live.

What this script expects:
    - a set of html blocks common to all pages on the site,
      stored as individual files (eg, header.html, footer.html). These
      blocks may contain placeholders for dynamic elements such as
      navigation links, a table of contents, etc. See below for
      how to format these placeholders.
    - a set of folders in any desired structure, each of which holds
      the unique content for one page on the site: specifically,
      a single markdown file plus any images or other content the file
      embeds (audio, images, video, gps data ...).

Output:
    - one html file for each markdown file, using the same name and
      stored in the same folder.
"""
# ----- UPDATE THESE CONSTANTS FOR YOUR SPECIFIC WEBSITE -----
# see the example files in /cmn for required and optional
# content for the head, header and footer files.
BASEURL = "https://example.com/"  #
SITENAME = "My Awesome Site"
LANGUAGE = "en" # use the two-letter iso code for your site's language
HEADFILE = "path/from/here/to/headfilename.ext"
HEADERFILE = "path/from/here/to/headerfile.ext"
FOOTERFILE = "./cmn/footer.html"
HASNAVLINKS = True  # one of : True, False
SORTKEY = "date"  # one of : "date", "title"
REVERSE = False  # one of : True, False
SORTDEPTH = "siblings"  # one of : "siblings", "children"

# how to format placeholders in head, header, footer files:
# ---------------------------------------------------------
# the script will look for the following strings and, if found,
# replace them with the appropriate values for each individual page:
#   <title></title>         (in your <head> file)
#   canonical href=""       (in your <head> file)
#   <!--PREVLINK-->         (in your <header> and <footer> files)
#   <!--NEXTLINK-->         (in your <header> and <footer> files)
#   <!--TOCLINK-->     (in your <header> and <footer> files)
#   
# see the files in the /cmn folder for sample use.

# how to format your head, header, footer files:
# ----------------------------------------------
# the script assumes the following:
#   HEADFILE begins with <head> and ends with </head>
#   HEADERFILE begins with <header> and ends with </header>
#   FOOTERFILE begins with <footer> and ends with </footer>
#
# the script inserts the necessary lines of html before HEADFILE
# and after FOOTERFILE.


# ----- END OF SPECIFIC WEBSITE UPDATES -----



import pypandoc as ppd  # markdown --> html conversion
from datetime import date  # to sort pages by date
import os  # to traverse local file structure
import re  # to find and replace nav placeholders
from operator import attrgetter  # to efficiently sort list of Page objects

# ----- CLASS DEFINITION -----
class Page(f, head, header, footer):
    """Build an html file from markdown file at f and
    html strings in head, header and footer.

    The path in f should be relative to the folder in which
    this script is running, not a full os path on the local system.
    f should end in *.md where * is any filename you like. The
    html page will be written to *.html in the same folder.

    The first six lines of the .md file are assumed to contain:
         ---
         title: "Title of Page Cased As Desired"
         date: YYYY-MM-DD
         navgroup: NAVKEY
         blurb: "Short description to use in table of contents."
         ---

    All four tags must appear in this order, with one space after
    the colon; THERE IS NO ERROR-CHECKING ON THIS. If the script
    borks on you, check your markdown file formatting.
    NAVKEY should be a one-word descriptor (no spaces) that is the
    same for all pages you would like to link to each other in prev-next
    fashion. If this page is not part of a prev-next collection, leave
    navgroup blank (ie, NAVKEY = "").
    Everything after the second --- will be included as is (after
    conversion to html).
    """

    def __init__(self):
        """After this, the object has five attributes, and
        an html file has been created on disk. The five attributes:
            self.title - to use in <head><title> element
            self.navgroup - to group pages that should link in a chain, like a blog
            self.date - for use in sorting all pages chronologically
            self.publ - the name of the original publication, if any
            self.blurb - to use in a table of contents
            self.link - to use in prev/next links
        """
        # Read in the markdown file
        with open(f, "r") as infile:
            lines = infile.readlines()

        # get the properly capitalized title for the page, to use
        # as the window title
        self.title = lines[1].replace("title: ", "").replace('"', "")

        # get the date first published, as a date object
        # (for chrono sorting)
        date_str = lines[2].replace("date: ", "")
        try:
            self.date = date.fromisoformat(date_str)
        except ValueError:
            self.date = date(1, 1, 1)  # Jan 1, 0001

        # get the name of the navigation group this page belongs to, if any
        self.navgroup = lines[3].replace("navgroup: ", "")

        # get the blurb, to use in TOC
        self.blurb = lines[4].replace("blurb: ", "").replace('"', "")

        # everything from line 7 onward is the actual content of the page;
        # convert it from markdown to html
        body = "\n<main>\n"
        body += ppd.convert_text(" ".join(lines[6:]), "html", format="md")
        body += "\n</main>\n"

        # TODO: safety checking on raw html from the markdown file?
        # TODO: make parsing the md tags more robust to extra whitespace,
        #       missing values, etc.

        # convert input .md filename to output .html filename;
        # and set the page link for use in canonical url
        # and, later, nav links
        f = f.replace(".md", ".html")
        # best practice is not to include index.html in canonical urls,
        # so check for that and set self.link accordingly
        if re.search("\/index.html", f):
            self.link = f.replace("index.html", "")
        else:
            self.link = f

        # stitch together an initial version of the page and write it to disk.
        # first, replace placeholders in head with specifics
        # for this page:
        head = (
            head
            .replace("<title>TITLE</title>", f"<title>{self.title}</title>")
            .replace('canonical href=""', f'canonical href="{BASEURL}{self.link}"')
        )

        # we can't replace navigation placeholders in the header and/or
        # footer until later, after we've created all pages in the site,
        # so for now this page is complete. Let's stitch it together:    
        html = "<!DOCTYPE html>\n"
        html += '<html lang="' + LANGUAGE + '">\n'
        html += head
        html += "\n\n<body>\n\n"
        html += body
        html += footer
        html += "\n\n</body>\n\n"
        html += "</html>"

        # and write out the html file (note we have to use f,
        # not self.link, in case the file is named index.html):
        with open(f, "w") as outfile:
            outfile.write(html)

        # and that's it, we've initialized this page!

# ----- END CLASS DEFINITION -----

# ----- DEFINE HELPER FUNCTIONS -----
def nextfile(path, pattern):
    """Generator to iterate recursively through path and subfolders.
    Yields the filename starting from path for files matching pattern.
    """
    pass
# ----- END HELPER FUNCTION DEFINITIONS -----


# ------ TEST CODE; COMMENT / UNCOMMENT AS DESIRED -----
page = Page()
print(page.date)
print(BASEURL[-1])


# ----- BUILD THE SITE -----

# the script makes multiple passes through each page,
# because it has to get the information for all pages
# before it can sort them to add eg. prev/next links.
# It also needs the page-specific details to fill
# in the right title and canonical link.

# to start, read in the common blocks and create the
# head, header, footer strings the script will use:
head = open(HEADFILE, "r").read()
header = open(HEADERFILE, "r").read()
footer = open(FOOTERFILE, "r").read()


# next, set up a container to access
# each page, which we can use later to sort pages based
# on dates, titles, etc.:
pages: list[Page] = []

# now walk through the site and create a first draft of
# each page, populating the pages list as we go:
# NOTE: nextfile should return a relative path from the input
# directory, not the whole local filepath
for f in nextfile("./", r".*\.md$"):
    pages.append(Page(f, head, header, footer))

# now that we have all the pages, we can loop through
# them to create a table of contents, prev/next links, etc.
# first, sort the pages based on your desired criterion
# (set it at the top of this file):
# TODO: maybe this could be an attribute of a Page? which
# would enable some pages to be linked like a blog, and others
# to not be part of that collection. Could also have a self.navlinkgroup
# attribute, so that all pages with the same nav link group would
# link to each other, create a single TOC, etc. 
if HASNAVLINKS:
    pages.sort(key=attrgetter(SORTKEY),reverse=REVERSE)

# now loop through all the pages on the site and replace
# any next/prev/toc placeholders with actual links:

# TODO: maybe the TOC could read in from the page what depth it should use?
# in which case a Page should also have self.has_toc & self.toc_depth attributes
# TODO: maybe the setting for nav link depth should be in the header/footer/section
# where the links will go? in which case the script should read it in from those
# files at the start and set a global variable to use (for header/footer nav).
# for section nav in a specific page, well, that's something else....but arguably
# there shouldn't be any of that, properly speaking that kind of linking would
# be more like a TOC.

