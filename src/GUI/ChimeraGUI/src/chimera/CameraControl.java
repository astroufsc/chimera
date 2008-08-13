/*
 * CameraControl.java
 *
 * Created on July 22, 2008, 6:46 PM
 */
package chimera;

import java.awt.Dimension;
import java.awt.GridLayout;
import java.awt.Point;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.io.File;
import java.io.IOException;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.StringTokenizer;
import java.util.Vector;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JRadioButton;
import javax.swing.JToggleButton;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;

/**
 *
 * @author  Denis
 */
public class CameraControl extends javax.swing.JInternalFrame
{

    boolean DEBUG = false;
    // used to show to sig figs for doubles
    NumberFormat myFormat = NumberFormat.getInstance();
    double maxCCDwidth;
    double maxCCDheight;
    double CCDratio = 1.0;
    double selectedCCDwidth;
    double selectedCCDheight;
    Point CCDselectedPoint;
    Vector<String> subframeVector;
    Vector<String> binVector;
    Vector<String> filterVector;
    int subframeIndex;
    JFrame subframeFrame;
    JFrame binFrame;
    JFrame filterFrame;
    JFrame optionsFrame;
    /**
     * xml rpc client
     */
    XmlRpcClient client = null;
    String cameraName = "";
    String clientURL = "";
    
    CameraObject myCamera;

    /** Creates new form CameraControl */
    public CameraControl(XmlRpcClient client, String cameraName, String clientURL)
    {

        this.client = client;
        this.cameraName = cameraName;
        this.clientURL = clientURL;
        
        myCamera = new CameraObject(client, cameraName);

        if (myFormat instanceof DecimalFormat)
        {
            ((DecimalFormat) myFormat).setDecimalSeparatorAlwaysShown(true);
            ((DecimalFormat) myFormat).applyPattern("0.00");
        } // end if ( myFormat instanceof DecimalFormat )
        getCCDinfo();
        fillVectors();

        initComponents();

        createFrames();
        updateFields();

    }

