"""	Class to handle VOTable
	Created: 2005-05-31 by Shui Hung Kwok, shkwok at computer.org

	See http://www.ivoa.net/Documents/latest/VOT.html .
"""

import sys
from types import *
import xml.sax
import xml.sax.handler 

class VONode (object):
	"""	Class representing an XML node of a VOTable
	""" 
	def __init__ (self, tagname=('','')):
		self._tagname = tagname
		self._nodeList = []
		self._attributes = {}

	def addNode (self, node):
		self._nodeList.append (node)
		if not isinstance (node, (StringType, UnicodeType)):
			name = node.getNamePart ()
			try:
				val = self.__dict__[name]
				if isinstance (val, ListType):
					val.append (node)
				else:
					self.__dict__[name] = [val, node]
			except:
				self.__dict__[name] = node
		else:
			self.content = node

	def addAttribute (self, attr):
		name,value = attr
		self._attributes[name] = value
		self.__dict__[name] = value

	def addAttributes (self, attrs):
		self._attributes.update (attrs)
		for k,v in attrs.items ():
			self.__dict__[k[1]] = v

	def __getitem__ (self, idx):
		return self._nodeList[idx].getContent ()

	def getAttribute (self, name):
		""" Returns attribute by name or '' if not found """
		return self._attributes.get (name)

	def getAttributes (self):
		""" Returns all attributes.
		"""
		res = {}
		for (ns,n),at in self._attributes.items():
			res[n] = at
		return res

	def getNodeList (self):
		""" Returns a list of nodes that are of type VONode
		"""
		res = []
		for node in self._nodeList:
			try:
				l = node._nodeList
				res.append (node)
			except Exception, e:
				pass
		return res		

	def getContent (self):
		""" Returns all strings of the node.
		"""
		res = []
		for node in self._nodeList:
			try:
				l = node.lower ()
				res.append (node)
			except Exception, e:
				pass
		return ''.join (res)
	
	def getNamePart (self):
		try:
			ns, n = self._tagname
			return n
		except:
			return n
			
	def getNodesByName (self, look4):
		""" Returns a list of nodes whose tagname = look4
		"""
		res = []
		for node in self._nodeList:
			try:
				if look4 != node.getNamePart ():
					continue
				l = node._nodeList
				res.append (node)
			except Exception, e:
				pass
		return res		

	def __str__ (self):
		try:
			return self.content
		except:
			return self.buildName (self._tagname)

	def getNode (self, path):
		"""	Returns a node for a given path.
			Path is of the form /tag1/tag2/tag3.
			Path can include array index, like /tag1/tag2[3]/tag4.
		"""
		node = self
		children = []
		pathArray = path.split ("/")

		rootName = self.getNamePart ()
		if rootName != pathArray[1]:
			return None

		pathArray = pathArray[2:]
		for elem in pathArray:
			tmp = elem.replace ('[', ']')
			list = tmp.split (']')
			name = list[0]
			if len (list) > 1:
				idx = int (list[1])
			else:
				idx = 0
			children = node.getNodesByName (name)
			nr = len (children)
			if idx >= nr:
				return None
			node = children [idx]
		return node	

	def getNodesByPath (self, path):
		"""	Returns an array of VONodes for a given path.
			Path is of the form /tag1/tag2/tag3.
			Path can include array index, like /tag1/tag2[3]/tag4.
		"""
		node = self
		children = []
		pathArray = path.split ("/")

		rootName = self.getNamePart ()
		if rootName != pathArray[1]:
			return None

		pathArray = pathArray[2:]
		for elem in pathArray:
			tmp = elem.replace ('[', ']')
			list = tmp.split (']')
			name = list[0]
			if len (list) > 1:
				idx = int (list[1])
			else:
				idx = 0
			children = node.getNodesByName (name)
			nr = len (children)
			if idx >= nr:
				return None
			node = children [idx]
		return children	

	def buildName (self, tname):
		""" Returns a name with namespace as prefix
			or just name if no namespace
			Note that the prefix is the real namespace
			and not the abbreviation used in the original XML
		"""
		ns,n = tname
		"""
		if ns:
			return "%s:%s" % (self.qname, n)
		else: 
			return n
		"""
		return n

	def printAllNodes (self, func=sys.stdout.write, prefix=''):
		"""	Recursive method to visit all nodes of the tree
			and calls the provided function to output the content.
		"""
		func ("%s<%s" % (prefix, self.buildName (self._tagname)))
		for ns,v in self._attributes.items ():
			func (" %s='%s'" % (self.buildName ((ns)), v))
		func (">")
		
		last = 0
		for n in self._nodeList:
			if isinstance (n, (StringType, UnicodeType)):
				if last == 2:
					func ("\n%s" % prefix)
				func ("%s" % n)
				last = 1
			else:
				if last <= 1:
					func ("\n")
				n.printAllNodes (func, prefix + '   ')
				last = 2
		if last <= 1:
			func ("</%s>\n" % self.buildName (self._tagname))
		else:
			func ("%s</%s>\n" % (prefix, self.buildName (self._tagname)))
		
