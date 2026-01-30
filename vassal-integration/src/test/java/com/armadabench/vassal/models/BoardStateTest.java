package com.armadabench.vassal.models;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the BoardState model.
 */
@DisplayName("BoardState")
class BoardStateTest {

    private BoardState boardState;

    @BeforeEach
    void setUp() {
        boardState = new BoardState();
        boardState.setRoundNumber(2);
        boardState.setCurrentPhase("Ship Phase");
        boardState.setActivePlayer("player1");
    }

    @Nested
    @DisplayName("Construction")
    class Construction {

        @Test
        @DisplayName("should create board state with timestamp")
        void constructorSetsTimestamp() {
            BoardState state = new BoardState();
            assertTrue(state.getTimestamp() > 0);
        }

        @Test
        @DisplayName("should initialize with empty collections")
        void initializesEmptyCollections() {
            BoardState state = new BoardState();
            assertNotNull(state.getShips());
            assertNotNull(state.getSquadrons());
            assertNotNull(state.getObstacles());
            assertNotNull(state.getTokens());
            assertTrue(state.getShips().isEmpty());
            assertTrue(state.getSquadrons().isEmpty());
            assertTrue(state.getObstacles().isEmpty());
            assertTrue(state.getTokens().isEmpty());
        }
    }

    @Nested
    @DisplayName("Game State Properties")
    class GameStateProperties {

        @Test
        @DisplayName("should get and set round number")
        void roundNumberGetterSetter() {
            boardState.setRoundNumber(3);
            assertEquals(3, boardState.getRoundNumber());
        }

        @Test
        @DisplayName("should get and set current phase")
        void currentPhaseGetterSetter() {
            boardState.setCurrentPhase("Squadron Phase");
            assertEquals("Squadron Phase", boardState.getCurrentPhase());
        }

        @Test
        @DisplayName("should get and set active player")
        void activePlayerGetterSetter() {
            boardState.setActivePlayer("player2");
            assertEquals("player2", boardState.getActivePlayer());
        }

        @Test
        @DisplayName("should get and set timestamp")
        void timestampGetterSetter() {
            long customTimestamp = 1234567890L;
            boardState.setTimestamp(customTimestamp);
            assertEquals(customTimestamp, boardState.getTimestamp());
        }
    }

    @Nested
    @DisplayName("Ships")
    class Ships {

        private ShipData createShip(String id, String name, String playerId) {
            ShipData ship = new ShipData(id, name);
            ship.setPlayerId(playerId);
            return ship;
        }

        @Test
        @DisplayName("should add ship")
        void addShip() {
            ShipData ship = createShip("ship-1", "Victory II", "player1");
            boardState.addShip(ship);

            assertEquals(1, boardState.getShips().size());
            assertEquals("Victory II", boardState.getShips().get(0).getName());
        }

        @Test
        @DisplayName("should set ships list")
        void setShips() {
            List<ShipData> ships = new ArrayList<>();
            ships.add(createShip("ship-1", "Victory II", "player1"));
            ships.add(createShip("ship-2", "CR90", "player2"));

            boardState.setShips(ships);

            assertEquals(2, boardState.getShips().size());
        }

        @Test
        @DisplayName("should get ship by id")
        void getShipById() {
            boardState.addShip(createShip("ship-1", "Victory II", "player1"));
            boardState.addShip(createShip("ship-2", "CR90", "player2"));

            ShipData found = boardState.getShipById("ship-2");
            assertNotNull(found);
            assertEquals("CR90", found.getName());
        }

        @Test
        @DisplayName("should return null for non-existent ship id")
        void getShipByIdNotFound() {
            boardState.addShip(createShip("ship-1", "Victory II", "player1"));

            ShipData found = boardState.getShipById("ship-999");
            assertNull(found);
        }

        @Test
        @DisplayName("should get ships for player")
        void getShipsForPlayer() {
            boardState.addShip(createShip("ship-1", "Victory II", "player1"));
            boardState.addShip(createShip("ship-2", "ISD", "player1"));
            boardState.addShip(createShip("ship-3", "CR90", "player2"));

            List<ShipData> player1Ships = boardState.getShipsForPlayer("player1");
            assertEquals(2, player1Ships.size());

            List<ShipData> player2Ships = boardState.getShipsForPlayer("player2");
            assertEquals(1, player2Ships.size());
            assertEquals("CR90", player2Ships.get(0).getName());
        }