    private void AbortImage()
    {
        try
        {
            Object[] obj = new Object[]{};

            Object[] result = (Object[]) client.execute(cameraName + ".expose", obj);
            
            System.out.println("Abort "+result[0].getClass());
            System.out.println("Abort "+result[0].toString());
            Debug("AbortImage() - Not yet implemented");
        }
        catch (XmlRpcException ex)
        {
            Logger.getLogger(CameraControl.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

    private void TakeIamge()
    {
        
       
            AbortEnabled();
            this.paintImmediately(this.getBounds());
            updateFields();

            SwingUtilities.invokeLater(new Runnable()
            {

                public void run()
                {
                    try
                    {
                        HashMap hs = new HashMap();
                        hs.put("exp_time", new Double(SecondsSpinner.getValue().toString()));
                        hs.put("frames", new Integer(SeriesSpinner.getValue().toString()));
                        hs.put("interval", new Double(0.0));
                        hs.put("shutter", new String("OPEN"));
                        hs.put("binning", new String("_" + BinTextField.getText().toUpperCase()));
                        hs.put("window", SubframeTextField.getText().replace(" ", "_").toUpperCase());
                        hs.put("filename", new String("$DATE-$TIME"));

                        Object[] obj = new Object[]
                        {
                            hs
                        };

                        Object[] result = (Object[]) client.execute(cameraName + ".expose", obj);

//            HashMap largeHash = (HashMap) result[0];
//            HashMap smallhash = (HashMap) largeHash.get("_config");
//            String hash = (String) smallhash.get("hash");

                        String linuxDir = "ds9 -url ";
                        String localdir = System.getProperty("user.dir") 
                                + System.getProperty("file.separator")
                                + "ds9 -url ";
                        String fullList = "";
                        for (int i = 0; i < result.length; i++)
                        {
                            fullList += "http://" + clientURL + ":7669/image/" + result[i].toString() + " ";
                        }
                        Runtime rt = Runtime.getRuntime();
                        rt.exec(linuxDir + fullList);
                    }
                    catch (IOException ex)
                    {
                        Logger.getLogger(CameraControl.class.getName()).log(Level.SEVERE, null, ex);
                    }
                    catch (XmlRpcException ex)
                    {
                        Logger.getLogger(CameraControl.class.getName()).log(Level.SEVERE, null, ex);
                    }
                }
            });

            java.awt.EventQueue.invokeLater(new Runnable()
            {

                public void run()
                {
                    Double time = Double.parseDouble(SecondsSpinner.getValue().toString()) * Double.parseDouble(SeriesSpinner.getValue().toString());
                    try
                    {
                        Thread.sleep((long) (time * 1000));
                        AbortDisabled();
                    }
                    catch (InterruptedException ex)
                    {
                        Logger.getLogger(CameraControl.class.getName()).log(Level.SEVERE, null, ex);
                    }
                }
            });
        }




    

    private void assembleBinPanel()
    {
        BinButtonsPanel.setLayout(new GridLayout(2, binVector.size()));
        for (String elem : binVector)
        {
            JLabel temp = new JLabel(elem.toString().replace("_", " ") + " ");
            temp.setName("BinLabel_" + elem.toString().replace(" ", "_"));
            temp.setHorizontalAlignment(SwingConstants.CENTER);
            BinButtonsPanel.add(temp);
        } // end for (String elem : binVector)
        for (String elem : binVector)
        {
            JRadioButton temp = new JRadioButton();
            temp.setName("BinRadioButton_" + elem.toString().replace(" ", "_"));
            temp.setHorizontalAlignment(SwingConstants.CENTER);
            BinButtonGroup.add(temp);
            BinButtonsPanel.add(temp);
        } // end for (String elem : binVector)
        ((JRadioButton) BinButtonGroup.getElements().nextElement()).setSelected(true);
    }

    private void assembleFilterPanel()
    {
        FilterButtonsPanel.setLayout(new GridLayout(2, filterVector.size()));
        for (String elem : filterVector)
        {
            JLabel temp = new JLabel(elem.toString());
            temp.setName("FilterLabel_" + elem.toString().replace(" ", "_"));
            temp.setHorizontalAlignment(SwingConstants.CENTER);
            FilterButtonsPanel.add(temp);
        } // end for (String elem : filterVector)
        for (String elem : filterVector)
        {
            JRadioButton temp = new JRadioButton();
            temp.setName("FilterRadioButton_" + elem.toString().replace(" ", "_"));
            temp.setHorizontalAlignment(SwingConstants.CENTER);
            FilterButtonGroup.add(temp);
            FilterButtonsPanel.add(temp);
        } // end for (String elem : filterVector)
        ((JRadioButton) FilterButtonGroup.getElements().nextElement()).setSelected(true);
    }

    private void assembleSubframePanel()
    {
        SubframeButtonsPanel.setLayout(new GridLayout(1, subframeVector.size() + 1, 10, 0));
        for (String elem : subframeVector)
        {
            StringBuffer txt = new StringBuffer();
            for (StringTokenizer token = new StringTokenizer(elem.toString(), "_", false); token.hasMoreTokens();)
            {
                StringBuffer temp = new StringBuffer(token.nextToken());
                txt.append(temp.substring(0, 1).toUpperCase());
                txt.append(temp.substring(1).toLowerCase() + " ");
            }
            txt = txt.deleteCharAt(txt.lastIndexOf(" "));

            JButton temp = new JButton(txt.toString());
            temp.setName("SubframeButton_" + elem.toString().replace(" ", "_"));
            temp.setHorizontalAlignment(SwingConstants.CENTER);
            temp.addActionListener(new java.awt.event.ActionListener()
            {

                public void actionPerformed(java.awt.event.ActionEvent evt)
                {
                    SubframeSizeButtonActionPerformed(evt);
                }
            });
            SubframeButtonsPanel.add(temp);
        } // end for (String elem : subframeVector)
        JButton temp = new JButton("Preview");
        temp.setName("SubframePreviewButton");
        temp.setHorizontalAlignment(SwingConstants.CENTER);
        temp.addActionListener(new java.awt.event.ActionListener()
        {

            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                SubframePreviewButtonActionPerformed(evt);
            }
        });
        SubframeButtonsPanel.add(temp);

    }

    private void SubframeSizeButtonActionPerformed(ActionEvent evt)
    {
        if (((JButton) evt.getSource()).getName().contains("FULL"))
        {
            Debug(((JButton) evt.getSource()).getName() + " selected.");

        }
        else if (((JButton) evt.getSource()).getName().contains("HALF"))
        {
            Debug(((JButton) evt.getSource()).getName() + " selected.");

        }
        else if (((JButton) evt.getSource()).getName().contains("QUARTER"))
        {
            Debug(((JButton) evt.getSource()).getName() + " selected.");

        }
        subframeIndex = subframeVector.indexOf(((JButton) evt.getSource()).getName().replace("SubframeButton_", ""));
    }

    private void SubframePreviewButtonActionPerformed(ActionEvent evt)
    {
        Debug(((JButton) evt.getSource()).getName() + " selected.");

    }

    private void assembleOptionsPanel()
    {
        
    }
    
    private void createFrames()
    {
        subframeFrame = new JFrame("Select a subframe size:");
        binFrame = new JFrame("Select a bin size:");
        filterFrame = new JFrame("Select a filter:");
        optionsFrame = new JFrame("Additonal Options:");

        assembleSubframePanel();
        assembleBinPanel();
        assembleFilterPanel();
        assembleOptionsPanel();

        subframeFrame.add(SubframePanel);
        binFrame.add(BinPanel);
        filterFrame.add(FilterPanel);
        optionsFrame.add(OptionsPanel);
        uniformFrames(subframeFrame);
        uniformFrames(binFrame);
        uniformFrames(filterFrame);
        uniformFrames(optionsFrame);
    }

    private void getCCDinfo()
    {
        // get CCD information from Chimera

        // set maxCCDwidth
        maxCCDwidth = 3000;
        // set maxCCDheight
        maxCCDheight = 2000;
        // get the screen size to figure out the ratio that will fit the screen
        Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
        Debug("Display Properties: width=" + dim.getWidth() + " -- h=" + dim.getHeight());
        // the formula to figure out the ratio is desired size / original size
        //  the -300 is to allow for the window borders and buttons
        double wr = (dim.getWidth() - 300) / maxCCDwidth;
        Debug("-- Calculated width ratio: " + wr);
        double hr = (dim.getHeight() - 300) / maxCCDheight;
        Debug("-- Calculated height ratio: " + hr);
        CCDratio = wr > hr ? hr : wr;
        Debug("Calculated ratio to be used: " + CCDratio);
        // we are going to default to full frame so set selected area the same
        //      as maxCCDwidth and maxCCDheight times the ratio to get the
        //      proportional size
        // set selectedCCDwidth = maxCCDwidth*CCDratio
        selectedCCDwidth = (maxCCDwidth * CCDratio);
        // set selectedCCDheight = maxCCDheight*CCDratio
        selectedCCDheight = (maxCCDheight * CCDratio);
        CCDselectedPoint = new Point(0, 0);
    }

    private void uniformFrames(JFrame frame)
    {
        final JFrame jf = frame;
        frame.addWindowListener(new java.awt.event.WindowAdapter()
        {

            @Override
            public void windowDeactivated(java.awt.event.WindowEvent evt)
            {
                if (!evt.getWindow().isVisible())
                {
                    formWindowDeactivated(jf);
                }
            }
        });
        frame.setResizable(false);
        frame.pack();

        // Get the size of the default screen
        Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
        int w = (int) dim.getWidth();
        int h = (int) dim.getHeight();
        frame.setLocation(((w / 2) - (frame.getWidth() / 2)), ((h / 2) - (frame.getHeight() / 2)));

    }

    private void formWindowDeactivated(JFrame frame)
    {
        if (frame.getTitle().contains("filter"))
        {
            filterFrame.setVisible(false);
            FilterToggleButton.setSelected(false);
        }
        else if (frame.getTitle().contains("bin"))
        {
            binFrame.setVisible(false);
            BinToggleButton.setSelected(false);
        }
        else if (frame.getTitle().contains("subframe"))
        {
            subframeFrame.setVisible(false);
            SubframeToggleButton.setSelected(false);
        }
        else if (frame.getTitle().contains("Options"))
        {
            optionsFrame.setVisible(false);
            OtherOptionsToggleButton.setSelected(false);
        }
        
        updateFields();
    }

    private void fillBinVector()
    {
        binVector.add("_1X1");
        binVector.add("_2X2");
        binVector.add("_3X3");
        binVector.add("_9X9");
        binVector.add("_1X2");
        binVector.add("_1X3");
        binVector.add("_1X9");
        binVector.add("_2X1");
        binVector.add("_3X1");
        binVector.add("_9X1");

    }

    private void fillFilterVector()
    {
        filterVector.add("CLEAR");
        filterVector.add("RED");
        filterVector.add("GREEN");
        filterVector.add("BLUE");
        filterVector.add("LUNAR");

    }

    private void fillSubframeVector()
    {
        subframeVector.add("FULL_FRAME");
        subframeVector.add("TOP_HALF");
        subframeVector.add("BOTTOM_HALF");

    }

    private void fillVectors()
    {
        subframeVector = new Vector<String>();
        binVector = new Vector<String>();
        filterVector = new Vector<String>();

        subframeIndex = 0;
//        binIndex = 0;
//        filterIndex = 0;

        fillSubframeVector();
        fillBinVector();
        fillFilterVector();

    }

    private void updateFields()
    {
        ExposureTimeTextArea.setText(prettyTime(SecondsSpinner.getValue().toString()));

        SeriesTextField.setText(prettySeries(SeriesSpinner.getValue().toString()));

//        SubframeTextField.setText( subframeVector.get( subframeIndex ) );
        StringBuffer subframeTextBuffer = new StringBuffer();
        for (StringTokenizer token = new StringTokenizer(subframeVector.get(subframeIndex), "_", false); token.hasMoreTokens();)
        {
            StringBuffer temp = new StringBuffer(token.nextToken());
            subframeTextBuffer.append(temp.substring(0, 1).toUpperCase());
            subframeTextBuffer.append(temp.substring(1).toLowerCase() + " ");
        }
        subframeTextBuffer = subframeTextBuffer.deleteCharAt(subframeTextBuffer.lastIndexOf(" "));
        SubframeTextField.setText(subframeTextBuffer.toString());
//        SubframeTextField.setText( "NO UPDATE AVAILABLE!" );

//        BinTextField.setText( binVector.get( binIndex ) );
        for (Enumeration e = BinButtonGroup.getElements(); e.hasMoreElements();)
        {
            JRadioButton temp = (JRadioButton) e.nextElement();
            if (temp.isSelected())
            {
                BinTextField.setText(temp.getName().replace("BinRadioButton_", "").replace("_", ""));
                break;

            } // end if ( tempButton.isSelected() )
        }


//        FilterTextField.setText( filterVector.get( filterIndex ) );
        for (Enumeration e = FilterButtonGroup.getElements(); e.hasMoreElements();)
        {
            JRadioButton tempButton = (JRadioButton) e.nextElement();
            if (tempButton.isSelected())
            {
                StringBuffer filterTextBuffer = new StringBuffer();
                for (StringTokenizer token = new StringTokenizer(tempButton.getName().replace("FilterRadioButton_", ""), "_", false); token.hasMoreTokens();)
                {
                    StringBuffer temp = new StringBuffer(token.nextToken());
                    filterTextBuffer.append(temp.substring(0, 1).toUpperCase());
                    filterTextBuffer.append(temp.substring(1).toLowerCase() + " ");
                }
                filterTextBuffer = filterTextBuffer.deleteCharAt(filterTextBuffer.lastIndexOf(" "));
                FilterTextField.setText(filterTextBuffer.toString());
                break;

            } // end if ( tempButton.isSelected() )
        }
    }

    private String prettyTime(String seconds)
    {
        StringBuffer rv = new StringBuffer();

        double sec = Double.parseDouble(seconds);

        if (sec > 59.99)
        {
            int min = (int) sec / 60;
            sec -= (min * 60.0);
            if (min == 1)
            {
                rv.append(min + " min &\n");
            }
            else
            {
                rv.append(min + " mins &\n");
            }
        }
        rv.append(myFormat.format(sec) + " sec");
        if (sec > 1.0)
        {
            rv.append("s");
        }

        return rv.toString();
    }

    private String prettySeries(String series)
    {
        StringBuffer rv = new StringBuffer();

        rv.append(series + " picture");

        if (Integer.parseInt(series) > 1)
        {
            rv.append("s");
        }

        return rv.toString();
    }

    private void AbortEnabled()
    {
        TakeImageButton.setEnabled(false);
        AbortButton.setEnabled(true);
        AbortButton.setSelected(true);
    }

    private void AbortDisabled()
    {
        AbortButton.setEnabled(false);
        TakeImageButton.setEnabled(true);
        AbortButton.setSelected(false);
    }

    public void launchDS(File ff)
    {
        String localdir = System.getProperty("user.dir");
        String os = System.getProperty("os.name");
        System.out.println(os);
        try
        {
            Runtime rt = Runtime.getRuntime();
            if (os.contains("Windows"))
            {
                Process proc = rt.exec(localdir + "\\ds9.exe " + ff.toString());
                System.out.println("Windows");
            }
            else if (os.contains("Linux"))
            {
                Process proc = rt.exec(localdir + "/ds9 " + ff.toString());
                System.out.println("Linux");
            }
            else
            {
                JOptionPane.showMessageDialog(null, "Unknown operating system.",
                        "System Error", JOptionPane.ERROR_MESSAGE);
            }

        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents()
    {
        java.awt.GridBagConstraints gridBagConstraints;

        FilterPanel = new javax.swing.JPanel();
        FilterButtonsPanel = new javax.swing.JPanel();
        FilterAcceptButtonPanel = new javax.swing.JPanel();
        FilterAcceptButton = new javax.swing.JButton();
        FilterButtonGroup = new javax.swing.ButtonGroup();
        BinPanel = new javax.swing.JPanel();
        BinButtonsPanel = new javax.swing.JPanel();
        BinAcceptButtonPanel = new javax.swing.JPanel();
        BinAcceptButton = new javax.swing.JButton();
        BinButtonGroup = new javax.swing.ButtonGroup();
        SubframePanel = new javax.swing.JPanel();
        SubframeDimensionPanel = new javax.swing.JPanel();
        SubframeAcceptButtonPanel = new javax.swing.JPanel();
        SubframeAcceptButton = new javax.swing.JButton();
        SubframeButtonsPanel = new javax.swing.JPanel();
        OptionsPanel = new javax.swing.JPanel();
        ImageDisplayOptionsPanel = new javax.swing.JPanel();
        DisplayImageCheckBox = new javax.swing.JCheckBox();
        ChooseImagesButton = new javax.swing.JButton();
        TemperatureOptionsPanel = new javax.swing.JPanel();
        IsCoolingLabel = new javax.swing.JLabel();
        IsFanningLabel = new javax.swing.JLabel();
        TemperatureLabel = new javax.swing.JLabel();
        SetpointLabel = new javax.swing.JLabel();
        NewSetpointLabel = new javax.swing.JLabel();
        IsCoolingTextField = new javax.swing.JTextField();
        IsFanningTextField = new javax.swing.JTextField();
        TemperatureTextField = new javax.swing.JTextField();
        SetpointTextField = new javax.swing.JTextField();
        NewSetpointTextField = new javax.swing.JTextField();
        StartStopCoolingButton = new javax.swing.JButton();
        StartStopFanningButton = new javax.swing.JButton();
        NewSetpointButton = new javax.swing.JButton();
        OptionsAcceptButtonPanel = new javax.swing.JPanel();
        OptionsAcceptButton = new javax.swing.JButton();
        ExposurePanel = new javax.swing.JPanel();
        SecondsLabel = new javax.swing.JLabel();
        SeriesLabel = new javax.swing.JLabel();
        SecondsSpinner = new javax.swing.JSpinner();
        SeriesSpinner = new javax.swing.JSpinner();
        CurrentConfigurationPanel = new javax.swing.JPanel();
        ExposureTimeLabel = new javax.swing.JLabel();
        ExposureTimeScrollPane = new javax.swing.JScrollPane();
        ExposureTimeTextArea = new javax.swing.JTextArea();
        SeriesOfLabel = new javax.swing.JLabel();
        SeriesTextField = new javax.swing.JTextField();
        SubframeLabel = new javax.swing.JLabel();
        SubframeTextField = new javax.swing.JTextField();
        BinLabel = new javax.swing.JLabel();
        BinTextField = new javax.swing.JTextField();
        FilterLabel = new javax.swing.JLabel();
        FilterTextField = new javax.swing.JTextField();
        DisplayImagesLabel = new javax.swing.JLabel();
        DisplayImagesTextField = new javax.swing.JTextField();
        CurrentlyFanningLabel = new javax.swing.JLabel();
        CurrentlyFanningTextField = new javax.swing.JTextField();
        CurrentlyCoolingLabel = new javax.swing.JLabel();
        CurrentlyCoolingTextField = new javax.swing.JTextField();
        CurrentTemperatureLabel = new javax.swing.JLabel();
        CurrentTemperatureTextField = new javax.swing.JTextField();
        CurrentSetpointLabel = new javax.swing.JLabel();
        CurrentSetpointTextField = new javax.swing.JTextField();
        AllButtonsPanel = new javax.swing.JPanel();
        ButtonsPanel = new javax.swing.JPanel();
        SubframeToggleButton = new javax.swing.JToggleButton();
        FilterToggleButton = new javax.swing.JToggleButton();
        BinToggleButton = new javax.swing.JToggleButton();
        OtherOptionsToggleButton = new javax.swing.JToggleButton();
        ImageButtonPanel = new javax.swing.JPanel();
        TakeImageButton = new javax.swing.JButton();
        AbortButton = new javax.swing.JButton();

        FilterButtonsPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Filters"));

        javax.swing.GroupLayout FilterButtonsPanelLayout = new javax.swing.GroupLayout(FilterButtonsPanel);
        FilterButtonsPanel.setLayout(FilterButtonsPanelLayout);
        FilterButtonsPanelLayout.setHorizontalGroup(
            FilterButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 115, Short.MAX_VALUE)
        );
        FilterButtonsPanelLayout.setVerticalGroup(
            FilterButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 30, Short.MAX_VALUE)
        );

        FilterAcceptButton.setText("Accept Selection");
        FilterAcceptButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                FilterAcceptButtonActionPerformed(evt);
            }
        });

