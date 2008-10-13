package xpa;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.LinkedList;
import java.util.Queue;
import java.util.Vector;

import xpa.exceptions.XpaError;


public class Xpa {
	
	private boolean initialized = false;
	public String exec_dir = ""; 
	
	public Xpa()
	{
		this(false, false);
	}
	
	public Xpa(boolean doRaise, boolean debug)
	{
		//Need to set exec_dir if xpa isn't on path! Include trailing path seperator
		initialized = true;
	}
	
	private static String[] runProc(String exec) throws IOException
	{
//		ProcessBuilder pb = new ProcessBuilder(exec);
//		pb.redirectErrorStream(true);
//		Process proc = pb.start();
		Process proc = Runtime.getRuntime().exec(exec);
		BufferedReader br = new BufferedReader(new InputStreamReader(proc.getInputStream()));
		Queue<String> lines = new LinkedList<String>();
		String line;
		while ((line = br.readLine()) != null) {
			lines.add(line);
		}
		br.close();
		br = new BufferedReader(new InputStreamReader(proc.getErrorStream()));
		while ((line = br.readLine()) != null) {
			lines.add(line);
		}
		br.close();
		String[] toReturn = new String[lines.size()];
		int i=0;
		while(!lines.isEmpty()) {
			toReturn[i] = lines.remove();
			i++;
		}
		return toReturn;
	}
	
	public String[] xpaget(String template, String arguments) throws XpaError, IOException
	{
		String command = exec_dir + "xpaget '" + template + "' " + arguments;
		String[] xpaRet;
		xpaRet = Xpa.runProc(command);
		if (xpaRet.length==0) {
			throw new XpaError(command, "No response from XPA");
		}
		if (xpaRet.length==1) {
			if (xpaRet[0].startsWith("XPA$ERROR")) {
				throw new XpaError(command, xpaRet[0].substring(9));
			}
		}
		return xpaRet;
	}
	
	public String[] xpaset(String template, String arguments, boolean ignoreError) throws XpaError, IOException
	{
		String command = exec_dir + "xpaset -p '" + template + "' " + arguments;
		String[] xpaRet;
		xpaRet = Xpa.runProc(command);
		if (xpaRet.length==1 && (!ignoreError)) {
			if (xpaRet[0].startsWith("XPA$ERROR")) {
				throw new XpaError(command, xpaRet[0].substring(9));
			}
		}
		return xpaRet;
	}
//	def setup(doRaise=False, debug=False):
//	    """Search for xpa and ds9 and set globals accordingly.
//	    Return None if all is well, else return an error string.
//	    The return value is also saved in global variable _SetupError.
//	    
//	    Sets globals:
//	    - _SetupError   same value as returned
//	    - _Popen        subprocess.Popen, if ds9 and xpa found,
//	                    else a variant that searches for ds9 and xpa
//	                    first and then runs subprocess.Popen if found
//	                    else raises an exception
//	                    This permits the user to install ds9 and xpa
//	                    and use this module without reloading it
//	    """
//	    global _SetupError, _Popen
//	    _SetupError = None
//	    try:
//	        ds9Dir, xpaDir = _findDS9AndXPA()
//	        if debug:
//	            print "ds9Dir=%r\npaDir=%r" % (ds9Dir, xpaDir)
//	    except (SystemExit, KeyboardInterrupt):
//	        raise
//	    except Exception, e:
//	        _SetupError = "RO.DS9 unusable: %s" % (e,)
//	        ds9Dir = xpaDir = None
//	    
//	    if _SetupError:
//	        class _Popen(subprocess.Popen):
//	            def __init__(self, *args, **kargs):
//	                setup(doRaise=True)
//	                subprocess.Popen.__init__(self, *args, **kargs)
//	        
//	        if doRaise:
//	            raise RuntimeError(_SetupError)
//	    else:
//	        _Popen = subprocess.Popen
//	    return _SetupError
//
//
//	errStr = setup(doRaise=False, debug=False)
//	if errStr:
//	    warnings.warn(errStr)
//
//	_ArrayKeys = ("dim", "dims", "xdim", "ydim", "zdim", "bitpix", "skip", "arch")
//	_DefTemplate = "ds9"
//
//	_OpenCheckInterval = 0.2 # seconds
//	_MaxOpenTime = 10.0 # seconds
//

}
