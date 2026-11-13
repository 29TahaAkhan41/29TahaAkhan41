package dev.teknikmod;

import dev.teknikmod.block.BatteryBlock;
import dev.teknikmod.block.CableBlock;
import dev.teknikmod.block.CoalGeneratorBlock;
import dev.teknikmod.block.ProcessingBlock;
import dev.teknikmod.block.SolarPanelBlock;
import dev.teknikmod.blockentity.BatteryBlockEntity;
import dev.teknikmod.blockentity.CableBlockEntity;
import dev.teknikmod.blockentity.CoalGeneratorBlockEntity;
import dev.teknikmod.blockentity.CrusherBlockEntity;
import dev.teknikmod.blockentity.ElectricFurnaceBlockEntity;
import dev.teknikmod.blockentity.SolarPanelBlockEntity;
import dev.teknikmod.menu.CoalGeneratorMenu;
import dev.teknikmod.menu.ProcessingMenu;
import dev.teknikmod.recipe.CrushingRecipe;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.ItemLike;
import net.neoforged.neoforge.registries.DeferredItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;

public final class ModRegistry {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(TeknikMod.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(TeknikMod.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, TeknikMod.MODID);
    public static final DeferredRegister<MenuType<?>> MENUS =
            DeferredRegister.create(Registries.MENU, TeknikMod.MODID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, TeknikMod.MODID);

    /** Yaratici sekmede gosterilecek sira. */
    private static final List<ItemLike> TAB_ORDER = new ArrayList<>();

    private static BlockBehaviour.Properties machineProps() {
        return BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(3.5F, 6.0F)
                .sound(SoundType.METAL).requiresCorrectToolForDrops();
    }

    private static <B extends Block> DeferredBlock<B> block(String name, java.util.function.Supplier<B> factory) {
        DeferredBlock<B> block = BLOCKS.register(name, factory);
        ITEMS.registerSimpleBlockItem(block);
        TAB_ORDER.add(block);
        return block;
    }

    /** Bir cihazin her kademesi icin blok kaydeder: coal_generator, advanced_coal_generator, elite_coal_generator. */
    private static <B extends Block> Map<Tier, DeferredBlock<B>> tiered(
            String name, BiFunction<BlockBehaviour.Properties, Tier, B> factory) {
        Map<Tier, DeferredBlock<B>> map = new EnumMap<>(Tier.class);
        for (Tier tier : Tier.values()) {
            map.put(tier, block(tier.prefix + name, () -> factory.apply(machineProps(), tier)));
        }
        return map;
    }

    private static DeferredBlock<CableBlock> cable(String name, MapColor color, int rate) {
        return block(name, () -> new CableBlock(BlockBehaviour.Properties.of().mapColor(color).strength(0.8F)
                .sound(SoundType.COPPER).noOcclusion(), rate));
    }

    private static Block[] all(Map<Tier, ? extends DeferredBlock<? extends Block>> map) {
        return map.values().stream().map(DeferredBlock::get).toArray(Block[]::new);
    }

    // --- Bloklar ---
    public static final Map<Tier, DeferredBlock<CoalGeneratorBlock>> COAL_GENERATORS = tiered("coal_generator",
            (props, tier) -> new CoalGeneratorBlock(props.lightLevel(s -> s.getValue(BlockStateProperties.LIT) ? 13 : 0), tier));
    public static final Map<Tier, DeferredBlock<SolarPanelBlock>> SOLAR_PANELS = tiered("solar_panel",
            (props, tier) -> new SolarPanelBlock(props.noOcclusion(), tier));
    public static final Map<Tier, DeferredBlock<BatteryBlock>> BATTERIES = tiered("battery", BatteryBlock::new);

    public static final Map<Tier, DeferredBlock<ProcessingBlock>> ELECTRIC_FURNACES = tiered("electric_furnace",
            (props, tier) -> new ProcessingBlock(props.lightLevel(s -> s.getValue(BlockStateProperties.LIT) ? 10 : 0), tier, ElectricFurnaceBlockEntity::new));
    public static final Map<Tier, DeferredBlock<ProcessingBlock>> CRUSHERS = tiered("crusher",
            (props, tier) -> new ProcessingBlock(props, tier, CrusherBlockEntity::new));

    public static final DeferredBlock<CableBlock> COPPER_CABLE = cable("copper_cable", MapColor.COLOR_ORANGE, Tier.COPPER_CABLE_RATE);
    public static final DeferredBlock<CableBlock> GOLD_CABLE = cable("gold_cable", MapColor.GOLD, Tier.GOLD_CABLE_RATE);
    public static final DeferredBlock<CableBlock> DIAMOND_CABLE = cable("diamond_cable", MapColor.DIAMOND, Tier.DIAMOND_CABLE_RATE);

    // --- Esyalar ---
    public static final DeferredItem<Item> IRON_DUST = item("iron_dust");
    public static final DeferredItem<Item> GOLD_DUST = item("gold_dust");
    public static final DeferredItem<Item> COPPER_DUST = item("copper_dust");

    private static DeferredItem<Item> item(String name) {
        DeferredItem<Item> item = ITEMS.registerSimpleItem(name);
        TAB_ORDER.add(item);
        return item;
    }

    // --- Tarif turleri ---
    public static final DeferredRegister<RecipeType<?>> RECIPE_TYPES = DeferredRegister.create(Registries.RECIPE_TYPE, TeknikMod.MODID);
    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS = DeferredRegister.create(Registries.RECIPE_SERIALIZER, TeknikMod.MODID);
    public static final DeferredHolder<RecipeType<?>, RecipeType<CrushingRecipe>> CRUSHING = RECIPE_TYPES.register("crushing",
            () -> RecipeType.simple(ResourceLocation.fromNamespaceAndPath(TeknikMod.MODID, "crushing")));
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<CrushingRecipe>> CRUSHING_SERIALIZER =
            RECIPE_SERIALIZERS.register("crushing", CrushingRecipe.Serializer::new);

    // --- Block entity'ler (her cihaz turunun tum kademeleri ayni tipi kullanir) ---
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CoalGeneratorBlockEntity>> COAL_GENERATOR_BE =
            BLOCK_ENTITIES.register("coal_generator", () -> BlockEntityType.Builder
                    .of(CoalGeneratorBlockEntity::new, all(COAL_GENERATORS)).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<SolarPanelBlockEntity>> SOLAR_PANEL_BE =
            BLOCK_ENTITIES.register("solar_panel", () -> BlockEntityType.Builder
                    .of(SolarPanelBlockEntity::new, all(SOLAR_PANELS)).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<BatteryBlockEntity>> BATTERY_BE =
            BLOCK_ENTITIES.register("battery", () -> BlockEntityType.Builder
                    .of(BatteryBlockEntity::new, all(BATTERIES)).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ElectricFurnaceBlockEntity>> ELECTRIC_FURNACE_BE =
            BLOCK_ENTITIES.register("electric_furnace", () -> BlockEntityType.Builder
                    .of(ElectricFurnaceBlockEntity::new, all(ELECTRIC_FURNACES)).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CrusherBlockEntity>> CRUSHER_BE =
            BLOCK_ENTITIES.register("crusher", () -> BlockEntityType.Builder
                    .of(CrusherBlockEntity::new, all(CRUSHERS)).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CableBlockEntity>> CABLE_BE =
            BLOCK_ENTITIES.register("cable", () -> BlockEntityType.Builder
                    .of(CableBlockEntity::new, COPPER_CABLE.get(), GOLD_CABLE.get(), DIAMOND_CABLE.get()).build(null));

    // --- Menuler ---
    public static final DeferredHolder<MenuType<?>, MenuType<CoalGeneratorMenu>> COAL_GENERATOR_MENU =
            MENUS.register("coal_generator", () -> IMenuTypeExtension.create(CoalGeneratorMenu::new));

    public static final DeferredHolder<MenuType<?>, MenuType<ProcessingMenu>> ELECTRIC_FURNACE_MENU =
            MENUS.register("electric_furnace", () -> IMenuTypeExtension.create(
                    (id, inv, buf) -> new ProcessingMenu(ModRegistry.ELECTRIC_FURNACE_MENU.get(), id, inv)));
    public static final DeferredHolder<MenuType<?>, MenuType<ProcessingMenu>> CRUSHER_MENU =
            MENUS.register("crusher", () -> IMenuTypeExtension.create(
                    (id, inv, buf) -> new ProcessingMenu(ModRegistry.CRUSHER_MENU.get(), id, inv)));

    // --- Yaratici sekme ---
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TAB = TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.teknikmod"))
                    .icon(() -> COAL_GENERATORS.get(Tier.BASIC).asItem().getDefaultInstance())
                    .displayItems((params, out) -> TAB_ORDER.forEach(out::accept))
                    .build());

    static void register(IEventBus bus) {
        BLOCKS.register(bus);
        ITEMS.register(bus);
        BLOCK_ENTITIES.register(bus);
        MENUS.register(bus);
        TABS.register(bus);
        RECIPE_TYPES.register(bus);
        RECIPE_SERIALIZERS.register(bus);
    }

    private ModRegistry() {}
}
