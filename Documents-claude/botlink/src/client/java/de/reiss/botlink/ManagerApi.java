package de.reiss.botlink;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;

/**
 * Talks to the local Begleiter manager (node manager.js) on 127.0.0.1 only. Everything is async so the
 * render/tick threads never wait on the network; if the manager is not running, calls just fail quietly.
 */
public final class ManagerApi {
	private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofMillis(400)).build();
	private final String basis;
	private volatile boolean erreichbar;

	public ManagerApi(int port) {
		this.basis = "http://127.0.0.1:" + port;
	}

	public boolean erreichbar() {
		return erreichbar;
	}

	public CompletableFuture<JsonObject> get(String pfad) {
		HttpRequest req = HttpRequest.newBuilder(URI.create(basis + pfad)).timeout(Duration.ofSeconds(2)).GET().build();
		return senden(req);
	}

	public CompletableFuture<JsonObject> post(String pfad, JsonObject body) {
		HttpRequest req = HttpRequest.newBuilder(URI.create(basis + pfad))
				.timeout(Duration.ofSeconds(3))
				.header("Content-Type", "application/json")
				.POST(HttpRequest.BodyPublishers.ofString(body.toString()))
				.build();
		return senden(req);
	}

	/** Reiner Text an einen anderen lokalen Dienst (z.B. die Arena auf 47812), Antwort als Text oder null. */
	public CompletableFuture<String> postText(int port, String text) {
		HttpRequest req = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/"))
				.timeout(Duration.ofSeconds(3))
				.POST(HttpRequest.BodyPublishers.ofString(text))
				.build();
		return http.sendAsync(req, HttpResponse.BodyHandlers.ofString())
				.thenApply(HttpResponse::body)
				.exceptionally(e -> null);
	}

	private CompletableFuture<JsonObject> senden(HttpRequest req) {
		return http.sendAsync(req, HttpResponse.BodyHandlers.ofString())
				.thenApply(res -> {
					erreichbar = true;
					String text = res.body();
					return text == null || text.isBlank() ? new JsonObject() : JsonParser.parseString(text).getAsJsonObject();
				})
				.exceptionally(e -> {
					erreichbar = false;
					return null;
				});
	}
}
