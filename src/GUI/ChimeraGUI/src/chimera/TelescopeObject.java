/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package chimera;

import java.util.Vector;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;

/**
 *
 * @author Denis
 */
public class TelescopeObject
{

    private XmlRpcClient myManager;
    private String myName;

    public TelescopeObject( XmlRpcClient manager, String telescopeName )
    {
        this.myManager = manager;
        this.myName = telescopeName;

        initComponents();

    }

    private void initComponents()
    {

    }

//        """Slew the scope to the the coordinates of the given
//        object. Object name will be converted to a coordinate using a
//        resolver like SIMBAD or NED.
//
//        @param name: Object name to slew to.
//        @type  name: str
//
//        @returns: Nothing.
//        @rtype: None
//        """
    private void slewToObject( String name )
    {// @todo
    }

//        """Slew the scope to the given equatorial coordinates.
//
//        @param position: the equatorial coordinates to slew to. It can
//        be given as a Position object or as a tuple with arguments to
//        Position.fromRaDec factory.
//        
//        @type position: L{Position} or tuple
//        
//        @returns: Nothing.
//        @rtype: None
//        """
    public void slewToRaDec( String RA, String DEC, String EPOCH ) throws XmlRpcException
    {
        Vector<Object> vec = new Vector<Object>();
        vec.add(new String( RA ));
        vec.add(new String( DEC ));
        vec.add(new String( EPOCH ));


        Object[] position = new Object[]{vec};
//            Object[] result;
//            result = (Object[])myManager.execute( myName + ".slewToRaDec", position );
        myManager.execute( myName + ".slewToRaDec", position );

    }

//        """Slew the scope to the given local coordinates.
//
//        @param position: the local coordinates to slew to. It can be
//        given as a Position object or as a tuple with arguments to
//        Position.fromAltAz factory.
//        
//        @type position: L{Position} or tuple
//        
//        @returns: Nothing.
//        @rtype: None
//        """
    private void slewToAltAz( String position )
    {// @todo
    }

//        """Try to abort the current slew.
//
//        @return: Nothing.
//        @rtype: None
//        """
    private void abortSlew()
    {// @todo
    }

//        """Ask if the telescope is slewing right now.
//
//        @return: True if the telescope is slewing, False otherwise.
//        @rtype: bool
//        """
    public boolean isSlewing()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.parseBoolean( myManager.execute( myName + ".isSlewing", obj ).toString() );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

//        """Move the scope I{offset} arcseconds East (if offset positive, West otherwise)
//
//        @param offset: Arcseconds to move East.
//        @type  offset: int or float
//
//        @param rate: Slew rate to be used when moving.
//        @type  rate: L{SlewRate}
//
//        @return: Nothing.
//        @rtype: None
//
//        @note: float accepted only to make life easier, probably we can't handle such precision.
//        """
    public void moveEast( double offset)
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(new Double( offset ));
            
            Object[] obj = new Object[]{vec};
            myManager.execute( myName + ".moveEast", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
        }
    }

//        """Move the scope I{offset} arcseconds West (if offset positive, East otherwise)
//
//        @param offset: Arcseconds to move West.
//        @type  offset: int or float
//
//        @param rate: Slew rate to be used when moving.
//        @type  rate: L{SlewRate}
//
//        @return: Nothing.
//        @rtype: None
//
//        @note: float accepted only to make life easier, probably we can't handle such precision.
//        """
    public void moveWest( double offset)
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(new Double( offset ));
            
            Object[] obj = new Object[]{vec};
            myManager.execute( myName + ".moveWest", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
        }
    }

//        """Move the scope I{offset} arcseconds North (if offset positive, South otherwise)
//
//        @param offset: Arcseconds to move North.
//        @type  offset: int or float
//
//        @param rate: Slew rate to be used when moving.
//        @type  rate: L{SlewRate}
//
//        @return: Nothing.
//        @rtype: None
//
//        @note: float accepted only to make life easier, probably we can't handle such precision.
//        """
    public void moveNorth( double offset )
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(new Double( offset ));
            
            Object[] obj = new Object[]{vec};
            myManager.execute( myName + ".moveNorth", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
        }
    }

//        """Move the scope {offset} arcseconds South (if offset positive, North otherwise)
//
//        @param offset: Arcseconds to move South.
//        @type  offset: int or float
//
//        @param rate: Slew rate to be used when moving.
//        @type  rate: L{SlewRate}
//
//        @return: Nothing.
//        @rtype: None
//
//        @note: float accepted only to make life easier, probably we can't handle such precision.
//        """
    public void moveSouth( double offset)
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(new Double( offset ));
            
            Object[] obj = new Object[]{vec};
            myManager.execute( myName + ".moveSouth", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
        }
    }

