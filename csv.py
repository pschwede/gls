#!/usr/bin/env python3

import sys
import io
import re
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams

re_spaces = re.compile(r"[ \t]+")
re_firstline = re.compile(r"[0-9]{2}\.[0-9]{2}\.")
re_ktline = re.compile(r".{13} [A-ZÄÖÜ0-9]")

def umsaetzeLines(inpath):
    laparams = LAParams()
    imagewriter = None
    rsrcmgr = PDFResourceManager()
    with open(inpath, 'rb') as f:
        outfile = io.StringIO()
        device = TextConverter(rsrcmgr, outfile, laparams=laparams, imagewriter=imagewriter)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(f, check_extractable=False):
            interpreter.process_page(page)
        for line in outfile.getvalue().split("\n"):
            if not re_ktline.match(line) \
                    or "geehrter Kunde" in line \
                    or "Schecks" in line:
                continue
            yield line

def umsaetzeGroups(inpath):
    group = []
    for u in umsaetzeLines(inpath):
        if re_firstline.match(u):
            if group:
                yield group
            group = [[x for x in re_spaces.split(u) if x]]
        else:
            group.append([x for x in re_spaces.split(u) if x])
    yield group


def umsaetzeDict(inpath):
    year = inpath.split("_")[1]
    for g in umsaetzeGroups(inpath):
        betrag_given = False
        try:
            betrag = (-1 if g[0][-1] == "S" else 1) * float(g[0][-2].replace(".","").replace(",","."))
            betrag_given = True
        except ValueError:
            continue
        yield { "Datum": g[0][0]+year,
                "Empfänger": "GLS" if (len(g) < 2 or not g[1]) else " ".join(g[1]),
                "Beschreibung": " ".join(g[0][2:-2] if betrag_given else g[0][2:]),
                "Betrag": betrag,
                "Einzahlung": None if betrag < 0. else betrag,
                "Auszahlung": None if betrag > 0. else -betrag,
                "g": g
                }


def toTable(dics, *keys):
    yield ";".join(keys)
    for d in dics:
        yield ";".join(["" if d[k] is None \
                else (f"\"{d[k]}\"" if type(d[k])==str else str(d[k])) \
                for k in keys])


if __name__ == "__main__":
    for line in toTable((i for s in (umsaetzeDict(a) for a in sys.argv[1:]) for i in s), \
            "Datum", "Empfänger", "Beschreibung", "Einzahlung", "Auszahlung"):
        print(line)
