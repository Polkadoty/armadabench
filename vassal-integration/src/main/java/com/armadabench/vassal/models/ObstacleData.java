package com.armadabench.vassal.models;

/**
 * Represents an obstacle on the board (asteroid, debris, station, etc.).
 */
public class ObstacleData {
    private String id;
    private String type;  // asteroid, debris, station, purrgil, etc.
    private double x;
    private double y;
    private double rotation;
    private double width;
    private double height;

    public ObstacleData() {}

    public ObstacleData(String id, String type) {
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

    public double getRotation() {
        return rotation;
    }

    public void setRotation(double rotation) {
        this.rotation = rotation;
    }

    public double getWidth() {
        return width;
    }

    public void setWidth(double width) {
        this.width = width;
    }

    public double getHeight() {
        return height;
    }

    public void setHeight(double height) {
        this.height = height;
    }

    /**
     * Check if this obstacle is a station (provides benefits).
     */
    public boolean isStation() {
        return type != null && type.toLowerCase().contains("station");
    }
}
