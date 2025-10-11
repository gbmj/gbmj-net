#! /usr/bin/env python

# Copyright (c) 2025 Grayson Bray Morris.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "python-frontmatter" = ">=1.1",
#     "pandoc" = ">=3.8",
#     "pypandoc" = ">=1.15",
# ]
# ///

"""Generate a static site for a shallow, blog-like collection of pages.

Assumed folder structure:
    litesite.py         (this file; required)
    *.foo               (0+ input files; ext customizable)
    *.*                 (0+ other files/folders)
    cmn/                (required; name customizable)
       |_ head.html     (required; name customizable)
       |_ cheader.html  (required; name customizable)
       |_ cfooter.html  (required; name customizable)
       |_ nheader.html  (optional; name customizable)
       |_ nfooter.html  (optional; name customizable)
    */                  (0+ other folders)
        |_ *.foo        (0+ input files)
        |_ *.*          (0+ other files)
        |_ */           (0+ subfolders with similar structure)

The script generates an html page for each input file in the root
folder plus subfolders up to MAXDEPTH (customizable). Each html
page uses the name of its input file. Example:
coolest-page-ever.foo will generate coolest-page-ever.html.

The script distinguishes between standalone pages and pages that
are part of a Collection. You tell the script which is which
using YAML frontmatter:
    - input files tagged `litesite: collection` generate Collection pages.
    - input files tagged `litesite:` with any other value (including
      an empty string) generate standalone pages.
    - input files with no `litesite:` tag do not generate html pages.
      This means you can also use the chosen extension for other things.

Collection pages use the cheader and cfooter files; standalone pages
use nheader and nfooter. This allows you to tailor the site navigation
to the page type. If you want all pages to have the same header and footer,
use cheader and cfooter for both.

The home page is a special case. If there is no top-level index.foo,
the script will create the page from scratch, using cheader and cfooter
and adding a table of contents (TOC) listing the Collection. If
index.foo does exist, the script will build a regular standalone page,
then scan the result for a TOC placeholder. If found, the script inserts
a TOC at this location.

How to Use:
    Copy litesite.py into the local folder of the site you want to build
    and edit the USER SETTINGS section. Use your preferred package manager
    (virtualenv, pipenv, conda, poetry, uv ...) to ensure access to the
    script's external dependencies, update the shebang line as needed,
    and run.

Advanced Use:
    In addition to supplying the required USER SETTINGS, you can
    optionally add custom logic to process your own tags and placeholders
    (more on those below). The script indicates where this logic is
    needed.

Requirements:
    - python 3.13 or later
    - pypandoc 1.15 or later (plus pandoc 3.8 or later),
      see pypi.org/project/pypandoc/
    - python-frontmatter 1.1 or later, see pypi.org/project/python-frontmatter/
    - the head, header, footer files must begin and end with their
      respective html tags: <head></head>, <header></header>,
      <foot></footer>.
    - you can use any file extension you like for your input files,
      including one you made up, but the actual content must be in
      a pandoc-supported input format. See pandoc.org/MANUAL.html#options.
    - all input files you want the script to process must include a
      YAML frontmatter block containing `litesite:`. Files without this
      tag will be ignored.

Optional frontmatter:
    In addition to the required `litesite:` tag, the script recognizes
    three optional tags:
        title: Title of Page
        date: YYYY-MM-DD
        blurb: A short summary to use in the table of contents.

    The date can be any valid ISO 8601 timestamp with at least the
    fields shown above. You don't need to wrap the title or blurb in
    quote marks, but you may. The tags can be in any order and additional
    frontmatter is fine; the script will ignore it (unless you add logic
    to handle them, see below.)

    For missing tags, the script defaults to:
        title: Titlecased Name Of File With Dashes Converted To Spaces
        date: 0001-01-01
        blurb: ''

    For files named `index`, the script uses the name of the enclosing
    folder for the title.

Optional placeholders:
    The script offers several placeholders you can use in your head,
    header, footer and .foo files. You can also create your own. The
    script's naming convention is meant to help you produce valid
    html:
        *_TEXT_PH - ordinary text
        *_URL_PH - a full web address including protocol (https://)
        *_LINK_PH - a full anchor element (<a href="...">...</a>)

List of standard placeholders:
    In the list below, (scope) indicates the pages on which the
    script will process the given placeholder. If you use a
    placeholder outside its scope, it will still be there in the
    final page (unless you modify the script to handle it).

(any)   DOMAIN_URL_PH, HOME_URL_PH - a convenience for converting
            relative links to absolute. Use these when you link to
            other pages on your domain, and you will only
            have to update two constants in this script if you change
            domain names or move the site folder. Note, these URLs
            contain a trailing slash, so proper use will look funny:
            For example, write <img href="DOMAIN_URL_PHimages/me.png">
            and not <img href="DOMAIN_URL_PH/images/me.png">.
(any)   SELF_URL_PH - insert the absolute URL to the current page. For
            use in a rel="canonical" link in your head file (and
            elsewhere as you desire).
(any)   YEAR_TEXT_PH, DATE_TEXT_PH - insert the year resp. full date
            specified in the page's frontmatter (else the default value).
            Note, the date will be in ISO 8601 format. Modify this
            script if you want something prettier :).
(any)   TITLE_TEXT_PH - insert the title specified in the page's
            frontmatter (else the default value). Use in the head file's
            <title></title> element (and elsewhere as you desire).
(coll)  PREV_URL_PH, NEXT_URL_PH - insert URLs to the page's TOC
            neighbors. Note, for nav links in page header or footer
            you might prefer the _LINK_ versions below.
(coll,  PREV_LINK_PH, HOME_LINK_PH, NEXT_LINK_PH - insert the entire
home        anchor element for the page's TOC neighbors resp. the home
w/no        page. Use these instead of the _URL_ placeholders to 'gray
.foo        out' nav links that shouldn't be active: the TOC link on the
file)       home page itself, and the previous resp. next links on
            the first resp. last pages in the Collection.
(home   TOC_BLOCK_PH - insert a table of contents listing the Collection,
with        with links to each page. Only active on the site's home
.foo        page, and only if there's a corresponding index.foo file.
file)

Custom tags and placeholders:
    You can process custom frontmatter tags and/or placeholders by
    adding the required logic where indicated in the script comments.

Tips:
    The script starts from the directory you run it in and creates a
    self-contained site -- so you could run it separately in several
    folders on your domain, creating multiple self-contained collections
    with their own styling and navigation. If you do that, be sure to
    set MAXDEPTH so you don't overwrite files in subfolders where you're
    running the script independently.

    You can create a non-blog-like site simply by omitting
    blog-like navigation placeholders (those with PREV, NEXT, TOC) and
    using the same header and footer files for all pages, or by having
    no input files with `collection: yes` in the frontmatter.

    I've mostly kept this script from enforcing particular
    choices, except for one: the URL it generates for pages named
    `index` goes to the enclosing folder and contains a trailing
    slash. Modify the script if you prefer different behavior.

Limitations:
    This script is only 'aware' of page-level headers and footers:
    their contents are inserted between the <body> and <main> (
    resp. </main> and </body>) tags. If you need section-level headers,
    footers, nav blocks or other in-page content that repeats on all pages,
    check out a more full-featured site generator like Jekyll or
    Hugo.
"""

