/*
 * TelescopeControl.java
 *
 * Created on July 30, 2008, 9:49 AM
 */
package chimera;

import sesame.*;

import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.HashMap;
import java.util.List;
import java.util.StringTokenizer;

import javax.swing.JComboBox;
import javax.swing.JFormattedTextField;
import javax.swing.JOptionPane;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.SwingWorker;
import javax.swing.Timer;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;

/**
 *
 * @author  Denis
 */
public class TelescopeControl extends javax.swing.JInternalFrame
{
    // show debug statements to System.out and System.err
    boolean DEBUG = true;
    // formatting for decimal numbers
    NumberFormat decimalFormat = NumberFormat.getInstance();
    // formatting for hours, degrees, and minutes
    NumberFormat hoursDegreesMinutesFormat = NumberFormat.getInstance();
    // XmlRpcClient used to communicate with the manager
    XmlRpcClient myManager;
    // the telescope this control panel is in charge of
    TelescopeObject myTelescope;
    // values from the manager of the telescope's current position
    HashMap<String, String> telescopeValues;
    // whether or not the display is currently updating
    boolean IS_UPDATING = false;
    // timer used to update the display
    Timer updateTimer;
    // Background task for loading initial values from the manager
    SwingWorker initializationWorker;
    // Background task for updating values from the manager
    SwingWorker updateWorker;

    /** Creates new form TelescopeControl */
    public TelescopeControl( XmlRpcClient manager, String telescopeName )
    {
        // used to show to sig figs for doubles
        if ( decimalFormat instanceof DecimalFormat )
        {
            ((DecimalFormat)decimalFormat).setDecimalSeparatorAlwaysShown( true );
            ((DecimalFormat)decimalFormat).applyPattern( "00.000" );

        } // end if ( decimalFormat instanceof DecimalFormat )
        // used to show to sig figs for integers
        hoursDegreesMinutesFormat.setMinimumIntegerDigits( 2 );

        myManager = manager;
        myTelescope = new TelescopeObject( myManager, telescopeName );

        // thread off GUI creation
        SwingUtilities.invokeLater( new Runnable()
                            {

                                public void run()
                                {
                                    createAndShowGUI();
                                }
                            } );

        // instantiate updateTimer with a 0 second initial delay so it fires immediately
        updateTimer = new Timer( 0, null );
        updateTimer.setDelay( 3000 );
        // add an ActionListener to the timer
        updateTimer.addActionListener( new java.awt.event.ActionListener()
                               {
                                   // what the timer is supposed to execute                                    
                                   public void actionPerformed( java.awt.event.ActionEvent evt )
                                   {
                                       updateTimerActionPerformed();
                                   }
                               } );

    // constructor completed
    }

    private void createAndShowGUI()
    {
        // Create components
        initComponents();

        // Setting default values before information is retrieved from the manager
        HAstatusTextField.setText( "Retrieving data..." );
        AMstatusTextField.setText( "Retrieving data..." );
        ALTstatusTextField.setText( "Retrieving data..." );
        AZstatusTextField.setText( "Retrieving data..." );
        RAstatusTextField.setText( "Retrieving data..." );
        DECstatusTextField.setText( "Retrieving data..." );
        RAinputHoursSpinner.setValue( 0 );
        RAinputMinutesSpinner.setValue( 0 );
        RAinputSecondsSpinner.setValue( 0 );
        DECinputDegreesSpinner.setValue( 0 );
        DECinputMinutesSpinner.setValue( 0 );
        DECinputSecondsSpinner.setValue( 0 );

        // retrieve initial values from the manager
        initializationWorker();

    // GUI creation complete
    }

    private void initializationWorker()
    {
        initializationWorker = new SwingWorker<HashMap<String, String>, Void>()
        {
            // retrieve initial values from the manager
            @Override
            public HashMap<String, String> doInBackground()
            {
//            DebugError( "Starting initializationWorker thread..." );
                HashMap<String, String> innerMap = new HashMap<String, String>();
                innerMap.put( "ALT", myTelescope.getAlt() );
                innerMap.put( "AZ", myTelescope.getAz() );
                innerMap.put( "RA", myTelescope.getRa() );
                innerMap.put( "DEC", myTelescope.getDec() );
//                innerMap.put( "HA", myTelescope.getHA() );
//            DebugError( "Finished initializationWorker thread." );
//            Debug( "innerMap size: " + innerMap.size() );
                return innerMap;
            }

            @Override
            public void done()
            {
//            DebugError( "Starting to process initializationWorker thread's contents..." );
                // store values into telescopeValues map
                try
                {
                    telescopeValues = get();
                }
                catch ( InterruptedException ignore )
                {
                }
                catch ( java.util.concurrent.ExecutionException e )
                {
                    String why;
                    Throwable cause = e.getCause();
                    if ( cause != null )
                        why = cause.getMessage();
                    else
                        why = e.getMessage();
                    System.err.println( "Error retrieving file: " + why );
                }
                // update the fields with the initial values
                updateFields();
                // populate the spinners with the current position of the telescope
                startingValues();
                // start the updating timer now that initial values have been retrieved
                updateTimer.start();
//            DebugError( "Finished processing initializationWorker thread's contents." );
                IS_UPDATING = false;
            }
        };
        initializationWorker.execute();

    // values initialization complete
    }

    private void updateTimerActionPerformed()
    {
        // if already updating, do nothing
        if ( !IS_UPDATING )
            updatingWorker(); // end if ( !IS_UPDATING )

    // timer action complete
    }

