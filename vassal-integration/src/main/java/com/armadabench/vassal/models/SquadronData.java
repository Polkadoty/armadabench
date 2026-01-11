package com.armadabench.vassal.models;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents the state of a squadron on the board.
 */
public class SquadronData {
    private String id;
    private String name;
    private String squadronType;
    private String faction;
    private String playerId;

    // Position
    private double x;
    private double y;

    // Status
    private int currentHull;
    private int maxHull;
    private boolean activated;
    private boolean engaged;

    // Abilities
    private List<String> keywords = new ArrayList<>();
    private boolean unique;

    // Dice
    private String antiShipDice;  // e.g., "1 blue"
    private String antiSquadronDice;  // e.g., "3 blue"

    // Movement
    private int speed;

    public SquadronData() {}

    public SquadronData(String id, String name) {
        this.id = id;
        this.name = name;
    }

    // Getters and setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getSquadronType() {
        return squadronType;
    }

    public void setSquadronType(String squadronType) {
        this.squadronType = squadronType;
    }

    public String getFaction() {
        return faction;
    }

    public void setFaction(String faction) {
        this.faction = faction;
    }

    public String getPlayerId() {
        return playerId;
    }

    public void setPlayerId(String playerId) {
        this.playerId = playerId;
    }

    public double getX() {
        return x;
    }

    public void setX(double x) {
        this.x = x;
    }

    public double getY() {
        return y;
    }

    public void setY(double y) {
        this.y = y;
    }

    public int getCurrentHull() {
        return currentHull;
    }

    public void setCurrentHull(int currentHull) {
        this.currentHull = currentHull;
    }

    public int getMaxHull() {
        return maxHull;
    }

    public void setMaxHull(int maxHull) {
        this.maxHull = maxHull;
    }

    public boolean isActivated() {
        return activated;
    }

    public void setActivated(boolean activated) {
        this.activated = activated;
    }

    public boolean isEngaged() {
        return engaged;
    }

    public void setEngaged(boolean engaged) {
        this.engaged = engaged;
    }

    public List<String> getKeywords() {
        return keywords;
    }

    public void setKeywords(List<String> keywords) {
        this.keywords = keywords;
    }

    public void addKeyword(String keyword) {
        keywords.add(keyword);
    }

    public boolean hasKeyword(String keyword) {
        return keywords.stream().anyMatch(k -> k.equalsIgnoreCase(keyword));
    }

    public boolean isUnique() {
        return unique;
    }

    public void setUnique(boolean unique) {
        this.unique = unique;
    }

    public String getAntiShipDice() {
        return antiShipDice;
    }

    public void setAntiShipDice(String antiShipDice) {
        this.antiShipDice = antiShipDice;
    }

    public String getAntiSquadronDice() {
        return antiSquadronDice;
    }

    public void setAntiSquadronDice(String antiSquadronDice) {
        this.antiSquadronDice = antiSquadronDice;
    }

    public int getSpeed() {
        return speed;
    }

    public void setSpeed(int speed) {
        this.speed = speed;
    }

    /**
     * Check if squadron is destroyed.
     */
    public boolean isDestroyed() {
        return currentHull <= 0;
    }

    /**
     * Check if squadron can move (not engaged or has specific keywords).
     */
    public boolean canMove() {
        if (!engaged) return true;
        return hasKeyword("Intel") || hasKeyword("Strategic");
    }
}
