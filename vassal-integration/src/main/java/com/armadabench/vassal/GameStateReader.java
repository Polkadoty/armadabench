package com.armadabench.vassal;

import VASSAL.build.module.Map;
import VASSAL.counters.GamePiece;
import VASSAL.counters.Stack;
import com.armadabench.vassal.models.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.awt.Point;
import java.util.HashMap;

/**
 * Reads and extracts game state from Vassal.
 *
 * This class traverses all pieces on the map and categorizes them
 * into ships, squadrons, obstacles, and tokens for the Armada game.
 */
public class GameStateReader {
    private static final Logger logger = LoggerFactory.getLogger(GameStateReader.class);

    private final VassalController controller;

    // Property keys used in the Armada Vassal module
    // These may need adjustment based on actual module structure
    private static final String PROP_PIECE_TYPE = "Type";
    private static final String PROP_PIECE_NAME = "BasicName";
    private static final String PROP_PLAYER = "PlayerSide";
    private static final String PROP_FACTION = "Faction";
    private static final String PROP_HULL = "Hull";
    private static final String PROP_MAX_HULL = "MaxHull";
    private static final String PROP_FRONT_SHIELDS = "FrontShield";
    private static final String PROP_LEFT_SHIELDS = "LeftShield";
    private static final String PROP_RIGHT_SHIELDS = "RightShield";
    private static final String PROP_REAR_SHIELDS = "RearShield";
    private static final String PROP_ACTIVATED = "Activated";
    private static final String PROP_SPEED = "Speed";

    public GameStateReader(VassalController controller) {
        this.controller = controller;
    }

    /**
     * Get the complete current board state.
     *
     * @return BoardState containing all game elements
     */
    public BoardState getCurrentState() {
        BoardState state = new BoardState();

        try {
            Map primaryMap = controller.getPrimaryMap();
            GamePiece[] pieces = primaryMap.getAllPieces();

            logger.info("Reading {} pieces from map", pieces.length);

            for (GamePiece piece : pieces) {
                processPiece(piece, state);
            }

            // Extract game-level state
            extractGameState(state);

        } catch (Exception e) {
            logger.error("Error reading game state: {}", e.getMessage(), e);
        }

        return state;
    }

    /**
     * Process a single piece and add it to the appropriate collection.
     */
    private void processPiece(GamePiece piece, BoardState state) {
        // Handle stacks (groups of pieces)
        if (piece instanceof Stack) {
            Stack stack = (Stack) piece;
            for (int i = 0; i < stack.getPieceCount(); i++) {
                processPiece(stack.getPieceAt(i), state);
            }
            return;
        }

        // Determine piece type
        String pieceType = getStringProperty(piece, PROP_PIECE_TYPE, "");

        if (isShip(pieceType, piece)) {
            state.addShip(extractShipData(piece));
        } else if (isSquadron(pieceType, piece)) {
            state.addSquadron(extractSquadronData(piece));
        } else if (isObstacle(pieceType, piece)) {
            state.addObstacle(extractObstacleData(piece));
        } else if (isToken(pieceType, piece)) {
            state.addToken(extractTokenData(piece));
        }
        // Ignore other pieces (markers, labels, etc.)
    }

    /**
     * Extract ship data from a GamePiece.
     */
    private ShipData extractShipData(GamePiece piece) {
        ShipData ship = new ShipData();

        // Basic identity
        ship.setId(piece.getId());
        ship.setName(getStringProperty(piece, PROP_PIECE_NAME, "Unknown Ship"));
        ship.setFaction(getStringProperty(piece, PROP_FACTION, ""));
        ship.setPlayerId(getStringProperty(piece, PROP_PLAYER, ""));

        // Position
        Point pos = piece.getPosition();
        if (pos != null) {
            ship.setX(pos.x);
            ship.setY(pos.y);
        }

        // Rotation (may be stored in a Rotate trait)
        ship.setRotation(getRotation(piece));

        // Hull
        ship.setCurrentHull(getIntProperty(piece, PROP_HULL, 0));
        ship.setMaxHull(getIntProperty(piece, PROP_MAX_HULL, 0));

        // Shields
        extractShields(piece, ship);

        // Status
        ship.setActivated(getBooleanProperty(piece, PROP_ACTIVATED, false));
        ship.setSpeed(getIntProperty(piece, PROP_SPEED, 0));

        // Defense tokens (would need to read from attached pieces)
        // extractDefenseTokens(piece, ship);

        // Upgrades (would need to read from attached pieces or properties)
        // extractUpgrades(piece, ship);

        logger.debug("Extracted ship: {} at ({}, {})", ship.getName(), ship.getX(), ship.getY());
        return ship;
    }

    /**
     * Extract squadron data from a GamePiece.
     */
    private SquadronData extractSquadronData(GamePiece piece) {
        SquadronData squadron = new SquadronData();

        squadron.setId(piece.getId());
        squadron.setName(getStringProperty(piece, PROP_PIECE_NAME, "Unknown Squadron"));
        squadron.setFaction(getStringProperty(piece, PROP_FACTION, ""));
        squadron.setPlayerId(getStringProperty(piece, PROP_PLAYER, ""));

        Point pos = piece.getPosition();
        if (pos != null) {
            squadron.setX(pos.x);
            squadron.setY(pos.y);
        }

        squadron.setCurrentHull(getIntProperty(piece, PROP_HULL, 0));
        squadron.setMaxHull(getIntProperty(piece, PROP_MAX_HULL, 0));
        squadron.setActivated(getBooleanProperty(piece, PROP_ACTIVATED, false));

        logger.debug("Extracted squadron: {} at ({}, {})", squadron.getName(), squadron.getX(), squadron.getY());
        return squadron;
    }

