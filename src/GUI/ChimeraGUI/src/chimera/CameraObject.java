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
public class CameraObject
{

    private XmlRpcClient myManager;
    private String myName;


    public CameraObject( XmlRpcClient manager, String cameraName )
    {
        this.myManager = manager;
        this.myName = cameraName;

        initComponents();

    }

    private void initComponents()
    {

    }

    private String[] expose( double exp_time, int frames, double interval,
                             String shutter, String binning, String window,
                             String filename )
    {
        

        return null;
    }

    public boolean abortExposure( boolean readout )
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(new Boolean(readout));
            Object[] obj = new Object[]{vec};
            return Boolean.valueOf(myManager.execute( myName + ".abortExposure", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }

    }

    public boolean isExposing()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".isExposing", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public boolean startCooling()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".startCooling", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public boolean stopCooling()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".stopCooling", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public boolean isCooling()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".isCooling", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public boolean setTemperature( double tempC )
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(tempC);
            Object[] obj = new Object[]{vec};
            return Boolean.valueOf(myManager.execute( myName + ".setTemperature", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public double getTemperature()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Double.parseDouble(myManager.execute( myName + ".isFanning", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return Double.NaN;
        }
    }

    public double getSetpoint()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Double.parseDouble(myManager.execute( myName + ".isFanning", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return Double.NaN;
        }
    }

    public boolean startFan()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".startFan", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public boolean stopFan()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".stopFan", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public boolean isFanning()
    {
        try
        {
            Object[] obj = new Object[]{};
            return Boolean.valueOf(myManager.execute( myName + ".isFanning", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }

    public Object getCCDs()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getCCDs", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
}

    public Object getCurrentCCD()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getCurrentCCD", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
    }

    public Object getBinnings()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getBinnings", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
    }

    public Object getADCs()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getADCs", obj );
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
    }

    public String getPhysicalSize()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getPhysicalSize", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
    }

    public String getPixelSize()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getPixelSize", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
    }

    public String getOverscanSize()
    {
        try
        {
            Object[] obj = new Object[]{};
            return myManager.execute( myName + ".getOverscanSize", obj ).toString();
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return "BAD DATA";
        }
    }

    private boolean supports(String feature)
    {
        try
        {
            Vector<Object> vec = new Vector<Object>();
            vec.add(new String(feature));
            Object[] obj = new Object[]{vec};
            return Boolean.valueOf(myManager.execute( myName + ".supports", obj ).toString());
        }
        catch ( XmlRpcException ex )
        {
            System.err.println( ex.toString() );
            return false;
        }
    }
}
