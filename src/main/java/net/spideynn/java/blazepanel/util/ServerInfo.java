package net.spideynn.java.blazepanel.util;

public class ServerInfo {
    private String name;
    private String jarType;
    private String owner;
    private boolean isRunning;

    public ServerInfo(String name, String jarType, String owner) {
        this.name = name;
        this.jarType = jarType;
        this.owner = owner;
    }

    public String getName() {
        return name;
    }

    public String getJarType() {
        return jarType;
    }

    public String getOwner() {
        return owner;
    }
}
