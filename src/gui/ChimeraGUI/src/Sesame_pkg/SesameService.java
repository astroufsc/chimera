/**
 * SesameService.java
 *
 * This file was auto-generated from WSDL
 * by the Apache Axis 1.4 Apr 22, 2006 (06:55:48 PDT) WSDL2Java emitter.
 */

package Sesame_pkg;

public interface SesameService extends javax.xml.rpc.Service {
    public java.lang.String getSesameAddress();

    public Sesame_pkg.Sesame getSesame() throws javax.xml.rpc.ServiceException;

    public Sesame_pkg.Sesame getSesame(java.net.URL portAddress) throws javax.xml.rpc.ServiceException;
}