    private void updatingWorker()
    {
        // mark us as updating
        IS_UPDATING = true;
        // Background task for updating values from the manager
        updateWorker = new SwingWorker<Void, HashMap<String, String>>()
        {
            // retrieve values from the manager
            @Override
            public Void doInBackground()
            {
//                DebugError( "Starting updateWorker thread..." );
                while ( !isCancelled() )
                {
                    HashMap<String, String> innerMap = new HashMap<String, String>();
                    innerMap.put( "ALT", myTelescope.getAlt() );
                    innerMap.put( "AZ", myTelescope.getAz() );
                    innerMap.put( "RA", myTelescope.getRa() );
                    innerMap.put( "DEC", myTelescope.getDec() );
//                    innerMap.put( "HA", myTelescope.getHA() );
//                    Debug( "HA: " + innerMap.get("HA") );
//                    Debug( "innerMap size: " + innerMap.size() );
                    // publish intermediate results
                    publish( innerMap );
                    try
                    {
                        Thread.sleep( 3000 );
                    }
                    catch ( InterruptedException ex )
                    {
                        // since there was an error, thread will be stopped
                        // mark us as no longer updating
                        IS_UPDATING = false;
                    }
                }
                // thread became cancelled; mark us as no longer updating
                IS_UPDATING = false;
//                DebugError( "Finished updateWorker thread." );
                return null;
            }

            @Override
            public void process( List<HashMap<String, String>> chunks )
            {
//                DebugError( "Starting to process updateWorker thread's contents..." );
                // store last set of values into telescopeValues map
                telescopeValues = chunks.get( chunks.size() - 1 );
                // update display with latest values
                updateFields();
//                DebugError( "Finished processing updateWorker thread's contents." );
            }
            
            @Override
            public void done()
            {
            	IS_UPDATING = false;
            }
        };
        // make me update
        updateWorker.execute();

    // updating worker complete
    }

    private void updateFields()
    {
        // @todo -- still need to know how to calculate HA
        HAstatusTextField.setText( "Not Implemented." );
        // @todo -- still need to know how to calculate AM
        AMstatusTextField.setText( "Not Implemented." );
        ALTstatusTextField.setText( telescopeValues.get( "ALT" ) );
        AZstatusTextField.setText( telescopeValues.get( "AZ" ) );
        RAstatusTextField.setText( telescopeValues.get( "RA" ) );
        DECstatusTextField.setText( telescopeValues.get( "DEC" ) );

    // updating fields complete
    }

