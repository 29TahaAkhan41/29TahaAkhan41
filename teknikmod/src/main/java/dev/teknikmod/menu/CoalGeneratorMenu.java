package dev.teknikmod.menu;

import dev.teknikmod.Config;
import dev.teknikmod.ModRegistry;
import dev.teknikmod.blockentity.CoalGeneratorBlockEntity;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

public class CoalGeneratorMenu extends AbstractContainerMenu {
    private final ContainerData data;
    private final ContainerLevelAccess access;

    /** Istemci tarafi. */
    public CoalGeneratorMenu(int id, Inventory inv, RegistryFriendlyByteBuf buf) {
        this(id, inv, new ItemStackHandler(1), new SimpleContainerData(4), ContainerLevelAccess.NULL);
    }

    /** Sunucu tarafi. */
    public CoalGeneratorMenu(int id, Inventory inv, CoalGeneratorBlockEntity be) {
        this(id, inv, be.getItems(), be.data, ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    private CoalGeneratorMenu(int id, Inventory inv, IItemHandler items, ContainerData data, ContainerLevelAccess access) {
        super(ModRegistry.COAL_GENERATOR_MENU.get(), id);
        this.data = data;
        this.access = access;
        addSlot(new SlotItemHandler(items, 0, 80, 44));
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                addSlot(new Slot(inv, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) addSlot(new Slot(inv, col, 8 + col * 18, 142));
        addDataSlots(data);
    }

    public int burnTime() { return data.get(0); }
    public int burnTimeTotal() { return data.get(1); }
    public int energy() { return (data.get(2) & 0xFFFF) | (data.get(3) << 16); }
    public int maxEnergy() { return Config.COAL_GENERATOR_CAPACITY; }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (index == 0) {
            if (!moveItemStackTo(stack, 1, 37, true)) return ItemStack.EMPTY;
        } else if (!moveItemStackTo(stack, 0, 1, false)) {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) slot.setByPlayer(ItemStack.EMPTY);
        else slot.setChanged();
        return copy;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, ModRegistry.COAL_GENERATOR.get());
    }
}