//        """Get the current telescope Right Ascension.
//
//        @return: Telescope's current Right Ascension.
//        @rtype: L{Coord}
//        """
    public String getRa()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getRa", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return getRa();
        }

    }

//        """Get the current telescope Declination.
//
//        @return: Telescope's current Declination.
//        @rtype: L{Coord}
//        """
    public String getDec()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getDec", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return getDec();
        }

    }

//        """Get the current telescope Azimuth.
//
//        @return: Telescope's current Azimuth.
//        @rtype: L{Coord}
//        """
    public String getAz()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getAz", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return getAz();
        }

    }

    //        """Get the current telescope Altitude.
    //
    //        @return: Telescope's current Alt
    //        @rtype: L{Coord}
    //        """
    public String getAlt()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getAlt", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return getAlt();
        }

    }
    
    public String getHA()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getHa", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return getHA();
        }

    }

//        """Get the current position of the telescope in equatorial coordinates.
//
//        @return: Telescope's current position (ra, dec).
//        @rtype: L{Position}
//        """
    private void getPositionRaDec()
    {// @todo
    }

//        """Get the current position of the telescope in local coordinates.
//
//        @return: Telescope's current position (az, alt).
//        @rtype: L{Position}
//        """
    private void getPositionAltAz()
    {// @todo
    }

//        """Get the current telescope target in equatorial coordinates.
//
//        @return: Telescope's current target (ra, dec).
//        @rtype: L{Position}
//        """
    private void getTargetRaDec()
    {// @todo
    }

//        """Get the current telescope target in local coordinates.
//
//        @return: Telescope's current target (az, alt).
//        @rtype: L{Position}
//        """
    private void getTargetAltAz()
    {// @todo
    }

//        """Synchronize the telescope using the coordinates of the
//        given object.
//        
//        @param name: Object name to sync in.
//        @type  name: str
//        """
    private void syncObject( String name )
    {// @todo
    }

//        """Synchronizes the telescope on the given equatorial
//        coordinates.
//
//        This mean different things to different telescopes, but the
//        general idea is that after this command, the logical position
//        that the telescope will return when asked about will be equal
//        to the given position.
//
//        @param position: coordinates to sync on as a Position or a
//        tuple with arguments to Position.fromRaDec.
//        
//        @type  position: L{Position} or tuple
//
//        @returns: Nothing
//        @rtype: None
//        """
    private void syncRaDec( String position )
    {// @todo
    }

//        """Synchronizes the telescope on the given local coordinates.
//
//        See L{syncRaDec} for more information.
//
//        @param position: coordinates to sync on as a Position or a
//        tuple with arguments to Position.fromAltAz.
//        
//        @type  position: L{Position} or tuple
//
//        @returns: Nothing
//        @rtype: None
//        """
    private void syncAltAz( String position )
    {// @todo
    }

//        """Park the telescope on the actual saved park position
//        (L{setParkPosition}) or on the private voidault position if none
//        setted.
//
//        When parked, the telescope will not track objects and may be
//        turned off (if the scope was able to).
//
//        @return: Nothing.
//        @rtype: None
//        """
    private void park()
    {
        try
        {
            Object[] obj = new Object[]{};
            myManager.execute( myName + ".park", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
//            return "BAD DATA";
        }
    }

//        """Wake up the telescope of the last park operation.
//        
//        @return: Nothing.
//        @rtype: None
//        """
    private void unpark()
    {// @todo
    }

//        """Ask if the telescope is at park position.
//
//        @return: True if the telescope is parked, False otherwise.
//        @rtype: bool
//        """
    private boolean isParked()
    {// @todo
        return false;
    }

//        """private voidines where the scope will park when asked to.
//
//        @param position: local coordinates to aprk the scope
//        @type  position: L{Position}
//
//        @return: Nothing.
//        @rtype: None
//        """
    private void setParkPosition( String position )
    {// @todo
    }

//        """
//        Start telescope tracking.
//
//        @return: Nothing
//        @rtype: None
//        """
    private void startTracking()
    {// @todo
    }

//        """
//        Stop telescope tracking.
//
//        @return: Nothing
//        @rtype: None
//        """
    private void stopTracking()
    {// @todo
    }

//        """
//        Ask if the telescope is tracking.
//
//        @return: True if the telescope is tracking, False otherwise.
//        @rtype: bool
//        
//        """
    private boolean isTracking()
    {// @todo
        return false;
    }
}
