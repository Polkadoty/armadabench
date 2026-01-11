package com.armadabench.extension;

import VASSAL.build.AbstractConfigurable;
import VASSAL.build.Buildable;
import VASSAL.build.GameModule;
import VASSAL.build.module.GameComponent;
import VASSAL.command.Command;
import VASSAL.configure.Configurer;
import VASSAL.i18n.Resources;
import VASSAL.build.module.documentation.HelpFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ArmadaBench Vassal Extension.
 *
 * This extension embeds a REST API server inside Vassal, allowing external
 * tools (like the MCP server) to query game state and execute actions.
 *
 * The extension registers itself as a GameComponent to receive game lifecycle
 * events and starts the API server when a game begins.
 */
public class ArmadaBenchExtension extends AbstractConfigurable implements GameComponent {
    private static final Logger logger = LoggerFactory.getLogger(ArmadaBenchExtension.class);

    private static final int DEFAULT_PORT = 8080;
    private static final String PORT_ATTR = "port";

    private EmbeddedApiServer apiServer;
    private int port = DEFAULT_PORT;
    private boolean serverStarted = false;

    public ArmadaBenchExtension() {
        logger.info("ArmadaBench Extension created");
    }

    @Override
    public void addTo(Buildable parent) {
        logger.info("ArmadaBench Extension adding to parent: {}", parent.getClass().getSimpleName());

        // Register as a GameComponent to receive game events
        GameModule.getGameModule().getGameState().addGameComponent(this);

        // Start the API server immediately since the module is loaded
        startApiServer();
    }

    @Override
    public void removeFrom(Buildable parent) {
        logger.info("ArmadaBench Extension being removed");
        stopApiServer();
        GameModule.getGameModule().getGameState().removeGameComponent(this);
    }

    /**
     * Called when a game is started or loaded.
     */
    @Override
    public void setup(boolean gameStarting) {
        logger.info("Game setup called, gameStarting={}", gameStarting);

        if (gameStarting && !serverStarted) {
            startApiServer();
        }
    }

    /**
     * Called to get the current game state for saving.
     */
    @Override
    public Command getRestoreCommand() {
        // We don't need to save any state
        return null;
    }

    private void startApiServer() {
        if (serverStarted) {
            logger.info("API server already running");
            return;
        }

        try {
            // Get port from system property if set
            String portProp = System.getProperty("armadabench.port");
            if (portProp != null) {
                port = Integer.parseInt(portProp);
            }

            logger.info("Starting ArmadaBench API server on port {}", port);

            GameModule module = GameModule.getGameModule();
            apiServer = new EmbeddedApiServer(module, port);
            apiServer.start();

            serverStarted = true;
            logger.info("ArmadaBench API server started successfully");

            // Log available endpoints
            logger.info("API Endpoints:");
            logger.info("  GET  /api/health - Health check");
            logger.info("  GET  /api/state - Get board state");
            logger.info("  GET  /api/ship/{{id}} - Get ship details");
            logger.info("  GET  /api/screenshot/base64 - Capture screenshot");

        } catch (Exception e) {
            logger.error("Failed to start API server: {}", e.getMessage(), e);
        }
    }

    private void stopApiServer() {
        if (apiServer != null) {
            logger.info("Stopping ArmadaBench API server");
            apiServer.stop();
            serverStarted = false;
        }
    }

    // AbstractConfigurable implementation

    @Override
    public String[] getAttributeNames() {
        return new String[]{PORT_ATTR};
    }

    @Override
    public String[] getAttributeDescriptions() {
        return new String[]{"API Server Port"};
    }

    @Override
    public Class<?>[] getAttributeTypes() {
        return new Class<?>[]{Integer.class};
    }

    @Override
    public void setAttribute(String key, Object value) {
        if (PORT_ATTR.equals(key)) {
            if (value instanceof String) {
                port = Integer.parseInt((String) value);
            } else if (value instanceof Integer) {
                port = (Integer) value;
            }
        }
    }

    @Override
    public String getAttributeValueString(String key) {
        if (PORT_ATTR.equals(key)) {
            return String.valueOf(port);
        }
        return null;
    }

    @Override
    public Class<?>[] getAllowableConfigureComponents() {
        return new Class<?>[0];
    }

    @Override
    public void build(org.w3c.dom.Element e) {
        super.build(e);
    }

    @Override
    public String getConfigureName() {
        return "ArmadaBench API Server";
    }

    @Override
    public Configurer getConfigurer() {
        return null;
    }

    @Override
    public HelpFile getHelpFile() {
        return null;
    }

    public static String getConfigureTypeName() {
        return "ArmadaBench Extension";
    }
}
