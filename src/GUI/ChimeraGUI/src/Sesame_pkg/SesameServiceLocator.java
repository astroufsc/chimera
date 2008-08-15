/**
 * SesameServiceLocator.java
 *
 * This file was auto-generated from WSDL
 * by the Apache Axis 1.4 Apr 22, 2006 (06:55:48 PDT) WSDL2Java emitter.
 */

package Sesame_pkg;

public class SesameServiceLocator extends org.apache.axis.client.Service implements Sesame_pkg.SesameService {

    public SesameServiceLocator() {
    }


    public SesameServiceLocator(org.apache.axis.EngineConfiguration config) {
        super(config);
    }

    public SesameServiceLocator(java.lang.String wsdlLoc, javax.xml.namespace.QName sName) throws javax.xml.rpc.ServiceException {
        super(wsdlLoc, sName);
    }

    // Use to get a proxy class for Sesame
    private java.lang.String Sesame_address = "http://cdsws.u-strasbg.fr/axis/services/Sesame";

    public java.lang.String getSesameAddress() {
        return Sesame_address;
    }

    // The WSDD service name defaults to the port name.
    private java.lang.String SesameWSDDServiceName = "Sesame";

    public java.lang.String getSesameWSDDServiceName() {
        return SesameWSDDServiceName;
    }

    public void setSesameWSDDServiceName(java.lang.String name) {
        SesameWSDDServiceName = name;
    }

    public Sesame_pkg.Sesame getSesame() throws javax.xml.rpc.ServiceException {
       java.net.URL endpoint;
        try {
            endpoint = new java.net.URL(Sesame_address);
        }
        catch (java.net.MalformedURLException e) {
            throw new javax.xml.rpc.ServiceException(e);
        }
        return getSesame(endpoint);
    }

    public Sesame_pkg.Sesame getSesame(java.net.URL portAddress) throws javax.xml.rpc.ServiceException {
        try {
            Sesame_pkg.SesameSoapBindingStub _stub = new Sesame_pkg.SesameSoapBindingStub(portAddress, this);
            _stub.setPortName(getSesameWSDDServiceName());
            return _stub;
        }
        catch (org.apache.axis.AxisFault e) {
            return null;
        }
    }

    public void setSesameEndpointAddress(java.lang.String address) {
        Sesame_address = address;
    }

    /**
     * For the given interface, get the stub implementation.
     * If this service has no port for the given interface,
     * then ServiceException is thrown.
     */
    public java.rmi.Remote getPort(Class serviceEndpointInterface) throws javax.xml.rpc.ServiceException {
        try {
            if (Sesame_pkg.Sesame.class.isAssignableFrom(serviceEndpointInterface)) {
                Sesame_pkg.SesameSoapBindingStub _stub = new Sesame_pkg.SesameSoapBindingStub(new java.net.URL(Sesame_address), this);
                _stub.setPortName(getSesameWSDDServiceName());
                return _stub;
            }
        }
        catch (java.lang.Throwable t) {
            throw new javax.xml.rpc.ServiceException(t);
        }
        throw new javax.xml.rpc.ServiceException("There is no stub implementation for the interface:  " + (serviceEndpointInterface == null ? "null" : serviceEndpointInterface.getName()));
    }

    /**
     * For the given interface, get the stub implementation.
     * If this service has no port for the given interface,
     * then ServiceException is thrown.
     */
    public java.rmi.Remote getPort(javax.xml.namespace.QName portName, Class serviceEndpointInterface) throws javax.xml.rpc.ServiceException {
        if (portName == null) {
            return getPort(serviceEndpointInterface);
        }
        java.lang.String inputPortName = portName.getLocalPart();
        if ("Sesame".equals(inputPortName)) {
            return getSesame();
        }
        else  {
            java.rmi.Remote _stub = getPort(serviceEndpointInterface);
            ((org.apache.axis.client.Stub) _stub).setPortName(portName);
            return _stub;
        }
    }

    public javax.xml.namespace.QName getServiceName() {
        return new javax.xml.namespace.QName("urn:Sesame", "SesameService");
    }

    private java.util.HashSet ports = null;

    public java.util.Iterator getPorts() {
        if (ports == null) {
            ports = new java.util.HashSet();
            ports.add(new javax.xml.namespace.QName("urn:Sesame", "Sesame"));
        }
        return ports.iterator();
    }

    /**
    * Set the endpoint address for the specified port name.
    */
    public void setEndpointAddress(java.lang.String portName, java.lang.String address) throws javax.xml.rpc.ServiceException {
        
if ("Sesame".equals(portName)) {
            setSesameEndpointAddress(address);
        }
        else 
{ // Unknown Port Name
            throw new javax.xml.rpc.ServiceException(" Cannot set Endpoint Address for Unknown Port" + portName);
        }
    }

    /**
    * Set the endpoint address for the specified port name.
    */
    public void setEndpointAddress(javax.xml.namespace.QName portName, java.lang.String address) throws javax.xml.rpc.ServiceException {
        setEndpointAddress(portName.getLocalPart(), address);
    }

}
