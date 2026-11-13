package dev.teknikmod.blockentity;

import dev.teknikmod.block.MachineBlock;
import dev.teknikmod.ModRegistry;
import dev.teknikmod.energy.EnergyUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;

import javax.annotation.Nullable;

/** Gunduz, gokyuzunu goruyorsa enerji uretir; yagmurda uretim yariya duser. */
public class SolarPanelBlockEntity extends MachineBlockEntity {
    private static final Direction[] OUTPUTS = {Direction.DOWN, Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST};
    private final IEnergyStorage output = energy.outputOnly();

    public SolarPanelBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.SOLAR_PANEL_BE.get(), pos, state,
                MachineBlock.tierOf(state).solarCapacity, 0, MachineBlock.tierOf(state).solarOutput);
    }

    /** Ust yuzey panel oldugu icin oradan baglanti verilmez. */
    @Nullable
    public IEnergyStorage getEnergy(@Nullable Direction side) {
        return side == Direction.UP ? null : output;
    }

    private int currentRate(Level level, BlockPos pos) {
        if (tier.creative) return tier.solarRate;
        if (!level.dimensionType().hasSkyLight() || !level.isDay() || !level.canSeeSky(pos.above())) return 0;
        return level.isRaining() ? tier.solarRate / 2 : tier.solarRate;
    }

    @Override
    public void serverTick(Level level, BlockPos pos, BlockState state) {
        int rate = currentRate(level, pos);
        if (rate > 0) energy.generate(rate);
        EnergyUtil.push(level, pos, energy, tier.solarOutput, OUTPUTS);
    }
}