    private void startingValues()
    {
        Debug( "Starting RA: " + telescopeValues.get( "RA" ) );
        // tokenize the RA received with latest value
        StringTokenizer RAtext = new StringTokenizer( telescopeValues.get( "RA" ), ":", false );
        if ( RAtext.hasMoreTokens() )
        {
            // leave off the plus sign when parsing the first token
            RAinputHoursSpinner.setValue( Integer.parseInt( RAtext.nextToken().replace( "+", "" ) ) );
            RAinputMinutesSpinner.setValue( Integer.parseInt( RAtext.nextToken() ) );
            RAinputSecondsSpinner.setValue( Double.parseDouble( RAtext.nextToken() ) );
        } // end if ( RAtext.hasMoreTokens() )

        Debug( "Starting DEC: " + telescopeValues.get( "DEC" ) );
        // tokenize the DEC received with latest value
        StringTokenizer DECtext = new StringTokenizer( telescopeValues.get( "DEC" ), ":", false );
        if ( DECtext.hasMoreTokens() )
        {
            // leave off the plus sign when parsing the first token
            DECinputDegreesSpinner.setValue( Integer.parseInt( DECtext.nextToken().replace( "+", "" ) ) );
            DECinputMinutesSpinner.setValue( Integer.parseInt( DECtext.nextToken() ) );
            DECinputSecondsSpinner.setValue( Double.parseDouble( DECtext.nextToken() ) );
        } // end if ( DECtext.hasMoreTokens() )

    // starting values complete
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {
        java.awt.GridBagConstraints gridBagConstraints;

        jFormattedTextField1 = new javax.swing.JFormattedTextField();
        jSpinner7 = new javax.swing.JSpinner();
        jSpinner8 = new javax.swing.JSpinner();
        jSpinner9 = new javax.swing.JSpinner();
        jSpinner10 = new javax.swing.JSpinner();
        MoveSpeedPanel = new javax.swing.JPanel();
        SlewToggleButton = new javax.swing.JToggleButton();
        GuideToggleButton = new javax.swing.JToggleButton();
        TrackToggleButton = new javax.swing.JToggleButton();
        InputPanel = new javax.swing.JPanel();
        RAinputLabel = new javax.swing.JLabel();
        DECinputLabel = new javax.swing.JLabel();
        EPOCHinputLabel = new javax.swing.JLabel();
        EPOCHinputFormattedTextField = new javax.swing.JFormattedTextField();
        SLEWinputButton = new javax.swing.JButton();
        NAMEinputLabel = new javax.swing.JLabel();
        NAMEinputTextField = new javax.swing.JTextField();
        GETCOORDINATESinputButton = new javax.swing.JButton();
        RAinputHoursSpinner = new javax.swing.JSpinner();
        RAinputMinutesSpinner = new javax.swing.JSpinner();
        RAinputSecondsSpinner = new javax.swing.JSpinner();
        DECinputDegreesSpinner = new javax.swing.JSpinner();
        DECinputMinutesSpinner = new javax.swing.JSpinner();
        DECinputSecondsSpinner = new javax.swing.JSpinner();
        StatusPanel = new javax.swing.JPanel();
        HAstatusLabel = new javax.swing.JLabel();
        HAstatusTextField = new javax.swing.JTextField();
        AMstatusLabel = new javax.swing.JLabel();
        AMstatusTextField = new javax.swing.JTextField();
        ALTstatusLabel = new javax.swing.JLabel();
        ALTstatusTextField = new javax.swing.JTextField();
        AZstatusLabel = new javax.swing.JLabel();
        AZstatusTextField = new javax.swing.JTextField();
        RAstatusLabel = new javax.swing.JLabel();
        RAstatusTextField = new javax.swing.JTextField();
        DECstatusLabel = new javax.swing.JLabel();
        DECstatusTextField = new javax.swing.JTextField();
        MovePanel = new javax.swing.JPanel();
        MoveDirectionPanel = new javax.swing.JPanel();
        MoveNorthButton = new javax.swing.JButton();
        MoveWestButton = new javax.swing.JButton();
        MoveEastButton = new javax.swing.JButton();
        MoveSouthButton = new javax.swing.JButton();
        MoveOptionsPanel = new javax.swing.JPanel();
        MoveOptionsComboBox = new javax.swing.JComboBox();
        MoveOptionsTextField = new javax.swing.JTextField();

        jFormattedTextField1.setText("jFormattedTextField1");

        MoveSpeedPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Speed"));
        MoveSpeedPanel.setLayout(new java.awt.GridBagLayout());

        SlewToggleButton.setText("Slew");
        SlewToggleButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                SlewToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTHWEST;
        gridBagConstraints.weightx = 1.0;
        MoveSpeedPanel.add(SlewToggleButton, gridBagConstraints);

        GuideToggleButton.setText("Guide");
        GuideToggleButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                GuideToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.PAGE_START;
        gridBagConstraints.weightx = 1.0;
        MoveSpeedPanel.add(GuideToggleButton, gridBagConstraints);

        TrackToggleButton.setSelected(true);
        TrackToggleButton.setText("Track");
        TrackToggleButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                TrackToggleButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.PAGE_START;
        gridBagConstraints.weightx = 1.0;
        MoveSpeedPanel.add(TrackToggleButton, gridBagConstraints);

        setDefaultCloseOperation(javax.swing.WindowConstants.HIDE_ON_CLOSE);
        setTitle("Telescope Controls");
        try {
            setSelected(true);
        } catch (java.beans.PropertyVetoException e1) {
            e1.printStackTrace();
        }
        setVisible(true);

        InputPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Input"));
        InputPanel.setLayout(new java.awt.GridBagLayout());

        RAinputLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        RAinputLabel.setText("RA:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(RAinputLabel, gridBagConstraints);

        DECinputLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        DECinputLabel.setText("DEC:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(DECinputLabel, gridBagConstraints);

        EPOCHinputLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        EPOCHinputLabel.setText("EPOCH:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(EPOCHinputLabel, gridBagConstraints);

        EPOCHinputFormattedTextField.setColumns(5);
        EPOCHinputFormattedTextField.setFormatterFactory(new javax.swing.text.DefaultFormatterFactory(new javax.swing.text.NumberFormatter(new java.text.DecimalFormat("0000"))));
        EPOCHinputFormattedTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        EPOCHinputFormattedTextField.setText("J2000");
        EPOCHinputFormattedTextField.setToolTipText("EPOCH Year");
        EPOCHinputFormattedTextField.addFocusListener(new java.awt.event.FocusAdapter() {
            public void focusGained(java.awt.event.FocusEvent evt) {
                EPOCHinputFormattedTextFieldFocusGained(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 5;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(EPOCHinputFormattedTextField, gridBagConstraints);

        SLEWinputButton.setText("SLEW");
        SLEWinputButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                SLEWinputButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 6;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(SLEWinputButton, gridBagConstraints);

        NAMEinputLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        NAMEinputLabel.setText("Name:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 7;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.gridheight = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.insets = new java.awt.Insets(23, 0, 0, 0);
        InputPanel.add(NAMEinputLabel, gridBagConstraints);

        NAMEinputTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        NAMEinputTextField.setToolTipText("Name to find");
        NAMEinputTextField.addFocusListener(new java.awt.event.FocusAdapter() {
            public void focusGained(java.awt.event.FocusEvent evt) {
                NAMEinputTextFieldFocusGained(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 9;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(NAMEinputTextField, gridBagConstraints);

        GETCOORDINATESinputButton.setText("Get Coordinates");
        GETCOORDINATESinputButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                GETCOORDINATESinputButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 10;
        gridBagConstraints.gridwidth = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        InputPanel.add(GETCOORDINATESinputButton, gridBagConstraints);

        RAinputHoursSpinner.setModel(new javax.swing.SpinnerNumberModel(0, -1, 24, 1));
        RAinputHoursSpinner.setToolTipText("Hours");
        RAinputHoursSpinner.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                RAinputHoursSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        InputPanel.add(RAinputHoursSpinner, gridBagConstraints);

        RAinputMinutesSpinner.setModel(new javax.swing.SpinnerNumberModel(0, -1, 60, 1));
        RAinputMinutesSpinner.setToolTipText("Minutes");
        RAinputMinutesSpinner.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                RAinputMinutesSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        InputPanel.add(RAinputMinutesSpinner, gridBagConstraints);

        RAinputSecondsSpinner.setModel(new javax.swing.SpinnerNumberModel(0.0d, -0.001d, 60.0d, 0.001d));
        RAinputSecondsSpinner.setToolTipText("Seconds");
        RAinputSecondsSpinner.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                RAinputSecondsSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 2;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        InputPanel.add(RAinputSecondsSpinner, gridBagConstraints);

        DECinputDegreesSpinner.setModel(new javax.swing.SpinnerNumberModel(0, -91, 90, 1));
        DECinputDegreesSpinner.setToolTipText("Degrees");
        DECinputDegreesSpinner.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                DECinputDegreesSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        InputPanel.add(DECinputDegreesSpinner, gridBagConstraints);

        DECinputMinutesSpinner.setModel(new javax.swing.SpinnerNumberModel(0, -60, 60, 1));
        DECinputMinutesSpinner.setToolTipText("Minutes");
        DECinputMinutesSpinner.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                DECinputMinutesSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 1;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        InputPanel.add(DECinputMinutesSpinner, gridBagConstraints);

        DECinputSecondsSpinner.setModel(new javax.swing.SpinnerNumberModel(0.0d, -60.0d, 60.001d, 0.001d));
        DECinputSecondsSpinner.setToolTipText("Seconds");
        DECinputSecondsSpinner.addChangeListener(new javax.swing.event.ChangeListener() {
            public void stateChanged(javax.swing.event.ChangeEvent evt) {
                DECinputSecondsSpinnerStateChanged(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 2;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        InputPanel.add(DECinputSecondsSpinner, gridBagConstraints);

        StatusPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Status"));
        StatusPanel.setLayout(new java.awt.GridBagLayout());

        HAstatusLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        HAstatusLabel.setText("HA:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(HAstatusLabel, gridBagConstraints);

        HAstatusTextField.setEditable(false);
        HAstatusTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        HAstatusTextField.setMinimumSize(new java.awt.Dimension(111, 20));
        HAstatusTextField.setPreferredSize(new java.awt.Dimension(111, 20));
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(HAstatusTextField, gridBagConstraints);

        AMstatusLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        AMstatusLabel.setText("AM:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 2;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(AMstatusLabel, gridBagConstraints);

        AMstatusTextField.setEditable(false);
        AMstatusTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 3;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(AMstatusTextField, gridBagConstraints);

        ALTstatusLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        ALTstatusLabel.setText("ALT:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 4;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(ALTstatusLabel, gridBagConstraints);

        ALTstatusTextField.setEditable(false);
        ALTstatusTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 5;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(ALTstatusTextField, gridBagConstraints);

        AZstatusLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        AZstatusLabel.setText("AZ:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 6;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(AZstatusLabel, gridBagConstraints);

        AZstatusTextField.setEditable(false);
        AZstatusTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 7;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(AZstatusTextField, gridBagConstraints);

        RAstatusLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        RAstatusLabel.setText("RA:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 8;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(RAstatusLabel, gridBagConstraints);

        RAstatusTextField.setEditable(false);
        RAstatusTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 9;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(RAstatusTextField, gridBagConstraints);

        DECstatusLabel.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        DECstatusLabel.setText("DEC:");
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 10;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(DECstatusLabel, gridBagConstraints);

        DECstatusTextField.setEditable(false);
        DECstatusTextField.setHorizontalAlignment(javax.swing.JTextField.CENTER);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 11;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        gridBagConstraints.weightx = 1.0;
        StatusPanel.add(DECstatusTextField, gridBagConstraints);

        MovePanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Move"));
        MovePanel.setLayout(new java.awt.GridBagLayout());

        MoveDirectionPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Direction"));
        MoveDirectionPanel.setLayout(new java.awt.GridBagLayout());

        MoveNorthButton.setText("N");
        MoveNorthButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                MoveNorthButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridwidth = java.awt.GridBagConstraints.REMAINDER;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTH;
        MoveDirectionPanel.add(MoveNorthButton, gridBagConstraints);

        MoveWestButton.setText("W");
        MoveWestButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                MoveWestButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.anchor = java.awt.GridBagConstraints.WEST;
        MoveDirectionPanel.add(MoveWestButton, gridBagConstraints);

        MoveEastButton.setText("E");
        MoveEastButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                MoveEastButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridwidth = java.awt.GridBagConstraints.REMAINDER;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.EAST;
        MoveDirectionPanel.add(MoveEastButton, gridBagConstraints);

        MoveSouthButton.setText("S");
        MoveSouthButton.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                MoveSouthButtonActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridwidth = java.awt.GridBagConstraints.REMAINDER;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.SOUTH;
        MoveDirectionPanel.add(MoveSouthButton, gridBagConstraints);

        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.anchor = java.awt.GridBagConstraints.NORTHEAST;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        MovePanel.add(MoveDirectionPanel, gridBagConstraints);

        MoveOptionsPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Options"));
        MoveOptionsPanel.setLayout(new java.awt.GridBagLayout());

        MoveOptionsComboBox.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "30\"", "1'", "5'", "15'", "30'", "1°", "----------", "Other" }));
        MoveOptionsComboBox.setSelectedIndex(6);
        MoveOptionsComboBox.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                MoveOptionsComboBoxActionPerformed(evt);
            }
        });
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        MoveOptionsPanel.add(MoveOptionsComboBox, gridBagConstraints);

        MoveOptionsTextField.setToolTipText("Valid values: #h, #d, #m, #s -- ie. 12s = 12 seconds");
        MoveOptionsTextField.setEnabled(false);
        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        MoveOptionsPanel.add(MoveOptionsTextField, gridBagConstraints);

        gridBagConstraints = new java.awt.GridBagConstraints();
        gridBagConstraints.gridx = 0;
        gridBagConstraints.gridy = 1;
        gridBagConstraints.fill = java.awt.GridBagConstraints.BOTH;
        gridBagConstraints.weightx = 1.0;
        gridBagConstraints.weighty = 1.0;
        MovePanel.add(MoveOptionsPanel, gridBagConstraints);

        javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addComponent(InputPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(StatusPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(MovePanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING, false)
                    .addComponent(MovePanel, javax.swing.GroupLayout.Alignment.LEADING, 0, 0, Short.MAX_VALUE)
                    .addComponent(StatusPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(InputPanel, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addContainerGap(31, Short.MAX_VALUE))
        );

        pack();
    }// </editor-fold>//GEN-END:initComponents
    private void SlewToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_SlewToggleButtonActionPerformed
    {//GEN-HEADEREND:event_SlewToggleButtonActionPerformed
        if ( SlewToggleButton.isSelected() )
        {
            GuideToggleButton.setSelected( false );
            TrackToggleButton.setSelected( false );
        }
        else
            SlewToggleButton.setSelected( true );   // end else // end if ( SlewToggleButton.isSelected() )
    }//GEN-LAST:event_SlewToggleButtonActionPerformed

    private void GuideToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_GuideToggleButtonActionPerformed
    {//GEN-HEADEREND:event_GuideToggleButtonActionPerformed
        if ( GuideToggleButton.isSelected() )
        {
            SlewToggleButton.setSelected( false );
            TrackToggleButton.setSelected( false );
        }
        else
            GuideToggleButton.setSelected( true );   // end else // end if ( GuideToggleButton.isSelected() )
    }//GEN-LAST:event_GuideToggleButtonActionPerformed

    private void TrackToggleButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_TrackToggleButtonActionPerformed
    {//GEN-HEADEREND:event_TrackToggleButtonActionPerformed
        if ( TrackToggleButton.isSelected() )
        {
            SlewToggleButton.setSelected( false );
            GuideToggleButton.setSelected( false );
        }
        else
            TrackToggleButton.setSelected( true );   // end else // end if ( TrackToggleButton.isSelected() )
    }//GEN-LAST:event_TrackToggleButtonActionPerformed

    private double calculateArcseconds()
    {
        double returnValue = 0.0d;
        switch ( MoveOptionsComboBox.getSelectedIndex() )
        {
            case 6:
                // Do nothing -- not a valid option
                JOptionPane.showMessageDialog( null, "Not a valid option choosen! Please select a value from the dropdown list.", "Error!", JOptionPane.ERROR_MESSAGE );
                MoveOptionsComboBox.requestFocusInWindow();
                break;
            case 7:
                // Other option selected -- convert to arcseconds
                String value = MoveOptionsTextField.getText();
                if ( value.length() < 1 )
                {
                    JOptionPane.showMessageDialog( null, "Not a valid value passed in! Please enter in a value in the form of #h, #m, #s, or #d -- ie. 12s = 12 seconds.", "Error!", JOptionPane.ERROR_MESSAGE );
                    MoveOptionsTextField.requestFocusInWindow();
                    MoveOptionsTextField.selectAll();
                    break;
                } // end if ( condvalue.length() < 1
                switch ( value.charAt( value.length() - 1 ) )
                {
                    case 'h':
//                        DebugError( "HOURS" );
                        returnValue = Double.parseDouble( value.substring( 0, value.length() - 1 ) ) * 54000.0d;
                        break;
                    case 'm':
//                        DebugError( "MINUTES" );
                        returnValue = Double.parseDouble( value.substring( 0, value.length() - 1 ) ) * 60.0d;
                        break;
                    case 's':
//                        DebugError( "SECONDS" );
                        returnValue = Double.parseDouble( value.substring( 0, value.length() - 1 ) );
                        break;
                    case 'd':
//                        DebugError( "DEGREES" );
                        returnValue = Double.parseDouble( value.substring( 0, value.length() - 1 ) ) * 3600.0d;
                        break;
                    default:
                        JOptionPane.showMessageDialog( null, "Not a valid value passed in! Please enter in a value in the form of #h, #m, #s, or #d -- ie. 12s = 12 seconds.", "Error!", JOptionPane.ERROR_MESSAGE );
                        MoveOptionsTextField.requestFocusInWindow();
                        MoveOptionsTextField.selectAll();
                        return returnValue;

                } // switch ( value.charAt(value.length()-1) )
//                DebugError( "Value to slew: " + returnValue );

                break;
            case 5:
                // 1 degree selected
                returnValue = 3600.0d;
                break;
            case 0:
                // 30 seconds selected
                returnValue = 30.0d;
                break;
            default:
                // other options in the list
                returnValue = Double.parseDouble( MoveOptionsComboBox.getSelectedItem().toString().substring( 0, MoveOptionsComboBox.getSelectedItem().toString().length() - 1 ) ) * 60.0d;
                break;
        } // switch ( MoveOptionsComboBox.getSelectedIndex() )

        return returnValue;
    }

    private void MoveNorthButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_MoveNorthButtonActionPerformed
    {//GEN-HEADEREND:event_MoveNorthButtonActionPerformed
        double offset = calculateArcseconds();

        if ( offset != 0.0d )
            myTelescope.moveNorth( offset );
        initializationWorker();
    }//GEN-LAST:event_MoveNorthButtonActionPerformed

    private void MoveWestButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_MoveWestButtonActionPerformed
    {//GEN-HEADEREND:event_MoveWestButtonActionPerformed
        double offset = calculateArcseconds();

        if ( offset != 0.0d )
            myTelescope.moveWest( offset );
        initializationWorker();
    }//GEN-LAST:event_MoveWestButtonActionPerformed

    private void MoveEastButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_MoveEastButtonActionPerformed
    {//GEN-HEADEREND:event_MoveEastButtonActionPerformed
        double offset = calculateArcseconds();

        if ( offset != 0.0d )
            myTelescope.moveEast( offset );
        initializationWorker();
    }//GEN-LAST:event_MoveEastButtonActionPerformed

    private void MoveSouthButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_MoveSouthButtonActionPerformed
    {//GEN-HEADEREND:event_MoveSouthButtonActionPerformed
        double offset = calculateArcseconds();

        if ( offset != 0.0d )
            myTelescope.moveSouth( offset );
        initializationWorker();
    }//GEN-LAST:event_MoveSouthButtonActionPerformed

    private void NAMEinputTextFieldFocusGained(java.awt.event.FocusEvent evt)//GEN-FIRST:event_NAMEinputTextFieldFocusGained
    {//GEN-HEADEREND:event_NAMEinputTextFieldFocusGained
        ((JTextField)(evt.getSource())).selectAll();
    }//GEN-LAST:event_NAMEinputTextFieldFocusGained

    private void EPOCHinputFormattedTextFieldFocusGained(java.awt.event.FocusEvent evt)//GEN-FIRST:event_EPOCHinputFormattedTextFieldFocusGained
    {//GEN-HEADEREND:event_EPOCHinputFormattedTextFieldFocusGained
        ((JFormattedTextField)(evt.getSource())).selectAll();
}//GEN-LAST:event_EPOCHinputFormattedTextFieldFocusGained

    private void MoveOptionsComboBoxActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_MoveOptionsComboBoxActionPerformed
    {//GEN-HEADEREND:event_MoveOptionsComboBoxActionPerformed
        if ( ((JComboBox)evt.getSource()).getSelectedIndex() == 7 )
        {
            MoveOptionsTextField.setEnabled( true );
            MoveOptionsTextField.requestFocusInWindow();
            MoveOptionsTextField.selectAll();
        }
        else
            MoveOptionsTextField.setEnabled( false );
    }//GEN-LAST:event_MoveOptionsComboBoxActionPerformed

    private void RAinputSecondsSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_RAinputSecondsSpinnerStateChanged
    {//GEN-HEADEREND:event_RAinputSecondsSpinnerStateChanged
        /*
         *  if sec > 59.999     // need to ++min
         *      if min > 58     // need to ++hr
         *          if hr > 22  // means it is 23+ which will make us over
         *              maxinput
         *              return
         *      sec = 0
         *      ++min
         *  else if sec < 0     // need to --min
         *      if min < 1      // need to --hr
         *          if hr < 1   // means it is 0- which will make us under
         *              mininput
         *              return
         *      --min
         *      sec = 59.999
         * 
         */
        double seconds = Double.parseDouble( RAinputSecondsSpinner.getValue().toString() );
        int minutes = Integer.parseInt( RAinputMinutesSpinner.getValue().toString() );
        int hours = Integer.parseInt( RAinputHoursSpinner.getValue().toString() );
        if ( seconds > 59.999 )
        {
            if ( minutes > 58 )
                if ( hours > 22 )
                {
                    maxRAinputs();
                    return;
                }
            RAinputSecondsSpinner.setValue( 0.0d );
            RAinputMinutesSpinner.setValue( minutes + 1 );
        }
        else if ( seconds < 0 )
        {
            if ( minutes < 1 )
                if ( hours < 1 )
                {
                    minRAinputs();
                    return;
                }
            RAinputMinutesSpinner.setValue( minutes - 1 );
            RAinputSecondsSpinner.setValue( 59.999d );
        }
        else if ( hours > 23 )
        {
            maxRAinputs();
            return;
        }
    }//GEN-LAST:event_RAinputSecondsSpinnerStateChanged

    private void RAinputMinutesSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_RAinputMinutesSpinnerStateChanged
    {//GEN-HEADEREND:event_RAinputMinutesSpinnerStateChanged
        /*
         *  if min > 59         // need to ++hr
         *      if hr > 22      // means it is 23+ which will make us over
         *          maxinput
         *          return
         *      min = 0
         *      ++hr
         *  else if min < 0     // need to --hr
         *      if hr < 1       // means it is 0- which will make us under
         *          mininput
         *          return
         *      --hr
         *      min = 59
         * 
         */
        int minutes = Integer.parseInt( RAinputMinutesSpinner.getValue().toString() );
        int hours = Integer.parseInt( RAinputHoursSpinner.getValue().toString() );
        if ( minutes > 59 )
        {
            if ( hours > 22 )
            {
                maxRAinputs();
                return;
            }
            RAinputMinutesSpinner.setValue( 0 );
            RAinputHoursSpinner.setValue( hours + 1 );
        }
        else if ( minutes < 0 )
        {
            if ( hours < 1 )
            {
                minRAinputs();
                return;
            }
            RAinputHoursSpinner.setValue( hours - 1 );
            RAinputMinutesSpinner.setValue( 59 );
        }
        else if ( hours > 23 )
        {
            maxRAinputs();
            return;
        }
    }//GEN-LAST:event_RAinputMinutesSpinnerStateChanged

    private void RAinputHoursSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_RAinputHoursSpinnerStateChanged
    {//GEN-HEADEREND:event_RAinputHoursSpinnerStateChanged
        int hours = Integer.parseInt( RAinputHoursSpinner.getValue().toString() );
        if ( hours > 23 )
            maxRAinputs();
        else if ( hours < 0 )
            minRAinputs();
    }//GEN-LAST:event_RAinputHoursSpinnerStateChanged

    private void maxRAinputs()
    {
        RAinputHoursSpinner.setValue( 24 );
        RAinputMinutesSpinner.setValue( 0 );
        RAinputSecondsSpinner.setValue( 0.0d );
    }

    private void minRAinputs()
    {
        RAinputHoursSpinner.setValue( 0 );
        RAinputMinutesSpinner.setValue( 0 );
        RAinputSecondsSpinner.setValue( 0.0d );
    }

    private void DECinputSecondsSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_DECinputSecondsSpinnerStateChanged
    {//GEN-HEADEREND:event_DECinputSecondsSpinnerStateChanged
        double seconds = Double.parseDouble( DECinputSecondsSpinner.getValue().toString() );
        int minutes = Integer.parseInt( DECinputMinutesSpinner.getValue().toString() );
        int degrees = Integer.parseInt( DECinputDegreesSpinner.getValue().toString() );
        if ( degrees > -1 ) //degrees is positive
        {
            if ( seconds > 59.999 )
            {
                if ( minutes > 58 )
                    if ( degrees > 88 )
                    {
                        maxDECinputs();
                        return;
                    }
                DECinputSecondsSpinner.setValue( 0.0d );
                DECinputMinutesSpinner.setValue( minutes + 1 );
            }
            else if ( seconds < 0 )
            {
                DECinputMinutesSpinner.setValue( minutes - 1 );
                DECinputSecondsSpinner.setValue( 59.999d );
            }
            else if ( degrees > 89 )
            {
                maxDECinputs();
                return;
            }
        }
        else if ( seconds > 59.999 )
        {
            DECinputSecondsSpinner.setValue( 0.0d );
            DECinputMinutesSpinner.setValue( minutes - 1 );
        }
        else if ( seconds < 0 )
        {
            if ( minutes < 1 )
                if ( degrees < -89 )
                {
                    minDECinputs();
                    return;
                }
            DECinputMinutesSpinner.setValue( minutes + 1 );
            DECinputSecondsSpinner.setValue( 59.999d );
        }
            
    }//GEN-LAST:event_DECinputSecondsSpinnerStateChanged

    private void DECinputMinutesSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_DECinputMinutesSpinnerStateChanged
    {//GEN-HEADEREND:event_DECinputMinutesSpinnerStateChanged
        int minutes = Integer.parseInt( DECinputMinutesSpinner.getValue().toString() );
        int degrees = Integer.parseInt( DECinputDegreesSpinner.getValue().toString() );
        if ( degrees > -1 ) //degrees is positive
        {
            if ( minutes > 59 )
            {
                if ( degrees > 88 )
                {
                    maxDECinputs();
                    return;
                }
                DECinputMinutesSpinner.setValue( 0 );
                DECinputDegreesSpinner.setValue( degrees + 1 );
            }
            else if ( minutes < 0 )
            {
                DECinputDegreesSpinner.setValue( degrees - 1 );
                DECinputMinutesSpinner.setValue( 59 );
            }
            else if ( degrees > 89 )
            {
                maxDECinputs();
                return;
            }
        }
        else if ( minutes > 59 )
        {
            DECinputMinutesSpinner.setValue( 0 );
            DECinputDegreesSpinner.setValue( degrees - 1 );
        }
        else if ( minutes < 0 )
        {
            DECinputDegreesSpinner.setValue( degrees + 1 );
            DECinputMinutesSpinner.setValue( 59 );
        }
            
    }//GEN-LAST:event_DECinputMinutesSpinnerStateChanged

    private void DECinputDegreesSpinnerStateChanged(javax.swing.event.ChangeEvent evt)//GEN-FIRST:event_DECinputDegreesSpinnerStateChanged
    {//GEN-HEADEREND:event_DECinputDegreesSpinnerStateChanged
        int degrees = Integer.parseInt( DECinputDegreesSpinner.getValue().toString() );
        if ( degrees > 89 )
            maxDECinputs();
        else if ( degrees < -89 )
            minDECinputs();
    }//GEN-LAST:event_DECinputDegreesSpinnerStateChanged

    private void maxDECinputs()
    {
        DECinputDegreesSpinner.setValue( 90 );
        DECinputMinutesSpinner.setValue( 0 );
        DECinputSecondsSpinner.setValue( 0.0d );
    }

    private void minDECinputs()
    {
        DECinputDegreesSpinner.setValue( -90 );
        DECinputMinutesSpinner.setValue( 0 );
        DECinputSecondsSpinner.setValue( 0.0d );
    }

    private void SLEWinputButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_SLEWinputButtonActionPerformed
    {//GEN-HEADEREND:event_SLEWinputButtonActionPerformed

        StringBuffer RAtext = new StringBuffer();
        RAtext.append( hoursDegreesMinutesFormat.format( RAinputHoursSpinner.getValue() ) + ":" );
        RAtext.append( hoursDegreesMinutesFormat.format( RAinputMinutesSpinner.getValue() ) + ":" );
        RAtext.append( decimalFormat.format( RAinputSecondsSpinner.getValue() ) );
        StringBuffer DECtext = new StringBuffer();
        DECtext.append( hoursDegreesMinutesFormat.format( DECinputDegreesSpinner.getValue() ) + ":" );
        DECtext.append( hoursDegreesMinutesFormat.format( DECinputMinutesSpinner.getValue() ) + ":" );
        DECtext.append( decimalFormat.format( DECinputSecondsSpinner.getValue() ) );
//        DebugError( "Values to send to server:\n\tRA: " + RAtext.toString() + "\n\tDEC: " + DECtext.toString() );
        try
        {
            myTelescope.slewToRaDec( RAtext.toString(), DECtext.toString(), EPOCHinputFormattedTextField.getText() );
        }
        catch ( XmlRpcException ex )
        {
            JOptionPane.showMessageDialog( null, ex.toString(), "Error: SLEW did not work correctly!", JOptionPane.ERROR_MESSAGE );
        }
        initializationWorker();
        
        
    }//GEN-LAST:event_SLEWinputButtonActionPerformed

	private void GETCOORDINATESinputButtonActionPerformed(java.awt.event.ActionEvent evt)//GEN-FIRST:event_GETCOORDINATESinputButtonActionPerformed
	{//GEN-HEADEREND:event_GETCOORDINATESinputButtonActionPerformed
		try
		{
			Position pos = sesame.Client.resolveObject(this.NAMEinputTextField.getText());
			
			this.RAinputHoursSpinner.setValue(pos.raH);
			this.RAinputMinutesSpinner.setValue(pos.raM);
			this.RAinputSecondsSpinner.setValue(pos.raS);
			
			this.DECinputDegreesSpinner.setValue(pos.decD);
			this.DECinputMinutesSpinner.setValue(pos.decM);
			this.DECinputSecondsSpinner.setValue(pos.decS);
		}
        catch ( Exception ex )
        {
            JOptionPane.showMessageDialog( null, ex.toString(), "Error: Unable to get coordinates!", JOptionPane.ERROR_MESSAGE );
        }
        
	}//GEN-LAST:event_GETCOORDINATESinputButtonActionPerformed
	
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JLabel ALTstatusLabel;
    private javax.swing.JTextField ALTstatusTextField;
    private javax.swing.JLabel AMstatusLabel;
    private javax.swing.JTextField AMstatusTextField;
    private javax.swing.JLabel AZstatusLabel;
    private javax.swing.JTextField AZstatusTextField;
    private javax.swing.JSpinner DECinputDegreesSpinner;
    private javax.swing.JLabel DECinputLabel;
    private javax.swing.JSpinner DECinputMinutesSpinner;
    private javax.swing.JSpinner DECinputSecondsSpinner;
    private javax.swing.JLabel DECstatusLabel;
    private javax.swing.JTextField DECstatusTextField;
    private javax.swing.JFormattedTextField EPOCHinputFormattedTextField;
    private javax.swing.JLabel EPOCHinputLabel;
    private javax.swing.JButton GETCOORDINATESinputButton;
    private javax.swing.JToggleButton GuideToggleButton;
    private javax.swing.JLabel HAstatusLabel;
    private javax.swing.JTextField HAstatusTextField;
    private javax.swing.JPanel InputPanel;
    private javax.swing.JPanel MoveDirectionPanel;
    private javax.swing.JButton MoveEastButton;
    private javax.swing.JButton MoveNorthButton;
    private javax.swing.JComboBox MoveOptionsComboBox;
    private javax.swing.JPanel MoveOptionsPanel;
    private javax.swing.JTextField MoveOptionsTextField;
    private javax.swing.JPanel MovePanel;
    private javax.swing.JButton MoveSouthButton;
    private javax.swing.JPanel MoveSpeedPanel;
    private javax.swing.JButton MoveWestButton;
    private javax.swing.JLabel NAMEinputLabel;
    private javax.swing.JTextField NAMEinputTextField;
    private javax.swing.JSpinner RAinputHoursSpinner;
    private javax.swing.JLabel RAinputLabel;
    private javax.swing.JSpinner RAinputMinutesSpinner;
    private javax.swing.JSpinner RAinputSecondsSpinner;
    private javax.swing.JLabel RAstatusLabel;
    private javax.swing.JTextField RAstatusTextField;
    private javax.swing.JButton SLEWinputButton;
    private javax.swing.JToggleButton SlewToggleButton;
    private javax.swing.JPanel StatusPanel;
    private javax.swing.JToggleButton TrackToggleButton;
    private javax.swing.JFormattedTextField jFormattedTextField1;
    private javax.swing.JSpinner jSpinner10;
    private javax.swing.JSpinner jSpinner7;
    private javax.swing.JSpinner jSpinner8;
    private javax.swing.JSpinner jSpinner9;
    // End of variables declaration//GEN-END:variables
    private void Debug( String str )
    {
        if ( DEBUG & str.length() > 0 )
            System.out.println( str ); // end if ( str.length()>0 )
    }

    private void Debug1( String str )
    {
        if ( DEBUG & str.length() > 0 )
            System.out.print( str ); // end if ( str.length()>0 )
    }

    private void DebugError( String str )
    {
        if ( DEBUG & str.length() > 0 )
            System.err.println( str ); // end if ( str.length()>0 )
    }
}
