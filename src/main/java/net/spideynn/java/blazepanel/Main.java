package net.spideynn.java.blazepanel;

import spark.ModelAndView;
import spark.template.pebble.PebbleTemplateEngine;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.sql.*;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

import static spark.Spark.*;

public class Main {

    private static final String DB_PATH = "data/blazepanel.db";
    private static Connection db;
    private static Properties prop = new Properties();

    public static void main(String[] args) {
        try {
            OutputStream output = new FileOutputStream("data/blazepanel.properties");
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }

        //Config.createJSONObjects();
        //Activity.startAllServers(); TODO: Load all servers, but do not start.
        //Console.console();
        staticFileLocation("/public");
        File dbFile = new File(DB_PATH);
        File dataFolder = new File("data");
        port(30074);
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

        post("/signup", ((request, response) -> {
            Map<String, Object> attr = new HashMap<>();

            return new ModelAndView(attr, "templates/signup.pebble");
        }));

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

        get("/_api", ((request, response) -> {
            return "NYI.";
        }));
        // Catch all other unknown pages. TODO: Fix this to not affect static files.
        /*
        get("/*", (req, res) -> {
            Map<String, Object> attr = new HashMap<>();
            return new ModelAndView(attr, "templates/error/404.pebble");
        }, new PebbleTemplateEngine()); */

        setupExceptions();
    }

    private static void setupExceptions() {
    }

    /**
     * Users API:
     * 1 - Normal User
     * 2 - Moderator
     * 3 - Admin
     * 4 - Super Admin
     */
    private static void createDb() {
        System.out.println("[WEB-UI] Database does not exist, running first time setup...");
        String setup1 = "PRAGMA secure_delete = ON";
        String setup2 = "CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE," +
                "email TEXT UNIQUE, password TEXT, rank INT, tempPass INTEGER)";
        String setup3 = "CREATE TABLE servers(sid INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT," +
                "owner TEXT, jartype TEXT, memory INT, customJartypePath STRING, worldName STRING)";
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

                statement.executeUpdate("INSERT INTO users (username, email, password, rank, tempPass) VALUES (" +
                        username + ", " +
                        email + ", " +
                        password + ", " +
                        "4, " +
                        "0)");
                statement.close();

            } else {
                System.out.println("[SETUP] [WARNING] Could not access current console, setting defaults. " +
                        "Be sure to change your password when you log in.");
                System.out.println("[SETUP] [WARNING] Username: admin");
                System.out.println("[SETUP] [WARNING] Password: blazepanel");
                System.out.println("[SETUP] [WARNING] Email: default@example.com");
                statement.executeUpdate("INSERT INTO users (username, email, password, rank) VALUES (" +
                        "'admin', " +
                        "'default@example.com', '" +
                        Crypto.getSaltedHash("blazepanel") + "', " +
                        "4)");
                statement.close();
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
