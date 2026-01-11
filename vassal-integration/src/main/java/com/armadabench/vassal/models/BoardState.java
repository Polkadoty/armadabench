package com.armadabench.vassal.models;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents the complete state of the game board.
 * This is the primary data structure returned by the get_board_state MCP tool.
 */
public class BoardState {
    private int roundNumber;
    private String currentPhase;
    private String activePlayer;
    private List<ShipData> ships = new ArrayList<>();
    private List<SquadronData> squadrons = new ArrayList<>();
    private List<ObstacleData> obstacles = new ArrayList<>();
    private List<TokenData> tokens = new ArrayList<>();
    private ObjectiveData objective;
    private long timestamp;

    public BoardState() {
        this.timestamp = System.currentTimeMillis();
    }

    // Ships
    public void addShip(ShipData ship) {
        ships.add(ship);
    }

    public List<ShipData> getShips() {
        return ships;
    }

    public void setShips(List<ShipData> ships) {
        this.ships = ships;
    }

    // Squadrons
    public void addSquadron(SquadronData squadron) {
        squadrons.add(squadron);
    }

    public List<SquadronData> getSquadrons() {
        return squadrons;
    }

    public void setSquadrons(List<SquadronData> squadrons) {
        this.squadrons = squadrons;
    }

    // Obstacles
    public void addObstacle(ObstacleData obstacle) {
        obstacles.add(obstacle);
    }

    public List<ObstacleData> getObstacles() {
        return obstacles;
    }

    public void setObstacles(List<ObstacleData> obstacles) {
        this.obstacles = obstacles;
    }

    // Tokens
    public void addToken(TokenData token) {
        tokens.add(token);
    }

    public List<TokenData> getTokens() {
        return tokens;
    }

    public void setTokens(List<TokenData> tokens) {
        this.tokens = tokens;
    }

    // Game state
    public int getRoundNumber() {
        return roundNumber;
    }

    public void setRoundNumber(int roundNumber) {
        this.roundNumber = roundNumber;
    }

    public String getCurrentPhase() {
        return currentPhase;
    }

    public void setCurrentPhase(String currentPhase) {
        this.currentPhase = currentPhase;
    }

    public String getActivePlayer() {
        return activePlayer;
    }

    public void setActivePlayer(String activePlayer) {
        this.activePlayer = activePlayer;
    }

    public ObjectiveData getObjective() {
        return objective;
    }

    public void setObjective(ObjectiveData objective) {
        this.objective = objective;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    /**
     * Get ship by ID.
     */
    public ShipData getShipById(String id) {
        return ships.stream()
                .filter(s -> s.getId().equals(id))
                .findFirst()
                .orElse(null);
    }

    /**
     * Get squadron by ID.
     */
    public SquadronData getSquadronById(String id) {
        return squadrons.stream()
                .filter(s -> s.getId().equals(id))
                .findFirst()
                .orElse(null);
    }

    /**
     * Get all ships for a specific player.
     */
    public List<ShipData> getShipsForPlayer(String playerId) {
        return ships.stream()
                .filter(s -> playerId.equals(s.getPlayerId()))
                .toList();
    }

    /**
     * Get all squadrons for a specific player.
     */
    public List<SquadronData> getSquadronsForPlayer(String playerId) {
        return squadrons.stream()
                .filter(s -> playerId.equals(s.getPlayerId()))
                .toList();
    }
}
