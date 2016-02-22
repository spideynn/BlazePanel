package net.spideynn.java.blazepanel;

import com.sun.management.OperatingSystemMXBean;
import net.spideynn.java.blazepanel.util.Crypto;
import net.spideynn.java.blazepanel.util.ServerInfo;
import org.json.simple.JSONObject;
import spark.ModelAndView;
import spark.template.pebble.PebbleTemplateEngine;

import javax.management.MBeanServerConnection;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.sql.*;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

import static spark.Spark.*;

/**
 * Main class for BlazePanel
 */
public class Main {

    /**
     * (Deprecated) Path to database file.
     */ // TODO: Move to config file.
    private static final String DB_PATH = "data/blazepanel.db";
    /** Main database connection for BlazePanel */
    private static Connection db;
    /** Main properties file. */
    private static Properties prop = new Properties();

    /**
     * Main entry point.
     *
     * @param args - Program arguments (unused at the moment)
     */
    public static void main(final String[] args) {
        loadConfig();

        //Config.createJSONObjects();
        //Activity.startAllServers(); TODO: Load all servers, but do not start.
        //Console.console();
        staticFileLocation("/public");
        File dbFile = new File(DB_PATH);
        File dataFolder = new File("data");

        if (!dataFolder.exists()) {
            dataFolder.mkdir();
        }
        if (!dbFile.exists()) {
            try {
                db = DriverManager.getConnection("jdbc:sqlite:" + DB_PATH);
                createDb();
            } catch (SQLException e) {
                e.printStackTrace();
            }
        } else {
            try {
                db = DriverManager.getConnection("jdbc:sqlite:" + DB_PATH);
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }
        setupRoutes();
    }

    /** Loads config variables before defining routes. */
    private static void loadConfig() {
        try {
            File propertiesFile = new File("data/blazepanel.properties");
            if (propertiesFile.exists()) {
                InputStream input = new FileInputStream("data/blazepanel.properties");
                prop.load(input);
                port(new Integer(prop.getProperty("panel.port")));
                if (prop.getProperty("panel.ip") != "0.0.0.0")
                    ipAddress(prop.getProperty("panel.ip").toString());
                if (prop.getProperty("panel.ssl") == "true")
                    setSecure(prop.getProperty("panel.ssl.keystore"), prop.getProperty("panel.ssl.keystore"), null, null);
                input.close();
            } else {
                OutputStream output = new FileOutputStream("data/blazepanel.properties");
                prop.setProperty("panel.port", "30074");
                prop.setProperty("panel.ssl", "false");

                // Convert a x509 Cert and Key to PKCS12: https://stackoverflow.com/questions/906402/importing-an-existing-x509-certificate-and-private-key-in-java-keystore-to-use-i/8224863#8224863
                prop.setProperty("panel.ssl.keystore", "none");
                prop.setProperty("panel.ssl.keystore.pass", "none");
                prop.setProperty("panel.ip", "0.0.0.0");
                prop.store(output, null);
                output.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /** Routes setup. */
    private static void setupRoutes() {
        before(((request1, response1) -> {
            if (!request1.uri().equals("/_api")) {
                System.out.println("[WEB-UI] IP " + request1.ip() + " accessed '" + request1.uri() + "' with UA '" + request1.userAgent() + "'");
            }
        }));

        get("/", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
            Map<String, Object> servers = new HashMap<>();
            Statement statement = db.createStatement();
            ResultSet rs = statement.executeQuery("SELECT name, owner, jartype, sid FROM servers ORDER BY sid DESC");
            statement.close();
            while (rs.next()) {
                Map<String, ServerInfo> server;
                servers.put(rs.getString("sid"), new ServerInfo(rs.getString("name"), rs.getString("jartype"), rs.getString("owner")));
            }
            if (request.session().attribute("logged_in") != null && request.session().attribute("username") != null) {
                attr.put("logged_in", request.session().attribute("logged_in"));
                attr.put("username", request.session().attribute("username"));
            }
            return new ModelAndView(attr, "templates\\home.pebble");
        }, new PebbleTemplateEngine());

        get("/login", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
            request.session(true);

            return new ModelAndView(attr, "templates/login.pebble");
        }, new PebbleTemplateEngine());

        post("/login", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
            Statement statement = db.createStatement();
            if (request.queryParams("username").equals("") && request.queryParams("password").equals("")) {
                attr.put("error", "You forgot to enter your username and your password.");
                return new ModelAndView(attr, "templates/login.pebble");
            } else if (request.queryParams("username").equals("")) {
                attr.put("error", "You forgot to enter your username.");
                return new ModelAndView(attr, "templates/login.pebble");
            } else if (request.queryParams("password").equals("")) {
                attr.put("error", "You forgot to enter your password.");
                return new ModelAndView(attr, "templates/login.pebble");
            }
            String username = request.queryParams("username");
            String password = Crypto.getSaltedHash(request.queryParams("password"));
            ResultSet rs = statement.executeQuery("SELECT * FROM users");
            if (!rs.isBeforeFirst()) {
                attr.put("error", "There are no users registered on this service.");
                return new ModelAndView(attr, "templates/login.pebble");
            }
            while (rs.next()) {
                if (rs.getString("username").equals(username)) {
                    if (Crypto.check(password, rs.getString("password"))) {
                        attr.put("error", "The username or password is incorrect");
                        statement.close();
                        return new ModelAndView(attr, "templates/login.pebble");
                    } else {
                        request.session().attribute("logged_in", "true");
                        request.session().attribute("username", username);
                        attr.put("logged_in", true);
                        attr.put("username", username);
                        statement.close();
                        response.redirect("/");
                    }
                }
            }
            attr.put("error", "The username or password is incorrect.");
            statement.close();
            return new ModelAndView(attr, "templates/login.pebble");
        }, new PebbleTemplateEngine());

        get("/signup", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();

            return new ModelAndView(attr, "templates/signup.pebble");
        }, new PebbleTemplateEngine());

        post("/signup", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
            if (request.queryParams("username").equals("")) {
                attr.put("error", "You forgot to enter a username.");
                return new ModelAndView(attr, "templates/signup.pebble");
            } else if (request.queryParams("password").equals("")) {
                attr.put("error", "You forgot to enter a password.");
                return new ModelAndView(attr, "templates/signup.pebble");
            } else if (request.queryParams("confirmpassword").equals("")) {
                attr.put("error", "You forgot to confirm your password.");
                return new ModelAndView(attr, "templates/signup.pebble");
            } else if (request.queryParams("email").equals("")) {
                attr.put("error", "You forgot to enter an email.");
                return new ModelAndView(attr, "templates/signup.pebble");
            }

            String username = request.queryParams("username");
            String email = request.queryParams("email");
            String pass = request.queryParams("password");
            String confirmpass = request.queryParams("confirmpassword");

            if (!pass.equals(confirmpass)) {
                attr.put("error", "Passwords do not match.");
                return new ModelAndView(attr, "templates/signup.pebble");
            } else {
                String passHash = Crypto.getSaltedHash(request.queryParams("password"));
                PreparedStatement prepare = db.prepareStatement("INSERT INTO users (username, email, password, rank) VALUES (?, ?, ?, 1)");
                prepare.setString(1, username);
                prepare.setString(2, email);
                prepare.setString(3, passHash);
                prepare.executeUpdate();
                prepare.close();
                attr.put("message", "Signed up successfully. You can now log in.");
                response.redirect("/");
            }

            return new ModelAndView(attr, "templates/error/500.pebble");
        }, new PebbleTemplateEngine());

