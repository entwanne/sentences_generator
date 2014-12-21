#!/usr/bin/env python

import random
import re
import argparse
import sys
from collections import Counter


def counter_choice(counter):
    n = random.randrange(sum(counter.values()))
    i = 0
    for item, weight in counter.items():
        i += weight
        if n < i:
            return item


def counter_mul(counter, k):
    if not counter:
        return counter
    new = Counter()
    for _ in range(k):
        new.update(counter)
    return new


class SpecialWord:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '<{}>'.format(self.name)


class WordsDict:
    def __init__(self, lookup_size, lookup_weight):
        self.BEGIN = SpecialWord('begin')
        self.END = SpecialWord('end')
        self.links = {}
        self.lookup_size, self.lookup_weight = lookup_size, lookup_weight

    @staticmethod
    def get_word(word):
        return word.lower()

    def refresh_lookup(self, lookup, word):
        if len(lookup) >= self.lookup_size:
            lookup = lookup[-self.lookup_size:][1:]
        return lookup + (word,)

    def add_link(self, lookup, word):
        lookup_ = lookup
        while lookup_:
            self.links.setdefault(lookup_, Counter())[word] += 1
            lookup_ = lookup_[1:]
        return self.refresh_lookup(lookup, word)

    def get_next(self, lookup):
        lookup_ = lookup
        choices = Counter()
        while lookup_:
            choices = counter_mul(choices, self.lookup_weight) + self.links.get(lookup_, Counter())
            lookup_ = lookup_[1:]
        word = counter_choice(choices)
        return word, self.refresh_lookup(lookup, word)

    def get_first(self):
        return self.get_next((self.BEGIN,))


def learn_sentence(words, s, regex=re.compile(r"\w+|[^\w]")):
    prevs = words.BEGIN,
    for word in regex.findall(s):
        word = words.get_word(word)
        prevs = words.add_link(prevs, word)
    words.add_link(prevs, words.END)


def learn_corpus(words, corpus, *args, **kwargs):
    for line in corpus:
        line = line.rstrip('\r\n')
        if line:
            learn_sentence(words, line, *args, **kwargs)


def gen_sentence(words):
    w, prevs = words.get_first()
    while w != words.END:
        yield str(w)
        w, prevs = words.get_next(prevs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("generator",
                                     description="Sentences generator")
    parser.add_argument(
        '-c, --corpus', dest='corpus', metavar='FILENAME', default=None,
        help='Corpus file (set of sentences)'
    )
    parser.add_argument(
        '-l, --lookup', dest='lookup', metavar='LOOKUP', default=5,
        type=int, help='Lookup size (eg: 5)'
    )
    parser.add_argument(
        '-w, --weight', dest='weight', metavar='WEIGHT', default=20,
        type=int, help='Lookup weight (eg: 20)'
    )
    args = parser.parse_args()

    words = WordsDict(args.lookup, args.weight)

    if args.corpus:
        with open(args.corpus, 'r') as corpus:
            learn_corpus(words, corpus)
    else:
        print('Learning...')
        print('Press ^D to stop')
        learn_corpus(words, sys.stdin)

    print('Generating...')
    print('Press ^C or ^D to stop, <enter> to continue')

    try:
        while True:
            print(''.join(gen_sentence(words)))
            input()
    except (KeyboardInterrupt, EOFError):
        pass
