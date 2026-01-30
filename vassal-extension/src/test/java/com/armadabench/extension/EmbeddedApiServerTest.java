package com.armadabench.extension;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.lang.reflect.Method;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the EmbeddedApiServer class.
 *
 * Note: Many methods require VASSAL runtime environment, so we focus on
 * testing the piece classification logic which can be unit tested.
 */
@DisplayName("EmbeddedApiServer")
class EmbeddedApiServerTest {

    /**
     * Helper to invoke private isShipPiece method via reflection.
     */
    private boolean invokeIsShipPiece(String nameLower) throws Exception {
        EmbeddedApiServer server = createServerWithNullModule();
        Method method = EmbeddedApiServer.class.getDeclaredMethod("isShipPiece", String.class);
        method.setAccessible(true);
        return (Boolean) method.invoke(server, nameLower);
    }

    /**
     * Helper to invoke private isSquadronPiece method via reflection.
     */
    private boolean invokeIsSquadronPiece(String nameLower) throws Exception {
        EmbeddedApiServer server = createServerWithNullModule();
        Method method = EmbeddedApiServer.class.getDeclaredMethod("isSquadronPiece", String.class);
        method.setAccessible(true);
        return (Boolean) method.invoke(server, nameLower);
    }

    /**
     * Create server instance for testing (module will be null, but ok for classification tests).
     */
    private EmbeddedApiServer createServerWithNullModule() {
        return new EmbeddedApiServer(null, 8080);
    }

    @Nested
    @DisplayName("Ship Classification")
    class ShipClassification {

        @ParameterizedTest
        @DisplayName("should identify ships by -class pattern")
        @ValueSource(strings = {
            "victory (victory-class)",
            "imperial (imperial-class)",
            "imperial i-class star destroyer",
            "acclamator i-class assault ship"
        })
        void identifiesShipsByClassPattern(String name) throws Exception {
            assertTrue(invokeIsShipPiece(name.toLowerCase()),
                "Should identify '" + name + "' as a ship");
        }

        @ParameterizedTest
        @DisplayName("should identify ships by hull type endings")
        @ValueSource(strings = {
            "victory cruiser",
            "assault frigate",
            "star destroyer",
            "hammerhead corvette",
            "imperial carrier",
            "super star dreadnought"
        })
        void identifiesShipsByHullType(String name) throws Exception {
            assertTrue(invokeIsShipPiece(name.toLowerCase()),
                "Should identify '" + name + "' as a ship");
        }

