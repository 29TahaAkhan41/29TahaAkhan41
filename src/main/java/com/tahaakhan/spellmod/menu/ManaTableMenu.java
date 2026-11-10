package com.tahaakhan.spellmod.menu;

import com.tahaakhan.spellmod.block.ManaTableBlockEntity;
import com.tahaakhan.spellmod.registry.ModMenus;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

public class ManaTableMenu extends AbstractContainerMenu {
    public static final int BUTTON_REFINE = 0;
    public static final int INPUT_X = 35, INPUT_Y = 17;
    public static final int FUEL_X = 35, FUEL_Y = 53;
    public static final int OUTPUT_X = 125, OUTPUT_Y = 35;
    public static final int INVENTORY_X = 8, INVENTORY_Y = 84;

    private final Container table;
    private final ContainerData data;

    /** Client side: a stand-in container that the server fills in. */
    public ManaTableMenu(int containerId, Inventory inventory) {
        this(containerId, inventory, new SimpleContainer(ManaTableBlockEntity.SLOT_COUNT), new SimpleContainerData(ManaTableBlockEntity.DATA_COUNT));
    }

    public ManaTableMenu(int containerId, Inventory inventory, Container table, ContainerData data) {
        super(ModMenus.MANA_TABLE.get(), containerId);
        checkContainerSize(table, ManaTableBlockEntity.SLOT_COUNT);
        checkContainerDataCount(data, ManaTableBlockEntity.DATA_COUNT);
        this.table = table;
        this.data = data;

        addSlot(new Slot(table, ManaTableBlockEntity.SLOT_INPUT, INPUT_X, INPUT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return ManaTableBlockEntity.isInput(stack);
            }
        });
        addSlot(new Slot(table, ManaTableBlockEntity.SLOT_FUEL, FUEL_X, FUEL_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return ManaTableBlockEntity.isFuel(stack);
            }
        });
        addSlot(new Slot(table, ManaTableBlockEntity.SLOT_OUTPUT, OUTPUT_X, OUTPUT_Y) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });
        addStandardInventorySlots(inventory, INVENTORY_X, INVENTORY_Y);
        addDataSlots(data);
    }

    public boolean isRunning() {
        return data.get(ManaTableBlockEntity.DATA_RUNNING) != 0;
    }

    public int progress() {
        return data.get(ManaTableBlockEntity.DATA_PROGRESS);
    }

    public int total() {
        return data.get(ManaTableBlockEntity.DATA_TOTAL);
    }

    public int lossPermille() {
        return data.get(ManaTableBlockEntity.DATA_LOSS);
    }

    /** Whether pressing the button would do anything right now. */
    public boolean canStart() {
        ItemStack output = table.getItem(ManaTableBlockEntity.SLOT_OUTPUT);
        return !isRunning()
                && ManaTableBlockEntity.isInput(table.getItem(ManaTableBlockEntity.SLOT_INPUT))
                && ManaTableBlockEntity.isFuel(table.getItem(ManaTableBlockEntity.SLOT_FUEL))
                && output.getCount() < output.getMaxStackSize();
    }

    @Override
    public boolean clickMenuButton(Player player, int buttonId) {
        if (buttonId != BUTTON_REFINE) {
            return false;
        }
        if (table instanceof ManaTableBlockEntity blockEntity && player instanceof ServerPlayer serverPlayer) {
            return blockEntity.start(serverPlayer);
        }
        return canStart();
    }

    @Override
    public ItemStack quickMoveStack(Player player, int slotIndex) {
        Slot slot = slots.get(slotIndex);
        if (!slot.hasItem()) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();
        int tableSlots = ManaTableBlockEntity.SLOT_COUNT;
        if (slotIndex < tableSlots) {
            // Table -> player inventory.
            if (!moveItemStackTo(stack, tableSlots, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (ManaTableBlockEntity.isInput(stack)) {
            if (!moveItemStackTo(stack, ManaTableBlockEntity.SLOT_INPUT, ManaTableBlockEntity.SLOT_INPUT + 1, false)) {
                return ItemStack.EMPTY;
            }
        } else if (ManaTableBlockEntity.isFuel(stack)) {
            if (!moveItemStackTo(stack, ManaTableBlockEntity.SLOT_FUEL, ManaTableBlockEntity.SLOT_FUEL + 1, false)) {
                return ItemStack.EMPTY;
            }
        } else {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) {
            slot.setByPlayer(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        if (stack.getCount() == original.getCount()) {
            return ItemStack.EMPTY;
        }
        slot.onTake(player, stack);
        return original;
    }

    @Override
    public boolean stillValid(Player player) {
        return table.stillValid(player);
    }
}
