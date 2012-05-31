'''
Created on Jan 4, 2012

@author: penteado
'''

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg


    

class SCH(object):
    '''
    classdocs
    '''

    #Regular expression to determine if something is an integer number
    intexpr='[-+]?(?:[0-9]+)' #1 group
    #Regular expression to determine if something is a floating point number
    fpexpr='[-+]?(?:(?:[0-9]*\.?[0-9]+)|(?:[0-9]+\.?[0-9]*))(?:[eEdD][-+]?[0-9]+)?' #4 groups
    #Regular expression for NaN
    nanexpr='[-+]?(?:nan)' #1 group
    #Regular expression for Infinity
    infexpr='[-+]?(?:inf)i?(?:in)?(?:ini)?(?:init)?(?:inity)?' #5 groups


    def __init__(self,file='example.sch',shootfile=''):
        '''
        Constructor
        '''
        if file:
            self.file=file
        else:
            self.file='example.sch'
            
        if shootfile:
            self.shootfile=shootfile
        else:
            import re
            s=re.search('(?P<root>.*)\.sch$',self.file)
            if s:
                self.shootfile=s.group('root')+'_shoot.txt'
            else:
                self.shootfile=self.shootfile+'_shoot.txt'
                



            
        
    def Read(self):
        f=open(self.file,'r')
        self.lines=f.readlines()
        f.close()
#        print 'lines:'
#        print self.lines
        #Parse the file content
        self.ParseFile()
        #Now read the shoot file, which has other needed data
        f=open(self.shootfile,'r')
        self.shootlines=f.readlines()
#        print 'shootlines:'
#        print self.shootlines
        #Parse the shoot file
        self.ParseShootFile()
        
        
    def ParseFile(self):
        headerline=-1
        import re
        print 'Parsing schedule file ('+self.file+')...'
        for l in self.lines:
            headerline+=1
            if re.search('OBSERVING SCHEDULE:',l):
                break
        else:
            raise InputError('',"Invalid SCH file: No 'OBSERVING SCHEDULE:'")
        tableline=0
        for l in self.lines[headerline+1:]:
            tableline+=1
            if re.search('(Slew)\s+(Exposure)\s+(Exp\.)\s+(Idle)',l):
                break
        else:
            raise InputError('',"Invalid SCH file: No table header line")
        tableline+=headerline
        if not re.search('(Start \(MJD\))\s+(Start \(MJD\))\s+(UT)\s+(Object)\s+(RA)\s+(dec)\s+(HA)\s+(alt)\s+'
        '(\(sec\))\s+(\(sec\))\s+(Type)\s+(Field)\s+(dRA \(h\))\s+(ddec \(deg\))\s+(User)\s+(Res\.)\s+'
        '(Mode)\s+(Size)\s+(Filter)\s+(Req\. ID)\s+(File)',self.lines[tableline+1]):
            raise InputError('',"Invalid SCH file: Invalid table header line")
        print 'Parsing schedule table...',
        #Read the table into dicts, to store in a structure later
        fpexpr=self.fpexpr        
        expr='(?P<ID>\d+)\s+(?P<Slewstart>'+fpexpr+')\s+(?P<Exposurestart>'+fpexpr+')\s+(?P<UT>\d{2}:\d{2})\
\s+(?P<Object>\S+.*\S+)\s+(?P<RA>'+fpexpr+')\s+(?P<Dec>'+fpexpr+')\s+(?P<HA>'+fpexpr+')\s+(?P<Alt>'+fpexpr+')\
\s+(?P<Exp>'+fpexpr+')\s+(?P<Idle>'+fpexpr+')\s+(?P<Side>\S)\s+(?P<Type>\S+)\s+(?P<Field>\(\s*\d+,\s*\d\))\
\s+(?P<DRA>'+fpexpr+')\s+(?P<Ddec>'+fpexpr+')\s+(?P<User>\S{3})\s+(?P<Res>\d+)\s+(?P<Mode>\S+)\s+\
(?P<Size>\d+)\s+(?P<Filter>\S+.*\S+)\s+(?P<ReqID>\S+)\s+(?P<File>\S+)'
        buffer=[]
        for l in self.lines[tableline+2:]:
            s=re.search(expr,l)
            if s:
                g=s.groupdict()
                buffer.append(g)
            else:
                if not re.search('\n',l):
                    break
        if not buffer:
            raise InputError('',"Invalid SCH file: Empty table")
        #Define the array to hold the table
        a='a80'
        d='f8'
        i='i4'
        self.nobs=len(buffer)
        import numpy
        self.schedule=numpy.zeros(self.nobs,dtype=[('ID',i),('Slewstart',d),('Exposurestart',d),
                                   ('UT',a),('Object',a),('RA',d),('Dec',d),
                                   ('HA',d),('Alt',d),('Exp',d),('Idle',d),('Side',a),('Type',a),
                                   ('Field',a),('DRA',d),('Ddec',d),('User',a),('Res',i),
                                   ('Mode',a),('Size',i),('Filter',a),('ReqID',a),('File',a),
                                   ('ra',d),('dec',d),('idle',d),('exp',d),('filter',i),('slewstart',d),
                                   ('dra',d),('ddec',d),('fitsfile',a),
                                   ('object',a),('user',a),('reqid',a)])
        i=0
        for b in buffer:
            #(schedule[i]['index'],schedule[i]['slewstart'])=(b[0],b[1])
            for key in b.keys():
                self.schedule[i][key]=b[key]
            i+=1
        print 'Done'
                                    
        
    def ParseShootFile(self):
        import re
        fpexpr=self.fpexpr
        expr='\s+(?P<ra>'+fpexpr+')\s+(?P<dec>'+fpexpr+')\s+(?P<object>\S+.*\S+)\s+(?P<user>\S{3})\s+\
(?P<idle>'+fpexpr+')\s+(?P<exp>'+fpexpr+')\s+(?P<filter>\d+)\s+(?P<slewstart>'+fpexpr+')\s+\
(?P<dra>'+fpexpr+')\s+(?P<ddec>'+fpexpr+')\s+(?P<reqid>\S+)\s+(?P<fitsfile>\S+)'
        print 'Parsing schedule shoot file ('+self.shootfile+')...',
        i=0
        for l in self.shootlines:
            if i == self.nobs:
                break
            s=re.search(expr,l)
            if s:
                g=s.groupdict()
                for key in g:
                    self.schedule[i][key]=g[key]
                i+=1
        print 'Done'
            
            
            

        
        
print "SCH.py executed"
        
        
if __name__ == "__main__":
    print "Ruuning SCH.py's main"
    t=SCH('../../example.sch')
    t.Read()
        