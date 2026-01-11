package com.armadabench.vassal.server;

import com.armadabench.vassal.GameStateReader;
import com.armadabench.vassal.ScreenshotCapture;
import com.armadabench.vassal.VassalController;
import com.armadabench.vassal.models.*;
import io.javalin.Javalin;
import io.javalin.http.Context;
import io.javalin.json.JavalinJackson;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * REST API server exposing Vassal game operations.
 *
 * This server provides HTTP endpoints that the Python MCP server
 * calls to interact with the Vassal engine.
 */
public class VassalApiServer {
    private static final Logger logger = LoggerFactory.getLogger(VassalApiServer.class);

    private final VassalController controller;
    private final GameStateReader stateReader;
    private final ScreenshotCapture screenshotCapture;
    private Javalin app;
    private int port;

    public VassalApiServer(VassalController controller) {
        this.controller = controller;
        this.stateReader = new GameStateReader(controller);
        this.screenshotCapture = new ScreenshotCapture(controller);
    }

    /**
     * Start the API server on the specified port.
     *
     * @param port Port to listen on
     */
    public void start(int port) {
        this.port = port;

        app = Javalin.create(config -> {
            config.jsonMapper(new JavalinJackson());
            config.showJavalinBanner = false;
        });

        // Health check
        app.get("/api/health", this::handleHealth);

        // Game state endpoints
        app.get("/api/state", this::handleGetState);
        app.get("/api/ship/{id}", this::handleGetShip);
        app.get("/api/squadron/{id}", this::handleGetSquadron);

        // Screenshot endpoints
        app.get("/api/screenshot", this::handleScreenshot);
        app.get("/api/screenshot/base64", this::handleScreenshotBase64);

        // Action endpoints
        app.post("/api/action/move", this::handleMoveAction);
        app.post("/api/action/attack", this::handleAttackAction);

        // Game lifecycle
        app.post("/api/game/new", this::handleNewGame);
        app.post("/api/game/load", this::handleLoadGame);

        // Error handling
        app.exception(Exception.class, (e, ctx) -> {
            logger.error("API error: {}", e.getMessage(), e);
            ctx.status(500).json(errorResponse(e.getMessage()));
        });

        app.start(port);
        logger.info("Vassal API server started on port {}", port);
    }

    /**
     * Stop the API server.
     */
    public void stop() {
        if (app != null) {
            app.stop();
            logger.info("Vassal API server stopped");
        }
    }

    // Handler methods

