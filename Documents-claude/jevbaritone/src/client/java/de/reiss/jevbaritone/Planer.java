package de.reiss.jevbaritone;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * "System 2": ein lokales LLM (LM Studio, OpenAI-kompatibel) zerlegt eine freie Nachricht in einfache
 * Einzelbefehle. Jeder Befehl geht danach einzeln an Jev, das typisiert entscheidet, was der Bot tut.
 */
final class Planer {
	private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build();
	private static final Gson GSON = new Gson();

	private static final String SYSTEM = """
		Du bist der Planer eines Minecraft-Begleitbots. Der Spieler schreibt dem Bot frei (Deutsch/Englisch, Tippfehler, Slang).
		Uebersetze die Nachricht in eine Liste einfacher, eindeutiger Einzelbefehle auf Deutsch, die der Bot nacheinander ausfuehrt.
		Der Bot kann NUR: dem Spieler folgen | zum Spieler herkommen | anhalten | einen Block oder Rohstoff abbauen (mit Menge oder "ohne Ende") |
		ein Item herstellen (mit Menge) | etwas im Ofen schmelzen oder braten (z.B. "schmelze das Roheisen") | Monster bekaempfen | zu Koordinaten gehen | Felder farmen | die Gegend erkunden | einen Tunnel graben |
		an die Oberflaeche gehen | nach Hause gehen | die aktuelle Stelle als Zuhause setzen | seinen Status sagen.
		Regeln: Jeder Befehl ist ein kurzer Satz mit genau einer Aktion, z.B. "baue 5 Holz ab", "stelle 1 Holzspitzhacke her".
		Zerlege Ziele in die noetigen Schritte, wenn Material fehlt (das Inventar des Bots steht dabei):
		Holzwerkzeug braucht ca. 3 Holz; Steinwerkzeug braucht ca. 2 Holz und 3 Bruchstein; eine Werkbank braucht 1 Holz.
		WICHTIG, Werkzeugstufen: Stein, Bruchstein, Kohle und Kupfer droppen nur mit einer Spitzhacke (mind. Holzspitzhacke);
		Eisen und Lapis brauchen mind. eine Steinspitzhacke; Gold, Diamant, Redstone und Smaragd mind. eine Eisenspitzhacke.
		Hat der Bot die noetige Spitzhacke nicht im Inventar, stelle sie VOR dem Abbauen her (und besorge vorher ihr Material).
		Eisen- und Goldwerkzeug brauchen Barren: Roheisen erst im Ofen schmelzen (Ofen und Kohle besorgt der Bot sonst nicht: baue vorher 8 Bruchstein und etwas Kohle ab).
		Baue in einem Befehl immer nur EINEN Rohstoff ab ("baue 8 Eisen ab" und "baue 5 Kohle ab" getrennt).
		Beispiel "mach eine Steinspitzhacke" ohne Inventar: ["baue 5 Holz ab", "stelle 1 Holzspitzhacke her", "baue 3 Bruchstein ab", "stelle 1 Steinspitzhacke her"].
		Zwischenprodukte (Bretter, Stoecke, Werkbank) stellt der Bot beim Herstellen selbst her, die musst du NICHT extra auffuehren.
		Was schon im Inventar ist, muss nicht mehr abgebaut werden.
		Halte dich an "minecraft_wissen" (Rezepte und Werkzeugstufen aus dem Spiel): gehe den Rezeptbaum von unten nach oben durch,
		ziehe ab, was im Inventar ist, und plane jeden fehlenden Rohstoff (mit Menge) und jede noetige Spitzhacke in der richtigen Reihenfolge.
		Ist die Nachricht nicht an den Bot gerichtet (Smalltalk mit anderen Spielern), gib an_bot=false und eine leere Liste.""";

	private static final Map<String, Object> SCHEMA = Map.of("type", "json_schema", "json_schema", Map.of(
		"name", "plan", "strict", true, "schema", Map.of(
			"type", "object",
			"properties", Map.of(
				"an_bot", Map.of("type", "boolean"),
				"befehle", Map.of("type", "array", "items", Map.of("type", "string"))),
			"required", List.of("an_bot", "befehle"))));

	private final String url;
	private final String modell;

	Planer(String url, String modell) {
		this.url = url;
		this.modell = modell;
	}

	/** Liefert die Einzelbefehle (leer = nicht an den Bot gerichtet). */
	CompletableFuture<List<String>> planen(String nachricht, Map<String, Integer> inventar, String wissen) {
		String user = GSON.toJson(Map.of("nachricht", nachricht, "bot_inventar", inventar,
			"minecraft_wissen", wissen + "\n" + Wissen.FAKTEN));
		String body = GSON.toJson(Map.of(
			"model", modell,
			"temperature", 0.1,
			"response_format", SCHEMA,
			"messages", List.of(Map.of("role", "system", "content", SYSTEM), Map.of("role", "user", "content", user))));
		HttpRequest req = HttpRequest.newBuilder(URI.create(url))
			.timeout(Duration.ofSeconds(120))
			.header("Content-Type", "application/json")
			.POST(HttpRequest.BodyPublishers.ofString(body))
			.build();
		return HTTP.sendAsync(req, HttpResponse.BodyHandlers.ofString()).thenApply(res -> {
			if (res.statusCode() / 100 != 2) throw new RuntimeException("LM Studio HTTP " + res.statusCode());
			String inhalt = JsonParser.parseString(res.body()).getAsJsonObject()
				.getAsJsonArray("choices").get(0).getAsJsonObject()
				.getAsJsonObject("message").get("content").getAsString();
			JsonObject plan = JsonParser.parseString(inhalt).getAsJsonObject();
			List<String> befehle = new ArrayList<>();
			if (!plan.get("an_bot").getAsBoolean()) return befehle;
			JsonArray arr = plan.getAsJsonArray("befehle");
			for (int i = 0; i < arr.size() && i < 8; i++) befehle.add(arr.get(i).getAsString());
			return befehle;
		});
	}
}
