package de.reiss.jevbaritone;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/** Minimaler Client fuer TypeSafe System One (Jev): state + Fragen rein, typisierte Antworten raus. */
public final class Jev {
	private static final URI ENDPOINT = URI.create("https://api.typesafe.ai/v1/systemone");
	private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
	private static final Gson GSON = new Gson();

	private final String apiKey;
	private final Map<String, Object> questions = new LinkedHashMap<>();

	private Jev(String apiKey) {
		this.apiKey = apiKey;
	}

	static Jev anfrage(String apiKey) {
		return new Jev(apiKey);
	}

	Jev noul(String id, String instructions) {
		questions.put(id, Map.of("type", "noul", "instructions", instructions));
		return this;
	}

	/** criteria: Label -> Beschreibung */
	Jev choice(String id, String instructions, Map<String, String> criteria) {
		questions.put(id, Map.of("type", "choice", "instructions", instructions, "criteria", criteria));
		return this;
	}

	CompletableFuture<JsonObject> senden(Object state) {
		String body = GSON.toJson(Map.of("state", state, "model", "jev-latest", "questions", questions));
		HttpRequest req = HttpRequest.newBuilder(ENDPOINT)
			.timeout(Duration.ofSeconds(10))
			.header("Authorization", "Bearer " + apiKey)
			.header("Content-Type", "application/json")
			.POST(HttpRequest.BodyPublishers.ofString(body))
			.build();
		return HTTP.sendAsync(req, HttpResponse.BodyHandlers.ofString()).thenApply(res -> {
			if (res.statusCode() / 100 != 2) {
				throw new RuntimeException("Jev HTTP " + res.statusCode() + ": " + res.body());
			}
			return JsonParser.parseString(res.body()).getAsJsonObject().getAsJsonObject("answers");
		});
	}

	static double noul(JsonObject answers, String id) {
		return answers.has(id) ? answers.getAsJsonObject(id).get("noul").getAsDouble() : 0;
	}

	static String wahl(JsonObject answers, String id) {
		return answers.has(id) ? answers.getAsJsonObject(id).get("choice").getAsString() : "unklar";
	}

	static double sicherheit(JsonObject answers, String id) {
		return answers.has(id) ? answers.getAsJsonObject(id).get("confidence").getAsDouble() : 0;
	}

	/**
	 * Key aus der Umgebung; Prism wurde evtl. vor "setx" gestartet und kennt ihn dann nicht,
	 * deshalb notfalls direkt aus den Benutzer-Umgebungsvariablen in der Registry lesen.
	 */
	static String apiKeyFinden() {
		String env = System.getenv("TYPESAFE_API_KEY");
		if (env != null && !env.isBlank()) return env.trim();
		try {
			Process p = new ProcessBuilder("reg", "query", "HKCU\\Environment", "/v", "TYPESAFE_API_KEY").start();
			try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
				String zeile;
				while ((zeile = r.readLine()) != null) {
					zeile = zeile.trim();
					if (zeile.startsWith("TYPESAFE_API_KEY")) {
						String[] teile = zeile.split("\\s+");
						return teile[teile.length - 1];
					}
				}
			}
		} catch (Exception ignored) {
		}
		return null;
	}
}
