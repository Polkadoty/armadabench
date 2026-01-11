package com.armadabench.vassal;

import VASSAL.build.module.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.util.Base64;

/**
 * Captures screenshots of the Vassal game board.
 */
public class ScreenshotCapture {
    private static final Logger logger = LoggerFactory.getLogger(ScreenshotCapture.class);

    private final VassalController controller;

    public ScreenshotCapture(VassalController controller) {
        this.controller = controller;
    }

    /**
     * Capture the entire board as a PNG image.
     *
     * @return PNG image bytes
     * @throws IOException if capture fails
     */
    public byte[] captureBoard() throws IOException {
        return captureBoard("PNG");
    }

    /**
     * Capture the entire board in specified format.
     *
     * @param format Image format (PNG, JPEG, etc.)
     * @return Image bytes
     * @throws IOException if capture fails
     */
    public byte[] captureBoard(String format) throws IOException {
        Map map = controller.getPrimaryMap();
        Dimension size = map.mapSize();
        double zoom = map.getZoom();

        int width = (int) Math.round(size.width * zoom);
        int height = (int) Math.round(size.height * zoom);

        logger.info("Capturing board: {}x{} at zoom {}", width, height, zoom);

        // Create buffered image
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        try {
            // Set rendering hints for quality
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);

            // Paint the map
            Rectangle bounds = new Rectangle(0, 0, width, height);
            map.paintRegion(g, bounds, null);

        } finally {
            g.dispose();
        }

        // Convert to bytes
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(image, format, baos);
        return baos.toByteArray();
    }

    /**
     * Capture board and return as base64 encoded string.
     *
     * @return Base64 encoded PNG image
     * @throws IOException if capture fails
     */
    public String captureBoardAsBase64() throws IOException {
        byte[] imageBytes = captureBoard();
        return Base64.getEncoder().encodeToString(imageBytes);
    }

    /**
     * Capture board as data URL suitable for web/LLM consumption.
     *
     * @return Data URL string (data:image/png;base64,...)
     * @throws IOException if capture fails
     */
    public String captureBoardAsDataUrl() throws IOException {
        String base64 = captureBoardAsBase64();
        return "data:image/png;base64," + base64;
    }

    /**
     * Capture a specific region of the board.
     *
     * @param x X coordinate
     * @param y Y coordinate
     * @param width Width of region
     * @param height Height of region
     * @return PNG image bytes
     * @throws IOException if capture fails
     */
    public byte[] captureRegion(int x, int y, int width, int height) throws IOException {
        Map map = controller.getPrimaryMap();

        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();

        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            // Translate to capture the specified region
            g.translate(-x, -y);
            Rectangle bounds = new Rectangle(x, y, width, height);
            map.paintRegion(g, bounds, null);

        } finally {
            g.dispose();
        }

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(image, "PNG", baos);
        return baos.toByteArray();
    }

    /**
     * Save board screenshot to a file.
     *
     * @param file Output file
     * @param format Image format
     * @throws IOException if save fails
     */
    public void saveBoardToFile(File file, String format) throws IOException {
        byte[] imageBytes = captureBoard(format);
        java.nio.file.Files.write(file.toPath(), imageBytes);
        logger.info("Saved screenshot to: {}", file.getAbsolutePath());
    }

    /**
     * Capture board scaled to a specific size (for LLM optimization).
     *
     * @param maxWidth Maximum width
     * @param maxHeight Maximum height
     * @return Scaled PNG image bytes
     * @throws IOException if capture fails
     */
    public byte[] captureBoardScaled(int maxWidth, int maxHeight) throws IOException {
        byte[] fullImage = captureBoard();

        // Load the full image
        BufferedImage original = ImageIO.read(new java.io.ByteArrayInputStream(fullImage));

        // Calculate scaled dimensions maintaining aspect ratio
        double scale = Math.min(
            (double) maxWidth / original.getWidth(),
            (double) maxHeight / original.getHeight()
        );

        if (scale >= 1.0) {
            // No scaling needed
            return fullImage;
        }

        int scaledWidth = (int) (original.getWidth() * scale);
        int scaledHeight = (int) (original.getHeight() * scale);

        // Create scaled image
        BufferedImage scaled = new BufferedImage(scaledWidth, scaledHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = scaled.createGraphics();

        try {
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
            g.drawImage(original, 0, 0, scaledWidth, scaledHeight, null);
        } finally {
            g.dispose();
        }

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(scaled, "PNG", baos);
        return baos.toByteArray();
    }
}
