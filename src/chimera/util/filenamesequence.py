
import os
import glob
import re


class FilenameSequence (object):

    def __init__ (self, filename, extension="fits", separator="-"):
        self.filename = filename # with dir
        self.separator = separator
        self.extension = extension

        self.fullpath = self.filename+self.separator
        self.re = re.compile("%s(?P<num>[0-9]+).%s" % (self.fullpath, self.extension))

    def next (self):
        """Get next sequence number.
        """

        nums = [0]
        
        filenames = glob.glob (self.fullpath + "*")

        for filename in filenames:
            match = self.re.match(filename)

            if not match: continue

            try:
                num = int(match.groups()[0])
                nums.append (num)
            except ValueError:
                continue

        return max(nums)+1
