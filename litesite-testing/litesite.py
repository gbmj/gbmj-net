#! /opt/miniconda3/envs/litesite/bin/python

"""Generates a static site for a shallow, blog-like collection of pages.

Assumed site structure:
    index.md            (required; you can set filetype (eg .md) below)
    *.md                (zero or more files such as privacy.md, license.md,...)
    *.*                 (zero or more files/folders with no .md file)
    cmn/                (required; you can set this folder name below)
       |_ head.html     (required; you can set this name below)
       |_ cheader.html   (required; you can set this name below)
       |_ cfooter.html   (required; you can set this name below)
       |_ nheader.html   (required; you can set this name below)
       |_ nfooter.html   (required; you can set this name below)
    */                  (zero or more folders holding pages in the collection)   
        |_ index.md     (required; you can set filetype (eg .md) below)
        |_ *.md         (zero or more other md files)
        |_ *.*          (zero or more non-md files/folders)

where:
    - the top-level index.md file generates the site home page. 
    - index.md files in a root-level subfolder generate pages in the Collection.
    - .md files with names other than 'index' will be created, but are not 
      part of the Collection.
    - the script will traverse subfolders up to MAXDEPTH (set this below).
    - cmn/cheader.html and cmn/cfooter.html contain the header and footer
      blocks for pages in the Collection. They may contain placeholders for 
      prev/home/next style navigation links. 
    - cmn/nheader.html and cmn/nfooter.html contain the header and footer
      blocks for all pages NOT in the Collection. These should not contain
      prev/next style link placeholders; the script will not replace those.
    - the top-level index.md file may contain a TOC placeholder, in which case
      the script will insert a sorted list of all pages in the Collection.
    - the script is blind to all links outside the Collection; specify
      links to other files (eg, privacy.html, style.css) directly in the cmn/ 
      or .md files where you want them. Be sure to use absolute links from
      your root domain in the cmn/ files: links that begin either with 
      "https://myawesomesite.com/" or "/". Examples: href="/style.css" or 
      href="/css/style.css" if you're running this script in the root; 
      href="/blog/style.css" or "/blog/css/style.css" or if you're running 
      this script in the blog/ folder of your root domain, etc.

Usage:
    The script starts from the directory you run it in and creates a
    self-contained blog-type site -- so you could run it in multiple
    different folders on your site, creating multiple self-contained
    collections with their own styling and navigation. If you do that,
    be sure to set MAXDEPTH below so that you don't overwrite files in
    subfolders where you're running the script independently.
"""


from typing import Iterable  # for type hinting support
import datetime  # to sort pages by date
import os  # to traverse local file structure
from pathlib  import Path # system-independent filepath manipulation
import re  # to find and replace nav placeholders
import frontmatter # to parse markdown files including YAML-style frontmatter
import pypandoc as ppd  # markdown --> html conversion
from operator import itemgetter  # to efficiently sort list of Page objects


# --- MODULE CONSTANTS ---
# update these for your website and preferences:
BASEURL = "https://gbmj.net/litesite-testing/" # the URL to this folder on your site
SITENAME = "My Awesome Site"
SITE_LANGUAGE = "en" # use the two-letter iso code for your site's language
CMN_DIR = "cmn"  # name of directory where head, header, footer files are
HEAD_FILENAME =  'head.html'
HEADER_FILENAME_FOR_PAGES_IN_COLLECTION =  'cheader.html'
HEADER_FILENAME_FOR_OTHER_PAGES =  'nheader.html'
FOOTER_FILENAME_FOR_PAGES_IN_COLLECTION =  'cfooter.html'
FOOTER_FILENAME_FOR_OTHER_PAGES =  'nfooter.html'

MAXDEPTH = 3  # root folder only = 1, add 1 for every level of subfolder the script should crawl
FILEXT = "md"  # markdown files; can be any input format supported by pandoc (pandoc.org/MANUAL.html)
COLLECTION_SORTKEY = 0  # 0 (zero) to sort on title, 1 for date
SORT_REVERSED = True  # True for reverse chrono order, False otherwise
TOC_HAS_YEARS = True  # True to group articles by year, False otherwise


# these are calculated from the above; do not change
OS_BASEDIR = Path(__file__).parent  # the folder this script is running in
HEAD_PATH = Path.joinpath(OS_BASEDIR, CMN_DIR + '/' + HEAD_FILENAME)
HEADER_PATH_COLL = Path.joinpath(OS_BASEDIR, CMN_DIR + '/' + HEADER_FILENAME_FOR_PAGES_IN_COLLECTION)
FOOTER_PATH_COLL = Path.joinpath(OS_BASEDIR, CMN_DIR + '/' + FOOTER_FILENAME_FOR_PAGES_IN_COLLECTION)
HEADER_PATH_OTHER = Path.joinpath(OS_BASEDIR, CMN_DIR + '/' + HEADER_FILENAME_FOR_OTHER_PAGES)
FOOTER_PATH_OTHER = Path.joinpath(OS_BASEDIR, CMN_DIR + '/' + FOOTER_FILENAME_FOR_OTHER_PAGES)

DOT_FILEXT = "." + FILEXT
FILEXT_PATTERN = r'*.' + FILEXT



# This script lets you write your page-specific content in any file format
# you prefer (as long as pandoc supports it). The script does assume
# YAML-style frontmatter somewhere in the file, containing at least these
# three lines:
#     title: "Title to use as window title in html"
#     date: YYYY-MM-DD 
#     blurb: "Short description to use in table of contents."
# The date can be any valid ISO 8601 timestamp that has at least the
# fields shown above. Additional frontmatter is fine; the script 
# simply ignores it.


