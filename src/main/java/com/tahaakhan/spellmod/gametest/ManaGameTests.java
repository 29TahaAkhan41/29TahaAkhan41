package com.tahaakhan.spellmod.gametest;

import com.mojang.authlib.GameProfile;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.block.ManaTableBlockEntity;
import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.mana.ManaEvents;
import com.tahaakhan.spellmod.mana.ManaStage;
import com.tahaakhan.spellmod.menu.ManaTableMenu;
import com.tahaakhan.spellmod.registry.ModBlocks;
import com.tahaakhan.spellmod.registry.ModItems;
import io.netty.channel.embedded.EmbeddedChannel;
import java.util.List;
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
import net.minecraft.tags.BlockTags;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Block;
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
        TEST_FUNCTIONS.register("capsule_and_table_recipes", () -> ManaGameTests::capsuleAndTableRecipes);
        TEST_FUNCTIONS.register("mana_table_block", () -> ManaGameTests::manaTableBlock);
        TEST_FUNCTIONS.register("refining_rules", () -> ManaGameTests::refiningRules);
        TEST_FUNCTIONS.register("table_refines_raw_mana", () -> ManaGameTests::tableRefinesRawMana);
        TEST_FUNCTIONS.register("table_can_destroy_mana", () -> ManaGameTests::tableCanDestroyMana);
        TEST_FUNCTIONS.register("table_needs_mana_and_fuel", () -> ManaGameTests::tableNeedsManaAndFuel);
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
        Mana.set(player, new ManaData(0, 50, 0, 0));
        Mana.AbsorbResult roomy = Mana.absorb(player);
        helper.assertValueEqual(roomy.overflow(), 0, "overflow with free capacity");
        helper.assertValueEqual(roomy.damage(), 0.0F, "damage with free capacity");
        helper.assertValueEqual(Mana.get(player).mana(), Mana.MANA_PER_REFINED, "mana stored");

        // The same overflow hurts less the more capacity the body has built up.
        helper.assertTrue(Mana.overflowDamage(8, 100) < Mana.overflowDamage(8, 2), "overflow should hurt less at high capacity");

        // Capacity never grows past the maximum.
        Mana.set(player, new ManaData(0, Mana.MAX_CAPACITY, 0, 0));
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

    private static void capsuleAndTableRecipes(GameTestHelper helper) {
        ItemStack glass = new ItemStack(Items.GLASS);
        ItemStack eye = new ItemStack(Items.ENDER_EYE);
        ItemStack obsidian = new ItemStack(Items.OBSIDIAN);
        ItemStack rawMana = new ItemStack(ModItems.RAW_MANA.get());
        ItemStack capsule = new ItemStack(ModItems.MANA_CAPSULE.get());
        ItemStack none = ItemStack.EMPTY;

        helper.assertTrue(craft(helper,
                glass, eye, glass,
                eye, rawMana, eye,
                glass, eye, glass).is(ModItems.MANA_CAPSULE.get()), "capsule recipe should give a mana capsule");
        helper.assertTrue(craft(helper,
                eye, glass, eye,
                none, capsule, none,
                obsidian, obsidian, obsidian).is(ModItems.MANA_TABLE.get()), "table recipe should give a mana table");
        // Wrong layouts give nothing from this mod.
        helper.assertFalse(craft(helper,
                eye, glass, eye,
                glass, rawMana, glass,
                eye, glass, eye).is(ModItems.MANA_CAPSULE.get()), "glass and eyes swapped should not give a capsule");
        helper.assertFalse(craft(helper,
                eye, glass, eye,
                none, rawMana, none,
                obsidian, obsidian, obsidian).is(ModItems.MANA_TABLE.get()), "raw mana instead of a capsule should not give a table");
        helper.succeed();
    }

    private static ItemStack craft(GameTestHelper helper, ItemStack... grid) {
        CraftingInput input = CraftingInput.of(3, 3, List.of(grid));
        return helper.getLevel().recipeAccess().getRecipeFor(RecipeType.CRAFTING, input, helper.getLevel())
                .map(recipe -> recipe.value().assemble(input))
                .orElse(ItemStack.EMPTY);
    }

    private static void manaTableBlock(GameTestHelper helper) {
        BlockPos pos = new BlockPos(0, 2, 0);
        helper.setBlock(pos, ModBlocks.MANA_TABLE.get());
        BlockState state = helper.getBlockState(pos);
        int light = state.getLightEmission(helper.getLevel(), helper.absolutePos(pos));
        helper.assertTrue(light >= 10, "the table should glow, light was " + light);
        helper.assertTrue(state.requiresCorrectToolForDrops(), "the table needs a pickaxe");
        helper.assertTrue(state.is(BlockTags.MINEABLE_WITH_PICKAXE), "the table should be mineable with a pickaxe");

        // Breaking it with a pickaxe gives the table back.
        List<ItemStack> drops = Block.getDrops(state, helper.getLevel(), helper.absolutePos(pos), null, null, new ItemStack(Items.DIAMOND_PICKAXE));
        helper.assertValueEqual(drops.size(), 1, "number of drops");
        helper.assertTrue(drops.getFirst().is(ModItems.MANA_TABLE.get()), "the table should drop itself");
        helper.setBlock(pos, Blocks.AIR);
        helper.succeed();
    }

    private static void refiningRules(GameTestHelper helper) {
        helper.assertValueEqual(Mana.refineTicks(0), 10 * 60 * 20, "first refining takes 10 minutes");
        helper.assertTrue(Mana.refineTicks(1) < Mana.refineTicks(0), "refining gets faster with practice");
        helper.assertTrue(Mana.refineTicks(30) < Mana.refineTicks(10), "and keeps getting faster");
        helper.assertValueEqual(Mana.refineTicks(1000), 20, "fastest refining takes 1 second");

        ManaData beginner = ManaData.EMPTY;
        ManaData practiced = new ManaData(0, 40, 60, 0);
        ManaData master = new ManaData(0, Mana.MAX_CAPACITY, 500, 0);
        helper.assertValueEqual(Mana.affinity(beginner), 0.0F, "affinity of a beginner");
        helper.assertValueEqual(Mana.affinity(master), 1.0F, "affinity of a master");
        helper.assertValueEqual(Mana.lossChance(beginner), Mana.MAX_LOSS_CHANCE, "loss chance of a beginner");
        helper.assertValueEqual(Mana.lossChance(master), Mana.MIN_LOSS_CHANCE, "loss chance of a master");
        helper.assertTrue(Mana.lossChance(practiced) < Mana.lossChance(beginner) && Mana.lossChance(practiced) > Mana.lossChance(master),
                "loss chance falls as affinity grows");
        helper.succeed();
    }

    private static void tableRefinesRawMana(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        // Practiced enough for the fastest time (1 second).
        Mana.set(player, new ManaData(0, 0, 0, 1000));
        ManaTableBlockEntity table = placeTable(helper, 2, 2);

        // Pressing the button in the menu takes one raw mana and one eye of ender.
        AbstractContainerMenu menu = table.createMenu(1, player.getInventory(), player);
        helper.assertTrue(menu.clickMenuButton(player, ManaTableMenu.BUTTON_REFINE), "the refine button should start the table");
        helper.assertTrue(table.isRunning(), "table should be running");
        helper.assertValueEqual(table.totalTicks(), 20, "refining time for this player");
        helper.assertValueEqual(table.lossPermille(), 750, "loss chance for this player, in 1/1000");
        helper.assertValueEqual(table.getItem(ManaTableBlockEntity.SLOT_INPUT).getCount(), 1, "raw mana left");
        helper.assertValueEqual(table.getItem(ManaTableBlockEntity.SLOT_FUEL).getCount(), 1, "eyes of ender left");
        helper.assertValueEqual(Mana.get(player).refined(), 1001, "player's refined count");
        helper.assertValueEqual(Mana.get(player).experience(), Mana.EXPERIENCE_PER_REFINE, "player's experience");
        helper.assertFalse(menu.clickMenuButton(player, ManaTableMenu.BUTTON_REFINE), "pressing again while running does nothing");

        // A roll above the loss chance succeeds, and the table carries on with the next piece by itself.
        table.complete(helper.getLevel(), 999);
        helper.assertValueEqual(table.getItem(ManaTableBlockEntity.SLOT_OUTPUT).getCount(), 1, "refined mana after first piece");
        helper.assertTrue(table.getItem(ManaTableBlockEntity.SLOT_OUTPUT).is(ModItems.REFINED_MANA.get()), "output should be refined mana");
        helper.assertTrue(table.isRunning(), "table should continue with the second piece");
        helper.assertTrue(table.getItem(ManaTableBlockEntity.SLOT_INPUT).isEmpty(), "all raw mana taken");

        // The second piece finishes on its own after the 1 second timer, then the table stops.
        helper.runAfterDelay(30, () -> {
            helper.assertFalse(table.isRunning(), "table should stop when the raw mana runs out");
            int refined = table.getItem(ManaTableBlockEntity.SLOT_OUTPUT).getCount();
            helper.assertTrue(refined == 1 || refined == 2, "second piece is refined or destroyed, output was " + refined);
            table.clearContent();
            helper.setBlock(new BlockPos(0, 2, 0), Blocks.AIR);
            finish(helper, player);
        });
    }

    private static void tableCanDestroyMana(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        ManaTableBlockEntity table = placeTable(helper, 1, 1);
        helper.assertTrue(table.start(player), "table should start");
        helper.assertValueEqual(table.totalTicks(), Mana.MAX_REFINE_TICKS, "a beginner waits the full 10 minutes");
        // A roll below the loss chance destroys the mana: fuel and raw mana are gone, nothing comes out.
        table.complete(helper.getLevel(), 0);
        helper.assertTrue(table.getItem(ManaTableBlockEntity.SLOT_OUTPUT).isEmpty(), "nothing comes out when the mana is destroyed");
        helper.assertTrue(table.getItem(ManaTableBlockEntity.SLOT_INPUT).isEmpty(), "raw mana is used up");
        helper.assertTrue(table.getItem(ManaTableBlockEntity.SLOT_FUEL).isEmpty(), "eye of ender is used up");
        helper.assertFalse(table.isRunning(), "table should stop");
        helper.setBlock(new BlockPos(0, 2, 0), Blocks.AIR);
        finish(helper, player);
    }

    private static void tableNeedsManaAndFuel(GameTestHelper helper) {
        ServerPlayer player = mockPlayer(helper);
        ManaTableBlockEntity table = placeTable(helper, 1, 0);
        helper.assertFalse(table.start(player), "no eye of ender: should not start");
        table.clearContent();
        table.setItem(ManaTableBlockEntity.SLOT_FUEL, new ItemStack(Items.ENDER_EYE));
        helper.assertFalse(table.start(player), "no raw mana: should not start");
        helper.assertValueEqual(Mana.get(player).refined(), 0, "nothing was refined");

        // Only the right items fit in the slots.
        helper.assertTrue(table.canPlaceItem(ManaTableBlockEntity.SLOT_INPUT, new ItemStack(ModItems.RAW_MANA.get())), "raw mana fits the input");
        helper.assertFalse(table.canPlaceItem(ManaTableBlockEntity.SLOT_INPUT, new ItemStack(Items.ENDER_EYE)), "eyes do not fit the input");
        helper.assertTrue(table.canPlaceItem(ManaTableBlockEntity.SLOT_FUEL, new ItemStack(Items.ENDER_EYE)), "eyes fit the fuel slot");
        helper.assertFalse(table.canPlaceItem(ManaTableBlockEntity.SLOT_FUEL, new ItemStack(Items.COAL)), "coal is not fuel");
        helper.assertFalse(table.canPlaceItem(ManaTableBlockEntity.SLOT_OUTPUT, new ItemStack(ModItems.REFINED_MANA.get())), "nothing can be put in the output");
        table.clearContent();
        helper.setBlock(new BlockPos(0, 2, 0), Blocks.AIR);
        finish(helper, player);
    }

    private static ManaTableBlockEntity placeTable(GameTestHelper helper, int rawMana, int eyes) {
        BlockPos pos = new BlockPos(0, 2, 0);
        helper.setBlock(pos, ModBlocks.MANA_TABLE.get());
        ManaTableBlockEntity table = helper.getBlockEntity(pos, ManaTableBlockEntity.class);
        table.setItem(ManaTableBlockEntity.SLOT_INPUT, new ItemStack(ModItems.RAW_MANA.get(), rawMana));
        table.setItem(ManaTableBlockEntity.SLOT_FUEL, new ItemStack(Items.ENDER_EYE, eyes));
        return table;
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
