# test task
# part 1: getting to philosophy law
'''
    Receive a Wikipedia link as input,
    go to next normal link on the page,
    repeat until:
    (a) philosophy page reached
    (b) no more outgoing wikilinks
    (c) stuck in a loop
'''

import sys
import requests
from bs4 import BeautifulSoup
import re
from time import sleep


def get_wikilinks(page_url):
    # ==== get html ====
    html_page = requests.get(page_url)

    # ==== parse page and build tree ====
    parsed_html = BeautifulSoup(html_page.text, "html.parser")

    # ==== find wikilinks ====
    # get all paragraphs that are direct
    # children of <div class="mw-parser-output">
    # this avoids selecting paragraphs that
    # may have been mistakenly used in tables
    # (check the link "Cognition" on en.wikipedia.org/Problem_solving, for example)
    main_pars = parsed_html.select("div.mw-parser-output > p")

    # prune links
    pruned_links = list()
    # remove external links
    for p in main_pars:
        internal_l = [l for l in p.find_all("a", href=re.compile("^/wiki/"))]
        pruned_links += internal_l

    # remove links in italic (but not in bold) as well as
    # links to IPA pronunciation, Wiktionary (non-latin words), etc.
    # leaving only bold or plain text links
    pruned_links = [l for l in pruned_links if l.parent.name in ["p", "b"]]
    # remove links to missing pages
    pruned_links = [l for l in pruned_links if l.get("class") != "new"]

    # remaining links are plain Wikipedia links
    # remove parenthesized links
    wikilinks = list()
    for l in pruned_links:
        par_balance = 0
        # loop over previous text
        # up to start of paragraph
        for s in l.previous_siblings:
            # if string is null,
            # skip iteration
            if s.string is None: continue
            # else, count parentheses
            if "(" in s.string:
                par_balance += 1
            if ")" in s.string:
                par_balance -= 1
        # normal wikilink if parentheses are balanced
        if par_balance == 0: wikilinks.append(l)

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
        if top_link in ["/wiki/Philosophy", "/wiki/Philosophical"]:
            print("Last: ", new_url)
            print("Got to Philosophy.")
            break

        # else, loop continues
        links.append(top_link)
        page_url = new_url
        print("Next: ", page_url)
        # wait one second
        # before querying Wikipedia again
        sleep(1.0)

# run main script
if __name__ == "__main__":
    main()
