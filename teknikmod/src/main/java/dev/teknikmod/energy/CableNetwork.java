package dev.teknikmod.energy;

import dev.teknikmod.block.CableBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Kablolar enerji depolamaz: bir kabloya verilen enerji, bagli kablo agindaki
 * tum alicilara aninda ve esit olarak dagitilir.
 */
public final class CableNetwork {
    public static final int MAX_CABLES = 4096;

    /** Bir kablo eklendiginde/kaldirildiginda veya komsusu degistiginde artar; onbellekleri gecersiz kilar. */
    private static int version;
    /** Ic ice dagitim derinligi; baska modlarin kablolariyla sonsuz donguyu onler. */
    private static final int MAX_DEPTH = 3;
    private static int depth;

    public record Sink(BlockPos pos, Direction side) {}

    public static void invalidate() {
        version++;
    }

    public static int version() {
        return version;
    }

    /** Baslangic kablosuna bagli agdaki, kablo olmayan tum block entity komsularini bulur. */
    public static List<Sink> scan(Level level, BlockPos start) {
        List<Sink> sinks = new ArrayList<>();
        Set<BlockPos> visited = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        visited.add(start);
        queue.add(start);
        while (!queue.isEmpty()) {
            BlockPos cable = queue.poll();
            for (Direction dir : Direction.values()) {
                BlockPos next = cable.relative(dir);
                if (!level.isLoaded(next)) continue;
                BlockState state = level.getBlockState(next);
                if (state.getBlock() instanceof CableBlock) {
                    if (visited.size() < MAX_CABLES && visited.add(next)) queue.add(next);
                } else if (state.hasBlockEntity()) {
                    sinks.add(new Sink(next, dir.getOpposite()));
                }
            }
        }
        return sinks;
    }

    /** Enerjiyi alicilara esit paylastirir; kabul edilen miktari dondurur. */
    public static int distribute(Level level, List<Sink> sinks, BlockPos source, int amount, boolean simulate) {
        if (depth >= MAX_DEPTH || amount <= 0) return 0;
        depth++;
        try {
            List<IEnergyStorage> targets = new ArrayList<>();
            for (Sink sink : sinks) {
                if (sink.pos().equals(source) || !level.isLoaded(sink.pos())) continue;
                IEnergyStorage storage = level.getCapability(Capabilities.EnergyStorage.BLOCK, sink.pos(), sink.side());
                if (storage != null && storage.canReceive()) targets.add(storage);
            }
            int remaining = amount;
            // Iki tur: ilk turda esit pay, ikinci turda dolu alicilardan artan enerji.
            for (int pass = 0; pass < 2 && remaining > 0; pass++) {
                for (int i = 0; i < targets.size() && remaining > 0; i++) {
                    int share = pass == 0 ? Math.max(1, remaining / (targets.size() - i)) : remaining;
                    remaining -= targets.get(i).receiveEnergy(Math.min(share, remaining), simulate);
                }
                if (simulate) break; // simulasyonda ayni aliciyi iki kez saymamak icin
            }
            return amount - remaining;
        } finally {
            depth--;
        }
    }

    private CableNetwork() {}
}
