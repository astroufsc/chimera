# Taken from http://code.activestate.com/recipes/137951/
# Originally licensed under the Python License (presumably
# version 2.0.1/2.1.1 or later)
# Relicensed under GPL of use in Chimera


def printDict(di, format="%-25s %s"):
    for (key, val) in di.items():
        print format % (str(key) + ':', val)


def dumpObj(obj, maxlen=77, lindent=24, maxspew=600):
    """Print a nicely formatted overview of an object.

    The output lines will be wrapped at maxlen, with lindent of space
    for names of attributes.  A maximum of maxspew characters will be
    printed for each attribute value.

    You can hand dumpObj any data type -- a module, class, instance,
    new class.

    Note that in reformatting for compactness the routine trashes any
    formatting in the docstrings it prints.

    Example:
       >>> class Foo(object):
               a = 30
               def bar(self, b):
                   "A silly method"
                   return a*b
       ... ... ... ... 
       >>> foo = Foo()
       >>> dumpObj(foo)
       Instance of class 'Foo' as defined in module __main__ with id 136863308
       Documentation string:   None
       Built-in Methods:       __delattr__, __getattribute__, __hash__, __init__
                               __new__, __reduce__, __repr__, __setattr__,       
                               __str__
       Methods:
         bar                   "A silly method"
       Attributes:
         __dict__              {}
         __weakref__           None
         a                     30
    """

    import types

    # Formatting parameters.
    ltab = 2    # initial tab in front of level 2 text

    # There seem to be a couple of other types; gather templates of them
    MethodWrapperType = type(object().__hash__)

    #
    # Gather all the attributes of the object
    #
    objclass = None
    objdoc = None
    objmodule = '<None defined>'

    methods = []
    builtins = []
    classes = []
    attrs = []
    for slot in dir(obj):
        attr = getattr(obj, slot)
        if slot == '__class__':
            objclass = attr.__name__
        elif slot == '__doc__':
            objdoc = attr
        elif slot == '__module__':
            objmodule = attr
        elif (isinstance(attr, types.BuiltinMethodType) or
              isinstance(attr, MethodWrapperType)):
            builtins.append(slot)
        elif (isinstance(attr, types.MethodType) or
              isinstance(attr, types.FunctionType)):
            methods.append((slot, attr))
        elif isinstance(attr, types.TypeType):
            classes.append((slot, attr))
        else:
            attrs.append((slot, attr))

    #
    # Organize them
    #
    methods.sort()
    builtins.sort()
    classes.sort()
    attrs.sort()

    #
    # Print a readable summary of those attributes
    #
    normalwidths = [lindent, maxlen - lindent]
    tabbedwidths = [ltab, lindent - ltab, maxlen - lindent - ltab]

    def truncstring(s, maxlen):
        if len(s) > maxlen:
            return s[0:maxlen] + ' ...(%d more chars)...' % (len(s) - maxlen)
        else:
            return s

    # Summary of introspection attributes
    if objclass == '':
        objclass = type(obj).__name__
    intro = "Instance of class '%s' as defined in module %s with id %d" % \
            (objclass, objmodule, id(obj))
    print '\n'.join(prettyPrint(intro, maxlen))

    # Object's Docstring
    if objdoc is None:
        objdoc = str(objdoc)
    else:
        objdoc = ('"""' + objdoc.strip() + '"""')
    print
    print prettyPrintCols(('Documentation string:',
                           truncstring(objdoc, maxspew)),
                          normalwidths, ' ')

    # Built-in methods
    if builtins:
        bi_str = delchars(str(builtins), "[']") or str(None)
        print
        print prettyPrintCols(('Built-in Methods:',
                               truncstring(bi_str, maxspew)),
                              normalwidths, ', ')

    # Classes
    if classes:
        print
        print 'Classes:'
    for (classname, classtype) in classes:
        classdoc = getattr(classtype, '__doc__', None) or '<No documentation>'
        print prettyPrintCols(('',
                               classname,
                               truncstring(classdoc, maxspew)),
                              tabbedwidths, ' ')

    # User methods
    if methods:
        print
        print 'Methods:'
    for (methodname, method) in methods:
        methoddoc = getattr(method, '__doc__', None) or '<No documentation>'
        print prettyPrintCols(('',
                               methodname,
                               truncstring(methoddoc, maxspew)),
                              tabbedwidths, ' ')

    # Attributes
    if attrs:
        print
        print 'Attributes:'
    for (attr, val) in attrs:
        print prettyPrintCols(('',
                               attr,
                               truncstring(unicode(val), maxspew)),
                              tabbedwidths, ' ')


def prettyPrintCols(strings, widths, split=' '):
    """Pretty prints text in colums, with each string breaking at
    split according to prettyPrint.  margins gives the corresponding
    right breaking point."""

    assert len(strings) == len(widths)

    strings = map(nukenewlines, strings)

    # pretty print each column
    cols = [''] * len(strings)
    for i in range(len(strings)):
        cols[i] = prettyPrint(strings[i], widths[i], split)

    # prepare a format line
    format = ''.join(["%%-%ds" % width for width in widths[0:-1]]) + "%s"

    def formatline(*cols):
        return format % tuple(map(lambda s: (s or ''), cols))

    # generate the formatted text
    return '\n'.join(map(formatline, *cols))


def prettyPrint(string, maxlen=75, split=' '):
    """Pretty prints the given string to break at an occurrence of
    split where necessary to avoid lines longer than maxlen.

    This will overflow the line if no convenient occurrence of split
    is found"""

    # Tack on the splitting character to guarantee a final match
    string += split

    lines = []
    oldeol = 0
    eol = 0
    while not (eol == -1 or eol == len(string) - 1):
        eol = string.rfind(split, oldeol, oldeol + maxlen + len(split))
        lines.append(string[oldeol:eol])
        oldeol = eol + len(split)

    return lines


def nukenewlines(string):
    """Strip newlines and any trailing/following whitespace; rejoin
    with a single space where the newlines were.

    Bug: This routine will completely butcher any whitespace-formatted
    text."""

    if not string:
        return ''
    lines = string.splitlines()
    return ' '.join([line.strip() for line in lines])


def delchars(str, chars):
    """Returns a string for which all occurrences of characters in
    chars have been removed."""

    # Translate demands a mapping string of 256 characters;
    # whip up a string that will leave all characters unmolested.
    identity = ''.join([chr(x) for x in range(256)])

    return str.translate(identity, chars)
