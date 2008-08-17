package xpa;

import java.io.IOException;

import xpa.exceptions.XpaError;

public class DS9 {
	
	private Xpa xpa;
	
	public DS9() throws IOException
	{
		this.xpa = new Xpa();
		try {
			this.xpa.xpaget("ds9", "file");	//Attempt to contact DS9
		} catch (XpaError xe) {
			//Couldn't contact; try to start ds9
			Runtime.getRuntime().exec("ds9");
			long t = System.currentTimeMillis();
			boolean notRunning = true;
			while (System.currentTimeMillis() < (t + 2000) && notRunning) {
				try {
					Thread.sleep(100);
				} catch (InterruptedException ie) {
					
				}
				try {
					this.xpa.xpaget("ds9", "file");	//Attempt to contact DS9
					notRunning = false;
				} catch (XpaError ixe) {
					//Keep waiting
				}
			}
			if (notRunning) {
				throw xe;
			}
		}
	}
	
	public void loadImageByHostAndHash(String host, String[] hashes) throws IOException
	{
		this.clearFrames();
		for (String hash : hashes) {
			this.xpa.xpaset("ds9", "frame new", false);
			this.xpa.xpaset("ds9", "file url 'http://" + host + "/image/" + hash + "'", true);
		}
	}
	
	public void loadImageURLs(String[] URLs) throws IOException
	{
		this.clearFrames();
		for (String URL : URLs) {
			this.xpa.xpaset("ds9", "frame new", false);
			this.xpa.xpaset("ds9", "file url '" + URL + "'", true);
		}
	}
	
	public void clearFrames() throws IOException
	{
		this.xpa.xpaset("ds9", "frame delete all", false);
		this.xpa.xpaset("ds9", "tile grid", false);
		this.xpa.xpaset("ds9", "tile yes", false);
	}
	
	public void loadURLNewFrame(String URL) throws IOException
	{
		this.xpa.xpaset("ds9", "frame new", false);
		this.xpa.xpaset("ds9", "file url '" + URL + "'", true);
		try {
			Thread.sleep(50);
		} catch (InterruptedException ie) {
			//Do nothing
		}
		//Sometimes, the first load fails
		this.xpa.xpaset("ds9", "file url '" + URL + "'", true);
	}
}
