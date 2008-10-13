package xpa.exceptions;

public class XpaError extends RuntimeException {

	public XpaError(String cmd, String message) {
		super(cmd + ": " + message);
		// TODO Auto-generated constructor stub
	}

	public XpaError(String cmd, Throwable cause) {
		super(cmd + ": unknown error", cause);
		// TODO Auto-generated constructor stub
	}

	public XpaError(String cmd, String message, Throwable cause) {
		super(message + ": unknown error", cause);
		// TODO Auto-generated constructor stub
	}

}