import datetime as dt  # enable sorting on date
from operator import itemgetter  # to create key fn for sorted
from pathlib import Path  # system-independent filepath manipulation
import re  # regular expression substition
import typing as typ  # import Generator, Iterator, Any  # type hinting support
import frontmatter  # parse input files containing YAML frontmatter
import pypandoc as ppd  # convert input files to html

#   -- USER SETTINGS ---
SITE_NAME = 'The Cancer Blog'
LANGUAGE = 'en'  # two-letter iso code
DOMAIN_SITENAME = 'Grayson Bray Morris'  # for root, if this is a subsite
DOMAIN = 'https://gbmj.net/'  # include protocol and end in /
PATH_FROM_DOMAIN_TO_HERE = 'cancer-blog/'  # end in / if not ''
HHF_SUBDIR = 'cmn/'  # where head, header, footer files are; end in /
HDFN = 'head.html'
HDRFN_C = 'cheader.html'
HDRFN_NC = 'nheader.html'
FTRFN_C = 'cfooter.html'
FTRFN_NC = 'nfooter.html'
INFILE_EXT = 'md'  # can be anything; no leading dot
CONVERT_FROM = 'markdown+smart'  # pandoc input type, with optional extensions
OPTS: list[str] = []  # pandoc options to pass in to conversion
MAXDEPTH = 2  # 1 = root only
SORTKEY = 1  # 0 = title, 1 = date, anything else = don't sort
SORT_REVERSED = False
TOC_TITLE = 'The Cancer Blog'
TOC_PRINT_YEAR_HEADINGS = True
TOC_PRINT_BLURBS = False
TOC_CLASS_NAME = 'toc'  # for css styling
TOC_NOBLURB_CLASS = 'noblurb'  # css class added on if PRINT_BLURBS = False
TOC_ID = ''  # '' = top of home page; '#foo' for any foo, jump to TOC title
PREV_ANCHOR_TXT = 'prev'
HOME_ANCHOR_TXT = 'TOC'
NEXT_ANCHOR_TXT = 'next'
# ---- END USER SETTTINGS ----
BASEURL = DOMAIN + PATH_FROM_DOMAIN_TO_HERE  # url to folder
BASEDIR = Path(__file__).parent  # filepath to folder
HEAD_PATH = Path.joinpath(BASEDIR, HHF_SUBDIR + '/' + HDFN)
HDR_PATH_C = Path.joinpath(BASEDIR, HHF_SUBDIR + '/' + HDRFN_C)
FTR_PATH_C = Path.joinpath(BASEDIR, HHF_SUBDIR + '/' + FTRFN_C)
HDR_PATH_NC = Path.joinpath(BASEDIR, HHF_SUBDIR + '/' + HDRFN_NC)
FTR_PATH_NC = Path.joinpath(BASEDIR, HHF_SUBDIR + '/' + FTRFN_NC)
PPD_HTML_TYPES = ['html', 'html4', 'html5']


