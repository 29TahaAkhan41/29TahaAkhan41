package dev.teknikmod.blockentity;

import dev.teknikmod.ModRegistry;
import dev.teknikmod.block.CableBlock;
import dev.teknikmod.energy.CableNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;

import javax.annotation.Nullable;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** Enerji depolamaz; aldigi enerjiyi agdaki alicilara aktarir. Tick basina aktarim kablo kademesiyle sinirlidir. */
public class CableBlockEntity extends BlockEntity {
    private final Map<Direction, IEnergyStorage> sides = new EnumMap<>(Direction.class);
    private List<CableNetwork.Sink> sinks;
    private int sinksVersion = -1;
    private long lastTick = -1;
    private int usedThisTick;

    public CableBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.CABLE_BE.get(), pos, state);
        for (Direction d : Direction.values()) sides.put(d, new SideHandler(d));
    }

    @Nullable
    public IEnergyStorage getEnergy(@Nullable Direction side) {
        return side == null ? null : sides.get(side);
    }

    @Override
    public void onLoad() {
        super.onLoad();
        CableNetwork.invalidate(); // yeni yuklenen chunk agi genisletebilir
    }

    private int rate() {
        return getBlockState().getBlock() instanceof CableBlock cable ? cable.transferRate() : 0;
    }

    private int transfer(Direction from, int amount, boolean simulate) {
        if (level == null || level.isClientSide) return 0;
        long now = level.getGameTime();
        if (now != lastTick) {
            lastTick = now;
            usedThisTick = 0;
        }
        int allowed = Math.min(amount, rate() - usedThisTick);
        if (allowed <= 0) return 0;
        if (sinks == null || sinksVersion != CableNetwork.version()) {
            sinks = CableNetwork.scan(level, worldPosition);
            sinksVersion = CableNetwork.version();
        }
        int sent = CableNetwork.distribute(level, sinks, worldPosition.relative(from), allowed, simulate);
        if (!simulate) usedThisTick += sent;
        return sent;
    }

    private final class SideHandler implements IEnergyStorage {
        private final Direction side;

        SideHandler(Direction side) {
            this.side = side;
        }

        @Override public int receiveEnergy(int amount, boolean simulate) { return transfer(side, amount, simulate); }
        @Override public int extractEnergy(int amount, boolean simulate) { return 0; }
        @Override public int getEnergyStored() { return 0; }
        @Override public int getMaxEnergyStored() { return rate(); }
        @Override public boolean canExtract() { return false; }
        @Override public boolean canReceive() { return true; }
    }
}
