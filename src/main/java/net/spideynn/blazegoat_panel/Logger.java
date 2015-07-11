package net.spideynn.blazegoat_panel;

public class Logger {
	public void info(String info) {
		System.out.println("[PANEL|INFO] " + info);
	}
	public void warn(String warn) {
		System.out.println("[PANEL|INFO] " + warn);
	}
	public void error(String error) {
		System.out.println("[PANEL|INFO] " + error);
	}
	public void crash(String crash, String ex) {
		System.out.println("[CRASH] BlazeGoat Panel has crashed, please report this error:");
		System.out.println(ex);
	}
}
