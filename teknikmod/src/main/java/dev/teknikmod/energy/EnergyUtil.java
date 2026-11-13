package dev.teknikmod.energy;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

public final class EnergyUtil {
    /** Depodaki enerjiyi verilen yonlerdeki komsulara iter. */
    public static void push(Level level, BlockPos pos, ModEnergyStorage storage, int maxPerTick, Direction... dirs) {
        int budget = Math.min(maxPerTick, storage.getEnergyStored());
        for (Direction dir : dirs) {
            if (budget <= 0) return;
            IEnergyStorage target = level.getCapability(Capabilities.EnergyStorage.BLOCK,
                    pos.relative(dir), dir.getOpposite());
            if (target == null || !target.canReceive()) continue;
            int sent = target.receiveEnergy(budget, false);
            if (sent > 0) {
                storage.setEnergy(storage.getEnergyStored() - sent);
                budget -= sent;
            }
        }
    }

    private EnergyUtil() {}
}
