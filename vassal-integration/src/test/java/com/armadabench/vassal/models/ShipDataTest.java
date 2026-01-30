package com.armadabench.vassal.models;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the ShipData model.
 */
@DisplayName("ShipData")
class ShipDataTest {

    private ShipData ship;

    @BeforeEach
    void setUp() {
        ship = new ShipData("ship-1", "Victory II-class Star Destroyer");
        ship.setShipType("victory-ii");
        ship.setFaction("empire");
        ship.setPlayerId("player1");
        ship.setX(100.0);
        ship.setY(200.0);
        ship.setRotation(45.0);
        ship.setCurrentHull(8);
        ship.setMaxHull(8);
        ship.setSpeed(2);
    }

    @Nested
    @DisplayName("Construction")
    class Construction {

        @Test
        @DisplayName("should create ship with default constructor")
        void defaultConstructor() {
            ShipData newShip = new ShipData();
            assertNotNull(newShip);
            assertNull(newShip.getId());
            assertNull(newShip.getName());
        }

        @Test
        @DisplayName("should create ship with id and name")
        void constructorWithIdAndName() {
            ShipData newShip = new ShipData("test-id", "Test Ship");
            assertEquals("test-id", newShip.getId());
            assertEquals("Test Ship", newShip.getName());
        }
    }

    @Nested
    @DisplayName("Identification")
    class Identification {

        @Test
        @DisplayName("should get and set id")
        void idGetterSetter() {
            ship.setId("new-id");
            assertEquals("new-id", ship.getId());
        }

        @Test
        @DisplayName("should get and set name")
        void nameGetterSetter() {
            ship.setName("Imperial Star Destroyer");
            assertEquals("Imperial Star Destroyer", ship.getName());
        }

        @Test
        @DisplayName("should get and set ship type")
        void shipTypeGetterSetter() {
            ship.setShipType("isd-i");
            assertEquals("isd-i", ship.getShipType());
        }

        @Test
        @DisplayName("should get and set faction")
        void factionGetterSetter() {
            ship.setFaction("rebel");
            assertEquals("rebel", ship.getFaction());
        }

        @Test
        @DisplayName("should get and set player id")
        void playerIdGetterSetter() {
            ship.setPlayerId("player2");
            assertEquals("player2", ship.getPlayerId());
        }
    }

    @Nested
    @DisplayName("Position")
    class Position {

        @Test
        @DisplayName("should get and set x coordinate")
        void xGetterSetter() {
            ship.setX(500.5);
            assertEquals(500.5, ship.getX(), 0.001);
        }

        @Test
        @DisplayName("should get and set y coordinate")
        void yGetterSetter() {
            ship.setY(300.25);
            assertEquals(300.25, ship.getY(), 0.001);
        }

        @Test
        @DisplayName("should get and set rotation")
        void rotationGetterSetter() {
            ship.setRotation(180.0);
            assertEquals(180.0, ship.getRotation(), 0.001);
        }
    }

    @Nested
    @DisplayName("Hull")
    class Hull {

        @Test
        @DisplayName("should get and set current hull")
        void currentHullGetterSetter() {
            ship.setCurrentHull(5);
            assertEquals(5, ship.getCurrentHull());
        }

        @Test
        @DisplayName("should get and set max hull")
        void maxHullGetterSetter() {
            ship.setMaxHull(11);
            assertEquals(11, ship.getMaxHull());
        }
    }

    @Nested
    @DisplayName("Shields")
    class Shields {

        @Test
        @DisplayName("should set and get shields for a zone")
        void setShield() {
            ship.setShield("front", 4, 4);
            ship.setShield("left", 3, 3);
            ship.setShield("right", 3, 3);
            ship.setShield("rear", 2, 2);

            assertEquals(4, ship.getShield("front"));
            assertEquals(3, ship.getShield("left"));
            assertEquals(3, ship.getShield("right"));
            assertEquals(2, ship.getShield("rear"));
        }

        @Test
        @DisplayName("should return 0 for unknown shield zone")
        void unknownZone() {
            assertEquals(0, ship.getShield("unknown"));
        }

        @Test
        @DisplayName("should calculate total shields")
        void totalShields() {
            ship.setShield("front", 4, 4);
            ship.setShield("left", 3, 3);
            ship.setShield("right", 3, 3);
            ship.setShield("rear", 2, 2);

            assertEquals(12, ship.getTotalShields());
        }

        @Test
        @DisplayName("should get and set shield maps directly")
        void shieldMaps() {
            Map<String, Integer> current = new HashMap<>();
            current.put("front", 3);
            current.put("rear", 1);

            Map<String, Integer> max = new HashMap<>();
            max.put("front", 4);
            max.put("rear", 2);

            ship.setCurrentShields(current);
            ship.setMaxShields(max);

            assertEquals(3, ship.getCurrentShields().get("front"));
            assertEquals(4, ship.getMaxShields().get("front"));
        }
    }

    @Nested
    @DisplayName("Defense Tokens")
    class DefenseTokens {