class VOTableHandler (xml.sax.handler.ContentHandler):
	""" Class implementing callbacks for the SAX parser.
	"""
	def __init__ (self, vonode=VONode):
		# Create a parser
		xml.sax.handler.ContentHandler.__init__ (self)
		self.parser = xml.sax.make_parser()
		self.parser.setFeature (xml.sax.handler.feature_namespaces, 1)
		self.parser.setContentHandler (self)
		self.vonode = vonode
		self.sentinel = vonode ()
		self.currNode = self.sentinel
		self.stack = []

	def startElementNS (self, (urn, name), qname, attrs):
		#print "start ", name
		self.stack.append (self.currNode)

		self.currNode = self.vonode ((urn, name))
		self.currNode.addAttributes (attrs)

	def characters (self, chunk):
		buf = chunk.strip ()
		if len (buf) == 0: return
		self.currNode.addNode (buf)

	def endElementNS (self, (urn, name), qname):
		#print "end ", name
		newNode = self.currNode
		self.currNode = self.stack.pop ()
		self.currNode.addNode (newNode)

	def parse (self, source):
		""" Main entry point.
			Source can be URL or file name.
		"""
		self.parser.parse (source)
		return self.sentinel #._nodeList[0]

class VOTable (object):
	""" Implementation of VOTable 
	"""
	def __init__ (self, source=None, vonode=VONode):
		""" Instantiate a VOTable.
			source can be URL, file name or a string representing the VOTable.
			vonode is a class representing VONode, must be derived from or
			compatible with VONode.
		"""
		self.vonode = vonode 
		self.root = None
		if source != None:
			self.parse (source)

	def parse (self, source):
		""" Invokes XML parser and stores VOTable
			in self.root as VONode.
		"""
		parser = VOTableHandler (self.vonode)
		self.root = parser.parse (source)

	def printAllNodes (self, func=sys.stdout.write):	
		"""	Output entire content as XML.
			func is the output method, defined as:
				func (outString)
		"""
		# _nodeList[0] is VOTABLE
		# We use _nodeList[0] instead, just in case
		# the xml content does not start with VOTABLE,
		# we still can print all nodes.
		node = self.root._nodeList[0] 
		node.printAllNodes (func)

	def getNode (self, path):
		""" Returns a VONode of the given path.
		"""
		return self.root._nodeList[0].getNode (path)

	def getContent (self, path):
		""" Returns the content of a node.
			Only strings are returned.
		"""
		node = self.getNode (path)
		return node.getContent ()

	def getColumnIdx (self, val):
		""" Returns the column index for the given name
			Will return any attribute value matching val.
		"""
		fields = self.getFields ()
		for coln, f in enumerate (fields):
			if val in f._attributes.values ():
				return coln
		return -1
		
	def getFields (self):
		""" Returns a list of VONode representing all the fields
		"""
		#table = self.root.VOTABLE.RESOURCE.TABLE
		#return table.getNodesByName ('FIELD')
		return self.root.VOTABLE.RESOURCE.TABLE.FIELD
	
	def getParams (self):
		"""	Returns a list of VONode representing all PARAMS
		"""
		return self.root.VOTABLE.RESOURCE.RESOURCE.PARAM

	def getFieldsAttrs (self):
		"""	Returns a list of maps that contains attributes.
			Returned list looks like this: [{},{},...]
		"""
		res = []
		fields = self.getFields ()
		for elem in fields:
			try:
				res.append (elem.getAttributes())
			except:
				pass
		return res
	
	def getDataRows (self):
		"""	Returns a list of VONodes representing rows of the table.
			Use getData () to extract data from each row.
			for x in getDataRows ():
				data = getData (x)
				#data = [values ...]
		"""
		tableData = self.root.VOTABLE.RESOURCE.TABLE.DATA.TABLEDATA
		return tableData._nodeList

	def getData (self, row):
		""" row is a VONode <TR> parent of a list of <TD>.
			Returns a list of values.
		"""
		res = []
		list = row._nodeList
		for elm in list:
			try:
				res.append (elm.getContent ())
			except:
				res.append ('')
		return res	
	
	def append (self, vot):
		""" Appends votable vot to the end of this VOTable. 
			No tests to see if fields are the same. 
			vot must have the same fields. 
		"""
		try:
			node1 = self.root.VOTABLE.RESOURCE.TABLE.DATA.TABLEDATA
		except:
			node1 = None
		try:
			node2 = vot.root.VOTABLE.RESOURCE.TABLE.DATA.TABLEDATA
		except:
			node2 = None

		if node1:
			if node2:
				node1._nodeList.extend (node2._nodeList)
		else:
			if node2:
				self.root.VOTABLE.RESOURCE.TABLE.DATA.TABLEDATA = node2
		
if __name__ == '__main__':
	votable = VOTable()
	votable.parse (sys.argv[1])
	#votable.printAllNodes ()
	#print [x.getAttribute ('ID') for x in votable.getFields () ]
	#print votable.root.VOTABLE.RESOURCE.TABLE.DATA.TABLEDATA.TR[1].TD[1]
	print votable.getFields ()