        @Test
        @DisplayName("should return empty list for player with no ships")
        void getShipsForPlayerEmpty() {
            boardState.addShip(createShip("ship-1", "Victory II", "player1"));

            List<ShipData> player2Ships = boardState.getShipsForPlayer("player2");
            assertTrue(player2Ships.isEmpty());
        }
    }

    @Nested
    @DisplayName("Squadrons")
    class Squadrons {

        private SquadronData createSquadron(String id, String name, String playerId) {
            SquadronData squadron = new SquadronData();
            squadron.setId(id);
            squadron.setName(name);
            squadron.setPlayerId(playerId);
            return squadron;
        }

        @Test
        @DisplayName("should add squadron")
        void addSquadron() {
            SquadronData squadron = createSquadron("squad-1", "TIE Fighter", "player1");
            boardState.addSquadron(squadron);

            assertEquals(1, boardState.getSquadrons().size());
        }

        @Test
        @DisplayName("should set squadrons list")
        void setSquadrons() {
            List<SquadronData> squadrons = new ArrayList<>();
            squadrons.add(createSquadron("squad-1", "TIE Fighter", "player1"));
            squadrons.add(createSquadron("squad-2", "X-Wing", "player2"));

            boardState.setSquadrons(squadrons);

            assertEquals(2, boardState.getSquadrons().size());
        }

        @Test
        @DisplayName("should get squadron by id")
        void getSquadronById() {
            boardState.addSquadron(createSquadron("squad-1", "TIE Fighter", "player1"));
            boardState.addSquadron(createSquadron("squad-2", "X-Wing", "player2"));

            SquadronData found = boardState.getSquadronById("squad-1");
            assertNotNull(found);
            assertEquals("TIE Fighter", found.getName());
        }

        @Test
        @DisplayName("should return null for non-existent squadron id")
        void getSquadronByIdNotFound() {
            boardState.addSquadron(createSquadron("squad-1", "TIE Fighter", "player1"));

            SquadronData found = boardState.getSquadronById("squad-999");
            assertNull(found);
        }

        @Test
        @DisplayName("should get squadrons for player")
        void getSquadronsForPlayer() {
            boardState.addSquadron(createSquadron("squad-1", "TIE Fighter", "player1"));
            boardState.addSquadron(createSquadron("squad-2", "TIE Fighter", "player1"));
            boardState.addSquadron(createSquadron("squad-3", "X-Wing", "player2"));

            List<SquadronData> player1Squadrons = boardState.getSquadronsForPlayer("player1");
            assertEquals(2, player1Squadrons.size());

            List<SquadronData> player2Squadrons = boardState.getSquadronsForPlayer("player2");
            assertEquals(1, player2Squadrons.size());
        }
    }

    @Nested
    @DisplayName("Obstacles")
    class Obstacles {

        @Test
        @DisplayName("should add obstacle")
        void addObstacle() {
            ObstacleData obstacle = new ObstacleData();
            obstacle.setId("obs-1");
            obstacle.setType("asteroid");

            boardState.addObstacle(obstacle);

            assertEquals(1, boardState.getObstacles().size());
        }

        @Test
        @DisplayName("should set obstacles list")
        void setObstacles() {
            List<ObstacleData> obstacles = new ArrayList<>();
            ObstacleData obs1 = new ObstacleData();
            obs1.setId("obs-1");
            obstacles.add(obs1);

            boardState.setObstacles(obstacles);

            assertEquals(1, boardState.getObstacles().size());
        }
    }

    @Nested
    @DisplayName("Tokens")
    class Tokens {

        @Test
        @DisplayName("should add token")
        void addToken() {
            TokenData token = new TokenData();
            token.setId("token-1");
            token.setType("objective");

            boardState.addToken(token);

            assertEquals(1, boardState.getTokens().size());
        }

        @Test
        @DisplayName("should set tokens list")
        void setTokens() {
            List<TokenData> tokens = new ArrayList<>();
            TokenData token = new TokenData();
            token.setId("token-1");
            tokens.add(token);

            boardState.setTokens(tokens);

            assertEquals(1, boardState.getTokens().size());
        }
    }

    @Nested
    @DisplayName("Objective")
    class Objective {

        @Test
        @DisplayName("should get and set objective")
        void objectiveGetterSetter() {
            ObjectiveData objective = new ObjectiveData();
            objective.setName("Advanced Gunnery");
            objective.setType("assault");

            boardState.setObjective(objective);

            assertNotNull(boardState.getObjective());
            assertEquals("Advanced Gunnery", boardState.getObjective().getName());
        }
    }
}