    /**
     * Extract obstacle data from a GamePiece.
     */
    private ObstacleData extractObstacleData(GamePiece piece) {
        ObstacleData obstacle = new ObstacleData();

        obstacle.setId(piece.getId());
        obstacle.setType(getStringProperty(piece, PROP_PIECE_TYPE, "Unknown"));

        Point pos = piece.getPosition();
        if (pos != null) {
            obstacle.setX(pos.x);
            obstacle.setY(pos.y);
        }

        obstacle.setRotation(getRotation(piece));

        // Get bounding box for size
        java.awt.Rectangle bounds = piece.boundingBox();
        if (bounds != null) {
            obstacle.setWidth(bounds.width);
            obstacle.setHeight(bounds.height);
        }

        return obstacle;
    }

    /**
     * Extract token data from a GamePiece.
     */
    private TokenData extractTokenData(GamePiece piece) {
        TokenData token = new TokenData();

        token.setId(piece.getId());
        token.setType(getStringProperty(piece, PROP_PIECE_TYPE, "Unknown"));

        Point pos = piece.getPosition();
        if (pos != null) {
            token.setX(pos.x);
            token.setY(pos.y);
        }

        token.setOwner(getStringProperty(piece, PROP_PLAYER, null));

        return token;
    }

    /**
     * Extract shield values for a ship.
     */
    private void extractShields(GamePiece piece, ShipData ship) {
        ship.setShield("front",
            getIntProperty(piece, PROP_FRONT_SHIELDS, 0),
            getIntProperty(piece, "Max" + PROP_FRONT_SHIELDS, 0));
        ship.setShield("left",
            getIntProperty(piece, PROP_LEFT_SHIELDS, 0),
            getIntProperty(piece, "Max" + PROP_LEFT_SHIELDS, 0));
        ship.setShield("right",
            getIntProperty(piece, PROP_RIGHT_SHIELDS, 0),
            getIntProperty(piece, "Max" + PROP_RIGHT_SHIELDS, 0));
        ship.setShield("rear",
            getIntProperty(piece, PROP_REAR_SHIELDS, 0),
            getIntProperty(piece, "Max" + PROP_REAR_SHIELDS, 0));
    }

    /**
     * Extract game-level state (round, phase, etc.).
     */
    private void extractGameState(BoardState state) {
        // This would read from global game properties
        // Implementation depends on how Armada module tracks this
        state.setRoundNumber(1);  // Default
        state.setCurrentPhase("Unknown");
    }

    // Piece type detection methods
    // These need to be adjusted based on actual Armada module structure

    private boolean isShip(String type, GamePiece piece) {
        if (type == null) return false;
        String lower = type.toLowerCase();
        return lower.contains("ship") || lower.contains("flotilla");
    }

    private boolean isSquadron(String type, GamePiece piece) {
        if (type == null) return false;
        String lower = type.toLowerCase();
        return lower.contains("squadron") || lower.contains("fighter");
    }

    private boolean isObstacle(String type, GamePiece piece) {
        if (type == null) return false;
        String lower = type.toLowerCase();
        return lower.contains("asteroid") || lower.contains("debris") ||
               lower.contains("station") || lower.contains("obstacle");
    }

    private boolean isToken(String type, GamePiece piece) {
        if (type == null) return false;
        String lower = type.toLowerCase();
        return lower.contains("token") || lower.contains("marker");
    }

    // Property extraction helpers

    private String getStringProperty(GamePiece piece, String key, String defaultValue) {
        Object value = piece.getProperty(key);
        if (value instanceof String) {
            return (String) value;
        }
        return defaultValue;
    }

    private int getIntProperty(GamePiece piece, String key, int defaultValue) {
        Object value = piece.getProperty(key);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        if (value instanceof String) {
            try {
                return Integer.parseInt((String) value);
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        }
        return defaultValue;
    }

    private boolean getBooleanProperty(GamePiece piece, String key, boolean defaultValue) {
        Object value = piece.getProperty(key);
        if (value instanceof Boolean) {
            return (Boolean) value;
        }
        if (value instanceof String) {
            return "true".equalsIgnoreCase((String) value);
        }
        return defaultValue;
    }

    private double getRotation(GamePiece piece) {
        // Rotation is typically stored in a Rotate decorator trait
        // This is a simplified extraction - may need adjustment
        Object rotation = piece.getProperty("Rotation");
        if (rotation instanceof Number) {
            return ((Number) rotation).doubleValue();
        }
        return 0.0;
    }

    /**
     * Get details for a specific ship.
     */
    public ShipData getShipById(String shipId) {
        BoardState state = getCurrentState();
        return state.getShipById(shipId);
    }

    /**
     * Get details for a specific squadron.
     */
    public SquadronData getSquadronById(String squadronId) {
        BoardState state = getCurrentState();
        return state.getSquadronById(squadronId);
    }
}
