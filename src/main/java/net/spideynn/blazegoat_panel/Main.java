package net.spideynn.blazegoat_panel;

import static spark.Spark.*;

import java.util.HashMap;
import java.util.Map;

import spark.ModelAndView;
import spark.template.handlebars.*;

import com.google.gson.Gson;

@SuppressWarnings("unused")
public class Main {

	public static void main(String[] args) {
		routes();
		initDatabase();
		System.out.println("Working Directory = "
				+ System.getProperty("user.dir"));
	}

	/**
	 * Builds routes for all possible URLS.
	 */
	// TODO: Routes, and route functions. Oh, and the pages.
	public static void routes() {
		staticFileLocation("/public");
		Map map = new HashMap(); // provide empty hashmap for now.
		/*
		 * get("/", (request, response) -> new ModelAndView(map,
		 * java.io.File.separator + "index.html"),
		 * new HandlebarsTemplateEngine(System.getProperty("user.dir") +
		 * java.io.File.separator + "templates" + java.io.File.separator));
		 */
		get("/", (request, response) -> {
			return "Welcome page";
		});
		get("/servers/:id", (request, response) -> {
			if (request.params(":id") == "create") {
				return "Create a Server";
			}
			return "Server Panel, ID: " + request.params(":id");
		});
		get("/servers/:id/_:option", (request, response) -> {
			return "Server API functions";
		});
		get("/servers", (request, response) -> {
			return "Servers you own or have access to";
		});
		get("/admin", (request, response) -> {
			return "Admin Index";
		});
		get("/admin/servers", (request, response) -> {
			return "Admin Server Settings";
		});
		get("/admin/panel", (request, response) -> {
			return "Admin Panel Settings";
		});
		get("/admin/users", (request, response) -> {
			return "Admin Users";
		});
		get("/users/:option", (request, response) -> {
			if (request.params(":option") == "register") {
				return "Register";
			} else if (request.params(":option") == "login") {
				return "Login";
			}
			return "404";
		});
		System.out.println("[INFO] Blazegoat Panel 2.0 is now online on port " + spark.Spark.SPARK_DEFAULT_PORT + ".");
	}

	public static void initDatabase() {
		// TODO: Init database stuff
		System.out.println("Database initialization NYI. Continuing.");
	}
}
