package com.tahaakhan.spellmod.gametest;

import com.mojang.authlib.GameProfile;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.mana.ManaEvents;
import com.tahaakhan.spellmod.mana.ManaStage;
import com.tahaakhan.spellmod.registry.ModItems;
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
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.RegisterGameTestsEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Automated in-game tests. Run them with {@code ./gradlew runGameTestServer}. */
public final class ManaGameTests {
    private static final DeferredRegister<Consumer<GameTestHelper>> TEST_FUNCTIONS =
            DeferredRegister.create(Registries.TEST_FUNCTION, SpellMod.MODID);

    static {
        TEST_FUNCTIONS.register("find_chance_grows_with_experience", () -> ManaGameTests::findChanceGrowsWithExperience);
        TEST_FUNCTIONS.register("raw_mana_drops_from_blocks", () -> ManaGameTests::rawManaDropsFromBlocks);
        TEST_FUNCTIONS.register("no_raw_mana_in_creative_or_instant_blocks", () -> ManaGameTests::noRawManaInCreativeOrInstantBlocks);
        TEST_FUNCTIONS.register("first_absorption_awakens_and_hurts", () -> ManaGameTests::firstAbsorptionAwakensAndHurts);
        TEST_FUNCTIONS.register("body_gets_used_to_mana", () -> ManaGameTests::bodyGetsUsedToMana);
        TEST_FUNCTIONS.register("stages_follow_capacity", () -> ManaGameTests::stagesFollowCapacity);
    }

    private ManaGameTests() {}

    public static void register(IEventBus modEventBus) {
        TEST_FUNCTIONS.register(modEventBus);
        modEventBus.addListener(ManaGameTests::registerTests);
    }

    private static void registerTests(RegisterGameTestsEvent event) {
        Holder<TestEnvironmentDefinition<?>> environment = event.registerEnvironment(SpellMod.id("default"));
        for (DeferredHolder<Consumer<GameTestHelper>, ? extends Consumer<GameTestHelper>> function : TEST_FUNCTIONS.getEntries()) {
            event.registerTest(function.getId(), new FunctionGameTestInstance(ResourceKey.create(Registries.TEST_FUNCTION, function.getId()),
                    new TestData<>(environment, Identifier.withDefaultNamespace("empty"), 100, 0, true)));
        }
    }

    private static void findChanceGrowsWithExperience(GameTestHelper helper) {
        helper.assertValueEqual(Mana.findChance(0), Mana.BASE_FIND_CHANCE, "chance with no experience");
        helper.assertTrue(Mana.findChance(10) > Mana.findChance(0), "experience should raise the chance");
        helper.assertTrue(Mana.findChance(50) > Mana.findChance(10), "more experience should raise it further");
        helper.assertValueEqual(Mana.findChance(1_000_000), Mana.MAX_FIND_CHANCE, "chance is capped");
        helper.succeed();
    }

    private static void rawManaDropsFromBlocks(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        BlockPos pos = helper.absolutePos(new BlockPos(0, 2, 0));
        BlockState stone = Blocks.STONE.defaultBlockState();
        float chance = Mana.findChance(0);

        // A roll just above the chance finds nothing...
        helper.assertFalse(ManaEvents.tryDropRawMana(helper.getLevel(), pos, stone, player, chance), "roll at the chance should miss");
        helper.assertValueEqual(rawManaNear(helper, pos), 0, "raw mana after a miss");
        helper.assertValueEqual(Mana.get(player).experience(), 0, "experience after a miss");

        // ...a roll below it drops raw mana and makes the player more experienced.
        helper.assertTrue(ManaEvents.tryDropRawMana(helper.getLevel(), pos, stone, player, chance / 2), "roll below the chance should hit");
        helper.assertValueEqual(rawManaNear(helper, pos), 1, "raw mana after a hit");
        helper.assertValueEqual(Mana.get(player).experience(), Mana.EXPERIENCE_PER_FIND, "experience after a hit");
        helper.assertTrue(Mana.findChance(Mana.get(player).experience()) > chance, "next find should be easier");
        finish(helper, player);
    }

    private static void noRawManaInCreativeOrInstantBlocks(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        BlockPos pos = helper.absolutePos(new BlockPos(0, 2, 0));
        helper.assertFalse(ManaEvents.tryDropRawMana(helper.getLevel(), pos, Blocks.SHORT_GRASS.defaultBlockState(), player, 0.0F),
                "instantly broken blocks never drop raw mana");
        player.setGameMode(GameType.CREATIVE);
        helper.assertFalse(ManaEvents.tryDropRawMana(helper.getLevel(), pos, Blocks.STONE.defaultBlockState(), player, 0.0F),
                "creative players never find raw mana");
        helper.assertValueEqual(rawManaNear(helper, pos), 0, "raw mana dropped");
        finish(helper, player);
    }