        get("/logout", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
            if (request.session().attribute("logged_in").equals("true") && request.session().attribute("username") != null) {
                request.session().attribute("username", null);
                request.session().attribute("logged_in", null);

                response.redirect("/");
            } else {
                return new ModelAndView(attr, "templates/error/403.pebble");
            }
            return new ModelAndView(attr, "templates/error/500.pebble");
        }, new PebbleTemplateEngine());

        get("/_api", (request, response) -> {
            MBeanServerConnection mbsc = ManagementFactory.getPlatformMBeanServer();

            OperatingSystemMXBean osMBean = ManagementFactory.newPlatformMXBeanProxy(
                    mbsc, ManagementFactory.OPERATING_SYSTEM_MXBEAN_NAME, OperatingSystemMXBean.class);

            long nanoBefore = System.nanoTime();
            long cpuBefore = osMBean.getProcessCpuTime();

            try {
                Thread.sleep(1000);
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
            }

            long cpuAfter = osMBean.getProcessCpuTime();
            long nanoAfter = System.nanoTime();

            long percent;
            if (nanoAfter > nanoBefore)
                percent = ((cpuAfter - cpuBefore) * 100L) / (nanoAfter - nanoBefore);
            else percent = 0;

            JSONObject obj = new JSONObject();

            obj.put("cpu", percent);
            obj.put("ram", 0);
            obj.put("pid", 0);

            return obj.toJSONString();
        });
    }

    /** Setup exception catchers. */
    private static void setupExceptions() {
    }

    /*
     * Users API:
     * 1 - Normal User
     * 2 - Moderator
     * 3 - Admin
     * 4 - Super Admin
     */

    /** Creates database if not found when starting. */
    private static void createDb() {
        System.out.println("[WEB-UI] Database does not exist, running first time setup...");
        String setup1 = "PRAGMA secure_delete = ON";
        String setup2 = "CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE,"
                + "email TEXT UNIQUE, password TEXT, rank INT, tempPass INTEGER)";
        String setup3 = "CREATE TABLE servers(sid INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT,"
                + "owner TEXT, jartype TEXT, memory INT, customJartypePath STRING, worldName STRING)";
        try {
            Statement statement = db.createStatement();
            statement.executeUpdate(setup1);
            statement.executeUpdate(setup2);
            statement.executeUpdate(setup3);
            statement.close();
        } catch (SQLException e) {
            e.printStackTrace();
        }

        try {
            Statement statement = db.createStatement();
            if (System.console() != null) {
                System.out.println("[SETUP] Please enter a username for the first Super Admin account.");
                String username = System.console().readLine();
                System.out.println("[SETUP] Please enter the email for the '" + username + "' account.");
                String email = System.console().readLine();
                System.out.println("[SETUP] Please enter the password for the '" + username + "' account");
                String passString = new String(System.console().readPassword());

                String password = Crypto.getSaltedHash(passString);

                statement.executeUpdate("INSERT INTO users (username, email, password, rank, tempPass) VALUES ("
                        + username + ", "
                        + email + ", "
                        + password + ", "
                        + "4, "
                        + "0)");
                statement.close();

            } else {
                System.out.println("[SETUP] [WARNING] Could not access current console, setting defaults. "
                        + "Be sure to change your password when you log in.");
                System.out.println("[SETUP] [WARNING] Username: admin");
                System.out.println("[SETUP] [WARNING] Password: blazepanel");
                System.out.println("[SETUP] [WARNING] Email: default@example.com");
                statement.executeUpdate("INSERT INTO users (username, email, password, rank) VALUES ("
                        + "'admin', "
                        + "'default@example.com', '"
                        + Crypto.getSaltedHash("blazepanel") + "', "
                        + "4)");
                statement.close();
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