        @Test
        @DisplayName("should add and get defense tokens")
        void addAndGetDefenseTokens() {
            ShipData.DefenseToken brace = new ShipData.DefenseToken("brace", "ready");
            ShipData.DefenseToken redirect = new ShipData.DefenseToken("redirect", "exhausted");

            ship.addDefenseToken(brace);
            ship.addDefenseToken(redirect);

            assertEquals(2, ship.getDefenseTokens().size());
            assertEquals("brace", ship.getDefenseTokens().get(0).getType());
            assertEquals("ready", ship.getDefenseTokens().get(0).getState());
        }

        @Test
        @DisplayName("should create defense token with default constructor")
        void defenseTokenDefaultConstructor() {
            ShipData.DefenseToken token = new ShipData.DefenseToken();
            assertNotNull(token);
            assertNull(token.getType());
        }

        @Test
        @DisplayName("should update defense token state")
        void updateDefenseTokenState() {
            ShipData.DefenseToken token = new ShipData.DefenseToken("evade", "ready");
            token.setState("exhausted");
            assertEquals("exhausted", token.getState());
        }
    }

    @Nested
    @DisplayName("Upgrades")
    class Upgrades {

        @Test
        @DisplayName("should add and get upgrades")
        void addAndGetUpgrades() {
            UpgradeData upgrade = new UpgradeData();
            upgrade.setId("darth-vader");
            upgrade.setName("Darth Vader");

            ship.addUpgrade(upgrade);

            assertEquals(1, ship.getUpgrades().size());
            assertEquals("Darth Vader", ship.getUpgrades().get(0).getName());
        }
    }

    @Nested
    @DisplayName("Damage")
    class Damage {

        @Test
        @DisplayName("should add and get damage cards")
        void addAndGetDamageCards() {
            ShipData.DamageCard card1 = new ShipData.DamageCard("Structural Damage", true);
            ShipData.DamageCard card2 = new ShipData.DamageCard("Standard", false);

            ship.addDamageCard(card1);
            ship.addDamageCard(card2);

            assertEquals(2, ship.getDamageCards().size());
            assertEquals(2, ship.getTotalDamage());
        }

        @Test
        @DisplayName("should create damage card with default constructor")
        void damageCardDefaultConstructor() {
            ShipData.DamageCard card = new ShipData.DamageCard();
            assertNotNull(card);
            assertNull(card.getName());
            assertFalse(card.isFaceUp());
        }

        @Test
        @DisplayName("should get and set damage card properties")
        void damageCardProperties() {
            ShipData.DamageCard card = new ShipData.DamageCard();
            card.setName("Projector Misaligned");
            card.setFaceUp(true);
            card.setEffect("Reduce shields by 1 in each arc.");

            assertEquals("Projector Misaligned", card.getName());
            assertTrue(card.isFaceUp());
            assertEquals("Reduce shields by 1 in each arc.", card.getEffect());
        }
    }

    @Nested
    @DisplayName("Activation")
    class Activation {

        @Test
        @DisplayName("should get and set activated status")
        void activatedGetterSetter() {
            ship.setActivated(true);
            assertTrue(ship.isActivated());
        }

        @Test
        @DisplayName("should get and set speed")
        void speedGetterSetter() {
            ship.setSpeed(3);
            assertEquals(3, ship.getSpeed());
        }

        @Test
        @DisplayName("should get and set command dial")
        void commandDialGetterSetter() {
            ship.setCommandDial("navigate");
            assertEquals("navigate", ship.getCommandDial());
        }

        @Test
        @DisplayName("should get and set command stack")
        void commandStackGetterSetter() {
            ship.setCommandStack(Arrays.asList("navigate", "squadron", "engineering"));
            assertEquals(3, ship.getCommandStack().size());
            assertEquals("navigate", ship.getCommandStack().get(0));
        }
    }

    @Nested
    @DisplayName("Destruction Check")
    class DestructionCheck {

        @Test
        @DisplayName("should report destroyed when hull is zero")
        void destroyedWhenHullZero() {
            ship.setCurrentHull(0);
            ship.setMaxHull(8);
            assertTrue(ship.isDestroyed());
        }

        @Test
        @DisplayName("should report destroyed when hull is negative")
        void destroyedWhenHullNegative() {
            ship.setCurrentHull(-1);
            ship.setMaxHull(8);
            assertTrue(ship.isDestroyed());
        }

        @Test
        @DisplayName("should report destroyed when damage exceeds hull")
        void destroyedWhenDamageExceedsHull() {
            ship.setCurrentHull(8);
            ship.setMaxHull(8);

            // Add 8 damage cards
            for (int i = 0; i < 8; i++) {
                ship.addDamageCard(new ShipData.DamageCard("Damage " + i, false));
            }

            assertTrue(ship.isDestroyed());
        }

        @Test
        @DisplayName("should report not destroyed when healthy")
        void notDestroyedWhenHealthy() {
            ship.setCurrentHull(8);
            ship.setMaxHull(8);
            assertFalse(ship.isDestroyed());
        }

        @Test
        @DisplayName("should report not destroyed when damaged but alive")
        void notDestroyedWhenDamagedButAlive() {
            ship.setCurrentHull(3);
            ship.setMaxHull(8);
            ship.addDamageCard(new ShipData.DamageCard("Damage", false));
            ship.addDamageCard(new ShipData.DamageCard("Damage", false));
            assertFalse(ship.isDestroyed());
        }
    }
}
