package com.armadabench.vassal.models;

/**
 * Represents an upgrade card attached to a ship.
 */
public class UpgradeData {
    private String id;
    private String name;
    private String type;  // commander, title, officer, weapons-team, etc.
    private int points;
    private String text;
    private boolean exhausted;
    private boolean discarded;
    private boolean unique;

    public UpgradeData() {}

    public UpgradeData(String id, String name, String type) {
        this.id = id;
        this.name = name;
        this.type = type;
    }

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

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public int getPoints() {
        return points;
    }

    public void setPoints(int points) {
        this.points = points;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public boolean isExhausted() {
        return exhausted;
    }

    public void setExhausted(boolean exhausted) {
        this.exhausted = exhausted;
    }

    public boolean isDiscarded() {
        return discarded;
    }

    public void setDiscarded(boolean discarded) {
        this.discarded = discarded;
    }

    public boolean isUnique() {
        return unique;
    }

    public void setUnique(boolean unique) {
        this.unique = unique;
    }

    /**
     * Check if upgrade is usable (not exhausted or discarded).
     */
    public boolean isUsable() {
        return !exhausted && !discarded;
    }
}