# --- define helper functions ---
def create_html_template(headfile: Path, headerfile: Path, footerfile: Path) -> str:
    """Return a complete html page with a placeholder for later
    per-page main content and possibly other placeholders from 
    the input files.
    """
    head = headfile.read_text()
    header = headerfile.read_text()
    footer = footerfile.read_text()

    html = "<!DOCTYPE html>\n"
    html += '<html lang="' + SITE_LANGUAGE + '">\n'
    html += head
    html += "\n\n<body>\n\n"
    html += header
    html += "\n<main>\n"
    html += "<!--PAGE BODY-->"
    html += "\n</main>\n"
    html += footer
    html += "\n\n</body>\n\n"
    html += "</html>"

    return html
   

def get_relevant_files(basedir: Path, pattern: str, maxdepth: int = 1000) -> Iterable[Path]:
        # TODO: could add a DIR_EXCLUSIONS constant above and r,d here and then
        # if r in DIR_EXCLUSIONS ( del d[:] break) (or whatever works correctly)
    files = basedir.glob(pattern)
    dirs = [c for c in basedir.iterdir() if c.is_dir()]
    yield files
    if maxdepth > 1:
        for path in dirs:
            for x in get_relevant_files(path, pattern, maxdepth-1):
                yield x



# --- end helper function definitions ---

# --- TESTING ---


# main script
if __name__ == "__main__":


    # initialize list where we'll store each page's
    # metadata: window title, date, blurb, url, filepath
    coll_meta: list[tuple[str,str,str,str,Path]] = []


    # create the html templates for the collection & pages not in the collection
    TEMPLATE_STR_COLL = create_html_template(HEAD_PATH, HEADER_PATH_COLL, FOOTER_PATH_COLL)
    TEMPLATE_STR_OTHER = create_html_template(HEAD_PATH, HEADER_PATH_OTHER, FOOTER_PATH_OTHER)

    # walk through OS_BASEDIR and its subfolders up to MAXDEPTH
    # to find all the webpage input files and create a first draft of
    # the corresponding html pages
    for files in get_relevant_files(OS_BASEDIR, FILEXT_PATTERN, MAXDEPTH):
        for filepath in files:
            # parse the file, build the initial draft of the web page, 
            # and write it to disk
            tags, content = frontmatter.parse(filepath.read_text())
            html_content = ppd.convert_text(content, "html", FILEXT)

            # html file lives in same folder as its input file
            html_path = filepath.with_suffix('.html')

            if html_path.name == "index.html" and not html_path.parent.samefile(OS_BASEDIR):
                # page is in the Collection
                url = BASEURL + str(html_path.parent.relative_to(OS_BASEDIR)) + "/"
                html_page =  TEMPLATE_STR_COLL.replace("<!--PAGE BODY-->", html_content)
                # save relevant metadata to use later in
                # sorting the Collection and adding
                # prev/next links in a second editing pass
                coll_meta.append((tags['title'], tags['date'], tags['blurb'],url,html_path))
            else:
                # page is not in the Collection
                url = BASEURL + str(html_path.relative_to(OS_BASEDIR))
                html_page =  TEMPLATE_STR_OTHER.replace("<!--PAGE BODY-->", html_content)

            # replace canonical and title placeholders in <head>
            # section for all pages, in and outside the Collection
            html_page = html_page.replace("<title></title>", f"<title>{tags['title']}</title>").replace('canonical" href=""', f'canonical" href="{url}"')

            # and write out this first draft of the page
            html_path.write_text(html_page)


    # now that we have all the files, we can replace the
    # <!--PREV--> and <!--NEXT--> placeholders in Collection
    # pages and create the TOC for the home page.

    sorted_meta = sorted(coll_meta,key=itemgetter(COLLECTION_SORTKEY),reverse=SORT_REVERSED)
    toc_md = "# Table of Contents\n"
    old_year, new_year = 1, 1

    for idx, (title, pdate, blurb, url, path) in enumerate(sorted_meta):

        # TODO: add TOC_CLASS constants above so the user
        # can style the TOC to be consistent with the rest of the site.
        # NOTE: this also means the other markdown input needs to
        # use these class identifiers, but that's up to the user to
        # enforce when they write those files.
        # HOWTO: use {#idtag .classtag key=value}
        # so, eg, ## [title](url) {.toctitle} for each title item,
        # or, eg, <section> {.toc} above the title line for the toc,
        # with </section> at the end, if user wants to style things
        # using .toc * to select anything that comes inside a toc block.

        # add entry to bottom of TOC, including
        # new year divider when relevant
        if TOC_HAS_YEARS and ((new_year := pdate.year) != old_year):
            toc_md += f"\n# {new_year}\n\n"
            old_year = new_year
        toc_md += f"## [{title}]({url})\n"
        toc_md += f"{blurb}\n\n"

        # read in page, replace prev/next placheolders,
        # and write back out
        html_page = path.read_text()

        i = (idx + 1) % len(sorted_meta)
        prev = sorted_meta[i - 2][3]
        next = sorted_meta[i][3]
        html_page = html_page.replace("<!--PREV-->", f"{prev}").replace(
            "<!--NEXT-->", f"{next}").replace("<!--HOME-->", BASEURL)

        path.write_text(html_page)


    # convert the TOC to html and insert into the home page
    toc = ppd.convert_text(toc_md, "html", "md")
    hpath = Path(OS_BASEDIR).joinpath("index.html")
    hpath.write_text(hpath.read_text().replace("<!--TOC-->", toc))

# --- end TESTING ---


