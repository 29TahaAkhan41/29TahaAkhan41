package dev.teknikmod.menu;

import dev.teknikmod.block.ProcessingBlock;
import dev.teknikmod.blockentity.ProcessingBlockEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

/** Elektrikli firin ve ogutucunun ortak menusu: giris yuvasi, cikis yuvasi, oyuncu envanteri. */
public class ProcessingMenu extends AbstractContainerMenu {
    private final ContainerData data;
    private final ContainerLevelAccess access;

    /** Istemci tarafi. */
    public ProcessingMenu(MenuType<?> type, int id, Inventory inv) {
        this(type, id, inv, new ItemStackHandler(2), new SimpleContainerData(ProcessingBlockEntity.DATA_COUNT), ContainerLevelAccess.NULL);
    }

    /** Sunucu tarafi. */
    public ProcessingMenu(MenuType<?> type, int id, Inventory inv, ProcessingBlockEntity be) {
        this(type, id, inv, be.getItems(), be.data, ContainerLevelAccess.create(be.getLevel(), be.getBlockPos()));
    }

    private ProcessingMenu(MenuType<?> type, int id, Inventory inv, IItemHandler items, ContainerData data, ContainerLevelAccess access) {
        super(type, id);
        this.data = data;
        this.access = access;
        addSlot(new SlotItemHandler(items, ProcessingBlockEntity.INPUT, 53, 35));
        addSlot(new SlotItemHandler(items, ProcessingBlockEntity.OUTPUT, 107, 35) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                addSlot(new Slot(inv, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) addSlot(new Slot(inv, col, 8 + col * 18, 142));
        addDataSlots(data);
    }

    public int progress() { return data.get(0); }
    public int maxProgress() { return data.get(1); }
    public int energy() { return (data.get(2) & 0xFFFF) | (data.get(3) << 16); }
    public int maxEnergy() { return (data.get(4) & 0xFFFF) | (data.get(5) << 16); }
    public int usage() { return data.get(6); }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (index < 2) {
            if (!moveItemStackTo(stack, 2, 38, true)) return ItemStack.EMPTY;
        } else if (!moveItemStackTo(stack, 0, 1, false)) {
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) slot.setByPlayer(ItemStack.EMPTY);
        else slot.setChanged();
        slot.onTake(player, stack);
        return copy;
    }

    @Override
    public boolean stillValid(Player player) {
        return access.evaluate((level, pos) -> level.getBlockState(pos).getBlock() instanceof ProcessingBlock
                && player.distanceToSqr(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5) <= 64.0, true);
    }
}
