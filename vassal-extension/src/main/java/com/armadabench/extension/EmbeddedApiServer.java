package com.armadabench.extension;

import VASSAL.build.GameModule;
import VASSAL.build.module.PieceWindow;
import VASSAL.build.widget.PieceSlot;
import VASSAL.counters.GamePiece;
import VASSAL.counters.Stack;
import VASSAL.tools.DataArchive;
import io.javalin.Javalin;
import io.javalin.http.Context;
import io.javalin.json.JavalinJackson;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import javax.swing.SwingUtilities;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.util.*;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * Embedded REST API server that runs inside Vassal.
 *
 * This server has direct access to the GameModule and can read
 * game state, capture screenshots, and execute commands.
 */
public class EmbeddedApiServer {
    private static final Logger logger = LoggerFactory.getLogger(EmbeddedApiServer.class);

    private final GameModule gameModule;
    private final int port;
    private Javalin app;

    public EmbeddedApiServer(GameModule gameModule, int port) {
        this.gameModule = gameModule;
        this.port = port;
    }

    public void start() {
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
        app.get("/api/pieces", this::handleGetAllPieces);
        app.get("/api/maps", this::handleGetMaps);

        // Screenshot endpoints
        app.get("/api/screenshot/base64", this::handleScreenshotBase64);

        // Game lifecycle
        app.post("/api/game/new", this::handleNewGame);
        app.post("/api/game/load", this::handleLoadGame);

        // Piece palette (for spawning pieces)
        app.get("/api/palette", this::handleGetPalette);
        app.post("/api/palette/spawn", this::handleSpawnPiece);

        // Error handling
        app.exception(Exception.class, (e, ctx) -> {
            logger.error("API error: {}", e.getMessage(), e);
            ctx.status(500).json(errorResponse(e.getMessage()));
        });

        app.start(port);
        logger.info("Embedded API server started on port {}", port);
    }

    public void stop() {
        if (app != null) {
            app.stop();
            logger.info("Embedded API server stopped");
        }
    }

    // Helper to run code on AWT thread and wait for result
    private <T> T runOnAwtThread(java.util.concurrent.Callable<T> task) throws Exception {
        return runOnAwtThread(task, 120); // Default 120 second timeout
    }

    private <T> T runOnAwtThread(java.util.concurrent.Callable<T> task, int timeoutSeconds) throws Exception {
        CompletableFuture<T> future = new CompletableFuture<>();
        SwingUtilities.invokeLater(() -> {
            try {
                T result = task.call();
                future.complete(result);
            } catch (Exception e) {
                future.completeExceptionally(e);
            }
        });
        return future.get(timeoutSeconds, TimeUnit.SECONDS);
    }

    // Handler methods

    private void handleHealth(Context ctx) {
        java.util.Map<String, Object> response = new HashMap<>();
        response.put("status", "ok");
        response.put("embedded", true);
        response.put("module_name", gameModule.getGameName());
        response.put("module_version", gameModule.getGameVersion());

        // Add game state info
        boolean gameStarted = gameModule.getGameState().isGameStarted();
        response.put("game_started", gameStarted);

        // Count maps
        List<VASSAL.build.module.Map> maps = VASSAL.build.module.Map.getMapList();
        response.put("map_count", maps.size());

        ctx.json(response);
    }

    private void handleGetMaps(Context ctx) {
        List<java.util.Map<String, Object>> mapList = new ArrayList<>();

        for (VASSAL.build.module.Map map : VASSAL.build.module.Map.getMapList()) {
            java.util.Map<String, Object> mapInfo = new HashMap<>();
            mapInfo.put("name", map.getMapName());

            Dimension size = map.mapSize();
            mapInfo.put("width", size.width);
            mapInfo.put("height", size.height);

            // Count pieces on this map
            GamePiece[] pieces = map.getAllPieces();
            mapInfo.put("piece_count", pieces.length);

            mapList.add(mapInfo);
        }

        java.util.Map<String, Object> response = new HashMap<>();
        response.put("maps", mapList);
        response.put("count", mapList.size());
        ctx.json(response);
    }

