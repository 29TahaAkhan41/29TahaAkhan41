package dev.teknikmod.blockentity;

import dev.teknikmod.block.MachineBlock;
import dev.teknikmod.ModRegistry;
import dev.teknikmod.block.BatteryBlock;
import dev.teknikmod.energy.EnergyUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;

import javax.annotation.Nullable;

public class BatteryBlockEntity extends MachineBlockEntity {
    private final IEnergyStorage input = energy.inputOnly();
    private final IEnergyStorage output = energy.outputOnly();

    public BatteryBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.BATTERY_BE.get(), pos, state,
                MachineBlock.tierOf(state).batteryCapacity, MachineBlock.tierOf(state).batteryIo, MachineBlock.tierOf(state).batteryIo);
    }

    public IEnergyStorage getEnergy(@Nullable Direction side) {
        if (side == null) return energy;
        return side == getBlockState().getValue(BatteryBlock.FACING) ? output : input;
    }

    @Override
    public void serverTick(Level level, BlockPos pos, BlockState state) {
        EnergyUtil.push(level, pos, energy, tier.batteryIo, state.getValue(BatteryBlock.FACING));
    }
}
