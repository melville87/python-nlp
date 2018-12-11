import sys
import requests
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from time import sleep

# ==== check if link's parents include
# ==== only elements in main text of article
def has_bad_parents(alink):
    allowed_parents = ["[document]", "div", "p", "b", "ul", "ol", "li"]
    for parent in alink.parents:
        if parent.name not in allowed_parents:
            return True
    return False

# ==== check if link contains words in italic ====
def is_italic(alink):
    not_allowed_children = ["i"]
    for child in alink.children:
        if child.name in not_allowed_children:
            return True
    return False

# ==== check if link points to missing article ====
def is_missing_link(alink):
    if alink.get("class")=="new":
        return True
    else:
        return False

# ==== check if link points to Wikipedia article ====
def is_internal(alink):
    if (alink.get("href") is not None
        and alink.get("href").startswith("/wiki/")):
        return True
    else:
        return False

# ==== check if link is parenthesized ====
def is_in_pars(atag):
    in_pars = False

    # loop over all siblings that
    # precede the selected tag
    for sib in atag.previous_siblings:
        # exit if there's nothing
        # that precedes the link
        # at the same level of the tree
        # (no text, no other tags)
        if sib is None: break

        # skip siblings that are not text
        if sib.name is not None: continue

        # if there is some text,
        # get first parenthesis (if any)
        # beware: string must be reversed
        for char in sib.string[::-1]:
            if char == ")":
                # if first parenthesis is closed,
                # link is not parenthesized
                return in_pars
            elif char == "(":
                in_pars = True
                return in_pars

    # returns False if link not parenthesized
    return in_pars


def get_wikilinks(page_url):
    # ==== get html ====
    html_page = requests.get(page_url)

    # ==== parse page and build tree ====
    # parse main text only
    only_main_text = SoupStrainer("div", class_ = "mw-parser-output")
    parsed_html = BeautifulSoup(html_page.text,
                                "html.parser",
                                parse_only=only_main_text)

    # ==== find wikilinks ====
    # get all paragraphs + lists
    parlist = parsed_html.select("p, ul, ol")

    # initialize empty list
    # will store all normal wikilinks
    wikilinks = list()

    # get all links
    links = list()
    for p in parlist:
        all_links_in_p = p.find_all("a")
        if all_links_in_p is not None:
            links += all_links_in_p
    # if no links, return here
    if not links: return wikilinks

    # remove links in italic (but not in bold)
    # remove links to IPA pronunciation, Wiktionary (non-latin words), etc.
    # remove links to missing articles
    pruned_links = [l for l in links
                    if has_bad_parents(l) is False
                    and is_italic(l) is False
                    and is_missing_link(l) is False
                    and is_internal(l) is True]
    # if no normal links, return here
    if not pruned_links: return wikilinks

    # remove parenthesized links
    for l in pruned_links:
        # link may be child
        # of bold tag, if so
        # go up one node and search from there
        if l.parent.name == "b":
            l = l.parent
            if is_in_pars(l) is False:
                # go down and return to link tag
                l = l.find_next()
                wikilinks.append(l)
        else:
            if is_in_pars(l) is False: wikilinks.append(l)

    # returns list of normal wikilinks
    return wikilinks



# ==== getting to philosophy ====
def main():
    # read url
    page_url = sys.argv[1]
    print("Start URL: ", page_url)
    if "/wiki/Philosophy" in page_url:
        print("Got to Philosophy.")
        return
    # store visited wikilinks
    links = [ page_url.replace("https://en.wikipedia.org", "") ]

    # loop breaks when one condition is met
    while True:
        wikilinks = get_wikilinks(page_url)

        # list is empty
        if not wikilinks:
            print("No outgoing Wikipedia links.")
            break

        top_link = wikilinks[0].get("href")
        new_url = "https://en.wikipedia.org" + top_link

        # loop gets stuck on same link
        if top_link in links:
            print("Stuck in a loop.")
            print("Last retrieved URL: ", new_url)
            break

        # got to philosophy?
        '''
        Many wikilinks redirect to the "Philosophy"
        Wikipedia article. I added just the most
        relevant one to this script.
        '''
        if top_link in ["/wiki/Philosophy", "/wiki/Philosophical"]:
            print("Last: ", new_url)
            print("Got to Philosophy.")
            break

        # else, loop continues
        links.append(top_link)
        page_url = new_url
        print("Next: ", page_url)
        # wait half a second
        # before sending the next query
        sleep(0.5)

# ==== run main script ====
if __name__ == "__main__":
    main()
