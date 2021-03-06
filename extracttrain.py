#!/usr/bin/env python3

import sys
import textgrid
import argparse
import ucto
import re


tokenizer = ucto.Tokenizer("tokconfig-nld")

def tokenize(text):
    #first we remove *d (dialetical or foreign), *u (other), *v (vreemde taal), *a (afgebroken woorden, *x (uncertain whether heard correctly)
    text = re.sub(r"\*[duvax]\b", "", text)
    tokenizer.process(text)
    return [str(token) for token in tokenizer]

def chunks(text):
    """Parse data into chunks, each entity and each non-entity is a chunk, text will be tokenised on the fly"""
    begin = None
    end = None
    cls = ""
    chunk = ""
    for i, c in enumerate(text.strip() + " "):
        if begin is not None:
            if c == '[':
                print("Skipping text because of nested brackets: " + text ,file=sys.stderr)
                break
            elif c == ']':
                end = i
            elif end is not None:
                if c == " ":
                    yield tokenize(text[begin+1:end]), cls
                    begin = end = None
                    cls = ""
                else:
                    cls = cls + c
        else:
            if c == '[':
                if chunk.strip():
                    yield tokenize(chunk), None
                    chunk = ""
                begin = i
            else:
                chunk += c
    if chunk.strip(): #don't forget the last one
        yield tokenize(chunk), None

def gettokens(inputfile):
    try:
        tg = textgrid.TextGrid.fromFile(inputfile)
    except textgrid.exceptions.TextGridError:
        print("ERROR: INVALID INPUTFILE:", inputfile,file=sys.stderr)
        sys.exit(2)
    for intervaltier in tg:
        for interval in intervaltier:
            text = interval.mark
            if text is not None:
                output = False
                for tokens, chunktype in chunks(text):
                    for i, token in enumerate(tokens):
                        output = True
                        if chunktype is None:
                            tag = "O"
                        elif i == 0:
                            tag = "B-" + chunktype
                        else:
                            tag = "I-" + chunktype
                        yield token, tag
                if output:
                    yield None, None


def main():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    #parser.add_argument('--storeconst',dest='settype',help="", action='store_const',const='somevalue')
    #parser.add_argument('-f','--dataset', type=str,help="", action='store',default="",required=False)
    #parser.add_argument('-i','--number',dest="num", type=int,help="", action='store',default="",required=False)
    parser.add_argument('inputfiles', nargs='+', help='Input files')
    args = parser.parse_args()

    for inputfile in args.inputfiles:
        for token, tag in gettokens(inputfile):
            if token is None:
                print("<utt>")
            else:
                print(token + "\t" + tag)

if __name__ == '__main__':
    main()
