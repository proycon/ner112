#!/usr/bin/env python3

import sys
import os
import argparse
from pynlpl.formats import folia
from frog import Frog, FrogOptions
from collections import defaultdict

def matchtext(testtext, reftext, exact):
    if exact:
        return testtext == reftext
    else:
        return reftext.lower().endswith(testtext.lower())

def evaluate(testdoc, refentities, nerset, classeval, exact):
    tp = 0
    fp = 0
    fn = 0
    testentities = list(testdoc.select(folia.Entity, set=nerset))
    print("    Test entities:", [ (e.text(), e.cls) for e in testentities ],file=sys.stderr)
    if refentities and not testentities:
        return None,0
    elif not refentities and testentities:
        return 0, None
    elif not refentities and not testentities:
        return None, None
    for refentity_text, refentity_cls in refentities:
        if any( matchtext(testentity.text(), refentity_text, exact) and testentity.cls == refentity_cls for testentity in testentities ):
            tp += 1
            print("MATCH\t" +  refentity_text + "\t" + refentity_cls, file=sys.stderr)
            classeval[refentity_cls]['tp'] += 1
        else:
            print("MISS\t" +  refentity_text + "\t" + refentity_cls, file=sys.stderr)
            classeval[refentity_cls]['fn'] += 1
            fn += 1
    for testentity in testentities:
        if not any( matchtext(testentity.text(), refentity_text, exact) and testentity.cls == refentity_cls for refentity_text, refentity_cls in refentities ):
            print("WRONG\t" +  testentity.text() + "\t" + testentity.cls, file=sys.stderr)
            classeval[testentity.cls]['fp'] += 1
            fp += 1
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return precision, recall

def readdata(filename):
    with open(filename,'r',encoding='utf-8') as f:
        for line in f:
            if line.strip() == "<utt>":
                yield None, None
            else:
                token, tag = line.strip().split("\t")
                yield token, tag

def main():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--nerset',type=str, help="NER FoLiA Set", action='store',default="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/namedentities.foliaset.ttl")
    parser.add_argument('-c','--config', type=str, help="Frog configuration", action='store',required=True)
    parser.add_argument('--notexact',dest='exact', help="Loose evaluation", action='store_false', default=True)
    parser.add_argument('files', nargs='+', help='bar help')
    args = parser.parse_args()

    frog = Frog(FrogOptions(ner=True, parser=False, xmlout=True), args.config)

    sentence = []
    entities = []
    precisions = []
    recalls = []
    entity = None
    entity_cls = None
    doc = None
    classeval = defaultdict(lambda: defaultdict(int))
    for filename in args.files:
        for token, tag in readdata(filename): #extracttrain also works on test gold standard
            if token is None: #end of sentence
                if entity:
                    entities.append((" ".join(entity), entity_cls))
                    entity = []
                if sentence:
                    print("Processing: ", " ".join(sentence),file=sys.stderr)
                    print("    Reference entities:", entities,file=sys.stderr)
                    doc = frog.process(" ".join(sentence))
                    precision, recall = evaluate(doc, entities, args.nerset, classeval, args.exact)
                    print("     precision=",precision, " recall=", recall, file=sys.stderr)
                    if precision is not None:
                        precisions.append(precision)
                    if recall is not None:
                        recalls.append(recall)
                    sentence = []
                    entities = []
            else:
                if tag[0] == 'B':
                    if entity:
                        entities.append((" ".join(entity), entity_cls))
                    entity = []
                    entity_cls = tag[2:]
                    entity.append(token)
                elif tag[0] == 'I':
                    entity.append(token)
                elif entity:
                    entities.append((" ".join(entity), entity_cls))
                    entity = []
                sentence.append(token)

    print("overall precision (macroav):\t", sum(precisions) / len(precisions))
    print("overall recall (macroav):\t", sum(recalls) / len(recalls))

    for cls, evaldata in classeval.items():
        try:
            print(cls + " precision (microav):\t", evaldata['tp'] / (evaldata['tp']+evaldata['fp']))
        except ZeroDivisionError:
            print(cls + " precision (microav):\tn/a")
        try:
            print(cls + " recall (microav):\t", evaldata['tp'] / (evaldata['tp']+evaldata['fn']))
        except ZeroDivisionError:
            print(cls + " recall (microav):\tn/a")

if __name__ == '__main__':
    main()
