/*
 * Copyright (c) 2004 NNL Technology AB
 * All rights reserved.
 *
 * "Work" shall mean the contents of this file.
 *
 * Redistribution, copying and use of the Work, with or without
 * modification, is permitted without restrictions.
 *
 * Visit www.infonode.net for information about InfoNode(R)
 * products and how to contact NNL Technology AB.
 *
 * THE WORK IS PROVIDED BY THE COPYRIGHT HOLDERS AND
 * CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
 * IN ANY WAY OUT OF THE USE OF THE WORK, EVEN IF ADVISED OF
 * THE POSSIBILITY OF SUCH DAMAGE.
 */// $Id: DockingWindowsExample.java,v 1.28 2007/01/28 21:25:10 jesper Exp $
package chimera;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.swing.Icon;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.SwingUtilities;

import net.infonode.docking.DockingWindow;
import net.infonode.docking.DockingWindowAdapter;
import net.infonode.docking.FloatingWindow;
import net.infonode.docking.OperationAbortedException;
import net.infonode.docking.RootWindow;
import net.infonode.docking.View;
import net.infonode.docking.mouse.DockingWindowActionMouseButtonListener;
import net.infonode.docking.properties.RootWindowProperties;
import net.infonode.docking.theme.DockingWindowsTheme;
import net.infonode.docking.theme.ShapedGradientDockingTheme;
import net.infonode.docking.util.DockingUtil;
import net.infonode.docking.util.ViewMap;
import net.infonode.util.Direction;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.server.PropertyHandlerMapping;
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.server.XmlRpcServerConfigImpl;
import org.apache.xmlrpc.webserver.WebServer;


/**
 * DockingWindowCH
 * @author $Author: jesper $
 * @version $Revision: 1.28 $
 * 
 * Modified by:
 * @author  Ryan rmann@oswego.edu
 * @author  Denis dbarrett@oswego.edu
 * TO ADD NEW PANELS, ONLY THE SECTION createRootWindow() NEEDS TO BE MODIFIED
 */ 
public class DockingWindowCH
{

    /**
     * event server class to listen for events form server
     * NOT IMPLEMENTED YET
     */
    class eventServer
    {

        public eventServer()
        {
            //do nothing default constructor
        }

        public boolean displayMessage(String str)
        {
            System.out.println(str);
            return true;
        }

        public boolean updateGUI(boolean bl)
        {
            if (bl)
            {
            }
            else
            {
            }
            return true;
        }
    }
    
    
    
    private static final int ICON_SIZE = 8;
    /**
     * Custom view icon.
     */
    private static final Icon VIEW_ICON = new Icon()
    {

        public int getIconHeight()
        {
            return ICON_SIZE;
        }

        public int getIconWidth()
        {
            return ICON_SIZE;
        }

        public void paintIcon(Component c, Graphics g, int x, int y)
        {
            Color oldColor = g.getColor();
            g.setColor(new Color(0, 192, 0));
            g.fill3DRect(x, y, ICON_SIZE, ICON_SIZE, true);
            g.setColor(oldColor);
        }
    };
    /**
     * The one and only root window
     */
    private RootWindow rootWindow;
    /**
     * An array of the static views
     */
    private ArrayList<View> views = new ArrayList<View>();
    /**
     * Contains all the static views
     */
    private ViewMap viewMap = new ViewMap();
    /**
     * The view menu items
     */
    private ArrayList<JMenuItem> viewItems = new ArrayList<JMenuItem>();
    /**
     * Contains the dynamic views that has been added to the root window
     */
    private DockingWindowsTheme currentTheme = new ShapedGradientDockingTheme();
    /**
     * In this properties object the modified property values for close buttons etc. are stored. This object is cleared
     * when the theme is changed.
     */
    private RootWindowProperties properties = new RootWindowProperties();
    /**
     * Where the layouts are stored.
     */
    private byte[][] layouts = new byte[3][];
    /**
     * The application frame
     */
    private JFrame frame = new JFrame("Chimera");
    /**
     * xml rpc client
     */
    XmlRpcClient client = null;
    /**
     * String of the host address.
     */
    String clientURL = "";

