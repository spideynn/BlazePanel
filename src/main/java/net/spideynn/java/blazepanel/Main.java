package net.spideynn.java.blazepanel;

import com.google.common.hash.Hashing;
import spark.ModelAndView;
import spark.template.pebble.PebbleTemplateEngine;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.util.HashMap;
import java.util.Map;

import static spark.Spark.*;

public class Main {

    private static final String DB_PATH = "data/blazepanel.db";
    private static Connection db;

    public static void main(String[] args) {
        //Config.createJSONObjects();
        //Activity.startAllServers(); TODO: Load all servers, but do not start.
        //Console.console();
        staticFileLocation("/public");
        File dbFile = new File(DB_PATH);
        File dataFolder = new File ("data");
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
            ResultSet rs = statement.executeQuery("select name, owner, jartype, sid from servers order by sid desc");
            statement.close();
            while (rs.next()) {
                Map<String, ServerInfo> server;
                servers.put(rs.getString("sid"), new ServerInfo(rs.getString("name"), rs.getString("jartype"), rs.getString("owner")));
            }
            return new ModelAndView(attr, "templates\\home.pebble");
        }, new PebbleTemplateEngine());

        get("/login", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
        
            return new ModelAndView(attr, "templates/login.pebble");
        }, new PebbleTemplateEngine());

        post("/login", (request, response) -> {
            Map<String, Object> attr = new HashMap<>();
            Statement statement = db.createStatement();
            String username = request.attribute("username");
            String password = Hashing.sha256().hashString("", StandardCharsets.UTF_8).toString();
            ResultSet rs = statement.executeQuery("select * from users");
            statement.close();
            if (!rs.isBeforeFirst()) {
                attr.put("error", "There are no users registered on this service.");
                return new ModelAndView(attr, "templates/login.pebble");
            }
            while (rs.next()) {
                if (username == rs.getString("username")) {
                    if (password != rs.getString("password")) {
                        attr.put("error", "The username or password is incorrect");
                        return new ModelAndView(attr, "templates/login.pebble");
                    } else {
                        response.cookie("logged_in","true");
                        attr.put("logged_in", true);
                        attr.put("username", username);
                        response.redirect("/");
                    }
                }
            }
            attr.put("error", "The username or password is incorrect.");
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
        // Catch all other unknown pages. TODO: Fix this to not affect static files.
        /*
        get("/*", (req, res) -> {
            Map<String, Object> attr = new HashMap<>();
            return new ModelAndView(attr, "templates/error/404.pebble");
        }, new PebbleTemplateEngine()); */

        setupExceptions();
    }

    private static void setupExceptions() {}

    /** Users API:
     * 1 - Normal User
     * 2 - Moderator
     * 3 - Admin
     * 4 - Super Admin
     */
    private static void createDb() {
        System.out.println("[WEB-UI] Database does not exist, running first time setup...");
        // TODO: Does secure_delete actually do anything?
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

                int ops = statement.executeUpdate("INSERT INTO users (username, email, password, rank, tempPass) VALUES (" +
                        username + ", " +
                        email + ", " +
                        Hashing.sha256().hashString(passString, StandardCharsets.UTF_8) + ", " +
                        "4, " +
                        "0)");
                statement.close();
                System.out.println("[SETUP] [DEBUG] Ran " + ops + " operations on the database.");

            } else {
                System.out.println("[SETUP] [WARNING] Could not access console, setting default. " +
                        "Be sure to change your password when you log in.");
                System.out.println("[SETUP] [WARNING] Username: admin");
                System.out.println("[SETUP] [WARNING] Password: blazepanel");
                System.out.println("[SETUP] [WARNING] Email: default@example.com");
                statement.executeUpdate("INSERT INTO users (username, email, password, rank, tempPass) VALUES (" +
                        "admin, " +
                        "default@example.com, " +
                        Hashing.sha256().hashString("blazepanel", StandardCharsets.UTF_8).toString() + ", " +
                        "4, " +
                        "0)");
                statement.close();
            }

        } catch (SQLException e) {

        }
    }
}
