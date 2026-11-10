package com.tahaakhan.spellmod.gametest;

import com.mojang.authlib.GameProfile;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.item.ManaCrystalItem;
import com.tahaakhan.spellmod.item.WandItem;
import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.registry.ModDataComponents;
import com.tahaakhan.spellmod.registry.ModItems;
import com.tahaakhan.spellmod.spell.Spell;
import io.netty.channel.embedded.EmbeddedChannel;
import java.util.UUID;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.FunctionGameTestInstance;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.TestData;
import net.minecraft.gametest.framework.TestEnvironmentDefinition;
import net.minecraft.network.Connection;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.projectile.hurtingprojectile.SmallFireball;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.RegisterGameTestsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Automated in-game tests. Run them with {@code ./gradlew runGameTestServer}. */
public final class SpellGameTests {
    private static final DeferredRegister<Consumer<GameTestHelper>> TEST_FUNCTIONS =
            DeferredRegister.create(Registries.TEST_FUNCTION, SpellMod.MODID);

    private static final String[] NAMES = {"fireball_costs_mana", "no_mana_no_cast", "heal_restores_health",
            "sneak_cycles_spell", "mana_crystal_restores_mana", "mana_regenerates", "blink_teleports", "lightning_strikes"};

    static {
        test(NAMES[0], SpellGameTests::fireballCostsMana);
        test(NAMES[1], SpellGameTests::noManaNoCast);
        test(NAMES[2], SpellGameTests::healRestoresHealth);
        test(NAMES[3], SpellGameTests::sneakCyclesSpell);
        test(NAMES[4], SpellGameTests::manaCrystalRestoresMana);
        test(NAMES[5], SpellGameTests::manaRegenerates);
        test(NAMES[6], SpellGameTests::blinkTeleports);
        test(NAMES[7], SpellGameTests::lightningStrikes);
    }

    private SpellGameTests() {}

    public static void register(IEventBus modEventBus) {
        TEST_FUNCTIONS.register(modEventBus);
        modEventBus.addListener(SpellGameTests::registerTests);
    }

    private static DeferredHolder<Consumer<GameTestHelper>, Consumer<GameTestHelper>> test(String name, Consumer<GameTestHelper> body) {
        return TEST_FUNCTIONS.register(name, () -> body);
    }

    private static void registerTests(RegisterGameTestsEvent event) {
        Holder<TestEnvironmentDefinition<?>> environment = event.registerEnvironment(SpellMod.id("default"));
        for (DeferredHolder<Consumer<GameTestHelper>, ? extends Consumer<GameTestHelper>> function : TEST_FUNCTIONS.getEntries()) {
            event.registerTest(function.getId(), new FunctionGameTestInstance(ResourceKey.create(Registries.TEST_FUNCTION, function.getId()),
                    new TestData<>(environment, Identifier.withDefaultNamespace("empty"), 100, 0, true)));
        }
    }

    private static void fireballCostsMana(GameTestHelper helper) {
        ServerPlayer player = wandPlayer(helper, Spell.FIREBALL);
        int fireballsBefore = fireballs(helper, player);
        helper.assertTrue(useMainHand(player).consumesAction(), "cast should succeed");
        helper.assertValueEqual(Mana.get(player), Mana.MAX - Spell.FIREBALL.manaCost(), "mana after fireball");
        helper.assertValueEqual(fireballs(helper, player), fireballsBefore + 1, "fireballs spawned");
        helper.assertTrue(player.getCooldowns().isOnCooldown(player.getMainHandItem()), "wand should be on cooldown");
        finish(helper, player);
    }

    private static void noManaNoCast(GameTestHelper helper) {
        ServerPlayer player = wandPlayer(helper, Spell.FIREBALL);
        Mana.set(player, Spell.FIREBALL.manaCost() - 1);
        int fireballsBefore = fireballs(helper, player);
        helper.assertFalse(useMainHand(player).consumesAction(), "cast should fail without mana");
        helper.assertValueEqual(Mana.get(player), Spell.FIREBALL.manaCost() - 1, "mana unchanged");
        helper.assertValueEqual(fireballs(helper, player), fireballsBefore, "no fireball spawned");
        finish(helper, player);
    }

    private static void healRestoresHealth(GameTestHelper helper) {
        ServerPlayer player = wandPlayer(helper, Spell.HEAL);
        // At full health the spell fizzles and costs nothing.
        helper.assertFalse(useMainHand(player).consumesAction(), "heal at full health should fail");
        helper.assertValueEqual(Mana.get(player), Mana.MAX, "mana unchanged at full health");
        player.setHealth(4.0F);
        helper.assertTrue(useMainHand(player).consumesAction(), "heal should succeed");
        helper.assertValueEqual(player.getHealth(), 12.0F, "health after heal");
        helper.assertValueEqual(Mana.get(player), Mana.MAX - Spell.HEAL.manaCost(), "mana after heal");
        finish(helper, player);
    }

    private static void sneakCyclesSpell(GameTestHelper helper) {
        ServerPlayer player = wandPlayer(helper, Spell.FIREBALL);
        player.setShiftKeyDown(true);
        for (Spell expected : new Spell[] {Spell.HEAL, Spell.BLINK, Spell.LIGHTNING, Spell.FIREBALL}) {
            useMainHand(player);
            helper.assertValueEqual(WandItem.getSpell(player.getMainHandItem()), expected, "selected spell");
        }
        helper.assertValueEqual(Mana.get(player), Mana.MAX, "switching spells is free");
        finish(helper, player);
    }