    /**
     * Default constructor to create and launch the main GUI
     * @param client
     * @param clientURL
     */
    public DockingWindowCH(XmlRpcClient client, String clientURL)
    {
        try
        {
            //set the global values passed from login GUI
            this.client = client;
            this.clientURL = clientURL;

            //setup methods for GUI and controls
            createRootWindow();
            showFrame();

            //Webserver for incoming events
            //NOT IMPLEMENTED YET
            WebServer webServer = new WebServer(7668);
            XmlRpcServer xmlRpcServer = webServer.getXmlRpcServer();

            PropertyHandlerMapping phm = new PropertyHandlerMapping();
            phm.addHandler("Chimera", eventServer.class);
            xmlRpcServer.setHandlerMapping(phm);

            XmlRpcServerConfigImpl serverConfig = (XmlRpcServerConfigImpl) xmlRpcServer.getConfig();
            serverConfig.setEnabledForExtensions(true);
            serverConfig.setContentLengthOptional(false);

            webServer.start();
            // end of webserver
        }
        catch (IOException ex)
        {
            Logger.getLogger(DockingWindowCH.class.getName()).log(Level.SEVERE, null, ex);
        }
        catch (XmlRpcException ex)
        {
            Logger.getLogger(DockingWindowCH.class.getName()).log(Level.SEVERE, null, ex);
        }

    }

    /**
     * Creates the root window and the views.
     */
    private void createRootWindow()
    {
        /**
         * This is the most important part of this code.  Here is where you load
         * all of the Panels into the main tab form.  Each one is creates dynamically
         * form the list gathered from the server.  Chimera reports the objects
         * that are running on the server.  
         * THIS SHOULD BE THE ONLY PLACE YOU NEED TO ADD CODE.  EVERYTHING ELSE
         * IS DONE FOR YOU. IF A NEW DEVICE NEEDS TO BE ADDED JUST DUPLICATE
         * A SECTION OF THE CODE BELOW WITH THE NEW DEVICE NAME.
         */
        try
        {
            //initialize the position for all tabs created
            int position = 0;

            //initialize the array for cameras
            Object[] camobj = new Object[]
            {
                new String("Camera")
            };

            //get the list of all cameras and create a tab for each
            Object[] cameras = (Object[]) client.execute("Chimera.getListOf", camobj);

            //dynamically create the tabs for how many objects exist
            for (int i = 0; i < cameras.length; i++)
            {
                //add the current panel to the array for display
                views.add(new View("Camera: " + cameras[i], VIEW_ICON, 
                        new JScrollPane(new CameraControl(client, cameras[i].toString(), clientURL))));
                viewMap.addView(position, views.get(views.size() - 1));
                //increment position of tab, CANNOT USE SAME NUMBER TWICE
                position++;
            }


            //initialize the array for focusers
            Object[] focobj = new Object[]
            {
                new String("Focuser")
            };

            //get the list of all cameras and create a tab for each
            Object[] focusers = (Object[]) client.execute("Chimera.getListOf", focobj);

            //dynamically create the tabs for how many objects exist
            for (int i = 0; i < focusers.length; i++)
            {
                //add the current panel to the array for display
                views.add(new View("Focuser: " + focusers[i], VIEW_ICON, 
                        new JScrollPane(new FocusControl(client, focusers[i].toString()))));
                viewMap.addView(position, views.get(views.size() - 1));
                //increment position of tab, CANNOT USE SAME NUMBER TWICE
                position++;
            }

            //initialize the array for telescopes
            Object[] telobj = new Object[]
            {
                new String("Telescope")
            };

            //get the list of all cameras and create a tab for each
            Object[] telescopes = (Object[]) client.execute("Chimera.getListOf", telobj);

            //dynamically create the tabs for how many objects exist
            for (int i = 0; i < telescopes.length; i++)
            {
                //add the current panel to the array for display
                views.add(new View("Telescope: " + telescopes[i], VIEW_ICON, 
                        new JScrollPane(new TelescopeControl(client, telescopes[i].toString()))));
                viewMap.addView(position, views.get(views.size() - 1));
                //increment position of tab, CANNOT USE SAME NUMBER TWICE
                position++;
            }
        }
        catch (XmlRpcException ex)
        {
            Logger.getLogger(CameraControl.class.getName()).log(Level.SEVERE, null, ex);
        }
        /**
         * END OF TAB LOADING SECTION 
         */
        rootWindow = DockingUtil.createRootWindow(viewMap, true);

        // Set gradient theme. The theme properties object is the super object of our properties object, which
        // means our property value settings will override the theme values
        properties.addSuperObject(currentTheme.getRootWindowProperties());

        // Our properties object is the super object of the root window properties object, so all property values of the
        // theme and in our property object will be used by the root window
        rootWindow.getRootWindowProperties().addSuperObject(properties);

        // Enable the bottom window bar
        rootWindow.getWindowBar(Direction.DOWN).setEnabled(true);

        // Add a listener which shows dialogs when a window is closing or closed.
        rootWindow.addListener(new DockingWindowAdapter()
        {

            public void windowAdded(DockingWindow addedToWindow, DockingWindow addedWindow)
            {
                updateViews(addedWindow, true);

                // If the added window is a floating window, then update it
                if (addedWindow instanceof FloatingWindow)
                {
                    updateFloatingWindow((FloatingWindow) addedWindow);
                }
            }

            public void windowRemoved(DockingWindow removedFromWindow, DockingWindow removedWindow)
            {
                updateViews(removedWindow, false);
            }

            public void windowClosing(DockingWindow window) throws OperationAbortedException
            {
                // Confirm close operation
                if (JOptionPane.showConfirmDialog(frame, "Close window '" + window + "'?") != JOptionPane.YES_OPTION)
                {
                    throw new OperationAbortedException("Window close was aborted!");
                }
            }

            public void windowDocking(DockingWindow window) throws OperationAbortedException
            {
                // Confirm dock operation
                if (JOptionPane.showConfirmDialog(frame, "Dock window '" + window + "'?") != JOptionPane.YES_OPTION)
                {
                    throw new OperationAbortedException("Window dock was aborted!");
                }
            }

            public void windowUndocking(DockingWindow window) throws OperationAbortedException
            {
                // Confirm undock operation 
                if (JOptionPane.showConfirmDialog(frame, "Undock window '" + window + "'?") != JOptionPane.YES_OPTION)
                {
                    throw new OperationAbortedException("Window undock was aborted!");
                }
            }
        });

        // Add a mouse button listener that closes a window when it's clicked with the middle mouse button.
        rootWindow.addTabMouseButtonListener(DockingWindowActionMouseButtonListener.MIDDLE_BUTTON_CLOSE_LISTENER);
    }

