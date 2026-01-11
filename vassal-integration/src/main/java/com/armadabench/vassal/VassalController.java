package com.armadabench.vassal;

import VASSAL.build.GameModule;
import VASSAL.build.module.GameState;
import VASSAL.build.module.Map;
import VASSAL.launch.BasicModule;
import VASSAL.tools.DataArchive;
import VASSAL.tools.menu.MenuManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.swing.JFrame;
import javax.swing.JMenuBar;
import java.io.File;
import java.io.IOException;
import java.util.List;

/**
 * Controller for managing Vassal engine lifecycle and module loading.
 *
 * This class provides the bridge between ArmadaBench and the Vassal engine,
 * handling module loading, game state access, and cleanup.
 */
public class VassalController {
    private static final Logger logger = LoggerFactory.getLogger(VassalController.class);

    private GameModule gameModule;
    private DataArchive dataArchive;
    private String modulePath;
    private boolean initialized = false;

    /**
     * Initialize Vassal with the specified module file.
     *
     * @param modulePath Path to the .vmod file
     * @throws IOException if the module cannot be loaded
     */
    public void initialize(String modulePath) throws IOException {
        if (initialized) {
            throw new IllegalStateException("VassalController already initialized. Call shutdown() first.");
        }

        this.modulePath = modulePath;
        File moduleFile = new File(modulePath);

        if (!moduleFile.exists()) {
            throw new IOException("Module file not found: " + modulePath);
        }

        logger.info("Loading Vassal module: {}", modulePath);

        try {
            // Initialize Vassal's infrastructure first
            // This is required before GameModule can be created
            initializeVassalInfrastructure();

            // Create DataArchive from the .vmod file
            dataArchive = new DataArchive(modulePath);

            // Initialize the GameModule using BasicModule (lighter weight)
            gameModule = new BasicModule(dataArchive);
            GameModule.init(gameModule);

            initialized = true;
            logger.info("Vassal module loaded successfully");

        } catch (Exception e) {
            logger.error("Failed to load Vassal module: {}", e.getMessage(), e);
            throw new IOException("Failed to load Vassal module: " + e.getMessage(), e);
        }
    }

    /**
     * Initialize Vassal's infrastructure (MenuManager, etc.) before loading a module.
     * This is normally done by Player or ModuleManager but we need to do it manually.
     */
    private void initializeVassalInfrastructure() throws Exception {
        logger.info("Initializing Vassal infrastructure...");

        // Check if MenuManager is already initialized
        try {
            MenuManager.getInstance();
            logger.info("MenuManager already initialized");
            return;
        } catch (IllegalStateException e) {
            logger.info("MenuManager not initialized, setting up...");
        }

        // Create a minimal frame for Vassal's menu system
        JFrame frame = new JFrame("ArmadaBench");
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        JMenuBar menuBar = new JMenuBar();
        frame.setJMenuBar(menuBar);

        // Initialize MenuManager using reflection since init() is package-private
        // MenuManager.init(frame) sets up the singleton
        try {
            java.lang.reflect.Method initMethod = MenuManager.class.getDeclaredMethod("init", JFrame.class);
            initMethod.setAccessible(true);
            initMethod.invoke(null, frame);
            logger.info("MenuManager initialized via reflection");
        } catch (NoSuchMethodException e) {
            // Try alternative approach - some versions use different signatures
            logger.warn("Could not find init(JFrame) method, trying alternative...");
            try {
                // Try creating instance directly via constructor
                java.lang.reflect.Constructor<?> ctor = MenuManager.class.getDeclaredConstructor(JFrame.class);
                ctor.setAccessible(true);
                Object instance = ctor.newInstance(frame);

                // Set the static instance field
                java.lang.reflect.Field instanceField = MenuManager.class.getDeclaredField("instance");
                instanceField.setAccessible(true);
                instanceField.set(null, instance);
                logger.info("MenuManager initialized via constructor reflection");
            } catch (Exception e2) {
                logger.error("Failed to initialize MenuManager: {}", e2.getMessage());
                throw new RuntimeException("Cannot initialize Vassal MenuManager", e2);
            }
        }

        logger.info("Vassal infrastructure initialized");
    }

    /**
     * Get the loaded GameModule.
     *
     * @return The GameModule instance
     * @throws IllegalStateException if not initialized
     */
    public GameModule getGameModule() {
        checkInitialized();
        return gameModule;
    }

    /**
     * Get the GameState from the loaded module.
     *
     * @return The GameState instance
     * @throws IllegalStateException if not initialized
     */
    public GameState getGameState() {
        checkInitialized();
        return gameModule.getGameState();
    }

    /**
     * Get all maps in the module.
     *
     * @return List of Map instances
     * @throws IllegalStateException if not initialized
     */
    public List<Map> getMaps() {
        checkInitialized();
        return Map.getMapList();
    }

    /**
     * Get the primary game map (usually the first one).
     *
     * @return The main Map instance
     * @throws IllegalStateException if not initialized or no maps found
     */
    public Map getPrimaryMap() {
        List<Map> maps = getMaps();
        if (maps.isEmpty()) {
            throw new IllegalStateException("No maps found in module");
        }
        return maps.get(0);
    }

    /**
     * Load a saved game file.
     *
     * @param savedGamePath Path to the .vsav or .vlog file
     * @throws IOException if the saved game cannot be loaded
     */
    public void loadSavedGame(String savedGamePath) throws IOException {
        checkInitialized();
        File saveFile = new File(savedGamePath);

        if (!saveFile.exists()) {
            throw new IOException("Saved game file not found: " + savedGamePath);
        }

        logger.info("Loading saved game: {}", savedGamePath);

        try {
            // Use Vassal's load game mechanism
            GameState gameState = getGameState();
            gameState.loadGameInBackground(saveFile);

            logger.info("Saved game loaded successfully");

        } catch (Exception e) {
            logger.error("Failed to load saved game: {}", e.getMessage(), e);
            throw new IOException("Failed to load saved game: " + e.getMessage(), e);
        }
    }

    /**
     * Start a new game with default setup.
     */
    public void startNewGame() {
        checkInitialized();
        logger.info("Starting new game");

        GameState gameState = getGameState();
        gameState.setup(true);
    }

    /**
     * Check if the controller is initialized.
     *
     * @return true if initialized
     */
    public boolean isInitialized() {
        return initialized;
    }

    /**
     * Get the path to the loaded module.
     *
     * @return The module path
     */
    public String getModulePath() {
        return modulePath;
    }

    /**
     * Shutdown and cleanup resources.
     */
    public void shutdown() {
        if (!initialized) {
            return;
        }

        logger.info("Shutting down VassalController");

        try {
            if (dataArchive != null) {
                dataArchive.close();
            }
        } catch (Exception e) {
            logger.warn("Error closing data archive: {}", e.getMessage());
        }

        gameModule = null;
        dataArchive = null;
        initialized = false;
    }

    private void checkInitialized() {
        if (!initialized) {
            throw new IllegalStateException("VassalController not initialized. Call initialize() first.");
        }
    }
}