def _create_html_template(headfile: Path, hdrfile: Path, ftrfile: Path) -> str:
    """Return a valid html page with a placeholder for later content."""
    head = headfile.read_text()
    header = hdrfile.read_text()
    footer = ftrfile.read_text()

    html = '<!DOCTYPE html>\n'
    html += '<html lang="' + LANGUAGE + '">\n'
    html += head
    html += '\n\n<body>\n\n'
    html += header
    html += '\n<main>\n'
    html += '<!--BODY-->'
    html += '</main>\n\n'
    html += footer
    html += '\n\n</body>\n\n'
    html += '</html>'

    return html


def _get_infiles(
    dir: Path, pattern: str, maxdepth: int = 10
) -> typ.Generator[typ.Iterator[Path]]:
    """Return a list of paths to files that contain `pattern`."""
    files = dir.glob(pattern)
    dirs = [c for c in dir.iterdir() if c.is_dir()]
    yield files
    if maxdepth > 1:
        for path in dirs:
            for x in _get_infiles(path, pattern, maxdepth - 1):
                yield x


def _create_meta_defaults(path: Path) -> dict[str, typ.Any]:
    """Set up fallback values for page metadata."""
    m: dict[str, typ.Any] = {}

    p = path.parent if path.stem == 'index' else path

    m['title'] = p.stem.replace('-', ' ').title()
    m['date'] = dt.date(1, 1, 1)  # January 1, 0001
    m['blurb'] = ''
    u = f'{BASEURL}{str(p.relative_to(BASEDIR))}'
    u = u + '/' if path.stem == 'index' else u.replace(f'{INFILE_EXT}', 'html')
    # pathlib relative_to returns . if paths are the same;
    # strip off the trailing ./ in that case
    m['url'] = u if not p.samefile(BASEDIR) else u[:-2]
    m['path'] = path.with_suffix('.html')

    # add your custom defaults here
    # end custom defaults

    return m


def _process_incoming_meta(
    current: dict[str, typ.Any], new: dict[str, typ.Any]
) -> None:
    """Replace current values with new ones if present, ignoring keys not
    already in current."""
    # don't assume the values in `new` are of the type you expect --
    # for example, frontmatter.parse returns a boolean, not the
    # actual value, for strings/ints like `yes`, `no`, `0`, ``, ...
    for key, val in new.items():
        if val and (key in current):
            current.update({key: val})


def _process_complex_meta(meta: dict[str, typ.Any]) -> None:
    """Do any further processing on page metadata."""
    # baked-in metadata doesn't need further processing,
    # unless you change that

    # process custom metadata here
    pass
    # end custom processing


# --- testing ---
_testing = False

if _testing:
    # test something here
    print('testing...')
# --- end testing ---

