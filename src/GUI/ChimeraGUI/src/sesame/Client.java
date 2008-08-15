package sesame;

import java.rmi.RemoteException;

import javax.xml.rpc.ServiceException;

import Sesame_pkg.*;
import sesame.Position;

public class Client {
	
	public static Position resolveObject(String name) throws ServiceException, RemoteException {
		SesameServiceLocator loc = new SesameServiceLocator();
		Sesame ses = loc.getSesame();
		String result = ses.sesame(name, "x");
		int first = result.indexOf("<jpos>");
		if (first == -1) {
			throw new RuntimeException("Invalid response -- perhaps that isn\'t an object.");
		}
		String[] pos = result.substring(first + 6, result.indexOf("</jpos>")).split(" ");
		if (pos.length != 2) {
			throw new RuntimeException("I didn't understand the position returned.");
		}
		Position toRet = new Position();
		String[] ra = pos[0].split(":");
		String[] dec = pos[1].split(":");
		toRet.raH = Integer.parseInt(ra[0]);
		toRet.raM = Integer.parseInt(ra[1]);
		toRet.raS = Float.parseFloat(ra[2]);
		toRet.decD = Integer.parseInt(dec[0].replace("+",""));
		toRet.decM = Integer.parseInt(dec[1]);
		toRet.decS = Float.parseFloat(dec[2]);
		return toRet;
		
	}
	
	  public Client() {

		    try {

		      // locator creation
		      SesameService locator = new SesameServiceLocator();

		      // Sesame object
		      Sesame myv = locator.getSesame();

		      // resolves the name for m31 and XML result format
		      String result = myv.sesame("m31", "x");
		      
		      System.out.println(result);
		    }
		    catch (Exception e ) {System.out.println("Sesame XML WS client : " + e);}
		  }

	  
	  public static void main(String[] args) {
		  Client c = new Client();
		  return;
	  }
}
