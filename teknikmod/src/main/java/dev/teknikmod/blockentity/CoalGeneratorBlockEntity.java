package dev.teknikmod.blockentity;

import dev.teknikmod.Config;
import dev.teknikmod.ModRegistry;
import dev.teknikmod.block.CoalGeneratorBlock;
import dev.teknikmod.energy.EnergyUtil;
import dev.teknikmod.menu.CoalGeneratorMenu;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.ItemStackHandler;

import javax.annotation.Nullable;

/** Firin yakitlarini yakarak enerji uretir. */
public class CoalGeneratorBlockEntity extends MachineBlockEntity implements MenuProvider {
    private final ItemStackHandler items = new ItemStackHandler(1) {
        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return stack.getBurnTime(RecipeType.SMELTING) > 0;
        }

        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }
    };
    private final IEnergyStorage output = energy.outputOnly();
    private int burnTime;
    private int burnTimeTotal;

    /** Menuye senkronlanan veriler; enerji 16 bitlik iki parcaya bolunur. */
    public final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case 0 -> burnTime;
                case 1 -> burnTimeTotal;
                case 2 -> energy.getEnergyStored() & 0xFFFF;
                case 3 -> energy.getEnergyStored() >>> 16;
                default -> 0;
            };
        }

        @Override public void set(int i, int value) {}
        @Override public int getCount() { return 4; }
    };

    public CoalGeneratorBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.COAL_GENERATOR_BE.get(), pos, state,
                Config.COAL_GENERATOR_CAPACITY, 0, Config.COAL_GENERATOR_OUTPUT);
    }

    public ItemStackHandler getItems() {
        return items;
    }

    public IEnergyStorage getEnergy(@Nullable Direction side) {
        return output;
    }

    @Override
    public void serverTick(Level level, BlockPos pos, BlockState state) {
        boolean wasLit = burnTime > 0;
        if (burnTime > 0) {
            burnTime--;
            energy.generate(Config.COAL_GENERATOR_RATE);
            setChanged();
        }
        // Yakit bittiyse ve depoda yer varsa yeni yakit yak.
        if (burnTime <= 0 && energy.getEnergyStored() + Config.COAL_GENERATOR_RATE <= energy.getMaxEnergyStored()) {
            ItemStack fuel = items.getStackInSlot(0);
            int time = fuel.getBurnTime(RecipeType.SMELTING);
            if (time > 0) {
                ItemStack remainder = fuel.getCraftingRemainingItem();
                fuel.shrink(1);
                if (fuel.isEmpty()) items.setStackInSlot(0, remainder); // or. lav kovasi -> bos kova
                burnTime = burnTimeTotal = time;
                setChanged();
            }
        }
        boolean lit = burnTime > 0;
        if (lit != wasLit) {
            level.setBlock(pos, state.setValue(CoalGeneratorBlock.LIT, lit), 3);
        }
        EnergyUtil.push(level, pos, energy, Config.COAL_GENERATOR_OUTPUT, Direction.values());
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put("Items", items.serializeNBT(registries));
        tag.putInt("BurnTime", burnTime);
        tag.putInt("BurnTimeTotal", burnTimeTotal);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("Items")) items.deserializeNBT(registries, tag.getCompound("Items"));
        burnTime = tag.getInt("BurnTime");
        burnTimeTotal = tag.getInt("BurnTimeTotal");
    }

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.teknikmod.coal_generator");
    }

    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inv, Player player) {
        return new CoalGeneratorMenu(id, inv, this);
    }
}