if __name__ == '__main__' and not _testing:
    coll: list[tuple[str, dt.date, str, str, Path]] = []
    idx_title, idx_date, idx_blurb, idx_url, idx_path = 0, 1, 2, 3, 4

    TEMPLATE_C = _create_html_template(HEAD_PATH, HDR_PATH_C, FTR_PATH_C)
    TEMPLATE_NC = _create_html_template(HEAD_PATH, HDR_PATH_NC, FTR_PATH_NC)

    for files in _get_infiles(BASEDIR, rf'*.{INFILE_EXT}', MAXDEPTH):
        for filepath in files:
            tags, body = frontmatter.parse(filepath.read_text())
            if 'litesite' in tags:
                html_body = (
                    ppd.convert_text(
                        body, 'html', CONVERT_FROM, extra_args=OPTS
                    )
                    if CONVERT_FROM not in PPD_HTML_TYPES
                    else body
                )
                m = _create_meta_defaults(filepath)
                _process_incoming_meta(m, tags)
                _process_complex_meta(m)
                if tags['litesite'] == 'collection':
                    coll.append(
                        (
                            m['title'],
                            m['date'],
                            m['blurb'],
                            m['url'],
                            m['path'],
                        )
                    )
                    html_page = TEMPLATE_C.replace('<!--BODY-->', html_body)
                else:
                    html_page = TEMPLATE_NC.replace('<!--BODY-->', html_body)

                # replace most placeholders now -- only SELF_URL_PH has to wait
                html_page = (
                    html_page.replace('SITENAME_TEXT_PH', SITE_NAME)
                    .replace('TITLE_TEXT_PH', m['title'])
                    .replace('HOME_URL_PH', BASEURL)
                    .replace('DOMAIN_URL_PH', DOMAIN)
                    .replace('DOMAIN_SITENAME_TXT_PH', DOMAIN_SITENAME)
                    .replace('YEAR_TEXT_PH', str(m['date'].year))
                    .replace('DATE_TEXT_PH', str(m['date']))
                )

                # a page shouldn't have a link to itself, other than
                # the canonical in the head section, which we haven't yet
                # filled in. That means we can search and replace
                # any self-links we do find with just the link text
                if m['url'] in html_page:
                    html_page = re.sub(
                        rf'<a href="{m["url"]}">(.*?)</a>', r'\1', html_page
                    )

                # and now at last we can replace SELF_URL_PH
                html_page = html_page.replace('SELF_URL_PH', m['url'])

                # --- CUSTOM ---
                # process any custom placeholders here
                # --- END CUSTOM ---
                m['path'].write_text(html_page)

    # all infiles have been processed; now sort the Collection and
    # create the TOC (if the collection isn't empty)

    if SORTKEY in [0, 1] and coll:
        key = itemgetter(SORTKEY)
        rev = SORT_REVERSED
        sorted_meta = sorted(coll, key=key, reverse=rev)
    else:
        sorted_meta = coll

    toc_md = f'# {TOC_TITLE}\n'
    year = 2  # the year 0002 -- must not equal date default

    for idx, (title, date, blurb, url, path) in enumerate(sorted_meta):
        # add page listing to TOC
        if TOC_PRINT_YEAR_HEADINGS and (date.year != year):
            toc_md += f'\n{date.year}\n\n'
            year = date.year
        toc_md += f'- [{title}]({url})'
        toc_md += f' &mdash; {blurb}\n' if TOC_PRINT_BLURBS else ''
        toc_md += '\n'

        # update nav links in page itself
        prev = PREV_ANCHOR_TXT
        if idx != 0:
            prev = f'<a href="{sorted_meta[idx - 1][idx_url]}">{prev}</a>'
        home = f'<a href="{BASEURL}{TOC_ID}">{HOME_ANCHOR_TXT}</a>'
        next = NEXT_ANCHOR_TXT
        if idx != len(sorted_meta) - 1:
            next = f'<a href="{sorted_meta[idx + 1][idx_url]}">{next}</a>'
        html_page = path.read_text()
        html_page = (
            html_page.replace('PREV_LINK_PH', f'{prev}')
            .replace('HOME_LINK_PH', f'{home}')
            .replace('NEXT_LINK_PH', f'{next}')
        )
        path.write_text(html_page)

    # complete the TOC
    toc_classes = TOC_CLASS_NAME
    toc_classes += f' {TOC_NOBLURB_CLASS}' if not TOC_PRINT_BLURBS else ''
    toc = f'<section class="{toc_classes}" id="{TOC_ID}">\n'
    toc += ppd.convert_text(toc_md, 'html', 'markdown+smart')
    toc += '</section>'

    # update / create the home page
    outfile = Path(BASEDIR).joinpath('index.html')
    infile = Path(BASEDIR).joinpath(f'index.{INFILE_EXT}')
    if infile.exists():
        html_page = outfile.read_text().replace('<p>TOC_BLOCK_PH</p>', toc)
    else:
        prev = PREV_ANCHOR_TXT
        next = NEXT_ANCHOR_TXT
        if sorted_meta:
            prev = f'<a href="{sorted_meta[-1][idx_url]}">{prev}</a>'
            next = f'<a href="{sorted_meta[0][idx_url]}">{next}</a>'
        html_page = (
            TEMPLATE_C.replace('SITENAME_TEXT_PH', SITE_NAME)
            .replace('TITLE_TEXT_PH', TOC_TITLE)
            .replace('SELF_URL_PH', BASEURL)
            .replace('HOME_URL_PH', BASEURL)
            .replace('DOMAIN_URL_PH', DOMAIN)
            .replace('DOMAIN_SITENAME_TXT_PH', DOMAIN_SITENAME)
            .replace('PREV_LINK_PH', prev)
            .replace('HOME_LINK_PH', HOME_ANCHOR_TXT)
            .replace('NEXT_LINK_PH', next)
            .replace('YEAR_TEXT_PH', '')
            .replace('DATE_TEXT_PH', '')
        )
        # --- CUSTOM ---
        # if you added custom placeholders that appear
        # in the header and/or footer for Collection pages,
        # set them appropriately for the home page
        # --- END CUSTOM ---
        html_page = html_page.replace('<!--BODY-->', toc)

    outfile.write_text(html_page)

# --- end if __main__ ---