    private void handleHealth(Context ctx) {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "ok");
        response.put("initialized", controller.isInitialized());
        response.put("modulePath", controller.getModulePath());
        ctx.json(response);
    }

    private void handleGetState(Context ctx) {
        BoardState state = stateReader.getCurrentState();
        ctx.json(state);
    }

    private void handleGetShip(Context ctx) {
        String shipId = ctx.pathParam("id");
        ShipData ship = stateReader.getShipById(shipId);

        if (ship == null) {
            ctx.status(404).json(errorResponse("Ship not found: " + shipId));
            return;
        }

        ctx.json(ship);
    }

    private void handleGetSquadron(Context ctx) {
        String squadronId = ctx.pathParam("id");
        SquadronData squadron = stateReader.getSquadronById(squadronId);

        if (squadron == null) {
            ctx.status(404).json(errorResponse("Squadron not found: " + squadronId));
            return;
        }

        ctx.json(squadron);
    }

    private void handleScreenshot(Context ctx) throws IOException {
        String format = ctx.queryParam("format");
        if (format == null) format = "PNG";

        int maxWidth = ctx.queryParamAsClass("maxWidth", Integer.class).getOrDefault(0);
        int maxHeight = ctx.queryParamAsClass("maxHeight", Integer.class).getOrDefault(0);

        byte[] imageBytes;
        if (maxWidth > 0 && maxHeight > 0) {
            imageBytes = screenshotCapture.captureBoardScaled(maxWidth, maxHeight);
        } else {
            imageBytes = screenshotCapture.captureBoard(format);
        }

        ctx.contentType("image/" + format.toLowerCase());
        ctx.result(imageBytes);
    }

    private void handleScreenshotBase64(Context ctx) throws IOException {
        String dataUrl = screenshotCapture.captureBoardAsDataUrl();

        Map<String, Object> response = new HashMap<>();
        response.put("image_url", dataUrl);
        response.put("timestamp", System.currentTimeMillis());

        ctx.json(response);
    }

    private void handleMoveAction(Context ctx) {
        MoveRequest request = ctx.bodyAsClass(MoveRequest.class);

        // TODO: Implement movement execution using Vassal Command pattern
        // This is a placeholder that returns success for now
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "Move action not yet implemented");
        response.put("pieceId", request.pieceId);
        response.put("targetX", request.targetX);
        response.put("targetY", request.targetY);

        ctx.json(response);
    }

    private void handleAttackAction(Context ctx) {
        AttackRequest request = ctx.bodyAsClass(AttackRequest.class);

        // TODO: Implement attack execution
        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "Attack action not yet implemented");

        ctx.json(response);
    }

    private void handleNewGame(Context ctx) {
        controller.startNewGame();

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "New game started");

        ctx.json(response);
    }

    private void handleLoadGame(Context ctx) throws IOException {
        LoadGameRequest request = ctx.bodyAsClass(LoadGameRequest.class);
        controller.loadSavedGame(request.path);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "Game loaded from: " + request.path);

        ctx.json(response);
    }

    private Map<String, Object> errorResponse(String message) {
        Map<String, Object> response = new HashMap<>();
        response.put("error", true);
        response.put("message", message);
        return response;
    }

    // Request DTOs

    public static class MoveRequest {
        public String pieceId;
        public double targetX;
        public double targetY;
        public double rotation;
        public boolean validateOnly;
    }

    public static class AttackRequest {
        public String attackerId;
        public String defenderId;
        public String arc;  // front, left, right, rear
        public String range;  // close, medium, long
    }

    public static class LoadGameRequest {
        public String path;
    }

    /**
     * Main entry point for the Vassal API server.
     */
    public static void main(String[] args) {
        int port = 8080;
        boolean mockMode = false;
        String modulePath = null;

        for (String arg : args) {
            if (arg.equals("--mock")) {
                mockMode = true;
            } else if (arg.equals("--help") || arg.equals("-h")) {
                printUsage();
                System.exit(0);
            } else if (!arg.startsWith("-")) {
                if (modulePath == null) {
                    modulePath = arg;
                } else {
                    try {
                        port = Integer.parseInt(arg);
                    } catch (NumberFormatException e) {
                        System.err.println("Invalid port: " + arg);
                        System.exit(1);
                    }
                }
            }
        }

        if (!mockMode && modulePath == null) {
            printUsage();
            System.exit(1);
        }

        try {
            if (mockMode) {
                startMockServer(port);
            } else {
                startVassalServer(modulePath, port);
            }
        } catch (Exception e) {
            System.err.println("Failed to start server: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static void printUsage() {
        System.err.println("Usage: java -jar vassal-integration.jar [options] <module-path> [port]");
        System.err.println("");
        System.err.println("Options:");
        System.err.println("  --mock        Run in mock mode (no Vassal, returns sample data)");
        System.err.println("  --help, -h    Show this help message");
        System.err.println("");
        System.err.println("Arguments:");
        System.err.println("  module-path   Path to the .vmod file");
        System.err.println("  port          HTTP port (default: 8080)");
        System.err.println("");
        System.err.println("Note: Vassal requires a display. Use --mock for testing without Vassal.");
        System.err.println("");
        System.err.println("Examples:");
        System.err.println("  java -jar vassal-integration.jar --mock 8080");
        System.err.println("  java -jar vassal-integration.jar ArmadaModule.vmod 8080");
    }

    private static void startMockServer(int port) throws Exception {
        System.out.println("Starting Vassal API Server in MOCK MODE on port " + port);
        System.out.println("This mode returns sample data without connecting to Vassal.");

        Javalin app = Javalin.create(config -> {
            config.jsonMapper(new JavalinJackson());
            config.showJavalinBanner = false;
        });

        // Health check
        app.get("/api/health", ctx -> {
            Map<String, Object> response = new HashMap<>();
            response.put("status", "ok");
            response.put("mock_mode", true);
            response.put("message", "Running in mock mode - no actual Vassal connection");
            ctx.json(response);
        });

        // Mock board state
        app.get("/api/state", ctx -> {
            Map<String, Object> state = createMockBoardState();
            ctx.json(state);
        });

        // Mock ship details
        app.get("/api/ship/{id}", ctx -> {
            String shipId = ctx.pathParam("id");
            Map<String, Object> ship = createMockShip(shipId);
            ctx.json(ship);
        });

        // Mock screenshot (returns a placeholder)
        app.get("/api/screenshot/base64", ctx -> {
            Map<String, Object> response = new HashMap<>();
            response.put("image_url", "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==");
            response.put("timestamp", System.currentTimeMillis());
            response.put("mock", true);
            ctx.json(response);
        });

        app.start(port);

        System.out.println("Mock server running at http://localhost:" + port);
        System.out.println("Endpoints:");
        System.out.println("  GET /api/health          - Health check");
        System.out.println("  GET /api/state           - Mock board state");
        System.out.println("  GET /api/ship/{id}       - Mock ship details");
        System.out.println("  GET /api/screenshot/base64 - Mock screenshot");
        System.out.println("");
        System.out.println("Press Ctrl+C to stop");

        Runtime.getRuntime().addShutdownHook(new Thread(app::stop));
        Thread.currentThread().join();
    }

    private static Map<String, Object> createMockBoardState() {
        Map<String, Object> state = new HashMap<>();
        state.put("roundNumber", 3);
        state.put("currentPhase", "Ship Phase");
        state.put("activePlayer", "player1");

        // Mock ships
        java.util.List<Map<String, Object>> ships = new java.util.ArrayList<>();
        ships.add(createMockShip("isd-1"));
        ships.add(createMockShip("cr90-1"));
        state.put("ships", ships);

        // Mock squadrons
        java.util.List<Map<String, Object>> squadrons = new java.util.ArrayList<>();
        squadrons.add(createMockSquadron("tie-1"));
        squadrons.add(createMockSquadron("xwing-1"));
        state.put("squadrons", squadrons);

        state.put("obstacles", java.util.Collections.emptyList());
        state.put("tokens", java.util.Collections.emptyList());
        state.put("timestamp", System.currentTimeMillis());

        return state;
    }

    private static Map<String, Object> createMockShip(String id) {
        Map<String, Object> ship = new HashMap<>();
        ship.put("id", id);
        ship.put("name", id.startsWith("isd") ? "Imperial Star Destroyer II" : "CR90 Corvette A");
        ship.put("shipType", id.startsWith("isd") ? "Imperial Star Destroyer" : "CR90 Corvette");
        ship.put("faction", id.startsWith("isd") ? "empire" : "rebel");
        ship.put("playerId", id.startsWith("isd") ? "player1" : "player2");
        ship.put("x", id.startsWith("isd") ? 200.0 : 400.0);
        ship.put("y", id.startsWith("isd") ? 300.0 : 350.0);
        ship.put("rotation", 0.0);
        ship.put("currentHull", id.startsWith("isd") ? 9 : 3);
        ship.put("maxHull", id.startsWith("isd") ? 11 : 4);

        Map<String, Integer> shields = new HashMap<>();
        shields.put("front", id.startsWith("isd") ? 4 : 2);
        shields.put("left", id.startsWith("isd") ? 3 : 1);
        shields.put("right", id.startsWith("isd") ? 3 : 1);
        shields.put("rear", id.startsWith("isd") ? 2 : 1);
        ship.put("currentShields", shields);
        ship.put("maxShields", shields);

        ship.put("activated", false);
        ship.put("speed", 2);

        return ship;
    }

    private static Map<String, Object> createMockSquadron(String id) {
        Map<String, Object> sq = new HashMap<>();
        sq.put("id", id);
        sq.put("name", id.startsWith("tie") ? "TIE Fighter Squadron" : "X-wing Squadron");
        sq.put("squadronType", id.startsWith("tie") ? "TIE Fighter" : "X-wing");
        sq.put("faction", id.startsWith("tie") ? "empire" : "rebel");
        sq.put("playerId", id.startsWith("tie") ? "player1" : "player2");
        sq.put("x", id.startsWith("tie") ? 250.0 : 380.0);
        sq.put("y", id.startsWith("tie") ? 280.0 : 320.0);
        sq.put("currentHull", 3);
        sq.put("maxHull", 3);
        sq.put("activated", false);
        sq.put("engaged", false);
        sq.put("speed", 4);
        return sq;
    }

    private static void startVassalServer(String modulePath, int port) throws Exception {
        System.out.println("Loading Vassal module: " + modulePath);
        System.out.println("Display: " + System.getenv("DISPLAY"));

        try {
            // Initialize Vassal controller
            VassalController controller = new VassalController();
            controller.initialize(modulePath);
            System.out.println("Vassal module loaded successfully!");

            // Create and start the API server
            VassalApiServer server = new VassalApiServer(controller);
            server.start(port);

            System.out.println("");
            System.out.println("=== Server Ready ===");
            System.out.println("API: http://localhost:" + port);
            System.out.println("Health: http://localhost:" + port + "/api/health");
            System.out.println("State: http://localhost:" + port + "/api/state");
            System.out.println("");
            System.out.println("Press Ctrl+C to stop");

            // Add shutdown hook
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                server.stop();
                controller.shutdown();
            }));

            // Keep the main thread alive
            Thread.currentThread().join();

        } catch (Exception e) {
            System.err.println("");
            System.err.println("ERROR: Failed to initialize Vassal: " + e.getMessage());
            e.printStackTrace();
            System.err.println("");
            System.err.println("Falling back to mock mode...");
            System.err.println("");

            // Fall back to mock mode
            startMockServer(port);
        }
    }
}
