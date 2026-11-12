package dev.lumina;

import dev.lumina.block.NodeBlock;
import dev.lumina.block.PedestalBlock;
import dev.lumina.blockentity.CellBlockEntity;
import dev.lumina.blockentity.CollectorBlockEntity;
import dev.lumina.blockentity.LensBlockEntity;
import dev.lumina.blockentity.PedestalBlockEntity;
import dev.lumina.blockentity.PrismBlockEntity;
import dev.lumina.item.LinkingWandItem;
import dev.lumina.recipe.InfusionRecipe;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

@Mod(Lumina.MODID)
public class Lumina {
    public static final String MODID = "lumina";

    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, MODID);
    public static final DeferredRegister<RecipeType<?>> RECIPE_TYPES =
            DeferredRegister.create(Registries.RECIPE_TYPE, MODID);
    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS =
            DeferredRegister.create(Registries.RECIPE_SERIALIZER, MODID);
    public static final DeferredRegister.DataComponents DATA_COMPONENTS =
            DeferredRegister.createDataComponents(Registries.DATA_COMPONENT_TYPE, MODID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    // ---- Shapes -----------------------------------------------------------
    private static final VoxelShape COLLECTOR_SHAPE = Shapes.or(
            Block.box(2, 0, 2, 14, 2, 14), Block.box(5, 2, 5, 11, 16, 11));
    private static final VoxelShape LENS_SHAPE = Shapes.or(
            Block.box(6, 0, 6, 10, 5, 10), Block.box(4, 5, 4, 12, 13, 12));
    private static final VoxelShape PRISM_SHAPE = Shapes.or(
            Block.box(6, 0, 6, 10, 4, 10), Block.box(3, 4, 3, 13, 7, 13),
            Block.box(5, 7, 5, 11, 11, 11), Block.box(7, 11, 7, 9, 15, 9));
    private static final VoxelShape PEDESTAL_SHAPE = Shapes.or(
            Block.box(2, 0, 2, 14, 3, 14), Block.box(5, 3, 5, 11, 11, 11),
            Block.box(3, 11, 3, 13, 14, 13));

    private static BlockBehaviour.Properties nodeProps(MapColor color, int light) {
        return BlockBehaviour.Properties.of()
                .mapColor(color)
                .strength(2.0F, 6.0F)
                .sound(SoundType.AMETHYST)
                .lightLevel(state -> light)
                .noOcclusion();
    }

    // ---- Blocks -----------------------------------------------------------
    public static final DeferredBlock<Block> LUMEN_ORE = BLOCKS.register("lumen_ore",
            () -> new DropExperienceBlock(UniformInt.of(1, 4), BlockBehaviour.Properties.of()
                    .mapColor(MapColor.STONE).requiresCorrectToolForDrops().strength(3.0F, 3.0F)
                    .lightLevel(state -> 3)));
    public static final DeferredBlock<Block> DEEPSLATE_LUMEN_ORE = BLOCKS.register("deepslate_lumen_ore",
            () -> new DropExperienceBlock(UniformInt.of(1, 4), BlockBehaviour.Properties.of()
                    .mapColor(MapColor.DEEPSLATE).requiresCorrectToolForDrops().strength(4.5F, 3.0F)
                    .sound(SoundType.DEEPSLATE).lightLevel(state -> 3)));

    public static final DeferredBlock<NodeBlock> STARLIGHT_COLLECTOR = BLOCKS.register("starlight_collector",
            () -> new NodeBlock(nodeProps(MapColor.COLOR_LIGHT_BLUE, 9), COLLECTOR_SHAPE, CollectorBlockEntity::new));
    public static final DeferredBlock<NodeBlock> RELAY_LENS = BLOCKS.register("relay_lens",
            () -> new NodeBlock(nodeProps(MapColor.COLOR_CYAN, 5), LENS_SHAPE, LensBlockEntity::new));
    public static final DeferredBlock<NodeBlock> SPLITTING_PRISM = BLOCKS.register("splitting_prism",
            () -> new NodeBlock(nodeProps(MapColor.COLOR_CYAN, 5), PRISM_SHAPE, PrismBlockEntity::new));
    public static final DeferredBlock<NodeBlock> STARLIGHT_CELL = BLOCKS.register("starlight_cell",
            () -> new NodeBlock(nodeProps(MapColor.COLOR_BLUE, 7), Shapes.block(), CellBlockEntity::new));
    public static final DeferredBlock<PedestalBlock> INFUSION_PEDESTAL = BLOCKS.register("infusion_pedestal",
            () -> new PedestalBlock(nodeProps(MapColor.QUARTZ, 4).sound(SoundType.STONE), PEDESTAL_SHAPE));

    // ---- Items ------------------------------------------------------------
    public static final DeferredItem<Item> LUMEN_SHARD = ITEMS.registerSimpleItem("lumen_shard");
    public static final DeferredItem<Item> CHARGED_LUMEN_SHARD = ITEMS.registerSimpleItem("charged_lumen_shard",
            new Item.Properties().rarity(Rarity.UNCOMMON));
    public static final DeferredItem<Item> POLISHED_LENS = ITEMS.registerSimpleItem("polished_lens");
    public static final DeferredItem<Item> STARLIT_INGOT = ITEMS.registerSimpleItem("starlit_ingot",
            new Item.Properties().rarity(Rarity.UNCOMMON));
    public static final DeferredItem<LinkingWandItem> LINKING_WAND = ITEMS.registerItem("linking_wand",
            LinkingWandItem::new, new Item.Properties().stacksTo(1));

    static {
        ITEMS.registerSimpleBlockItem(LUMEN_ORE);
        ITEMS.registerSimpleBlockItem(DEEPSLATE_LUMEN_ORE);
        ITEMS.registerSimpleBlockItem(STARLIGHT_COLLECTOR);
        ITEMS.registerSimpleBlockItem(RELAY_LENS);
        ITEMS.registerSimpleBlockItem(SPLITTING_PRISM);
        ITEMS.registerSimpleBlockItem(STARLIGHT_CELL);
        ITEMS.registerSimpleBlockItem(INFUSION_PEDESTAL);
    }

    // ---- Block entities ---------------------------------------------------
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CollectorBlockEntity>> COLLECTOR_BE =
            BLOCK_ENTITIES.register("starlight_collector", () -> BlockEntityType.Builder
                    .of(CollectorBlockEntity::new, STARLIGHT_COLLECTOR.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<LensBlockEntity>> LENS_BE =
            BLOCK_ENTITIES.register("relay_lens", () -> BlockEntityType.Builder
                    .of(LensBlockEntity::new, RELAY_LENS.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<PrismBlockEntity>> PRISM_BE =
            BLOCK_ENTITIES.register("splitting_prism", () -> BlockEntityType.Builder
                    .of(PrismBlockEntity::new, SPLITTING_PRISM.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CellBlockEntity>> CELL_BE =
            BLOCK_ENTITIES.register("starlight_cell", () -> BlockEntityType.Builder
                    .of(CellBlockEntity::new, STARLIGHT_CELL.get()).build(null));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<PedestalBlockEntity>> PEDESTAL_BE =
            BLOCK_ENTITIES.register("infusion_pedestal", () -> BlockEntityType.Builder
                    .of(PedestalBlockEntity::new, INFUSION_PEDESTAL.get()).build(null));

    // ---- Recipes ----------------------------------------------------------
    public static final DeferredHolder<RecipeType<?>, RecipeType<InfusionRecipe>> INFUSION_TYPE =
            RECIPE_TYPES.register("infusion",
                    () -> RecipeType.simple(ResourceLocation.fromNamespaceAndPath(MODID, "infusion")));
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<InfusionRecipe>> INFUSION_SERIALIZER =
            RECIPE_SERIALIZERS.register("infusion", InfusionRecipe.Serializer::new);

    // ---- Data components --------------------------------------------------
    /** Position of the node a linking wand is currently "holding" as beam source. */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<BlockPos>> LINK_SOURCE =
            DATA_COMPONENTS.registerComponentType("link_source",
                    builder -> builder.persistent(BlockPos.CODEC).networkSynchronized(BlockPos.STREAM_CODEC));

    // ---- Creative tab -----------------------------------------------------
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TAB = TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.lumina"))
                    .icon(() -> new ItemStack(STARLIGHT_COLLECTOR.get()))
                    .displayItems((params, out) -> {
                        out.accept(LINKING_WAND.get());
                        out.accept(STARLIGHT_COLLECTOR.get());
                        out.accept(RELAY_LENS.get());
                        out.accept(SPLITTING_PRISM.get());
                        out.accept(STARLIGHT_CELL.get());
                        out.accept(INFUSION_PEDESTAL.get());
                        out.accept(LUMEN_ORE.get());
                        out.accept(DEEPSLATE_LUMEN_ORE.get());
                        out.accept(LUMEN_SHARD.get());
                        out.accept(CHARGED_LUMEN_SHARD.get());
                        out.accept(POLISHED_LENS.get());
                        out.accept(STARLIT_INGOT.get());
                    })
                    .build());

    public Lumina(IEventBus modBus) {
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        BLOCK_ENTITIES.register(modBus);
        RECIPE_TYPES.register(modBus);
        RECIPE_SERIALIZERS.register(modBus);
        DATA_COMPONENTS.register(modBus);
        TABS.register(modBus);
        modBus.addListener(Lumina::registerCapabilities);
    }

    private static void registerCapabilities(RegisterCapabilitiesEvent event) {
        // Lets hoppers and pipes feed the pedestal and pull finished items out.
        event.registerBlockEntity(Capabilities.ItemHandler.BLOCK, PEDESTAL_BE.get(),
                (pedestal, side) -> pedestal.getItemHandler());
    }
}
