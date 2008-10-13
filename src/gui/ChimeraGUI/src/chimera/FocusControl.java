/*
 * FocusControl.java
 *
 * Created on August 3, 2008, 3:39 PM
 */
package chimera;

import java.awt.Color;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.swing.SpinnerNumberModel;

import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.chart.plot.XYPlot;
import org.jfree.chart.renderer.xy.XYLineAndShapeRenderer;
import org.jfree.data.xy.XYDataset;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;

/**
 *
 * @author  Ryan
 */
public class FocusControl extends javax.swing.JInternalFrame
{

    /**
     * xml rpc client and device name
     */
    XmlRpcClient client = null;
    String focusName = "";
    /**
     * final values for focuser
     */
    Integer MIN_POSITION;
    Integer MAX_POSITION;
    /**
     * Small and large steps
     */
    Integer SMALL_STEP;
    Integer LARGE_STEP;
    /**
     * data set series
     */
    XYSeries series1;
    XYSeriesCollection data;
    Double x = 0.0;
    Double y = 0.0;

    /** Creates new form FocusControl */
    public FocusControl(XmlRpcClient client, String focusName)
    {
        this.client = client;
        this.focusName = focusName;
        initComponents();
        setVisible(true);
        smallRadio.setSelected(true);

        getrange();

        positionField.setText("Focus Position: " + getCurrent());

        GOTOspinner.setModel(new SpinnerNumberModel(getCurrent().intValue(), MIN_POSITION.intValue(), MAX_POSITION.intValue(), 1));

        jFStext.setText(MIN_POSITION.toString());
        jFEtext.setText(MAX_POSITION.toString());

        jSexpose.setModel(new SpinnerNumberModel(0, 0, 15, 1));
        jSstart.setModel(new SpinnerNumberModel(0, MIN_POSITION.intValue(), MAX_POSITION.intValue(), 1));
        jSend.setModel(new SpinnerNumberModel(0, MIN_POSITION.intValue(), MAX_POSITION.intValue(), 1));
        jSstep.setModel(new SpinnerNumberModel(0, 0, 500, 100));

        createChartFocus();

    }