    private void handleGetState(Context ctx) {
        java.util.Map<String, Object> state = new HashMap<>();

        // Get game info
        state.put("gameName", gameModule.getGameName());
        state.put("gameVersion", gameModule.getGameVersion());
        state.put("gameStarted", gameModule.getGameState().isGameStarted());

        // Get all pieces from all maps
        List<java.util.Map<String, Object>> ships = new ArrayList<>();
        List<java.util.Map<String, Object>> squadrons = new ArrayList<>();
        List<java.util.Map<String, Object>> otherPieces = new ArrayList<>();

        for (VASSAL.build.module.Map map : VASSAL.build.module.Map.getMapList()) {
            GamePiece[] pieces = map.getAllPieces();
            for (GamePiece piece : pieces) {
                processPiece(piece, ships, squadrons, otherPieces);
            }
        }

        state.put("ships", ships);
        state.put("squadrons", squadrons);
        state.put("otherPieces", otherPieces);
        state.put("timestamp", System.currentTimeMillis());

        ctx.json(state);
    }

    private void processPiece(GamePiece piece,
                              List<java.util.Map<String, Object>> ships,
                              List<java.util.Map<String, Object>> squadrons,
                              List<java.util.Map<String, Object>> otherPieces) {
        // Handle stacks
        if (piece instanceof Stack) {
            Stack stack = (Stack) piece;
            for (Iterator<GamePiece> it = stack.getPiecesIterator(); it.hasNext();) {
                processPiece(it.next(), ships, squadrons, otherPieces);
            }
            return;
        }

        java.util.Map<String, Object> pieceData = extractPieceData(piece);
        String pieceName = (String) pieceData.get("name");

        if (pieceName != null) {
            String nameLower = pieceName.toLowerCase();
            // Categorize based on name patterns (Armada-specific)
            // Ships are named like "Victory (VICTORY-CLASS)", "Imperial (IMPERIAL-CLASS)"
            // Squadrons contain "Squadron" or specific fighter names
            if (isShipPiece(nameLower)) {
                ships.add(pieceData);
            } else if (isSquadronPiece(nameLower)) {
                squadrons.add(pieceData);
            } else {
                otherPieces.add(pieceData);
            }
        } else {
            otherPieces.add(pieceData);
        }
    }