    private static void firstAbsorptionAwakensAndHurts(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        helper.assertValueEqual(Mana.get(player), ManaData.EMPTY, "new players start with nothing");
        helper.assertValueEqual(Mana.get(player).stage(), ManaStage.UNAWAKENED, "starting stage");

        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModItems.REFINED_MANA.get(), 3));
        ItemStack stack = player.getMainHandItem();
        helper.assertTrue(stack.use(helper.getLevel(), player, InteractionHand.MAIN_HAND).consumesAction(), "absorbing should succeed");

        ManaData data = Mana.get(player);
        helper.assertValueEqual(player.getMainHandItem().getCount(), 2, "refined mana left");
        helper.assertValueEqual(data.capacity(), Mana.CAPACITY_PER_ABSORB, "capacity after first absorption");
        helper.assertValueEqual(data.mana(), Mana.CAPACITY_PER_ABSORB, "mana is limited by capacity");
        helper.assertValueEqual(data.experience(), Mana.EXPERIENCE_PER_ABSORB, "experience after absorbing");
        helper.assertValueEqual(data.stage(), ManaStage.AWAKENED, "stage after first absorption");
        finish(helper, player);
    }

    private static void bodyGetsUsedToMana(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        // An unprepared body cannot hold the mana: most of it overflows and it hurts.
        Mana.AbsorbResult first = Mana.absorb(player);
        helper.assertValueEqual(first.overflow(), Mana.MANA_PER_REFINED - Mana.CAPACITY_PER_ABSORB, "overflow of first absorption");
        helper.assertTrue(first.damage() >= 1.0F, "first absorption should hurt, damage was " + first.damage());
        helper.assertTrue(first.stageChanged(), "first absorption awakens the player");

        // With room to spare there is no overflow and no pain.
        Mana.set(player, new ManaData(0, 50, 0));
        Mana.AbsorbResult roomy = Mana.absorb(player);
        helper.assertValueEqual(roomy.overflow(), 0, "overflow with free capacity");
        helper.assertValueEqual(roomy.damage(), 0.0F, "damage with free capacity");
        helper.assertValueEqual(Mana.get(player).mana(), Mana.MANA_PER_REFINED, "mana stored");

        // The same overflow hurts less the more capacity the body has built up.
        helper.assertTrue(Mana.overflowDamage(8, 100) < Mana.overflowDamage(8, 2), "overflow should hurt less at high capacity");

        // Capacity never grows past the maximum.
        Mana.set(player, new ManaData(0, Mana.MAX_CAPACITY, 0));
        Mana.absorb(player);
        helper.assertValueEqual(Mana.get(player).capacity(), Mana.MAX_CAPACITY, "capacity is capped");
        finish(helper, player);
    }

    private static void stagesFollowCapacity(GameTestHelper helper) {
        helper.assertValueEqual(ManaStage.forCapacity(0), ManaStage.UNAWAKENED, "stage at 0");
        helper.assertValueEqual(ManaStage.forCapacity(1), ManaStage.AWAKENED, "stage at 1");
        helper.assertValueEqual(ManaStage.forCapacity(19), ManaStage.AWAKENED, "stage at 19");
        helper.assertValueEqual(ManaStage.forCapacity(20), ManaStage.APPRENTICE, "stage at 20");
        helper.assertValueEqual(ManaStage.forCapacity(50), ManaStage.ADEPT, "stage at 50");
        helper.assertValueEqual(ManaStage.forCapacity(100), ManaStage.MAGE, "stage at 100");
        helper.assertValueEqual(ManaStage.forCapacity(200), ManaStage.ARCHMAGE, "stage at 200");
        helper.succeed();
    }

    private static int rawManaNear(GameTestHelper helper, BlockPos pos) {
        return helper.getLevel().getEntitiesOfClass(ItemEntity.class, new AABB(pos).inflate(2.0),
                item -> item.getItem().is(ModItems.RAW_MANA.get())).size();
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
        return player;
    }

    private static void finish(GameTestHelper helper, ServerPlayer player) {
        helper.getLevel().getEntitiesOfClass(ItemEntity.class, new AABB(player.blockPosition()).inflate(4.0)).forEach(ItemEntity::discard);
        helper.getLevel().getServer().getPlayerList().remove(player);
        helper.succeed();
    }
}