    public void getrange()
    {
        try
        {
            Object[] obj = new Object[]
            {
            };
            Object[] result = (Object[]) client.execute(focusName + ".getRange", obj);
            MIN_POSITION = new Integer(result[0].toString());
            MAX_POSITION = new Integer(result[1].toString());

            SMALL_STEP = (MAX_POSITION - MIN_POSITION) / 20;
            LARGE_STEP = (MAX_POSITION - MIN_POSITION) / 10;
        }
        catch (XmlRpcException ex)
        {
            Logger.getLogger(FocusControl.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

    public Integer getCurrent()
    {
        Integer result = 0;
        try
        {
            Object[] obj = new Object[]
            {
            };
            result = (Integer) client.execute(focusName + ".getPosition", obj);
        }
        catch (XmlRpcException ex)
        {
            Logger.getLogger(FocusControl.class.getName()).log(Level.SEVERE, null, ex);
        }
        return result;
    }

    public void createChartFocus()
    {
        final XYDataset dataset = createDataset();
        final JFreeChart chart = createChart(dataset);
        final ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setPreferredSize(jChart.getSize());
        chartPanel.setVisible(true);
        jChart.setContentPane(chartPanel);
    }

    private JFreeChart createChart(XYDataset dataset)
    {
        // create the chart...
        final JFreeChart chart = ChartFactory.createXYLineChart(
                "Focus Chart", // chart title
                "Images", // x axis label
                "Size", // y axis label
                dataset, // data
                PlotOrientation.VERTICAL,
                true, // include legend
                true, // tooltips
                false // urls
                );

        // NOW DO SOME OPTIONAL CUSTOMISATION OF THE CHART...
        chart.setBackgroundPaint(Color.white);
        // get a reference to the plot for further customisation...
        final XYPlot plot = chart.getXYPlot();
        plot.setBackgroundPaint(Color.lightGray);
        plot.setDomainGridlinePaint(Color.white);
        plot.setRangeGridlinePaint(Color.white);

        final XYLineAndShapeRenderer renderer = new XYLineAndShapeRenderer();
        renderer.setSeriesLinesVisible(0, true);
        renderer.setSeriesShapesVisible(1, true);
        plot.setRenderer(renderer);

        // change the auto tick unit selection to integer units only...
        final NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        rangeAxis.setStandardTickUnits(NumberAxis.createStandardTickUnits());
        // OPTIONAL CUSTOMISATION COMPLETED.

        return chart;

    }

    private XYDataset createDataset()
    {
        series1 = new XYSeries("Trial Images");
        data = new XYSeriesCollection();
        data.addSeries(series1);
        return data;
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    @SuppressWarnings("unchecked")
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        focusGroup = new javax.swing.ButtonGroup();
        positionPanel = new javax.swing.JPanel();
        positionField = new javax.swing.JTextField();
        manualPanel = new javax.swing.JPanel();
        INbutton = new javax.swing.JButton();
        OUTbutton = new javax.swing.JButton();
        smallRadio = new javax.swing.JRadioButton();
        largeRadio = new javax.swing.JRadioButton();
        gotoPanel = new javax.swing.JPanel();
        GOTOspinner = new javax.swing.JSpinner();
        GOTObutton = new javax.swing.JButton();
        jPanel1 = new javax.swing.JPanel();
        jSstart = new javax.swing.JSpinner();
        jSexpose = new javax.swing.JSpinner();
        jSend = new javax.swing.JSpinner();
        jSstep = new javax.swing.JSpinner();
        jExpose = new javax.swing.JLabel();
        jStart = new javax.swing.JLabel();
        jEnd = new javax.swing.JLabel();
        jStep = new javax.swing.JLabel();
        jFS = new javax.swing.JLabel();
        jFE = new javax.swing.JLabel();
        jFStext = new javax.swing.JTextField();
        jFEtext = new javax.swing.JTextField();
        jSeparator1 = new javax.swing.JSeparator();
        jPanel2 = new javax.swing.JPanel();
        STARTfocus = new javax.swing.JButton();
        ABORTfocus = new javax.swing.JButton();
        jChart = new javax.swing.JInternalFrame();

        setTitle("Focus Controls");
        setAutoscrolls(true);

        positionPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Current Position"));

        positionField.setEditable(false);

        javax.swing.GroupLayout positionPanelLayout = new javax.swing.GroupLayout(positionPanel);
        positionPanel.setLayout(positionPanelLayout);
        positionPanelLayout.setHorizontalGroup(
            positionPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(positionPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(positionField, javax.swing.GroupLayout.DEFAULT_SIZE, 165, Short.MAX_VALUE)
                .addContainerGap())
        );
        positionPanelLayout.setVerticalGroup(
            positionPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, positionPanelLayout.createSequentialGroup()
                .addContainerGap(javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addComponent(positionField, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap())
        );

        manualPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Manual Adjustment"));

        INbutton.setText("IN");
        INbutton.setToolTipText("Click to move focus IN");
        INbutton.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                INbuttonMouseClicked(evt);
            }
        });

        OUTbutton.setText("OUT");
        OUTbutton.setToolTipText("Click to move focus OUT");
        OUTbutton.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                OUTbuttonMouseClicked(evt);
            }
        });

        focusGroup.add(smallRadio);
        smallRadio.setText("Small (5%)");

        focusGroup.add(largeRadio);
        largeRadio.setText("Large (10%)");

        javax.swing.GroupLayout manualPanelLayout = new javax.swing.GroupLayout(manualPanel);
        manualPanel.setLayout(manualPanelLayout);
        manualPanelLayout.setHorizontalGroup(
            manualPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(manualPanelLayout.createSequentialGroup()
                .addGroup(manualPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(OUTbutton)
                    .addComponent(INbutton, javax.swing.GroupLayout.PREFERRED_SIZE, 92, javax.swing.GroupLayout.PREFERRED_SIZE))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                .addGroup(manualPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(smallRadio)
                    .addComponent(largeRadio)))
        );

        manualPanelLayout.linkSize(javax.swing.SwingConstants.HORIZONTAL, new java.awt.Component[] {INbutton, OUTbutton});

        manualPanelLayout.setVerticalGroup(
            manualPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(manualPanelLayout.createSequentialGroup()
                .addGroup(manualPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(INbutton)
                    .addComponent(smallRadio))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(manualPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(OUTbutton)
                    .addComponent(largeRadio)))
        );

        gotoPanel.setBorder(javax.swing.BorderFactory.createTitledBorder("Goto Index"));

        GOTObutton.setText("GOTO");
        GOTObutton.setToolTipText("Click to goto value specified");
        GOTObutton.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                GOTObuttonMouseClicked(evt);
            }
        });

        javax.swing.GroupLayout gotoPanelLayout = new javax.swing.GroupLayout(gotoPanel);
        gotoPanel.setLayout(gotoPanelLayout);
        gotoPanelLayout.setHorizontalGroup(
            gotoPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, gotoPanelLayout.createSequentialGroup()
                .addComponent(GOTObutton, javax.swing.GroupLayout.DEFAULT_SIZE, 91, Short.MAX_VALUE)
                .addGap(18, 18, 18)
                .addComponent(GOTOspinner, javax.swing.GroupLayout.PREFERRED_SIZE, 66, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(10, 10, 10))
        );
        gotoPanelLayout.setVerticalGroup(
            gotoPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(gotoPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                .addComponent(GOTObutton)
                .addComponent(GOTOspinner, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
        );

        jPanel1.setBorder(javax.swing.BorderFactory.createTitledBorder("Auto Focus"));

        jExpose.setText("Exposer Time:");

        jStart.setText("Start Focus Range:");

        jEnd.setText("End Focus Range:");

        jStep.setText("Step Index For Exposer:");

        jFS.setText("Focus Start:");

        jFE.setText("Focus End:");

        jFStext.setEditable(false);
        jFStext.setHorizontalAlignment(javax.swing.JTextField.RIGHT);

        jFEtext.setEditable(false);
        jFEtext.setHorizontalAlignment(javax.swing.JTextField.RIGHT);

        STARTfocus.setText("START");
        STARTfocus.setEnabled(false);
        STARTfocus.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                STARTfocusMouseClicked(evt);
            }
        });

        ABORTfocus.setText("ABORT");
        ABORTfocus.setEnabled(false);
        ABORTfocus.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                ABORTfocusMouseClicked(evt);
            }
        });

        javax.swing.GroupLayout jPanel2Layout = new javax.swing.GroupLayout(jPanel2);
        jPanel2.setLayout(jPanel2Layout);
        jPanel2Layout.setHorizontalGroup(
            jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel2Layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(STARTfocus, javax.swing.GroupLayout.Alignment.TRAILING, javax.swing.GroupLayout.DEFAULT_SIZE, 113, Short.MAX_VALUE)
                    .addComponent(ABORTfocus, javax.swing.GroupLayout.DEFAULT_SIZE, 113, Short.MAX_VALUE))
                .addContainerGap())
        );
        jPanel2Layout.setVerticalGroup(
            jPanel2Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, jPanel2Layout.createSequentialGroup()
                .addContainerGap()
                .addComponent(STARTfocus, javax.swing.GroupLayout.DEFAULT_SIZE, 75, Short.MAX_VALUE)
                .addGap(22, 22, 22)
                .addComponent(ABORTfocus, javax.swing.GroupLayout.PREFERRED_SIZE, 74, javax.swing.GroupLayout.PREFERRED_SIZE))
        );

        javax.swing.GroupLayout jPanel1Layout = new javax.swing.GroupLayout(jPanel1);
        jPanel1.setLayout(jPanel1Layout);
        jPanel1Layout.setHorizontalGroup(
            jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel1Layout.createSequentialGroup()
                .addGap(18, 18, 18)
                .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(jSeparator1, javax.swing.GroupLayout.Alignment.TRAILING, javax.swing.GroupLayout.DEFAULT_SIZE, 214, Short.MAX_VALUE)
                    .addGroup(jPanel1Layout.createSequentialGroup()
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                            .addComponent(jStep)
                            .addComponent(jEnd)
                            .addComponent(jStart)
                            .addComponent(jExpose)
                            .addComponent(jFS)
                            .addComponent(jFE))
                        .addGap(31, 31, 31)
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING, false)
                            .addComponent(jFEtext)
                            .addComponent(jSend, javax.swing.GroupLayout.DEFAULT_SIZE, 50, Short.MAX_VALUE)
                            .addComponent(jSstart, javax.swing.GroupLayout.DEFAULT_SIZE, 50, Short.MAX_VALUE)
                            .addComponent(jSstep)
                            .addComponent(jFStext, javax.swing.GroupLayout.Alignment.TRAILING, javax.swing.GroupLayout.DEFAULT_SIZE, 65, Short.MAX_VALUE)
                            .addComponent(jSexpose))))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(jPanel2, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap())
        );
        jPanel1Layout.setVerticalGroup(
            jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel1Layout.createSequentialGroup()
                .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addGroup(jPanel1Layout.createSequentialGroup()
                        .addContainerGap()
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(jFS)
                            .addComponent(jFStext, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(jFE)
                            .addComponent(jFEtext, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addComponent(jSeparator1, javax.swing.GroupLayout.PREFERRED_SIZE, 5, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(jExpose)
                            .addComponent(jSexpose, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(jSstart, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                            .addComponent(jStart))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(jSend, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                            .addComponent(jEnd))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(jPanel1Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(jSstep, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                            .addComponent(jStep)))
                    .addComponent(jPanel2, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addContainerGap())
        );

        jChart.setResizable(true);
        jChart.setVisible(true);

        javax.swing.GroupLayout jChartLayout = new javax.swing.GroupLayout(jChart.getContentPane());
        jChart.getContentPane().setLayout(jChartLayout);
        jChartLayout.setHorizontalGroup(
            jChartLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 588, Short.MAX_VALUE)
        );
        jChartLayout.setVerticalGroup(
            jChartLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 283, Short.MAX_VALUE)
        );

        javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(jChart)
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING, false)
                            .addComponent(gotoPanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                            .addComponent(positionPanel, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                            .addComponent(manualPanel, 0, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addComponent(jPanel1, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)))
                .addContainerGap())
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING, false)
                    .addComponent(jPanel1, javax.swing.GroupLayout.Alignment.LEADING, 0, 215, Short.MAX_VALUE)
                    .addGroup(javax.swing.GroupLayout.Alignment.LEADING, layout.createSequentialGroup()
                        .addComponent(manualPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addComponent(gotoPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addComponent(positionPanel, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(jChart)
                .addContainerGap())
        );

        pack();
    }// </editor-fold>//GEN-END:initComponents

private void INbuttonMouseClicked(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_INbuttonMouseClicked
    try
    {
        Integer choice = 0;
        if (smallRadio.isSelected())
        {
            choice = SMALL_STEP;
        }
        else
        {
            choice = LARGE_STEP;
        }
        Integer current = getCurrent();
        if ((current - choice) < MIN_POSITION)
        {
            choice = MIN_POSITION + current;
        }
        Object[] obj = new Object[]//GEN-LAST:event_INbuttonMouseClicked
            {
                new Integer(choice)
            };
            Object val = client.execute(focusName + ".moveIn", obj);
            positionField.setText("Focus Position: " + getCurrent());
        }
        catch (XmlRpcException ex)
        {
            Logger.getLogger(FocusControl.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

private void OUTbuttonMouseClicked(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_OUTbuttonMouseClicked

    try
    {
        Integer choice = 0;
        if (smallRadio.isSelected())
        {
            choice = SMALL_STEP;
        }
        else
        {
            choice = LARGE_STEP;
        }
        Integer current = getCurrent();
        if ((current + choice) > MAX_POSITION)
        {
            choice = MAX_POSITION - current;
        }
        Object[] obj = new Object[]
        {
            new Integer(choice)
        };
        Object val = client.execute(focusName + ".moveOut", obj);
        positionField.setText("Focus Position: " + getCurrent());
    }
    catch (XmlRpcException ex)
    {
        Logger.getLogger(FocusControl.class.getName()).log(Level.SEVERE, null, ex);
    }
}//GEN-LAST:event_OUTbuttonMouseClicked

private void GOTObuttonMouseClicked(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_GOTObuttonMouseClicked

    try
    {

        Integer value = Integer.parseInt(GOTOspinner.getValue().toString());
        if (value > MAX_POSITION)
        {
            value = MAX_POSITION;
        }
        if (value < MIN_POSITION)
        {
            value = MIN_POSITION;
        }
        Object[] obj = new Object[]
        {
            new Integer(value)
        };
        Object val = client.execute(focusName + ".moveTo", obj);
        positionField.setText("Focus Position: " + getCurrent());
    }
    catch (XmlRpcException ex)
    {
        Logger.getLogger(FocusControl.class.getName()).log(Level.SEVERE, null, ex);
    }
}//GEN-LAST:event_GOTObuttonMouseClicked

private void STARTfocusMouseClicked(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_STARTfocusMouseClicked

    series1.add(x++, y++);
    data.removeAllSeries();
    data.addSeries(series1);
}//GEN-LAST:event_STARTfocusMouseClicked

private void ABORTfocusMouseClicked(java.awt.event.MouseEvent evt) {//GEN-FIRST:event_ABORTfocusMouseClicked
    series1.clear();
    data.removeAllSeries();  
    x =0.0;
    y=0.0;
}//GEN-LAST:event_ABORTfocusMouseClicked
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JButton ABORTfocus;
    private javax.swing.JButton GOTObutton;
    private javax.swing.JSpinner GOTOspinner;
    private javax.swing.JButton INbutton;
    private javax.swing.JButton OUTbutton;
    private javax.swing.JButton STARTfocus;
    private javax.swing.ButtonGroup focusGroup;
    private javax.swing.JPanel gotoPanel;
    private javax.swing.JInternalFrame jChart;
    private javax.swing.JLabel jEnd;
    private javax.swing.JLabel jExpose;
    private javax.swing.JLabel jFE;
    private javax.swing.JTextField jFEtext;
    private javax.swing.JLabel jFS;
    private javax.swing.JTextField jFStext;
    private javax.swing.JPanel jPanel1;
    private javax.swing.JPanel jPanel2;
    private javax.swing.JSpinner jSend;
    private javax.swing.JSeparator jSeparator1;
    private javax.swing.JSpinner jSexpose;
    private javax.swing.JSpinner jSstart;
    private javax.swing.JSpinner jSstep;
    private javax.swing.JLabel jStart;
    private javax.swing.JLabel jStep;
    private javax.swing.JRadioButton largeRadio;
    private javax.swing.JPanel manualPanel;
    private javax.swing.JTextField positionField;
    private javax.swing.JPanel positionPanel;
    private javax.swing.JRadioButton smallRadio;
    // End of variables declaration//GEN-END:variables
}
