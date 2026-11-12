package dev.lumina.test;

import dev.lumina.Lumina;
import dev.lumina.blockentity.CellBlockEntity;
import dev.lumina.blockentity.CollectorBlockEntity;
import dev.lumina.blockentity.PedestalBlockEntity;
import dev.lumina.blockentity.PrismBlockEntity;
import dev.lumina.blockentity.StarlightNodeBlockEntity;
import dev.lumina.starlight.LinkResult;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** In-world checks of the starlight mechanic, run with {@code ./gradlew runGameTestServer}. */
@GameTestHolder(Lumina.MODID)
@PrefixGameTestTemplate(false)
public class StarlightTests {
    private static final BlockPos LEFT = new BlockPos(1, 1, 2);
    private static final BlockPos MIDDLE = new BlockPos(4, 1, 2);
    private static final BlockPos RIGHT = new BlockPos(7, 1, 2);

    private static <T extends StarlightNodeBlockEntity> T node(GameTestHelper helper, BlockPos pos, Class<T> type) {
        if (type.isInstance(helper.getBlockEntity(pos))) {
            return type.cast(helper.getBlockEntity(pos));
        }
        helper.fail("Expected " + type.getSimpleName(), pos);
        throw new IllegalStateException();
    }

    private static void expectLink(GameTestHelper helper, StarlightNodeBlockEntity from, BlockPos to,
            LinkResult expected) {
        LinkResult actual = from.link(helper.absolutePos(to));
        helper.assertTrue(actual == expected, "Expected link result " + expected + " but got " + actual);
    }

    /** Night sky -> collector -> pedestal turns an iron ingot into a starlit ingot. */
    @GameTest(template = "empty", batch = "night", timeoutTicks = 900)
    public static void collectorInfusesItemAtNight(GameTestHelper helper) {
        helper.setDayTime(18000);
        helper.setBlock(LEFT, Lumina.STARLIGHT_COLLECTOR.get());
        helper.setBlock(RIGHT, Lumina.INFUSION_PEDESTAL.get());
        PedestalBlockEntity pedestal = node(helper, RIGHT, PedestalBlockEntity.class);
        pedestal.setItem(new ItemStack(Items.IRON_INGOT));
        expectLink(helper, node(helper, LEFT, CollectorBlockEntity.class), RIGHT, LinkResult.LINKED);
        helper.succeedWhen(() -> helper.assertTrue(pedestal.getItem().is(Lumina.STARLIT_INGOT.get()),
                "Iron ingot was not infused yet"));
    }

    /** Beams go through glass but an opaque block cuts them, both when linking and afterwards. */
    @GameTest(template = "empty", batch = "night", timeoutTicks = 200)
    public static void opaqueBlocksStopBeams(GameTestHelper helper) {
        helper.setBlock(LEFT, Lumina.STARLIGHT_CELL.get());
        helper.setBlock(RIGHT, Lumina.STARLIGHT_CELL.get());
        CellBlockEntity source = node(helper, LEFT, CellBlockEntity.class);
        CellBlockEntity sink = node(helper, RIGHT, CellBlockEntity.class);
        source.receive(5000.0F);

        helper.setBlock(MIDDLE, Blocks.STONE);
        expectLink(helper, source, RIGHT, LinkResult.NO_LINE_OF_SIGHT);
        helper.setBlock(MIDDLE, Blocks.GLASS);
        expectLink(helper, source, RIGHT, LinkResult.LINKED);
        expectLink(helper, sink, LEFT, LinkResult.WOULD_LOOP);

        helper.runAfterDelay(40, () -> {
            float throughGlass = sink.getStarlight();
            helper.assertTrue(throughGlass > 0.0F, "Starlight should pass through glass");
            helper.setBlock(MIDDLE, Blocks.STONE);
            helper.runAfterDelay(40, () -> {
                helper.assertTrue(sink.getStarlight() == throughGlass, "Stone should block the beam");
                helper.succeed();
            });
        });
    }

    /** A prism shares its light between its beams, and distance costs some of it. */
    @GameTest(template = "empty", batch = "night", timeoutTicks = 200)
    public static void prismSplitsEvenlyWithLoss(GameTestHelper helper) {
        BlockPos near = new BlockPos(4, 1, 0);
        BlockPos far = new BlockPos(4, 1, 4);
        helper.setBlock(MIDDLE, Lumina.SPLITTING_PRISM.get());
        helper.setBlock(near, Lumina.STARLIGHT_CELL.get());
        helper.setBlock(far, Lumina.STARLIGHT_CELL.get());
        PrismBlockEntity prism = node(helper, MIDDLE, PrismBlockEntity.class);
        CellBlockEntity first = node(helper, near, CellBlockEntity.class);
        CellBlockEntity second = node(helper, far, CellBlockEntity.class);
        prism.receive(400.0F);
        expectLink(helper, prism, near, LinkResult.LINKED);
        expectLink(helper, prism, far, LinkResult.LINKED);

        helper.runAfterDelay(100, () -> {
            helper.assertTrue(prism.getStarlight() == 0.0F, "Prism should have emptied itself");
            helper.assertTrue(Math.abs(first.getStarlight() - second.getStarlight()) < 0.01F,
                    "Both beams should carry the same amount");
            float delivered = first.getStarlight() + second.getStarlight();
            helper.assertTrue(Math.abs(delivered - 400.0F * 0.97F) < 0.5F,
                    "Two blocks of travel should cost 3%, delivered " + delivered);
            helper.succeed();
        });
    }

    /** No stars during the day, and none under a roof at night either. */
    @GameTest(template = "empty", batch = "day", timeoutTicks = 200)
    public static void collectorNeedsNightSky(GameTestHelper helper) {
        helper.setDayTime(6000);
        helper.setBlock(LEFT, Lumina.STARLIGHT_COLLECTOR.get());
        helper.setBlock(RIGHT, Lumina.STARLIGHT_COLLECTOR.get());
        helper.setBlock(RIGHT.above(2), Blocks.STONE);
        CollectorBlockEntity open = node(helper, LEFT, CollectorBlockEntity.class);
        CollectorBlockEntity roofed = node(helper, RIGHT, CollectorBlockEntity.class);

        helper.runAfterDelay(40, () -> {
            helper.assertTrue(open.getStarlight() == 0.0F, "Collector must not gather starlight by day");
            helper.setDayTime(18000);
            helper.runAfterDelay(40, () -> {
                helper.assertTrue(open.getStarlight() > 0.0F, "Collector should gather starlight at night");
                helper.assertTrue(roofed.getStarlight() == 0.0F, "A roofed collector must stay empty");
                helper.succeed();
            });
        });
    }
}
