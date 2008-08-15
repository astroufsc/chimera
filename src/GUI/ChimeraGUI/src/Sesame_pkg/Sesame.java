/**
 * Sesame.java
 *
 * This file was auto-generated from WSDL
 * by the Apache Axis 1.4 Apr 22, 2006 (06:55:48 PDT) WSDL2Java emitter.
 */

package Sesame_pkg;

public interface Sesame extends java.rmi.Remote {
    public java.lang.String sesame(java.lang.String name, java.lang.String resultType) throws java.rmi.RemoteException;
    public java.lang.String sesame(java.lang.String name, java.lang.String resultType, boolean all) throws java.rmi.RemoteException;
    public java.lang.String sesame(java.lang.String name, java.lang.String resultType, boolean all, java.lang.String service) throws java.rmi.RemoteException;
    public java.lang.String sesameXML(java.lang.String name) throws java.rmi.RemoteException;
    public java.lang.String sesame(java.lang.String name) throws java.rmi.RemoteException;
    public java.lang.String getAvailability() throws java.rmi.RemoteException;
}
