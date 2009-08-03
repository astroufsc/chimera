from chimera.util.votable import VOTable

from httplib import HTTPConnection
import tempfile
import os
import urllib

class VizQuery(object):
    """
    Queries A catalog in Vizier 
    within a given radius or box of the zenith
    """
    def __init__(self):
        self.args = {}
        self.args["-mime"] = "xml"
        self.columns = None

    
    def useCat(self, catName):
        """
        @param catName: the catalog's name in Vizier
        @type catName: str

        Simply sets the catalog's name
        """

        self.args["-source"] = catName

    def useColumns(self, columns, sortBy, reverse=False):
        """
        @param columns: list of catalog's columns to use
        @type columns: list

        @param sortBy: define which column to sort by
        @type sortBy: str

        @param reverse: decide to reverse sort @type reverse: bool

        Define which columns will be fetched and which column will be used
        for sorting.
        """

        self.columns = columns.split(",")

        self.args["-out"] = columns

        if reverse:
            self.args["-sort"] = "-"+sortBy
        else:
            self.args["-sort"] = sortBy

    def sortBy(self, column):
        """
        One sets here which column to sort by
        @param column: name of column to sort by
        @type  column: str
        """

    def constrainColumns(self, columns):
        """
        Use this to add constraints to any of the columns
        @param columns: list of dictionaries {COLUMN:condition}
        @type  columns: list
        """
        self.args.update(columns)


    def useTarget(self, center, radius=None, box=None):
        """
        @param center: center of search in catalog
        @type center: L{Position}

        @param radius: radius of search
        @type radius: float

        @param box: box size, if you want a square use an integer
                    if you want a rectangle use a tuple (ww,hh)
        @type box: int | tuple
        """

        self.args["-c"] = str(center)
        self.args["-c.eq"] = "J2000"
        
        if radius:
            self.args["-c.rd"] = radius
        elif box:
            try:
                self.args["-c.bd"] = "=%fx%f" % radius
            except:
                self.args["-c.bd"] = radius
        else:
            raise TypeError("You must specify either radius or box size")

    def find(self, limit=9999):
        """
        @param limit: Number of stars to return from Vizier
        @type limit: int

        """

        assert "-c.rd" in self.args or "-c.bd" in self.args, "No target selected, use useTarget method first."

        self.args["-out.max"] = limit
        
        results = tempfile.NamedTemporaryFile(mode='w+', 
                                              prefix="chimera.vizquery", 
                                              dir=tempfile.gettempdir())

        # query the catalog in Vizier's database
        conn = HTTPConnection("webviz.u-strasbg.fr")

        s = urllib.urlencode(self.args)

        conn.request("POST", "/viz-bin/votable",s)  
        resp = conn.getresponse()
        ret = resp.read()

        f = open(results.name, "w")
        f.write(ret)
        f.close()

        obj = []

        votable = VOTable(results.name)

        for linha in votable.getDataRows():
            v = [c.getContent() for c in linha.getNodeList()]
            obj.append(dict(zip(self.columns, v)))

        return obj
