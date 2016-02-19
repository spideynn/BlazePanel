package net.spideynn.java.blazepanel.serverapi.event;

import net.spideynn.java.blazepanel.serverapi.Server;

public class LoginEvent extends Event {

    public LoginEvent(Server server) {
        super(server, "login", "joined the game");
    }

    @Override
    public String getArgument(String line) {
        String[] str = line.split(this.event)[0].split("\\s+");
        return str[str.length - 1];
    }
}