    /**
     * Update view menu items and dynamic view map.
     *
     * @param window the window in which to search for views
     * @param added  if true the window was added
     */
    private void updateViews(DockingWindow window, boolean added)
    {
        if (window instanceof View)
        {

            for (int i = 0; i < views.size(); i++)
            {
                if (views.get(i) == window && viewItems.get(i) != null)
                {
                    viewItems.get(i).setEnabled(!added);
                }
            }

        }
        else
        {
            for (int i = 0; i < window.getChildWindowCount(); i++)
            {
                updateViews(window.getChildWindow(i), added);
            }
        }
    }

    /**
     * Initializes the frame and shows it.
     */
    private void showFrame()
    {
        frame.getContentPane().add(rootWindow, BorderLayout.CENTER);
        frame.setJMenuBar(createMenuBar());
        frame.setSize(800, 600);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setVisible(true);
        frame.setLocationRelativeTo(null);
    }

    /**
     * Creates the frame menu bar.
     *
     * @return the menu bar
     */
    private JMenuBar createMenuBar()
    {
        JMenuBar menu = new JMenuBar();
        menu.add(createLayoutMenu());
        menu.add(createFocusViewMenu());
        menu.add(createPropertiesMenu());
        menu.add(createViewMenu());
        return menu;
    }

