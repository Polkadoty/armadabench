package com.armadabench.vassal.models;

/**
 * Represents a token on the board (objective tokens, command tokens, etc.).
 */
public class TokenData {
    private String id;
    private String type;
    private double x;
    private double y;
    private String owner;  // player ID or null for neutral
    private String attachedTo;  // ID of ship/squadron if attached

    public TokenData() {}

    public TokenData(String id, String type) {
        this.id = id;
        this.type = type;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
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

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public String getAttachedTo() {
        return attachedTo;
    }

    public void setAttachedTo(String attachedTo) {
        this.attachedTo = attachedTo;
    }
}
