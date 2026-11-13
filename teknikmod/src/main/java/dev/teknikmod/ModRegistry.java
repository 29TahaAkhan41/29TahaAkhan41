package dev.teknikmod;

import dev.teknikmod.block.BatteryBlock;
import dev.teknikmod.block.CableBlock;
import dev.teknikmod.block.CoalGeneratorBlock;
import dev.teknikmod.block.SolarPanelBlock;
import dev.teknikmod.blockentity.BatteryBlockEntity;
import dev.teknikmod.blockentity.CableBlockEntity;
import dev.teknikmod.blockentity.CoalGeneratorBlockEntity;
import dev.teknikmod.blockentity.SolarPanelBlockEntity;
import dev.teknikmod.menu.CoalGeneratorMenu;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModRegistry {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(TeknikMod.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(TeknikMod.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, TeknikMod.MODID);
    public static final DeferredRegister<MenuType<?>> MENUS =
            DeferredRegister.create(Registries.MENU, TeknikMod.MODID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, TeknikMod.MODID);

    private static BlockBehaviour.Properties machineProps() {
        return BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(3.5F, 6.0F)
                .sound(SoundType.METAL).requiresCorrectToolForDrops();
    }

    private static BlockBehaviour.Properties cableProps(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).strength(0.8F).sound(SoundType.COPPER).noOcclusion();
    }

    // --- Bloklar ---
    public static final DeferredBlock<CoalGeneratorBlock> COAL_GENERATOR = BLOCKS.register("coal_generator",
            () -> new CoalGeneratorBlock(machineProps()
                    .lightLevel(s -> s.getValue(BlockStateProperties.LIT) ? 13 : 0)));
    public static final DeferredBlock<SolarPanelBlock> SOLAR_PANEL = BLOCKS.register("solar_panel",
            () -> new SolarPanelBlock(machineProps().noOcclusion()));
    public static final DeferredBlock<BatteryBlock> BATTERY = BLOCKS.register("battery",
            () -> new BatteryBlock(machineProps()));
    public static final DeferredBlock<CableBlock> COPPER_CABLE = BLOCKS.register("copper_cable",
            () -> new CableBlock(cableProps(MapColor.COLOR_ORANGE), Config.COPPER_CABLE_RATE));
    public static final DeferredBlock<CableBlock> GOLD_CABLE = BLOCKS.register("gold_cable",
            () -> new CableBlock(cableProps(MapColor.GOLD), Config.GOLD_CABLE_RATE));

    // --- Itemler ---
    public static final DeferredItem<BlockItem> COAL_GENERATOR_ITEM = ITEMS.registerSimpleBlockItem(COAL_GENERATOR);
    public static final DeferredItem<BlockItem> SOLAR_PANEL_ITEM = ITEMS.registerSimpleBlockItem(SOLAR_PANEL);
    public static final DeferredItem<BlockItem> BATTERY_ITEM = ITEMS.registerSimpleBlockItem(BATTERY);
    public static final DeferredItem<BlockItem> COPPER_CABLE_ITEM = ITEMS.registerSimpleBlockItem(COPPER_CABLE);
    public static final DeferredItem<BlockItem> GOLD_CABLE_ITEM = ITEMS.registerSimpleBlockItem(GOLD_CABLE);

    // --- Block entity'ler ---
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CoalGeneratorBlockEntity>> COAL_GENERATOR_BE =
            BLOCK_ENTITIES.register("coal_generator", () -> BlockEntityType.Builder
                    .of(CoalGeneratorBlockEntity::new, COAL_GENERATOR.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<SolarPanelBlockEntity>> SOLAR_PANEL_BE =
            BLOCK_ENTITIES.register("solar_panel", () -> BlockEntityType.Builder
                    .of(SolarPanelBlockEntity::new, SOLAR_PANEL.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<BatteryBlockEntity>> BATTERY_BE =
            BLOCK_ENTITIES.register("battery", () -> BlockEntityType.Builder
                    .of(BatteryBlockEntity::new, BATTERY.get()).build(null));
    /** Tum kablo kademeleri ayni block entity tipini kullanir. */
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CableBlockEntity>> COPPER_CABLE_BE =
            BLOCK_ENTITIES.register("cable", () -> BlockEntityType.Builder
                    .of(CableBlockEntity::new, COPPER_CABLE.get(), GOLD_CABLE.get()).build(null));

    // --- Menuler ---
    public static final DeferredHolder<MenuType<?>, MenuType<CoalGeneratorMenu>> COAL_GENERATOR_MENU =
            MENUS.register("coal_generator", () -> IMenuTypeExtension.create(CoalGeneratorMenu::new));

    // --- Yaratici sekme ---
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TAB = TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.teknikmod"))
                    .icon(() -> COAL_GENERATOR_ITEM.get().getDefaultInstance())
                    .displayItems((params, out) -> {
                        out.accept(COAL_GENERATOR_ITEM.get());
                        out.accept(SOLAR_PANEL_ITEM.get());
                        out.accept(BATTERY_ITEM.get());
                        out.accept(COPPER_CABLE_ITEM.get());
                        out.accept(GOLD_CABLE_ITEM.get());
                    }).build());

    static void register(IEventBus bus) {
        BLOCKS.register(bus);
        ITEMS.register(bus);
        BLOCK_ENTITIES.register(bus);
        MENUS.register(bus);
        TABS.register(bus);
    }

    private ModRegistry() {}
}