    private static void manaCrystalRestoresMana(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.MANA_CRYSTAL.get(), 2));
        // Full mana: crystal is not consumed.
        useMainHand(player);
        helper.assertValueEqual(player.getMainHandItem().getCount(), 2, "crystals at full mana");
        Mana.set(player, 10);
        useMainHand(player);
        helper.assertValueEqual(Mana.get(player), 10 + ManaCrystalItem.RESTORE_AMOUNT, "mana after crystal");
        helper.assertValueEqual(player.getMainHandItem().getCount(), 1, "crystals left");
        Mana.set(player, 90);
        useMainHand(player);
        helper.assertValueEqual(Mana.get(player), Mana.MAX, "mana is capped");
        finish(helper, player);
    }

    private static void manaRegenerates(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        Mana.set(player, 0);
        // Mock players are not ticked by the server (no real connection), so tick by hand
        // (tickCount is normally advanced by the level, doTick by the connection).
        for (int i = 0; i < 40; i++) {
            player.tickCount++;
            player.doTick();
        }
        helper.assertValueEqual(Mana.get(player), 8, "mana after 40 ticks");
        finish(helper, player);
    }

    private static void blinkTeleports(GameTestHelper helper) {
        ServerPlayer player = wandPlayer(helper, Spell.BLINK);
        // Float in the air and look straight down at a block we place below.
        BlockPos floor = helper.absolutePos(new BlockPos(0, 3, 0));
        helper.getLevel().setBlockAndUpdate(floor, Blocks.STONE.defaultBlockState());
        player.teleportTo(floor.getX() + 0.5, floor.getY() + 7.0, floor.getZ() + 0.5);
        lookDown(player, 90.0F);
        helper.assertTrue(useMainHand(player).consumesAction(), "blink should succeed");
        helper.assertValueEqual(player.getY(), floor.getY() + 1.0, "player lands on top of the targeted block");
        helper.assertValueEqual(Mana.get(player), Mana.MAX - Spell.BLINK.manaCost(), "mana after blink");
        helper.getLevel().setBlockAndUpdate(floor, Blocks.AIR.defaultBlockState());
        finish(helper, player);
    }

    private static void lightningStrikes(GameTestHelper helper) {
        ServerPlayer player = wandPlayer(helper, Spell.LIGHTNING);
        // Looking at the sky: nothing to hit, so the spell fizzles for free.
        lookDown(player, -90.0F);
        helper.assertFalse(useMainHand(player).consumesAction(), "lightning needs a target");
        helper.assertValueEqual(Mana.get(player), Mana.MAX, "mana unchanged without target");
        BlockPos floor = helper.absolutePos(new BlockPos(0, 3, 0));
        helper.getLevel().setBlockAndUpdate(floor, Blocks.STONE.defaultBlockState());
        player.teleportTo(floor.getX() + 0.5, floor.getY() + 5.0, floor.getZ() + 0.5);
        lookDown(player, 90.0F);
        helper.assertTrue(useMainHand(player).consumesAction(), "lightning should succeed");
        int bolts = helper.getLevel().getEntitiesOfClass(LightningBolt.class, new AABB(floor).inflate(2.0)).size();
        helper.assertValueEqual(bolts, 1, "lightning bolts at target");
        helper.assertValueEqual(Mana.get(player), Mana.MAX - Spell.LIGHTNING.manaCost(), "mana after lightning");
        helper.getLevel().setBlockAndUpdate(floor, Blocks.AIR.defaultBlockState());
        finish(helper, player);
    }

    private static void lookDown(ServerPlayer player, float pitch) {
        player.setXRot(pitch);
        // Same as what the next tick would do; some ray casts read the previous tick's rotation.
        player.xRotO = pitch;
    }

    private static InteractionResult useMainHand(ServerPlayer player) {
        ItemStack stack = player.getMainHandItem();
        return stack.use(player.level(), player, InteractionHand.MAIN_HAND);
    }

    private static int fireballs(GameTestHelper helper, ServerPlayer player) {
        return helper.getLevel().getEntitiesOfClass(SmallFireball.class, player.getBoundingBox().inflate(4.0)).size();
    }

    private static ServerPlayer wandPlayer(GameTestHelper helper, Spell spell) {
        ServerPlayer player = mockPlayer(helper);
        ItemStack wand = new ItemStack(ModItems.WAND.get());
        wand.set(ModDataComponents.SELECTED_SPELL, spell);
        player.setItemInHand(InteractionHand.MAIN_HAND, wand);
        return player;
    }

    /** A survival-mode player that is really logged in, so packets and attachments work. */
    private static ServerPlayer mockPlayer(GameTestHelper helper) {
        CommonListenerCookie cookie = CommonListenerCookie.createInitial(new GameProfile(UUID.randomUUID(), "test-mock-player"), false);
        ServerPlayer player = new ServerPlayer(helper.getLevel().getServer(), helper.getLevel(), cookie.gameProfile(), cookie.clientInformation());
        Connection connection = new Connection(PacketFlow.SERVERBOUND);
        new EmbeddedChannel(connection);
        helper.getLevel().getServer().getPlayerList().placeNewPlayer(connection, player, cookie);
        player.setGameMode(GameType.SURVIVAL);
        Vec3 pos = helper.absoluteVec(new Vec3(0.5, 1.0, 0.5));
        player.teleportTo(pos.x, pos.y, pos.z);
        Mana.set(player, Mana.MAX);
        return player;
    }

    private static void finish(GameTestHelper helper, ServerPlayer player) {
        helper.getLevel().getServer().getPlayerList().remove(player);
        helper.succeed();
    }
}