        @ParameterizedTest
        @DisplayName("should identify Imperial ships")
        @ValueSource(strings = {
            "victory i",
            "victory ii",
            "imperial i",
            "imperial ii",
            "gladiator i",
            "gladiator ii",
            "raider i",
            "raider ii",
            "arquitens command cruiser",
            "quasar fire i",
            "interdictor suppression refit",
            "onager star destroyer",
            "gozanti cruisers",
            "executor"
        })
        void identifiesImperialShips(String name) throws Exception {
            assertTrue(invokeIsShipPiece(name.toLowerCase()),
                "Should identify Imperial ship '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should identify Rebel ships")
        @ValueSource(strings = {
            "assault frigate mark ii",
            "nebulon-b escort frigate",
            "mc30c torpedo frigate",
            "mc80 assault cruiser",
            "mc75 armored cruiser",
            "cr90 corvette a",
            "liberty class star cruiser",
            "home one",
            "profundity",
            "starhawk battleship",
            "gr-75 medium transports",
            "hammerhead torpedo corvette",
            "pelta command ship"
        })
        void identifiesRebelShips(String name) throws Exception {
            assertTrue(invokeIsShipPiece(name.toLowerCase()),
                "Should identify Rebel ship '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should identify Republic ships")
        @ValueSource(strings = {
            "acclamator i assault ship",
            "venator i star destroyer",
            "venator ii",
            "consular armed cruiser",
            "charger c70 retrofit"
        })
        void identifiesRepublicShips(String name) throws Exception {
            assertTrue(invokeIsShipPiece(name.toLowerCase()),
                "Should identify Republic ship '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should identify Separatist ships")
        @ValueSource(strings = {
            "providence dreadnought",
            "munificent star frigate",
            "hardcell transport",
            "recusant light destroyer",
            "invisible hand"
        })
        void identifiesSeparatistShips(String name) throws Exception {
            assertTrue(invokeIsShipPiece(name.toLowerCase()),
                "Should identify Separatist ship '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should not classify non-ships as ships")
        @ValueSource(strings = {
            "tie fighter squadron",
            "x-wing squadron",
            "darth vader",
            "admiral ackbar",
            "engineering token",
            "command dial"
        })
        void doesNotClassifyNonShipsAsShips(String name) throws Exception {
            assertFalse(invokeIsShipPiece(name.toLowerCase()),
                "Should NOT identify '" + name + "' as a ship");
        }
    }

    @Nested
    @DisplayName("Squadron Classification")
    class SquadronClassification {

        @ParameterizedTest
        @DisplayName("should identify squadrons by 'squadron' keyword")
        @ValueSource(strings = {
            "tie fighter squadron",
            "x-wing squadron",
            "b-wing squadron",
            "vulture-class droid fighter squadron"
        })
        void identifiesSquadronsByKeyword(String name) throws Exception {
            assertTrue(invokeIsSquadronPiece(name.toLowerCase()),
                "Should identify '" + name + "' as a squadron");
        }

        @ParameterizedTest
        @DisplayName("should identify Imperial fighter types")
        @ValueSource(strings = {
            "tie fighter",
            "tie advanced",
            "tie bomber",
            "tie interceptor",
            "tie defender",
            "tie phantom",
            "tie/ln fighter"
        })
        void identifiesImperialFighters(String name) throws Exception {
            assertTrue(invokeIsSquadronPiece(name.toLowerCase()),
                "Should identify Imperial fighter '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should identify Rebel fighter types")
        @ValueSource(strings = {
            "x-wing",
            "y-wing",
            "a-wing",
            "b-wing",
            "e-wing",
            "hwk-290",
            "vcx-100 ghost",
            "phantom ii",
            "yt-1300",
            "yt-2400",
            "z-95 headhunter",
            "lancer pursuit craft"
        })
        void identifiesRebelFighters(String name) throws Exception {
            assertTrue(invokeIsSquadronPiece(name.toLowerCase()),
                "Should identify Rebel fighter '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should identify Republic fighter types")
        @ValueSource(strings = {
            "arc-170",
            "delta-7 aethersprite",
            "btl-b y-wing",
            "v-19 torrent",
            "clone z-95",
            "eta-2 actis"
        })
        void identifiesRepublicFighters(String name) throws Exception {
            assertTrue(invokeIsSquadronPiece(name.toLowerCase()),
                "Should identify Republic fighter '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should identify Separatist fighter types")
        @ValueSource(strings = {
            "vulture droid fighter",
            "hyena bomber",
            "droid tri-fighter",
            "belbullab-22",
            "nantex starfighter"
        })
        void identifiesSeparatistFighters(String name) throws Exception {
            assertTrue(invokeIsSquadronPiece(name.toLowerCase()),
                "Should identify Separatist fighter '" + name + "'");
        }

        @ParameterizedTest
        @DisplayName("should not classify non-squadrons as squadrons")
        @ValueSource(strings = {
            "victory star destroyer",
            "imperial class",
            "admiral piett",
            "turbolaser reroute circuits",
            "engineering dial"
        })
        void doesNotClassifyNonSquadronsAsSquadrons(String name) throws Exception {
            assertFalse(invokeIsSquadronPiece(name.toLowerCase()),
                "Should NOT identify '" + name + "' as a squadron");
        }
    }

    @Nested
    @DisplayName("Edge Cases")
    class EdgeCases {

        @Test
        @DisplayName("should handle empty string")
        void handlesEmptyString() throws Exception {
            assertFalse(invokeIsShipPiece(""));
            assertFalse(invokeIsSquadronPiece(""));
        }

        @Test
        @DisplayName("should be case insensitive (input already lowercase)")
        void caseInsensitive() throws Exception {
            assertTrue(invokeIsShipPiece("victory ii"));
            assertTrue(invokeIsSquadronPiece("tie fighter"));
        }

        @Test
        @DisplayName("should handle partial matches correctly")
        void handlesPartialMatches() throws Exception {
            // "victory" alone should match (ship pattern)
            assertTrue(invokeIsShipPiece("victory i"));

            // Random text containing "class" should not match
            assertFalse(invokeIsShipPiece("first class upgrade"));
        }
    }
}