    /**
     * Check if a piece name matches ship patterns.
     * Ships in Armada Vassal module are named like:
     * - "Victory (VICTORY-CLASS)" - ship bases
     * - "Imperial (IMPERIAL-CLASS)"
     * - "Victory I", "Victory II" - specific ship titles
     * - "Acclamator I-class Assault Ship" - full ship card names
     * - "Venator II" - short names
     */
    private boolean isShipPiece(String nameLower) {
        // Ship base pieces end with "-class)" or contain "-class "
        if (nameLower.contains("-class)") || nameLower.contains("-class ")) {
            return true;
        }

        // Ship type endings
        if (nameLower.endsWith(" ship") || nameLower.endsWith(" cruiser") ||
            nameLower.endsWith(" frigate") || nameLower.endsWith(" destroyer") ||
            nameLower.endsWith(" corvette") || nameLower.endsWith(" carrier") ||
            nameLower.endsWith(" dreadnought") || nameLower.endsWith(" dreadnaught")) {
            return true;
        }

        // Specific ship names/patterns
        String[] shipPatterns = {
            // Empire
            "victory i", "victory ii", "imperial i", "imperial ii",
            "gladiator i", "gladiator ii", "raider i", "raider ii",
            "arquitens", "quasar", "interdictor", "onager", "gozanti",
            "executor", "star dreadnought", "star dreadnaught",
            // Rebels
            "assault frigate", "nebulon-b", "mc30", "mc80", "mc75",
            "cr90", "liberty", "home one", "profundity", "starhawk",
            "gr-75", "hammerhead", "pelta",
            // Republic
            "acclamator", "venator", "consular", "charger",
            // Separatists
            "providence", "munificent", "hardcell", "recusant",
            // Unique ship names
            "radiant vii", "tranquility", "resolute", "invisible hand"
        };
        for (String pattern : shipPatterns) {
            if (nameLower.contains(pattern)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Check if a piece name matches squadron patterns.
     * Squadrons contain "Squadron" or specific fighter names.
     */
    private boolean isSquadronPiece(String nameLower) {
        // Direct squadron mentions
        if (nameLower.contains("squadron")) {
            return true;
        }

        // Imperial fighters
        String[] imperialFighters = {"tie fighter", "tie advanced", "tie bomber",
            "tie interceptor", "tie defender", "tie phantom", "tie/", "(tie "};
        for (String fighter : imperialFighters) {
            if (nameLower.contains(fighter)) {
                return true;
            }
        }

        // Rebel fighters
        String[] rebelFighters = {"x-wing", "y-wing", "a-wing", "b-wing", "e-wing",
            "hwk-290", "vcx-100", "ghost", "phantom ii", "yt-1300", "yt-2400",
            "z-95", "lancer"};
        for (String fighter : rebelFighters) {
            if (nameLower.contains(fighter)) {
                return true;
            }
        }

        // Republic fighters
        String[] republicFighters = {"arc-170", "delta-7", "btl-b", "v-19",
            "clone z-95", "eta-2"};
        for (String fighter : republicFighters) {
            if (nameLower.contains(fighter)) {
                return true;
            }
        }

        // Separatist fighters
        String[] separatistFighters = {"vulture", "hyena", "droid tri", "belbullab",
            "nantex"};
        for (String fighter : separatistFighters) {
            if (nameLower.contains(fighter)) {
                return true;
            }
        }

        return false;
    }

    private java.util.Map<String, Object> extractPieceData(GamePiece piece) {
        java.util.Map<String, Object> data = new HashMap<>();

        data.put("id", piece.getId());
        data.put("name", piece.getName());
        data.put("type", piece.getClass().getSimpleName());

        // Get position
        Point pos = piece.getPosition();
        if (pos != null) {
            data.put("x", pos.x);
            data.put("y", pos.y);
        }

        // Get the map this piece is on
        VASSAL.build.module.Map map = piece.getMap();
        if (map != null) {
            data.put("mapName", map.getMapName());
        }

        // Get piece state (contains all properties)
        String state = piece.getState();
        data.put("state", state);

        // Try to extract common properties
        try {
            extractArmadaProperties(piece, data);
        } catch (Exception e) {
            logger.debug("Could not extract properties for piece {}: {}", piece.getName(), e.getMessage());
        }

        return data;
    }

    private void extractArmadaProperties(GamePiece piece, java.util.Map<String, Object> data) {
        // Common Vassal piece properties
        String[] propertyNames = {
            "CurrentHull", "Hull", "Shields", "FrontShield", "LeftShield", "RightShield", "RearShield",
            "Speed", "Activated", "Owner", "Faction", "Points", "CommandValue"
        };

        for (String prop : propertyNames) {
            Object value = piece.getProperty(prop);
            if (value != null) {
                data.put(prop.substring(0, 1).toLowerCase() + prop.substring(1), value);
            }
        }
    }

    private void handleGetShip(Context ctx) {
        String shipId = ctx.pathParam("id");
        GamePiece piece = findPieceById(shipId);

        if (piece == null) {
            ctx.status(404).json(errorResponse("Ship not found: " + shipId));
            return;
        }

        ctx.json(extractPieceData(piece));
    }

    private void handleGetSquadron(Context ctx) {
        String squadronId = ctx.pathParam("id");
        GamePiece piece = findPieceById(squadronId);

        if (piece == null) {
            ctx.status(404).json(errorResponse("Squadron not found: " + squadronId));
            return;
        }

        ctx.json(extractPieceData(piece));
    }

    private void handleGetAllPieces(Context ctx) {
        List<java.util.Map<String, Object>> allPieces = new ArrayList<>();

        for (VASSAL.build.module.Map map : VASSAL.build.module.Map.getMapList()) {
            GamePiece[] pieces = map.getAllPieces();
            for (GamePiece piece : pieces) {
                collectAllPieces(piece, allPieces);
            }
        }

        java.util.Map<String, Object> response = new HashMap<>();
        response.put("pieces", allPieces);
        response.put("count", allPieces.size());
        ctx.json(response);
    }

    private void collectAllPieces(GamePiece piece, List<java.util.Map<String, Object>> allPieces) {
        if (piece instanceof Stack) {
            Stack stack = (Stack) piece;
            for (Iterator<GamePiece> it = stack.getPiecesIterator(); it.hasNext();) {
                collectAllPieces(it.next(), allPieces);
            }
        } else {
            allPieces.add(extractPieceData(piece));
        }
    }

    private GamePiece findPieceById(String id) {
        for (VASSAL.build.module.Map map : VASSAL.build.module.Map.getMapList()) {
            GamePiece[] pieces = map.getAllPieces();
            for (GamePiece piece : pieces) {
                GamePiece found = findPieceByIdRecursive(piece, id);
                if (found != null) {
                    return found;
                }
            }
        }
        return null;
    }

    private GamePiece findPieceByIdRecursive(GamePiece piece, String id) {
        if (piece instanceof Stack) {
            Stack stack = (Stack) piece;
            for (Iterator<GamePiece> it = stack.getPiecesIterator(); it.hasNext();) {
                GamePiece found = findPieceByIdRecursive(it.next(), id);
                if (found != null) {
                    return found;
                }
            }
        } else if (id.equals(piece.getId())) {
            return piece;
        }
        return null;
    }

    private void handleScreenshotBase64(Context ctx) {
        try {
            // Get the primary map
            List<VASSAL.build.module.Map> maps = VASSAL.build.module.Map.getMapList();
            if (maps.isEmpty()) {
                ctx.status(400).json(errorResponse("No maps available"));
                return;
            }

            VASSAL.build.module.Map primaryMap = maps.get(0);

            // Get map dimensions
            Dimension mapSize = primaryMap.mapSize();

            // Use minimum dimensions if map has no size
            int width = mapSize.width > 0 ? Math.min(mapSize.width, 1920) : 1920;
            int height = mapSize.height > 0 ? Math.min(mapSize.height, 1080) : 1080;

            // Create image
            BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
            Graphics2D g2d = image.createGraphics();

            // Set rendering hints for quality
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2d.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);

            // Fill with dark background
            g2d.setColor(new Color(30, 30, 40));
            g2d.fillRect(0, 0, width, height);

            // Draw the map
            try {
                primaryMap.paintRegion(g2d, new Rectangle(0, 0, width, height));
            } catch (Exception e) {
                logger.warn("Could not paint map region: {}", e.getMessage());
            }

            g2d.dispose();

            // Convert to base64
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "PNG", baos);
            byte[] imageBytes = baos.toByteArray();
            String base64 = Base64.getEncoder().encodeToString(imageBytes);

            java.util.Map<String, Object> response = new HashMap<>();
            response.put("image_url", "data:image/png;base64," + base64);
            response.put("width", width);
            response.put("height", height);
            response.put("map_name", primaryMap.getMapName());
            response.put("timestamp", System.currentTimeMillis());

            ctx.json(response);

        } catch (Exception e) {
            logger.error("Screenshot capture failed: {}", e.getMessage(), e);
            ctx.status(500).json(errorResponse("Screenshot failed: " + e.getMessage()));
        }
    }

    private void handleNewGame(Context ctx) {
        try {
            Boolean result = runOnAwtThread(() -> {
                gameModule.getGameState().setup(true);
                return true;
            });

            java.util.Map<String, Object> response = new HashMap<>();
            response.put("success", result);
            response.put("message", "New game started");
            response.put("game_started", gameModule.getGameState().isGameStarted());
            ctx.json(response);

        } catch (Exception e) {
            logger.error("Failed to start new game: {}", e.getMessage(), e);
            ctx.status(500).json(errorResponse("Failed to start new game: " + e.getMessage()));
        }
    }

    private void handleLoadGame(Context ctx) {
        try {
            String path = ctx.queryParam("path");
            if (path == null || path.isEmpty()) {
                ctx.status(400).json(errorResponse("Missing 'path' query parameter"));
                return;
            }

            File saveFile = new File(path);
            if (!saveFile.exists()) {
                ctx.status(404).json(errorResponse("Save file not found: " + path));
                return;
            }

            System.out.println("[ArmadaBench] Loading saved game from: " + path);

            // Load and execute the saved game commands directly
            String result = runOnAwtThread(() -> {
                try {
                    System.out.println("[ArmadaBench] Reading vlog file...");

                    // Use GameState's decodeSavedGame to properly decode the file
                    VASSAL.build.module.GameState gameState = gameModule.getGameState();

                    // Decode the saved game file
                    VASSAL.command.Command command = gameState.decodeSavedGame(saveFile);

                    if (command == null) {
                        System.out.println("[ArmadaBench] ERROR: Decoded command is null");
                        return "error: Failed to decode saved game commands";
                    }

                    System.out.println("[ArmadaBench] Decoded command type: " + command.getClass().getName());

                    // Get sub-commands to understand the structure
                    VASSAL.command.Command[] subCommands = command.getSubCommands();
                    System.out.println("[ArmadaBench] Top-level command has " + subCommands.length + " sub-commands");

                    // Extract and execute the actual commands from the command tree
                    // LogCommands wrap actual commands - we need to extract them
                    int executed = 0;

                    // Process all sub-commands recursively
                    java.util.List<VASSAL.command.Command> allCommands = new java.util.ArrayList<>();
                    collectExecutableCommands(command, allCommands);

                    System.out.println("[ArmadaBench] Found " + allCommands.size() + " executable commands");

                    // Execute each command
                    for (VASSAL.command.Command cmd : allCommands) {
                        String cmdType = cmd.getClass().getSimpleName();
                        try {
                            cmd.execute();
                            executed++;
                            if (executed <= 10 || executed % 100 == 0) {
                                System.out.println("[ArmadaBench] Executed #" + executed + ": " + cmdType);
                            }
                        } catch (Exception e) {
                            System.out.println("[ArmadaBench] Error executing " + cmdType + ": " + e.getMessage());
                        }
                    }

                    System.out.println("[ArmadaBench] Executed " + executed + " commands total");
                    return "success: Loaded " + executed + " commands";
                } catch (Exception e) {
                    System.out.println("[ArmadaBench] ERROR loading game: " + e.getClass().getSimpleName() + ": " + e.getMessage());
                    e.printStackTrace();
                    return "error: " + e.getClass().getSimpleName() + ": " + e.getMessage();
                }
            });

            // Count pieces after loading
            int totalPieces = 0;
            for (VASSAL.build.module.Map map : VASSAL.build.module.Map.getMapList()) {
                totalPieces += map.getAllPieces().length;
            }
            logger.info("After load: {} pieces on maps", totalPieces);

            java.util.Map<String, Object> response = new HashMap<>();
            response.put("success", result.startsWith("success"));
            response.put("message", result);
            response.put("path", path);
            response.put("game_started", gameModule.getGameState().isGameStarted());
            response.put("piece_count", totalPieces);

            ctx.json(response);

        } catch (Exception e) {
            logger.error("Failed to load game: {}", e.getMessage(), e);
            e.printStackTrace();
            ctx.status(500).json(errorResponse("Failed to load game: " + e.getClass().getSimpleName() + ": " + e.getMessage()));
        }
    }

    private void handleGetPalette(Context ctx) {
        try {
            List<java.util.Map<String, Object>> pieces = new ArrayList<>();

            // Get piece windows from the module
            for (PieceWindow pw : gameModule.getAllDescendantComponentsOf(PieceWindow.class)) {
                // Get all piece slots from the piece window
                for (PieceSlot slot : pw.getAllDescendantComponentsOf(PieceSlot.class)) {
                    java.util.Map<String, Object> slotInfo = new HashMap<>();

                    GamePiece piece = slot.getPiece();
                    if (piece != null) {
                        slotInfo.put("name", piece.getName());
                        slotInfo.put("id", slot.getGpId());
                        slotInfo.put("type", piece.getClass().getSimpleName());

                        // Try to get additional properties
                        try {
                            Object faction = piece.getProperty("Faction");
                            if (faction != null) slotInfo.put("faction", faction);

                            Object points = piece.getProperty("Points");
                            if (points != null) slotInfo.put("points", points);
                        } catch (Exception e) {
                            // Ignore property extraction errors
                        }

                        pieces.add(slotInfo);
                    }
                }
            }

            java.util.Map<String, Object> response = new HashMap<>();
            response.put("pieces", pieces);
            response.put("count", pieces.size());
            ctx.json(response);

        } catch (Exception e) {
            logger.error("Failed to get palette: {}", e.getMessage(), e);
            ctx.status(500).json(errorResponse("Failed to get palette: " + e.getMessage()));
        }
    }

    private void handleSpawnPiece(Context ctx) {
        try {
            String gpId = ctx.queryParam("gpId");
            String xStr = ctx.queryParam("x");
            String yStr = ctx.queryParam("y");
            String mapName = ctx.queryParam("map");

            if (gpId == null || gpId.isEmpty()) {
                ctx.status(400).json(errorResponse("Missing 'gpId' query parameter"));
                return;
            }

            int x = xStr != null ? Integer.parseInt(xStr) : 500;
            int y = yStr != null ? Integer.parseInt(yStr) : 500;

            logger.info("Spawning piece {} at ({}, {})", gpId, x, y);

            // Find the piece slot
            PieceSlot targetSlot = null;
            for (PieceWindow pw : gameModule.getAllDescendantComponentsOf(PieceWindow.class)) {
                for (PieceSlot slot : pw.getAllDescendantComponentsOf(PieceSlot.class)) {
                    if (gpId.equals(slot.getGpId())) {
                        targetSlot = slot;
                        break;
                    }
                }
                if (targetSlot != null) break;
            }

            if (targetSlot == null) {
                ctx.status(404).json(errorResponse("Piece not found in palette: " + gpId));
                return;
            }

            final PieceSlot slot = targetSlot;
            final int finalX = x;
            final int finalY = y;

            // Find the target map
            VASSAL.build.module.Map targetMap = null;
            List<VASSAL.build.module.Map> maps = VASSAL.build.module.Map.getMapList();

            if (mapName != null && !mapName.isEmpty()) {
                for (VASSAL.build.module.Map m : maps) {
                    if (mapName.equals(m.getMapName())) {
                        targetMap = m;
                        break;
                    }
                }
            }

            if (targetMap == null && !maps.isEmpty()) {
                targetMap = maps.get(0);
            }

            if (targetMap == null) {
                ctx.status(400).json(errorResponse("No maps available"));
                return;
            }

            final VASSAL.build.module.Map map = targetMap;

            String result = runOnAwtThread(() -> {
                // Get a fresh copy of the piece
                GamePiece newPiece = slot.getPiece();
                if (newPiece == null) {
                    return null;
                }

                // Place the piece on the map
                map.placeOrMerge(newPiece, new Point(finalX, finalY));

                return newPiece.getId();
            });

            if (result == null) {
                ctx.status(500).json(errorResponse("Failed to create piece from slot"));
                return;
            }

            java.util.Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("piece_id", result);
            response.put("x", x);
            response.put("y", y);
            response.put("map", map.getMapName());
            ctx.json(response);

        } catch (Exception e) {
            logger.error("Failed to spawn piece: {}", e.getMessage(), e);
            ctx.status(500).json(errorResponse("Failed to spawn piece: " + e.getMessage()));
        }
    }

    /**
     * Recursively collect executable commands from a command tree.
     * LogCommands wrap actual commands - we extract those.
     * SetupCommands are skipped to avoid wizard dialogs.
     */
    private void collectExecutableCommands(VASSAL.command.Command cmd, java.util.List<VASSAL.command.Command> result) {
        if (cmd == null) return;

        // Check if this is a LogCommand - extract the logged command
        if (cmd instanceof VASSAL.build.module.BasicLogger.LogCommand) {
            VASSAL.build.module.BasicLogger.LogCommand logCmd =
                (VASSAL.build.module.BasicLogger.LogCommand) cmd;
            VASSAL.command.Command logged = logCmd.getLoggedCommand();
            if (logged != null) {
                // Recursively process the logged command
                collectExecutableCommands(logged, result);
            }
        }
        // Skip SetupCommands to avoid wizard
        else if (cmd instanceof VASSAL.build.module.GameState.SetupCommand) {
            // Don't add SetupCommand, but process its sub-commands
        }
        // For other commands, add them to the result
        else {
            result.add(cmd);
        }

        // Process sub-commands
        for (VASSAL.command.Command sub : cmd.getSubCommands()) {
            collectExecutableCommands(sub, result);
        }
    }

    private java.util.Map<String, Object> errorResponse(String message) {
        java.util.Map<String, Object> response = new HashMap<>();
        response.put("error", true);
        response.put("message", message);
        return response;
    }
}
