#! /opt/miniconda3/bin/python

"""Static site generator for a collection of articles with
a table of contents as the home page, and prev/TOC/next links
in the navigation header, and publication information in the
footer.

Inspired by Erik Johannes Husom's site, erikjohannes.no.
See https://codeberg.org/erikjohannes/erikjohannesno/buildsite.py

Author of this version:
    Grayson Bray Morris

Created:
    2025-09-26

"""

from datetime import date
import html
import os
import re
import markdown as md


class Website:

    # TO DO : update this to assume a flat structure (no nested files) and to write out in the folder + index.html setup.
    # this will work for stories.gbmj.net then, and for any blog I might set up (blog.gbmj.net) it will enforce flat
    # structure and provide folders that could hold the .md files, any images etc. See EJH's build_blog method.
    # ALSO, create a TOC generating method like EJH does in the build_blog method -- this can create the TOC for
    # stories.gbmj.net, and for any future blog (though the two may need custom tweaks for the different use cases,
    # ie, dated reverse chrono list vs static list).
    #
    # NOTE that EJH doesn't include prev / next links in his blog posts or pages. Think about this. I use them in
    # Grayson's Book of Stories but do I really need them? If so, figure out how to add them into the header nav
    # section. Mmm, it will require having the list of all pages at hand and walking through it. Not hard, but
    # it means setting that up before building the pages themselves.

    """Generate pages from common elements plus page-specific content,
    enabling single-point-of-change site-wide updates.

    Input:
        This script assumes all common page blocks (head, header, footer) are
        in one top-level folder together, and all hrefs in these blocks are
        designed for the home page in the root directory. Other site-wide assets
        (css, favicons, etc) are in a separate top-level folder together.
        Page-specific content is grouped in folders, one for each page, and this
        folder name represents the page title. There are two options:

            yyyy-mm-dd-title-of-this-page
            title-of-this-page

        All folders must use the same option; toggle it with self.posts_have_dates.

        The page content is in a file named index.md. There may be other resources
        in the folder, such as images shown on the page. Any on-page content that is
        not part of the site-wide common blocks (header, footer, etc) should be
        in this folder, or it will not be found.

    Output:
        This script generates one index.html file for each page: the home page in
        the root folder, plus each subfolder. The home page contains a list of all
        pages on the site (TOC); the nav header on each page, including the home page,
        provides links to prev, TOC, and next.
    """

    def __init__(self):

        # site-wide definitions
        self.baseurl = "https://gbmj.net/"
        self.site_title = "Grayson Bray Morris"

        # identify internal folder names, for easy renaming if the fancy strikes me
        self.common_blocks_folder = "cmn"
        self.common_blocks_filenames = ["head.html", "header.html", "footer.html"]
        self.common_assets_folder = "assets"
        self.css_filename = "style.css"  # this should import any other css files you're using; they won't be loaded separately
        self.favicon_filename = "favico.ico"

        # and some standard page names, for easy renaming
        self.license_pagename = "license"
        self.privacy_pagename = "privacy"

        # adapt these to meet the needs of your site
        self.markdown_extensions = []
        self.posts_have_dates = True
        self.TOC_sort_key = "dates"  # one of "dates", "titles"

        # load the site-wide page styling elements (head, header, footer)
        self.common_blocks = []
        for f in self.common_blocks_filenames:
            with open(self.common_blocks_folder + "/" + f, "r") as infile:
                self.common_blocks.append(infile.read())

        # now replace the site-wide placeholders in those common blocks
        # with the desired values set above
        updated_cblocks = []
        for b in self.common_blocks:
            updated_cblocks.append(
                b.replace("<!--LICENSE FILENAME-->", f"{self.license_pagename}")
                .replace("<!--PRIVACY FILENAME-->", f"{self.privacy_pagename}")
                .replace("<!--CSS FILENAME-->", f"{self.css_filename}")
                .replace("<!--ASSETS FOLDER NAME-->", f"{self.common_assets_folder}")
                .replace("<!--FAVICON FILENAME-->", f"{self.favicon_filename}")
            )
        self.common_blocks = updated_cblocks

    def build_page(self, cblocks, path):
        """Combine common & page-specific content and write out as HTML file.

        cblocks passes in a list with the head, header & footer code,
        while path passes in the local path to a markdown file with the page-
        specific content. The first six lines of the .md file are
        assumed to contain:
             ---
             title: "Title of Article Cased As Desired"
             date: YYYY-MM-DD
             publ: "Name of Magazine where article was first published"
             blurb: "Short description to use in table of contents."
             ---

        The HTML file will be written to the same folder (ie, the one in path).
        """
        # Read in the markdown file
        with open(path + "/index.md", "r") as infile:
            lines = infile.readlines()

        # get the properly capitalized title for the page, to use
        # as the window title
        title = lines[1].replace("title: ", "").replace('"', "")

        # get the date first published, as a date object
        # (for chrono sorting)
        date_str = lines[2].replace("date: ", "")
        date = date.fromisoformat(date_str)

        # get the name of the original publication, if any
        publ = lines[3].replace("publ: ", "").replace('"', "")

        # get the blurb, to use on the home page in the TOC
        blurb = lines[4].replace("blurb: ", "").replace('"', "")

        # everything from line 7 onward is the actual content of the page
        md_body = " ".join(lines[6:])

        # convert the markdown to HTML
        body = md.markdown(md_body, extensions=self.markdown_extensions)

        # Update window title and canonical ref in head.
        # Here we have to distinguish between the local path on the machine
        # we're building on, and the web URL we want to insert. That means we
        # only want the name of the present directory, not the entire local path.
        # Note that os.basename(path) only works here if the path string doesn't have a
        # trailing slash. So whatever creates the path variable -- in our case,
        # os.listdir() -- should make sure there isn't one.
        # Also note that your canonical URLs should be consistent
        # across your site regarding trailing slashes. I use Cloudflare which
        # always redirects to trailing-slash pages, so I'm using them in my
        # canonicals.
        head = (
            cblocks[0]
            .replace("<!--TITLE-->", title)
            .replace("<!--CANONICAL-->", self.baseurl + os.basename(path) + "/")
        )

        # TODO figure out where to put the "first published" venue and year info,
        # if not in the footer.

        # Now put it all together as an HTML page
        page = "<!DOCTYPE html>\n"
        page += '<html lang="en">\n'
        page += head  # head
        page += "\n\n<body>\n\n"
        page += cblocks[1]  # header
        page += "\n\n<article>\n\n"
        page += body
        page += "\n\n</article>\n\n"
        page += updated_cblocks[2]  # footer
        page += "\n\n</body>\n"
        page += "</html>"

        # And write it to disk
        with open(path + "/index.html", "w", encoding="utf-8") as outfile:
            outfile.write(page)

        print("Created index.html in ", path)

        # return the file path, title, date, and blurb
        # for use in constructing the TOC
        return (path, title, date, blurb)

    def build_pages(self):
        """Build the whole website."""

        # first, update the hrefs in common files to work
        # for pages that are one folder down from the root.
        updated_common_blocks = []
        for b in self.common_blocks:
            updated_common_blocks.append(b.replace('href="', 'href="../'))

        # initialize the TOC contents
        page_links = []
        page_titles = []
        page_dates = []
        page_blurbs = []

        # now build each non-home page, by visiting
        # every folder with an index.md page.
        for f in os.listdir():
            if os.path.isdir(f) and "index.md" in os.listdir(f):
                link, title, date, blurb = self.build_page(
                    updated_common_blocks, f"{f}/index.md"
                )
                # add page attributes to TOC
                page_links.append(link)
                page_titles.append(title)
                page_dates.append(date)
                page_blurbs.append(blurb)

        # now sort all these pages by the desired TOC_sort_key:
        if self.TOC_sort_key == "dates":
            page_dates, page_titles, page_links, page_blurbs = zip(
                *sorted(zip(page_dates, page_titles, page_links, page_blurbs))
            )
        else:
            page_titles, page_dates, page_links, page_blurbs = zip(
                *sorted(zip(page_titles, page_dates, page_links, page_blurbs))
            )

        # using this sorted order, revisit each page
        # to fill in its prev/next links:
        for idx, path in enumerate(page_links):
            with open(path + "index.html", "r") as infile:
                content = infile.read()
            prev = page_links[idx - 1]
            next = page_links[idx + 1]
            content = content.replace("<!--PREV-->", f"{prev}").replace(
                "<!--NEXT-->", f"{next}"
            )
            with open(path + "index.html", "w") as outfile:
                outfile.write(content)

        # now build the home page, which is the TOC
        # first, update the head, header, footer as needed
        head = (
            self.common_blocks[0]
            .replace("<!--TITLE-->", self.site_title)
            .replace("<!--CANONICAL-->", self.baseurl)
        )
        header = (
            self.common_blocks[1]
            .replace('<a href="index.html">TOC</a>', "TOC")
            .replace("<!--PREV-->", f"{page_links[-1]}")
            .replace("<!--NEXT-->", f"{page_links[0]}")
        )

        page = "<!DOCTYPE html>\n"
        page += '<html lang="en">\n'
        page += head  # head
        page += "\n\n<body>\n\n"
        page += header  # header
        page += "\n\n<article>\n\n"
        page += body
        page += "\n\n</article>\n\n"
        page += self.common_blocks[2]  # footer
        page += "\n\n</body>\n"
        page += "</html>"

        # And write it to disk
        with open(path + "/index.html", "w", encoding="utf-8") as outfile:
            outfile.write(page)

        print("Created index.html in ", path)


# Make sure you only build the site by directly running the script :)
if __name__ == "__main__":

    website = Website("gbmj.net", "Grayson Bray Morris")
    website.build_pages()
