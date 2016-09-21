#!/usr/bin/env python
import sys
import re
from collections import defaultdict
import os

# ~ for related words?
# ... for date/number range?

TEXT_FILES = {'.md', '.txt', '.json', '.csv', '.tsv'}


class Query:
    ORDER = ('filetype', 'intitle', 'substr')

    def __init__(self, path, *args, include_hidden=False):
        self.path = path
        self.args = args
        self.pos_conditions, self.neg_conditions = self.parse_args(*args)
        self.include_hidden = include_hidden

        self.check_fns = {
            'filetype': self.check_filetype,
            'intitle': self.check_intitle,
            'substr': self.check_substr
        }

    def parse_args(self, *args):
        pos_conditions = defaultdict(list)
        neg_conditions = defaultdict(list)
        for arg in args:
            if arg.startswith('-'):
                argtype, condition = self.parse_arg(arg[1:])
                neg_conditions[argtype].append(condition)
            else:
                argtype, condition = self.parse_arg(arg)
                neg_conditions[argtype].append(condition)

        return pos_conditions, neg_conditions

    def parse_arg(self, arg):
        if arg.startswith('filetype:'):
            argtype = 'filetype'
            arg_re = self.str2re(arg[9:])
        elif arg.startswith('intitle:'):
            argtype = 'intitle'
            arg_re = self.str2re(arg[8:])
        elif arg.startswith('"') and arg.endswith('"'):
            argtype = 'substr'
            arg_re = self.str2re(arg[1:-1])
        elif arg.startswith('~'):
            argtype = 'substr'
            arg_re = self.related_re(arg[1:])
        else:
            argtype = 'substr'
            arg_re = self.str2re(arg)

        return argtype, arg_re

    def str2re(self, s):
        s = s.replace('*', '\w+')
        return re.compile(s)

    def related_re(self, s):
        raise NotImplementedError

    def execute(self):
        return list(self._execute())

    def _execute(self):
        for dirpath, dirnames, filenames in os.walk(self.path):
            if not self.include_hidden and os.path.basename(dirpath).startswith('.'):
                continue

            for filename in filenames:
                if os.path.splitext(filename)[1] not in TEXT_FILES:
                    continue

                filepath = os.path.join(dirpath, filename)

                for argtype in Query.ORDER:
                    if not self.check_fns[argtype](filepath, self.pos_conditions[argtype]):
                        break  # file does not match positive conditions
                    if self.check_fns[argtype](filepath, self.neg_conditions[argtype]):
                        break  # file matches negative conditions

                else:
                    yield filepath

    def check_filetype(self, filepath, conditions):
        _, ext = os.path.splitext(filepath)

        for condition in conditions:
            if not condition.search(ext):
                return False

        return True

    def check_intitle(self, filepath, conditions):
        fname = os.path.basename(filepath)

        for condition in conditions:
            if not condition.search(fname):
                return False

        return True

    def check_substr(self, filepath, conditions):
        with open(filepath) as f:
            text = f.read()

        for condition in conditions:
            if not condition.search(text):
                return False

        return True

    def pprint_results(self):
        lines = [' '.join('"{}"'.format(arg) for arg in args)] + self.execute()
        print('\n'.join(lines))

if __name__ == '__main__':
    path = sys.argv[1]
    args = sys.argv[2:]

    q = Query(path, *args)
    q.pprint_results()