    /**
     * Creates the menu where layout can be saved/loaded and a frame shown with
     * Java pseudo-like code over the current layout in the root window.
     *
     * @return the layout menu
     */
    private JMenu createLayoutMenu()
    {
        JMenu layoutMenu = new JMenu("Layout");

        for (int i = 0; i < layouts.length; i++)
        {
            final int j = i;
            layoutMenu.add("Save Layout " + i).addActionListener(new ActionListener()
            {

                public void actionPerformed(ActionEvent e)
                {
                    try
                    {
                        // Save the layout in a byte array
                        ByteArrayOutputStream bos = new ByteArrayOutputStream();
                        ObjectOutputStream out = new ObjectOutputStream(bos);
                        rootWindow.write(out, false);
                        out.close();
                        layouts[j] = bos.toByteArray();
                    }
                    catch (IOException e1)
                    {
                        throw new RuntimeException(e1);
                    }
                }
            });
        }
        layoutMenu.addSeparator();
        for (int i = 0; i < layouts.length; i++)
        {
            final int j = i;
            layoutMenu.add("Load Layout " + j).addActionListener(new ActionListener()
            {

                public void actionPerformed(ActionEvent e)
                {
                    SwingUtilities.invokeLater(new Runnable()
                    {

                        public void run()
                        {
                            if (layouts[j] != null)
                            {
                                try
                                {
                                    // Load the layout from a byte array
                                    ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(layouts[j]));
                                    rootWindow.read(in, true);
                                    in.close();
                                }
                                catch (IOException e1)
                                {
                                    throw new RuntimeException(e1);
                                }
                            }
                        }
                    });
                }
            });
        }
        layoutMenu.addSeparator();
        return layoutMenu;
    }

    /**
     * Creates the menu where views can be shown and focused.
     *
     * @return the focus view menu
     */
    private JMenu createFocusViewMenu()
    {
        JMenu viewsMenu = new JMenu("View Window");

        for (int i = 0; i < views.size(); i++)
        {
            final View view = views.get(i);
            viewsMenu.add("Window " + view.getTitle()).addActionListener(new ActionListener()
            {

                public void actionPerformed(ActionEvent e)
                {
                    SwingUtilities.invokeLater(new Runnable()
                    {

                        public void run()
                        {
                            // Ensure the view is shown in the root window
                            DockingUtil.addWindow(view, rootWindow);

                            // Transfer focus to the view
                            view.restoreFocus();
                        }
                    });
                }
            });
        }
        return viewsMenu;
    }

    /**
     * Creates the menu where different property values can be modified.
     *
     * @return the properties menu
     */
    private JMenu createPropertiesMenu()
    {
        JMenu buttonsMenu = new JMenu("Properties");

        buttonsMenu.add("Enable Close").addActionListener(new ActionListener()
        {

            public void actionPerformed(ActionEvent e)
            {
                properties.getDockingWindowProperties().setCloseEnabled(true);
            }
        });

        buttonsMenu.add("Hide Close Buttons").addActionListener(new ActionListener()
        {

            public void actionPerformed(ActionEvent e)
            {
                properties.getDockingWindowProperties().setCloseEnabled(false);
            }
        });

        buttonsMenu.add("Freeze Layout").addActionListener(new ActionListener()
        {

            public void actionPerformed(ActionEvent e)
            {
                freezeLayout(true);
            }
        });

        buttonsMenu.add("Unfreeze Layout").addActionListener(new ActionListener()
        {

            public void actionPerformed(ActionEvent e)
            {
                freezeLayout(false);
            }
        });

        return buttonsMenu;
    }

    /**
     * Freezes or unfreezes the window layout and window operations.
     *
     * @param freeze true for freeze, otherwise false
     */
    private void freezeLayout(boolean freeze)
    {
        // Freeze window operations
        properties.getDockingWindowProperties().setDragEnabled(!freeze);
        properties.getDockingWindowProperties().setCloseEnabled(!freeze);
        properties.getDockingWindowProperties().setMinimizeEnabled(!freeze);
        properties.getDockingWindowProperties().setRestoreEnabled(!freeze);
        properties.getDockingWindowProperties().setMaximizeEnabled(!freeze);
        properties.getDockingWindowProperties().setUndockEnabled(!freeze);
        properties.getDockingWindowProperties().setDockEnabled(!freeze);

        // Freeze tab reordering inside tabbed panel
        properties.getTabWindowProperties().getTabbedPanelProperties().setTabReorderEnabled(!freeze);
    }

    /**
     * Creates the menu where not shown views can be shown.
     *
     * @return the view menu
     */
    private JMenu createViewMenu()
    {
        JMenu menu = new JMenu("Views");
        for (int i = 0; i < views.size(); i++)
        {
            final View view = views.get(i);
            viewItems.add(new JMenuItem(view.getTitle()));
            viewItems.get(i).setEnabled(views.get(i).getRootWindow() == null);
            menu.add(viewItems.get(i)).addActionListener(new ActionListener()
            {

                public void actionPerformed(ActionEvent e)
                {
                    if (view.getRootWindow() != null)
                    {
                        view.restoreFocus();
                    }
                    else
                    {
                        DockingUtil.addWindow(view, rootWindow);
                    }
                }
            });
        }
        return menu;
    }

    /**
     * Update the floating window by adding a menu bar and a status label if menu option is choosen.
     *
     * @param fw the floating window
     */
    private void updateFloatingWindow(FloatingWindow fw)
    {
        // Create and add a status label
        JLabel statusLabel = new JLabel("Undocked window! Drag back into main form to redock.");

        // Add it as the SOUTH component to the root pane's content pane. Note that the actual floating
        // window is placed in the CENTER position and must not be removed.
        fw.getRootPane().getContentPane().add(statusLabel, BorderLayout.SOUTH);

    }
}
