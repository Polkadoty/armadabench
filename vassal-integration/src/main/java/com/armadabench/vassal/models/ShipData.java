package com.armadabench.vassal.models;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Represents the state of a ship on the board.
 */
public class ShipData {
    private String id;
    private String name;
    private String shipType;
    private String faction;
    private String playerId;

    // Position
    private double x;
    private double y;
    private double rotation;

    // Status
    private int currentHull;
    private int maxHull;
    private Map<String, Integer> currentShields = new HashMap<>();  // front, left, right, rear
    private Map<String, Integer> maxShields = new HashMap<>();

    // Defense tokens
    private List<DefenseToken> defenseTokens = new ArrayList<>();

    // Upgrades
    private List<UpgradeData> upgrades = new ArrayList<>();

    // Damage cards
    private List<DamageCard> damageCards = new ArrayList<>();

    // Activation
    private boolean activated;
    private int speed;
    private String commandDial;
    private List<String> commandStack = new ArrayList<>();

    // Constructors
    public ShipData() {}

    public ShipData(String id, String name) {
        this.id = id;
        this.name = name;
    }

    // ID and identification
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

    public String getShipType() {
        return shipType;
    }

    public void setShipType(String shipType) {
        this.shipType = shipType;
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

    // Position
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

    public double getRotation() {
        return rotation;
    }

    public void setRotation(double rotation) {
        this.rotation = rotation;
    }

    // Hull
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

    // Shields
    public Map<String, Integer> getCurrentShields() {
        return currentShields;
    }

    public void setCurrentShields(Map<String, Integer> currentShields) {
        this.currentShields = currentShields;
    }

    public Map<String, Integer> getMaxShields() {
        return maxShields;
    }

    public void setMaxShields(Map<String, Integer> maxShields) {
        this.maxShields = maxShields;
    }

    public void setShield(String zone, int current, int max) {
        currentShields.put(zone, current);
        maxShields.put(zone, max);
    }

    public int getShield(String zone) {
        return currentShields.getOrDefault(zone, 0);
    }

    // Defense tokens
    public List<DefenseToken> getDefenseTokens() {
        return defenseTokens;
    }

    public void setDefenseTokens(List<DefenseToken> defenseTokens) {
        this.defenseTokens = defenseTokens;
    }

    public void addDefenseToken(DefenseToken token) {
        defenseTokens.add(token);
    }

    // Upgrades
    public List<UpgradeData> getUpgrades() {
        return upgrades;
    }

    public void setUpgrades(List<UpgradeData> upgrades) {
        this.upgrades = upgrades;
    }

    public void addUpgrade(UpgradeData upgrade) {
        upgrades.add(upgrade);
    }

    // Damage
    public List<DamageCard> getDamageCards() {
        return damageCards;
    }

    public void setDamageCards(List<DamageCard> damageCards) {
        this.damageCards = damageCards;
    }

    public void addDamageCard(DamageCard card) {
        damageCards.add(card);
    }

    public int getTotalDamage() {
        return damageCards.size();
    }

    // Activation
    public boolean isActivated() {
        return activated;
    }

    public void setActivated(boolean activated) {
        this.activated = activated;
    }

    public int getSpeed() {
        return speed;
    }

    public void setSpeed(int speed) {
        this.speed = speed;
    }

    public String getCommandDial() {
        return commandDial;
    }

    public void setCommandDial(String commandDial) {
        this.commandDial = commandDial;
    }

    public List<String> getCommandStack() {
        return commandStack;
    }

    public void setCommandStack(List<String> commandStack) {
        this.commandStack = commandStack;
    }

    /**
     * Check if ship is destroyed.
     */
    public boolean isDestroyed() {
        return currentHull <= 0 || getTotalDamage() >= maxHull;
    }

    /**
     * Calculate total shield points remaining.
     */
    public int getTotalShields() {
        return currentShields.values().stream().mapToInt(Integer::intValue).sum();
    }

    /**
     * Nested class for defense tokens.
     */
    public static class DefenseToken {
        private String type;  // brace, redirect, evade, scatter, contain, salvo
        private String state; // ready, exhausted, discarded

        public DefenseToken() {}

        public DefenseToken(String type, String state) {
            this.type = type;
            this.state = state;
        }

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }

        public String getState() {
            return state;
        }

        public void setState(String state) {
            this.state = state;
        }
    }

    /**
     * Nested class for damage cards.
     */
    public static class DamageCard {
        private String name;
        private boolean faceUp;
        private String effect;

        public DamageCard() {}

        public DamageCard(String name, boolean faceUp) {
            this.name = name;
            this.faceUp = faceUp;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public boolean isFaceUp() {
            return faceUp;
        }

        public void setFaceUp(boolean faceUp) {
            this.faceUp = faceUp;
        }

        public String getEffect() {
            return effect;
        }

        public void setEffect(String effect) {
            this.effect = effect;
        }
    }
}
