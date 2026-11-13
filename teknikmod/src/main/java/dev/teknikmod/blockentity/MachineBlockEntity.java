package dev.teknikmod.blockentity;

import dev.teknikmod.Tier;
import dev.teknikmod.block.MachineBlock;
import dev.teknikmod.energy.ModEnergyStorage;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

public abstract class MachineBlockEntity extends BlockEntity {
    protected final ModEnergyStorage energy;
    protected final Tier tier;

    protected MachineBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state,
                                 int capacity, int maxReceive, int maxExtract) {
        super(type, pos, state);
        this.tier = MachineBlock.tierOf(state);
        this.energy = new ModEnergyStorage(capacity, maxReceive, maxExtract, this::setChanged, MachineBlock.tierOf(state).creative,
                () -> level != null ? level.getGameTime() : 0L);
    }

    public ModEnergyStorage energy() {
        return energy;
    }

    public abstract void serverTick(Level level, BlockPos pos, BlockState state);

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("Energy", energy.getEnergyStored());
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        energy.setEnergy(tag.getInt("Energy"));
    }
}
