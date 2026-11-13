package dev.teknikmod.blockentity;

import dev.teknikmod.block.MachineBlock;
import dev.teknikmod.ModRegistry;
import dev.teknikmod.TeknikMod;
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
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.ItemStackHandler;

import javax.annotation.Nullable;

/** Komur yakarak enerji uretir; kabul edilen yakitlar {@link #FUEL} etiketiyle belirlenir. */
public class CoalGeneratorBlockEntity extends MachineBlockEntity implements MenuProvider {
    /** Varsayilan: komur, odun komuru, komur blogu. Veri paketiyle degistirilebilir. */
    public static final TagKey<Item> FUEL = ItemTags.create(ResourceLocation.fromNamespaceAndPath(TeknikMod.MODID, "coal_generator_fuel"));

    public static boolean isFuel(ItemStack stack) {
        return stack.is(FUEL) && stack.getBurnTime(RecipeType.SMELTING) > 0;
    }

    private final ItemStackHandler items = new ItemStackHandler(1) {
        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return isFuel(stack);
        }

        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }
    };
    private final IEnergyStorage output = energy.outputOnly();
    public static final int DATA_COUNT = 8;
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
                case 4 -> tier.coalCapacity & 0xFFFF;
                case 5 -> tier.coalCapacity >>> 16;
                case 6 -> tier.coalRate & 0xFFFF;
                case 7 -> tier.coalRate >>> 16;
                default -> 0;
            };
        }

        @Override public void set(int i, int value) {}
        @Override public int getCount() { return DATA_COUNT; }
    };

    public CoalGeneratorBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.COAL_GENERATOR_BE.get(), pos, state,
                MachineBlock.tierOf(state).coalCapacity, 0, MachineBlock.tierOf(state).coalOutput);
    }

    public ItemStackHandler getItems() {
        return items;
    }

    public IEnergyStorage getEnergy(@Nullable Direction side) {
        return output;
    }

    @Override
    public void serverTick(Level level, BlockPos pos, BlockState state) {
        if (tier.creative) { // yakitsiz, surekli calisir
            burnTime = burnTimeTotal = 1;
            if (!state.getValue(CoalGeneratorBlock.LIT)) level.setBlock(pos, state.setValue(CoalGeneratorBlock.LIT, true), 3);
            EnergyUtil.push(level, pos, energy, tier.coalOutput, Direction.values());
            return;
        }
        boolean wasLit = burnTime > 0;
        if (burnTime > 0) {
            burnTime--;
            energy.generate(tier.coalRate);
            setChanged();
        }
        // Yakit bittiyse ve depoda yer varsa yeni yakit yak.
        if (burnTime <= 0 && energy.getEnergyStored() + tier.coalRate <= energy.getMaxEnergyStored()) {
            ItemStack fuel = items.getStackInSlot(0);
            int time = isFuel(fuel) ? fuel.getBurnTime(RecipeType.SMELTING) : 0;
            if (time > 0) {
                ItemStack remainder = fuel.getCraftingRemainingItem();
                fuel.shrink(1);
                if (fuel.isEmpty()) items.setStackInSlot(0, remainder);
                burnTime = burnTimeTotal = time;
                setChanged();
            }
        }
        boolean lit = burnTime > 0;
        if (lit != wasLit) {
            level.setBlock(pos, state.setValue(CoalGeneratorBlock.LIT, lit), 3);
        }
        EnergyUtil.push(level, pos, energy, tier.coalOutput, Direction.values());
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
        return getBlockState().getBlock().getName();
    }

    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inv, Player player) {
        return new CoalGeneratorMenu(id, inv, this);
    }
}
