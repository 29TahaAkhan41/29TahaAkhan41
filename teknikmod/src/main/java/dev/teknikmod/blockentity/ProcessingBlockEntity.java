package dev.teknikmod.blockentity;

import dev.teknikmod.block.MachineBlock;
import dev.teknikmod.block.ProcessingBlock;
import dev.teknikmod.menu.ProcessingMenu;
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
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;

import javax.annotation.Nullable;

/** Tek giris, tek cikis yuvali; enerji harcayarak tarif isleyen makine. */
public abstract class ProcessingBlockEntity extends MachineBlockEntity implements MenuProvider {
    public static final int INPUT = 0, OUTPUT = 1, DATA_COUNT = 7;

    /** Giristeki esya icin bulunan is: uretilecek esya ve temel sure (tick). */
    public record Job(ItemStack output, int baseTime) {}

    private final ItemStackHandler items = new ItemStackHandler(2) {
        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return slot == INPUT;
        }

        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }
    };
    /** Huni/boru gibi otomasyon icin: yalnizca girise koyulur, yalnizca cikistan alinir. */
    private final IItemHandler automation = new IItemHandler() {
        @Override public int getSlots() { return items.getSlots(); }
        @Override public ItemStack getStackInSlot(int slot) { return items.getStackInSlot(slot); }
        @Override public ItemStack insertItem(int slot, ItemStack stack, boolean simulate) {
            return slot == INPUT ? items.insertItem(slot, stack, simulate) : stack;
        }
        @Override public ItemStack extractItem(int slot, int amount, boolean simulate) {
            return slot == OUTPUT ? items.extractItem(slot, amount, simulate) : ItemStack.EMPTY;
        }
        @Override public int getSlotLimit(int slot) { return items.getSlotLimit(slot); }
        @Override public boolean isItemValid(int slot, ItemStack stack) { return items.isItemValid(slot, stack); }
    };
    private final IEnergyStorage input = energy.inputOnly();
    private int progress;
    private int maxProgress;
    private int litTicks;

    /** Menuye senkronlanan veriler; enerji ve kapasite 16 bitlik iki parcaya bolunur. */
    public final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case 0 -> progress;
                case 1 -> maxProgress;
                case 2 -> energy.getEnergyStored() & 0xFFFF;
                case 3 -> energy.getEnergyStored() >>> 16;
                case 4 -> tier.machineCapacity & 0xFFFF;
                case 5 -> tier.machineCapacity >>> 16;
                case 6 -> tier.machineUse;
                default -> 0;
            };
        }

        @Override public void set(int i, int value) {}
        @Override public int getCount() { return DATA_COUNT; }
    };

    protected ProcessingBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state) {
        super(type, pos, state, MachineBlock.tierOf(state).machineCapacity, MachineBlock.tierOf(state).machineInput, 0);
    }

    /** Verilen giris icin tarif yoksa null. */
    @Nullable
    protected abstract Job findJob(Level level, ItemStack input);

    protected abstract MenuType<ProcessingMenu> menuType();

    public ItemStackHandler getItems() {
        return items;
    }

    public IItemHandler getAutomationItems(@Nullable Direction side) {
        return automation;
    }

    public IEnergyStorage getEnergy(@Nullable Direction side) {
        return input;
    }

    private boolean fitsOutput(ItemStack result) {
        ItemStack out = items.getStackInSlot(OUTPUT);
        return out.isEmpty() || (ItemStack.isSameItemSameComponents(out, result)
                && out.getCount() + result.getCount() <= out.getMaxStackSize());
    }

    @Override
    public void serverTick(Level level, BlockPos pos, BlockState state) {
        ItemStack in = items.getStackInSlot(INPUT);
        Job job = in.isEmpty() ? null : findJob(level, in);
        boolean running = false;
        if (job != null && !job.output().isEmpty() && fitsOutput(job.output())) {
            maxProgress = Math.max(1, job.baseTime() / tier.machineSpeed);
            if (tier.creative || energy.getEnergyStored() >= tier.machineUse) {
                if (!tier.creative) energy.setEnergy(energy.getEnergyStored() - tier.machineUse);
                running = true;
                if (++progress >= maxProgress) {
                    progress = 0;
                    items.extractItem(INPUT, 1, false);
                    ItemStack out = items.getStackInSlot(OUTPUT);
                    items.setStackInSlot(OUTPUT, out.isEmpty() ? job.output().copy()
                            : out.copyWithCount(out.getCount() + job.output().getCount()));
                }
                setChanged();
            }
        } else if (progress != 0 || maxProgress != 0) {
            progress = 0;
            maxProgress = 0;
            setChanged();
        }
        // Enerji yetersizken gorunumun her tick yanip sonmesini onlemek icin kisa bir bekleme payi.
        if (running) litTicks = 20;
        else if (litTicks > 0) litTicks--;
        boolean lit = litTicks > 0;
        if (state.getValue(ProcessingBlock.LIT) != lit) {
            level.setBlock(pos, state.setValue(ProcessingBlock.LIT, lit), 3);
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put("Items", items.serializeNBT(registries));
        tag.putInt("Progress", progress);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("Items")) items.deserializeNBT(registries, tag.getCompound("Items"));
        progress = tag.getInt("Progress");
    }

    @Override
    public Component getDisplayName() {
        return getBlockState().getBlock().getName();
    }

    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inv, Player player) {
        return new ProcessingMenu(menuType(), id, inv, this);
    }
}
