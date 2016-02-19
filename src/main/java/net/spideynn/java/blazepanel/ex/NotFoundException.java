package net.spideynn.java.blazepanel.ex;

public class NotFoundException extends Exception {

    private String message;

    public NotFoundException() {
        super();
    }

    public NotFoundException(String message) {
        super(message);
        this.message = message;
    }

    public String toString() {
        return message;
    }

    public String getMessage() {
        return message;
    }
}