        javax.swing.GroupLayout FilterAcceptButtonPanelLayout = new javax.swing.GroupLayout(FilterAcceptButtonPanel);
        FilterAcceptButtonPanel.setLayout(FilterAcceptButtonPanelLayout);
        FilterAcceptButtonPanelLayout.setHorizontalGroup(
            FilterAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(FilterAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(FilterAcceptButton, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addContainerGap())
        );
        FilterAcceptButtonPanelLayout.setVerticalGroup(
            FilterAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, FilterAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addComponent(FilterAcceptButton)
                .addContainerGap())
        );

        javax.swing.GroupLayout FilterPanelLayout = new javax.swing.GroupLayout(FilterPanel);
        FilterPanel.setLayout(FilterPanelLayout);
        FilterPanelLayout.setHorizontalGroup(
            FilterPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, FilterPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addGroup(FilterPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                    .addComponent(FilterButtonsPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(FilterAcceptButtonPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addContainerGap())
        );
        FilterPanelLayout.setVerticalGroup(
            FilterPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, FilterPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(FilterButtonsPanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(FilterAcceptButtonPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap())
        );

        BinButtonsPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Bins"));

        javax.swing.GroupLayout BinButtonsPanelLayout = new javax.swing.GroupLayout(BinButtonsPanel);
        BinButtonsPanel.setLayout(BinButtonsPanelLayout);
        BinButtonsPanelLayout.setHorizontalGroup(
            BinButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 115, Short.MAX_VALUE)
        );
        BinButtonsPanelLayout.setVerticalGroup(
            BinButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 44, Short.MAX_VALUE)
        );

        BinAcceptButton.setText("Accept Selection");
        BinAcceptButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                BinAcceptButtonActionPerformed(evt);
            }
        });

        javax.swing.GroupLayout BinAcceptButtonPanelLayout = new javax.swing.GroupLayout(BinAcceptButtonPanel);
        BinAcceptButtonPanel.setLayout(BinAcceptButtonPanelLayout);
        BinAcceptButtonPanelLayout.setHorizontalGroup(
            BinAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(BinAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(BinAcceptButton, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addContainerGap())
        );
        BinAcceptButtonPanelLayout.setVerticalGroup(
            BinAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, BinAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addComponent(BinAcceptButton)
                .addContainerGap())
        );

        javax.swing.GroupLayout BinPanelLayout = new javax.swing.GroupLayout(BinPanel);
        BinPanel.setLayout(BinPanelLayout);
        BinPanelLayout.setHorizontalGroup(
            BinPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, BinPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addGroup(BinPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                    .addComponent(BinButtonsPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(BinAcceptButtonPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addContainerGap())
        );
        BinPanelLayout.setVerticalGroup(
            BinPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, BinPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(BinButtonsPanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(BinAcceptButtonPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap())
        );

        SubframeDimensionPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Subframe"));

        javax.swing.GroupLayout SubframeDimensionPanelLayout = new javax.swing.GroupLayout(SubframeDimensionPanel);
        SubframeDimensionPanel.setLayout(SubframeDimensionPanelLayout);
        SubframeDimensionPanelLayout.setHorizontalGroup(
            SubframeDimensionPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 115, Short.MAX_VALUE)
        );
        SubframeDimensionPanelLayout.setVerticalGroup(
            SubframeDimensionPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 0, Short.MAX_VALUE)
        );

        SubframeAcceptButton.setText("Accept Selection");
        SubframeAcceptButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                SubframeAcceptButtonActionPerformed(evt);
            }
        });

        javax.swing.GroupLayout SubframeAcceptButtonPanelLayout = new javax.swing.GroupLayout(SubframeAcceptButtonPanel);
        SubframeAcceptButtonPanel.setLayout(SubframeAcceptButtonPanelLayout);
        SubframeAcceptButtonPanelLayout.setHorizontalGroup(
            SubframeAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(SubframeAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(SubframeAcceptButton, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addContainerGap())
        );
        SubframeAcceptButtonPanelLayout.setVerticalGroup(
            SubframeAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, SubframeAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addComponent(SubframeAcceptButton)
                .addContainerGap())
        );

        javax.swing.GroupLayout SubframeButtonsPanelLayout = new javax.swing.GroupLayout(SubframeButtonsPanel);
        SubframeButtonsPanel.setLayout(SubframeButtonsPanelLayout);
        SubframeButtonsPanelLayout.setHorizontalGroup(
            SubframeButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 131, Short.MAX_VALUE)
        );
        SubframeButtonsPanelLayout.setVerticalGroup(
            SubframeButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 45, Short.MAX_VALUE)
        );

        javax.swing.GroupLayout SubframePanelLayout = new javax.swing.GroupLayout(SubframePanel);
        SubframePanel.setLayout(SubframePanelLayout);
        SubframePanelLayout.setHorizontalGroup(
            SubframePanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, SubframePanelLayout.createSequentialGroup()
                .addContainerGap()
                .addGroup(SubframePanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                    .addComponent(SubframeDimensionPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(SubframeButtonsPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(SubframeAcceptButtonPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addContainerGap())
        );
        SubframePanelLayout.setVerticalGroup(
            SubframePanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, SubframePanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(SubframeDimensionPanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(SubframeButtonsPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(SubframeAcceptButtonPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap())
        );

        ImageDisplayOptionsPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Image Display Options:"));
        ImageDisplayOptionsPanel.setLayout(new java.awt.GridBagLayout());

        DisplayImageCheckBox.setSelected(true);
        DisplayImageCheckBox.setText("Display taken image in DS9");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ImageDisplayOptionsPanel.add(DisplayImageCheckBox, gridBagConstraints);

        ChooseImagesButton.setText("Choose Images to Display");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ImageDisplayOptionsPanel.add(ChooseImagesButton, gridBagConstraints);

        TemperatureOptionsPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Temperature Options:"));
        TemperatureOptionsPanel.setLayout(new java.awt.GridBagLayout());

        IsCoolingLabel.setText("Is Cooling?");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(IsCoolingLabel, gridBagConstraints);

        IsFanningLabel.setText("Is Fanning?");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(IsFanningLabel, gridBagConstraints);

        TemperatureLabel.setText("Current Temperature:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(TemperatureLabel, gridBagConstraints);

        SetpointLabel.setText("Current Setpoint:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(SetpointLabel, gridBagConstraints);

        NewSetpointLabel.setText("New Setpoint:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(NewSetpointLabel, gridBagConstraints);

        IsCoolingTextField.setEditable(false);
        IsCoolingTextField.setText("Not Implemented.");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(IsCoolingTextField, gridBagConstraints);

        IsFanningTextField.setEditable(false);
        IsFanningTextField.setText("Not Implemented.");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(IsFanningTextField, gridBagConstraints);

        TemperatureTextField.setEditable(false);
        TemperatureTextField.setText("Not Implemented.");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(TemperatureTextField, gridBagConstraints);

        SetpointTextField.setEditable(false);
        SetpointTextField.setText("Not Implemented.");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(SetpointTextField, gridBagConstraints);

        NewSetpointTextField.setText("Not Implemented.");
        NewSetpointTextField.setToolTipText("New temperature for the setpoint - in degrees Celcius");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(NewSetpointTextField, gridBagConstraints);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 2;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(StartStopCoolingButton, gridBagConstraints);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 2;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(StartStopFanningButton, gridBagConstraints);

        NewSetpointButton.setText("Set New Temp");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 2;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        TemperatureOptionsPanel.add(NewSetpointButton, gridBagConstraints);

        OptionsAcceptButton.setText("Accept Options Selected");
        OptionsAcceptButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                OptionsAcceptButtonActionPerformed(evt);
            }
        });

        javax.swing.GroupLayout OptionsAcceptButtonPanelLayout = new javax.swing.GroupLayout(OptionsAcceptButtonPanel);
        OptionsAcceptButtonPanel.setLayout(OptionsAcceptButtonPanelLayout);
        OptionsAcceptButtonPanelLayout.setHorizontalGroup(
            OptionsAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(OptionsAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(OptionsAcceptButton, javax.swing.GroupLayout.DEFAULT_SIZE, 306, Short.MAX_VALUE)
                .addContainerGap())
        );
        OptionsAcceptButtonPanelLayout.setVerticalGroup(
            OptionsAcceptButtonPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, OptionsAcceptButtonPanelLayout.createSequentialGroup()
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addComponent(OptionsAcceptButton)
                .addContainerGap())
        );

        javax.swing.GroupLayout OptionsPanelLayout = new javax.swing.GroupLayout(OptionsPanel);
        OptionsPanel.setLayout(OptionsPanelLayout);
        OptionsPanelLayout.setHorizontalGroup(
            OptionsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, OptionsPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addGroup(OptionsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                    .addComponent(OptionsAcceptButtonPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(TemperatureOptionsPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.PREFERRED_SIZE, 326, Short.MAX_VALUE)
                    .addComponent(ImageDisplayOptionsPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addContainerGap())
        );
        OptionsPanelLayout.setVerticalGroup(
            OptionsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(OptionsPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(ImageDisplayOptionsPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(TemperatureOptionsPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(OptionsAcceptButtonPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap(17, Short.MAX_VALUE))
        );

        setTitle("Camera Controls");
        setAutoscrolls(true);
        try
        {
            setSelected(true);
        } catch (java.beans.PropertyVetoException e1)
        {
            e1.printStackTrace();
        }
        setVisible(true);

        ExposurePanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Exposure"));
        ExposurePanel.setLayout(new java.awt.GridBagLayout());

        SecondsLabel.setHorizontalAlignment(javax.swing.SwingConstants.RIGHT);
        SecondsLabel.setText("Seconds:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ExposurePanel.add(SecondsLabel, gridBagConstraints);

        SeriesLabel.setHorizontalAlignment(javax.swing.SwingConstants.RIGHT);
        SeriesLabel.setText("Number of Exposures:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ExposurePanel.add(SeriesLabel, gridBagConstraints);

        SecondsSpinner.setModel(new javax.swing.SpinnerNumberModel(Double.valueOf(1.0d), Double.valueOf(0.0d), null, Double.valueOf(0.01d)));
        SecondsSpinner.addChangeListener(new javax.swing.event.ChangeListener()
        {
            public void stateChanged(javax.swing.event.ChangeEvent evt)
            {
                SecondsSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ExposurePanel.add(SecondsSpinner, gridBagConstraints);

        SeriesSpinner.setModel(new javax.swing.SpinnerNumberModel(1, 1, 500, 1));
        SeriesSpinner.addChangeListener(new javax.swing.event.ChangeListener()
        {
            public void stateChanged(javax.swing.event.ChangeEvent evt)
            {
                SeriesSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ExposurePanel.add(SeriesSpinner, gridBagConstraints);

        CurrentConfigurationPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Current Configuration:"));
        CurrentConfigurationPanel.setLayout(new java.awt.GridBagLayout());

        ExposureTimeLabel.setText("Exposure Time:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(ExposureTimeLabel, gridBagConstraints);

        ExposureTimeScrollPane.setBorder(null);
        ExposureTimeScrollPane.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        ExposureTimeScrollPane.setVerticalScrollBarPolicy(javax.swing.ScrollPaneConstants.VERTICAL_SCROLLBAR_NEVER);
        ExposureTimeScrollPane.setEnabled(false);
        ExposureTimeScrollPane.setFocusable(false);
        ExposureTimeScrollPane.setWheelScrollingEnabled(false);

        ExposureTimeTextArea.setBackground(new java.awt.Color(224, 223, 227));
        ExposureTimeTextArea.setColumns(12);
        ExposureTimeTextArea.setEditable(false);
        ExposureTimeTextArea.setLineWrap(true);
        ExposureTimeTextArea.setRows(2);
        ExposureTimeTextArea.setAutoscrolls(false);
        ExposureTimeTextArea.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        ExposureTimeTextArea.setOpaque(false);
        ExposureTimeScrollPane.setViewportView(ExposureTimeTextArea);

        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(ExposureTimeScrollPane, gridBagConstraints);

        SeriesOfLabel.setText("Series of:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(SeriesOfLabel, gridBagConstraints);

        SeriesTextField.setEditable(false);
        SeriesTextField.setAutoscrolls(false);
        SeriesTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(SeriesTextField, gridBagConstraints);

        SubframeLabel.setText("Subframe:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(SubframeLabel, gridBagConstraints);

        SubframeTextField.setEditable(false);
        SubframeTextField.setAutoscrolls(false);
        SubframeTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(SubframeTextField, gridBagConstraints);

        BinLabel.setText("Bin:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(BinLabel, gridBagConstraints);

        BinTextField.setEditable(false);
        BinTextField.setAutoscrolls(false);
        BinTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(BinTextField, gridBagConstraints);

        FilterLabel.setText("Filter:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(FilterLabel, gridBagConstraints);

        FilterTextField.setEditable(false);
        FilterTextField.setAutoscrolls(false);
        FilterTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(FilterTextField, gridBagConstraints);

        DisplayImagesLabel.setText("Will Images Display?");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 9;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(DisplayImagesLabel, gridBagConstraints);

        DisplayImagesTextField.setEditable(false);
        DisplayImagesTextField.setAutoscrolls(false);
        DisplayImagesTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 9;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(DisplayImagesTextField, gridBagConstraints);

        CurrentlyFanningLabel.setText("Currently Fanning?");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 5;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentlyFanningLabel, gridBagConstraints);

        CurrentlyFanningTextField.setEditable(false);
        CurrentlyFanningTextField.setAutoscrolls(false);
        CurrentlyFanningTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 5;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentlyFanningTextField, gridBagConstraints);

        CurrentlyCoolingLabel.setText("Currently Cooling?");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 6;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentlyCoolingLabel, gridBagConstraints);

        CurrentlyCoolingTextField.setEditable(false);
        CurrentlyCoolingTextField.setAutoscrolls(false);
        CurrentlyCoolingTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 6;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentlyCoolingTextField, gridBagConstraints);

        CurrentTemperatureLabel.setText("Current Temperature:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 7;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentTemperatureLabel, gridBagConstraints);

        CurrentTemperatureTextField.setEditable(false);
        CurrentTemperatureTextField.setAutoscrolls(false);
        CurrentTemperatureTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 7;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentTemperatureTextField, gridBagConstraints);

        CurrentSetpointLabel.setText("Current Setpoint:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 8;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentSetpointLabel, gridBagConstraints);

        CurrentSetpointTextField.setEditable(false);
        CurrentSetpointTextField.setAutoscrolls(false);
        CurrentSetpointTextField.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 1, 1, 1));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 8;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        CurrentConfigurationPanel.add(CurrentSetpointTextField, gridBagConstraints);

        ButtonsPanel.setLayout(new java.awt.GridBagLayout());

        SubframeToggleButton.setText("Subframe");
        SubframeToggleButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                SubframeToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.HORIZONTAL;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ButtonsPanel.add(SubframeToggleButton, gridBagConstraints);

        FilterToggleButton.setText("Filter");
        FilterToggleButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                FilterToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.HORIZONTAL;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ButtonsPanel.add(FilterToggleButton, gridBagConstraints);

        BinToggleButton.setText("Bin");
        BinToggleButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                BinToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.HORIZONTAL;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ButtonsPanel.add(BinToggleButton, gridBagConstraints);

        OtherOptionsToggleButton.setText("Other Options");
        OtherOptionsToggleButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                OtherOptionsToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.HORIZONTAL;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ButtonsPanel.add(OtherOptionsToggleButton, gridBagConstraints);

        ImageButtonPanel.setLayout(new java.awt.GridBagLayout());

        TakeImageButton.setFont(new java.awt.Font("Tahoma", 1, 11));
        TakeImageButton.setText("Take Image");
        TakeImageButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                TakeImageButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.gridheight = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ImageButtonPanel.add(TakeImageButton, gridBagConstraints);

        AbortButton.setFont(new java.awt.Font("Tahoma", 1, 11)); // NOI18N
        AbortButton.setText("Abort");
        AbortButton.setEnabled(false);
        AbortButton.addActionListener(new java.awt.event.ActionListener()
        {
            public void actionPerformed(java.awt.event.ActionEvent evt)
            {
                AbortButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.gridheight = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        ImageButtonPanel.add(AbortButton, gridBagConstraints);

        javax.swing.GroupLayout AllButtonsPanelLayout = new javax.swing.GroupLayout(AllButtonsPanel);
        AllButtonsPanel.setLayout(AllButtonsPanelLayout);
        AllButtonsPanelLayout.setHorizontalGroup(
            AllButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(AllButtonsPanelLayout.createSequentialGroup()
                .addGroup(AllButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(ButtonsPanel, javax.swing.GroupLayout.PREFERRED_SIZE, 101, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(ImageButtonPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );
        AllButtonsPanelLayout.setVerticalGroup(
            AllButtonsPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(AllButtonsPanelLayout.createSequentialGroup()
                .addComponent(ButtonsPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(18, 18, 18)
                .addComponent(ImageButtonPanel, javax.swing.GroupLayout.DEFAULT_SIZE, 159, Short.MAX_VALUE)
                .addContainerGap())
        );

        javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING, false)
                    .addComponent(ExposurePanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(CurrentConfigurationPanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(AllButtonsPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING, false)
                    .addComponent(AllButtonsPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addGroup(javax.swing.GroupLayout.Alignment.LEADING, layout.createSequentialGroup()
                        .addComponent(ExposurePanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addComponent(CurrentConfigurationPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)))
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );

        pack();
    }// </editor-fold>//GEN-END:initComponents
    private void SecondsSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_SecondsSpinnerStateChanged
    {//GEN-HEADEREND:event_SecondsSpinnerStateChanged
        updateFields();
    }//GEN-LAST:event_SecondsSpinnerStateChanged

    private void TakeImageButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_TakeImageButtonActionPerformed
    {//GEN-HEADEREND:event_TakeImageButtonActionPerformed
        TakeIamge();
    }//GEN-LAST:event_TakeImageButtonActionPerformed

    private void AbortButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_AbortButtonActionPerformed
    {//GEN-HEADEREND:event_AbortButtonActionPerformed
        System.out.println("Abort clicked");
        AbortDisabled();
        AbortImage();

    }//GEN-LAST:event_AbortButtonActionPerformed

    private void SeriesSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_SeriesSpinnerStateChanged
    {//GEN-HEADEREND:event_SeriesSpinnerStateChanged
        updateFields();
    }//GEN-LAST:event_SeriesSpinnerStateChanged

    private void FilterToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_FilterToggleButtonActionPerformed
    {//GEN-HEADEREND:event_FilterToggleButtonActionPerformed
        if (((JToggleButton) evt.getSource()).isSelected())
        {
            Debug("Filter Button selected.");
            filterFrame.setVisible(true);
        }
        else
        {
            Debug("Filter Button unselected.");
            formWindowDeactivated(filterFrame);

        } // end if ( ((JToggleButton)evt.getSource()).isSelected() ) else
    }//GEN-LAST:event_FilterToggleButtonActionPerformed

    private void FilterAcceptButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_FilterAcceptButtonActionPerformed
    {//GEN-HEADEREND:event_FilterAcceptButtonActionPerformed
        Debug("Accept Selection Button pressed - FilterPanel.");
        formWindowDeactivated(filterFrame);

    }//GEN-LAST:event_FilterAcceptButtonActionPerformed

    private void BinAcceptButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_BinAcceptButtonActionPerformed
    {//GEN-HEADEREND:event_BinAcceptButtonActionPerformed
        Debug("Accept Selection Button pressed - BinPanel.");
        formWindowDeactivated(binFrame);
}//GEN-LAST:event_BinAcceptButtonActionPerformed

    private void SubframeAcceptButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_SubframeAcceptButtonActionPerformed
    {//GEN-HEADEREND:event_SubframeAcceptButtonActionPerformed
        Debug("Accept Selection Button pressed - SubframePanel.");
        formWindowDeactivated(subframeFrame);
}//GEN-LAST:event_SubframeAcceptButtonActionPerformed

    private void BinToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_BinToggleButtonActionPerformed
    {//GEN-HEADEREND:event_BinToggleButtonActionPerformed
        if (((JToggleButton) evt.getSource()).isSelected())
        {
            Debug("Bin Button selected.");
            binFrame.setVisible(true);
        }
        else
        {
            Debug("Bin Button unselected.");
            formWindowDeactivated(binFrame);

        } // end if ( ((JToggleButton)evt.getSource()).isSelected() ) else
    }//GEN-LAST:event_BinToggleButtonActionPerformed

    private void SubframeToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_SubframeToggleButtonActionPerformed
    {//GEN-HEADEREND:event_SubframeToggleButtonActionPerformed
        if (((JToggleButton) evt.getSource()).isSelected())
        {
            Debug("Subframe Button selected.");
            subframeFrame.setVisible(true);
        }
        else
        {
            Debug("Subframe Button unselected.");
            formWindowDeactivated(subframeFrame);

        } // end if ( ((JToggleButton)evt.getSource()).isSelected() ) else
    }//GEN-LAST:event_SubframeToggleButtonActionPerformed

    private void OtherOptionsToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_OtherOptionsToggleButtonActionPerformed
    {//GEN-HEADEREND:event_OtherOptionsToggleButtonActionPerformed
        if (((JToggleButton) evt.getSource()).isSelected())
        {
            Debug("Other Options Button selected.");
            optionsFrame.setVisible(true);
        }
        else
        {
            Debug("Other Options Button unselected.");
            formWindowDeactivated(optionsFrame);

        } // end if ( ((JToggleButton)evt.getSource()).isSelected() ) else
    }//GEN-LAST:event_OtherOptionsToggleButtonActionPerformed

    private void OptionsAcceptButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_OptionsAcceptButtonActionPerformed
    {//GEN-HEADEREND:event_OptionsAcceptButtonActionPerformed
        Debug("Accept Selection Button pressed - OptionsPanel.");
        formWindowDeactivated(optionsFrame);
}//GEN-LAST:event_OptionsAcceptButtonActionPerformed

    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JButton AbortButton;
    private javax.swing.JPanel AllButtonsPanel;
    private javax.swing.JButton BinAcceptButton;
    private javax.swing.JPanel BinAcceptButtonPanel;
    private javax.swing.ButtonGroup BinButtonGroup;
    private javax.swing.JPanel BinButtonsPanel;
    private javax.swing.JLabel BinLabel;
    private javax.swing.JPanel BinPanel;
    private javax.swing.JTextField BinTextField;
    private javax.swing.JToggleButton BinToggleButton;
    private javax.swing.JPanel ButtonsPanel;
    private javax.swing.JButton ChooseImagesButton;
    private javax.swing.JPanel CurrentConfigurationPanel;
    private javax.swing.JLabel CurrentSetpointLabel;
    private javax.swing.JTextField CurrentSetpointTextField;
    private javax.swing.JLabel CurrentTemperatureLabel;
    private javax.swing.JTextField CurrentTemperatureTextField;
    private javax.swing.JLabel CurrentlyCoolingLabel;
    private javax.swing.JTextField CurrentlyCoolingTextField;
    private javax.swing.JLabel CurrentlyFanningLabel;
    private javax.swing.JTextField CurrentlyFanningTextField;
    private javax.swing.JCheckBox DisplayImageCheckBox;
    private javax.swing.JLabel DisplayImagesLabel;
    private javax.swing.JTextField DisplayImagesTextField;
    private javax.swing.JPanel ExposurePanel;
    private javax.swing.JLabel ExposureTimeLabel;
    private javax.swing.JScrollPane ExposureTimeScrollPane;
    private javax.swing.JTextArea ExposureTimeTextArea;
    private javax.swing.JButton FilterAcceptButton;
    private javax.swing.JPanel FilterAcceptButtonPanel;
    private javax.swing.ButtonGroup FilterButtonGroup;
    private javax.swing.JPanel FilterButtonsPanel;
    private javax.swing.JLabel FilterLabel;
    private javax.swing.JPanel FilterPanel;
    private javax.swing.JTextField FilterTextField;
    private javax.swing.JToggleButton FilterToggleButton;
    private javax.swing.JPanel ImageButtonPanel;
    private javax.swing.JPanel ImageDisplayOptionsPanel;
    private javax.swing.JLabel IsCoolingLabel;
    private javax.swing.JTextField IsCoolingTextField;
    private javax.swing.JLabel IsFanningLabel;
    private javax.swing.JTextField IsFanningTextField;
    private javax.swing.JButton NewSetpointButton;
    private javax.swing.JLabel NewSetpointLabel;
    private javax.swing.JTextField NewSetpointTextField;
    private javax.swing.JButton OptionsAcceptButton;
    private javax.swing.JPanel OptionsAcceptButtonPanel;
    private javax.swing.JPanel OptionsPanel;
    private javax.swing.JToggleButton OtherOptionsToggleButton;
    private javax.swing.JLabel SecondsLabel;
    private javax.swing.JSpinner SecondsSpinner;
    private javax.swing.JLabel SeriesLabel;
    private javax.swing.JLabel SeriesOfLabel;
    private javax.swing.JSpinner SeriesSpinner;
    private javax.swing.JTextField SeriesTextField;
    private javax.swing.JLabel SetpointLabel;
    private javax.swing.JTextField SetpointTextField;
    private javax.swing.JButton StartStopCoolingButton;
    private javax.swing.JButton StartStopFanningButton;
    private javax.swing.JButton SubframeAcceptButton;
    private javax.swing.JPanel SubframeAcceptButtonPanel;
    private javax.swing.JPanel SubframeButtonsPanel;
    private javax.swing.JPanel SubframeDimensionPanel;
    private javax.swing.JLabel SubframeLabel;
    private javax.swing.JPanel SubframePanel;
    private javax.swing.JTextField SubframeTextField;
    private javax.swing.JToggleButton SubframeToggleButton;
    private javax.swing.JButton TakeImageButton;
    private javax.swing.JLabel TemperatureLabel;
    private javax.swing.JPanel TemperatureOptionsPanel;
    private javax.swing.JTextField TemperatureTextField;
    // End of variables declaration//GEN-END:variables
    private void Debug(String str)
    {
        if (DEBUG & str.length() > 0)
        {
            System.out.println(str);

        } // end if ( str.length()>0 )
    }

    private void Debug1(String str)
    {
        if (DEBUG & str.length() > 0)
        {
            System.out.print(str);

        } // end if ( str.length()>0 )
    }
}
